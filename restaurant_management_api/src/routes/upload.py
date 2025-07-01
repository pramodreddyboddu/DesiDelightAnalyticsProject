from flask import Blueprint, request, jsonify, g
from ..models import db, Item, Chef, ChefDishMapping, Sale, Expense, UncategorizedItem, FileUpload, Category, Tenant
from ..utils.auth import tenant_admin_required
import pandas as pd
import os
from datetime import datetime
from werkzeug.utils import secure_filename
import tempfile
import logging
import re
import hashlib
import uuid

upload_bp = Blueprint('upload', __name__)
logger = logging.getLogger(__name__)

UPLOAD_FOLDER = '/tmp/uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_upload_folder():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

def clean_column_names(df):
    """Cleans DataFrame column names to make them predictable."""
    cleaned_columns = []
    for col in df.columns:
        name = col.lower().strip()
        name = re.sub(r'[^a-z0-9_]+', '_', name)
        name = re.sub(r'__+', '_', name)
        name = name.strip('_')
        cleaned_columns.append(name)
    df.columns = cleaned_columns
    logger.info(f"Cleaned column names: {df.columns.tolist()}")

def generate_short_clover_id(prefix, name, tenant_id, index):
    """Generate a shorter, more reliable clover_id"""
    # Create a hash of the name and tenant_id
    hash_input = f"{name}_{tenant_id}_{index}".encode('utf-8')
    hash_result = hashlib.md5(hash_input).hexdigest()[:12]  # Use first 12 chars of MD5
    return f"{prefix}_{hash_result}"

@upload_bp.route('/sales', methods=['POST'])
@tenant_admin_required
def upload_sales():
    tenant_id = request.tenant_id
    create_upload_folder()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid or no file selected'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    file_upload = FileUpload(filename=filename, file_type='sales', status='processing')
    db.session.add(file_upload)
    db.session.commit()

    processed_records, failed_records, error_details = 0, 0, []
    
    try:
        df = pd.read_csv(filepath, encoding='utf-8')
        total_records = len(df)
        logger.info(f"Processing {total_records} sales records for tenant {tenant_id}")
        
        # Process in batches to improve performance
        batch_size = 100
        sales_to_add = []
        
        for index, row in df.iterrows():
            try:
                date_str = row.get('Line Item Date', '')
                if pd.isna(date_str) or not date_str:
                    continue
                    
                line_item_date = pd.to_datetime(date_str.replace('CDT', '').strip())

                item_name = row.get('Item Name')
                if pd.isna(item_name) or not item_name:
                    continue
                    
                # Check if item exists by name first
                item = Item.query.filter_by(name=item_name, tenant_id=tenant_id).first()
                if not item:
                    # Create new item with a unique clover_id and commit immediately
                    price = float(row.get('Item Revenue', 0.0)) if not pd.isna(row.get('Item Revenue')) else 0.0
                    # Generate shorter unique clover_id for item
                    unique_clover_id = generate_short_clover_id("ITEM", item_name, tenant_id, index)
                    item = Item(
                        name=item_name, 
                        price=price, 
                        category='Uncategorized', 
                        is_active=False, 
                        tenant_id=tenant_id,
                        clover_id=unique_clover_id
                    )
                    db.session.add(item)
                    db.session.commit()  # Commit immediately to get item.id
                    logger.info(f"Created new item: {item_name} with ID: {item.id}")

                # Create sale record with unique clover_id
                quantity = float(row.get('Per Unit Quantity', 1.0)) if not pd.isna(row.get('Per Unit Quantity')) else 1.0
                total_revenue = float(row.get('Total Revenue', 0.0)) if not pd.isna(row.get('Total Revenue')) else 0.0
                item_revenue = float(row.get('Item Revenue', 0.0)) if not pd.isna(row.get('Item Revenue')) else 0.0
                
                # Generate shorter unique clover_id for sale
                sale_clover_id = generate_short_clover_id("SALE", f"{row.get('Order ID', 'NO_ORDER')}_{index}", tenant_id, index)
                
                sale = Sale(
                    clover_id=sale_clover_id,
                    line_item_date=line_item_date,
                    item_id=item.id,  # Now item.id will be available
                    quantity=quantity,
                    item_revenue=item_revenue,
                    total_revenue=total_revenue,
                    item_total_with_tax=total_revenue,  # Use total_revenue as item_total_with_tax
                    tenant_id=tenant_id,
                    order_id=row.get('Order ID', None)
                )
                sales_to_add.append(sale)
                processed_records += 1
                
                # Commit sales in batches
                if len(sales_to_add) >= batch_size:
                    try:
                        db.session.add_all(sales_to_add)
                        db.session.commit()
                        sales_to_add = []
                        logger.info(f"Processed {processed_records} records so far...")
                    except Exception as batch_error:
                        db.session.rollback()
                        logger.error(f"Batch commit failed: {batch_error}")
                        # Continue processing but mark these as failed
                        failed_records += len(sales_to_add)
                        error_details.append({'batch_error': str(batch_error)})
                        sales_to_add = []
                    
            except Exception as e:
                failed_records += 1
                error_details.append({'row': index, 'error': str(e), 'data': row.to_dict()})
                logger.error(f"Error processing row {index}: {e}")
                # Rollback the session to clear any pending changes
                try:
                    db.session.rollback()
                except:
                    pass
        
        # Commit any remaining sales records
        if sales_to_add:
            try:
                db.session.add_all(sales_to_add)
                db.session.commit()
            except Exception as final_error:
                db.session.rollback()
                logger.error(f"Final batch commit failed: {final_error}")
                failed_records += len(sales_to_add)
                error_details.append({'final_batch_error': str(final_error)})
        
        file_upload.status = 'completed'
        file_upload.processed_records = processed_records
        file_upload.failed_records = failed_records
        db.session.commit()

        logger.info(f"Sales upload completed: {processed_records} processed, {failed_records} failed")
        return jsonify({
            'message': 'Sales data processed',
            'processed_records': processed_records,
            'failed_records': failed_records,
            'errors': error_details[:10]
        }), 200

    except Exception as e:
        logger.error(f"Sales upload failed: {e}")
        file_upload.status = 'failed'
        file_upload.error_message = str(e)
        db.session.commit()
        return jsonify({'error': f'File processing failed: {str(e)}'}), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

@upload_bp.route('/inventory', methods=['POST'])
@tenant_admin_required
def upload_inventory():
    tenant_id = request.tenant_id
    create_upload_folder()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'No selected file or file type not allowed'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    try:
        # Read the 'Items' sheet specifically
        df_peek = pd.read_excel(filepath, sheet_name='Items', header=None)
        header_row_index = -1
        for i, row in df_peek.head(10).iterrows():
            # Look for the header row containing 'Name' (case-insensitive)
            if any(str(cell).strip().lower() == 'name' for cell in row):
                header_row_index = i
                break

        if header_row_index == -1:
            logger.warning(f"Inventory upload for tenant {tenant_id} failed. Could not find a header row containing 'Name'.")
            return jsonify({'error': "Upload failed. Could not find the header row. Please ensure the 'Items' sheet has a column for 'Name'."}), 400

        # Now, read the file again with the correct header
        df = pd.read_excel(filepath, sheet_name='Items', header=header_row_index)
        clean_column_names(df)
        logger.info(f"Tenant {tenant_id} inventory upload: Cleaned column names are {df.columns.tolist()}")

        if 'name' not in df.columns:
            logger.warning(f"Inventory upload failed for tenant {tenant_id}. Missing 'name' column. Found: {df.columns.tolist()}")
            return jsonify({'error': "Upload failed. The file must contain a column for 'Name'."}), 400
            
        processed_count = 0
        for _, row in df.iterrows():
            item_name = row.get('name')
            if not item_name:
                continue # Skip rows with no item name

            # Find existing item or create a new one
            item = Item.query.filter_by(name=item_name, tenant_id=tenant_id).first()
            if not item:
                item = Item(name=item_name, tenant_id=tenant_id)
            
            # Update item attributes
            item.clover_id = row.get('clover_id', item.clover_id)
            item.category = row.get('categories', item.category)
            # Handle price safely
            price = row.get('price', item.price if item.price is not None else 0)
            if pd.isna(price):
                price = 0
            item.price = float(price)
            # Handle quantity safely
            quantity = row.get('quantity', item.quantity if item.quantity is not None else 0)
            if pd.isna(quantity):
                quantity = 0
            item.quantity = int(quantity)
            
            db.session.add(item)
            processed_count += 1
        
        db.session.commit()
        
    except Exception as e:
        logger.error(f"Error processing inventory file for tenant {tenant_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'An error occurred while processing the file.', 'details': str(e)}), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
            
    return jsonify({'message': f'Inventory updated successfully. {processed_count} items processed.'})

@upload_bp.route('/chef-mapping', methods=['POST'])
@tenant_admin_required
def upload_chef_mapping():
    tenant_id = request.tenant_id
    create_upload_folder()

    try:
        if 'file' not in request.files:
            logger.error(f"Chef mapping upload failed: No file provided")
            return jsonify({'error': 'No file part'}), 400
        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename):
            logger.error(f"Chef mapping upload failed: Invalid file - filename: {file.filename}")
            return jsonify({'error': 'No selected file or file type not allowed'}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        logger.info(f"Processing chef mapping file: {filename} for tenant {tenant_id}")
        file.save(filepath)
        logger.info(f"File saved to: {filepath}")

        # Try to read the Excel or CSV file
        try:
            if filename.lower().endswith('.csv'):
                df = pd.read_csv(filepath)
            else:
                df = pd.read_excel(filepath)
            logger.info(f"Successfully read file with {len(df)} rows and columns: {df.columns.tolist()}")
        except Exception as e:
            logger.error(f"Failed to read file: {str(e)}")
            return jsonify({'error': f'Failed to read file: {str(e)}'}), 500

        clean_column_names(df)
        logger.info(f"After cleaning, columns are: {df.columns.tolist()}")

        if 'chef_name' not in df.columns or 'item_name' not in df.columns:
            logger.error(f"Chef mapping upload failed for tenant {tenant_id}. Missing columns. Found: {df.columns.tolist()}")
            return jsonify({'error': "Upload failed. The file must contain columns for 'Chef Name' and 'Item Name'."}), 400

        mappings_created = 0
        mappings_updated = 0
        items_not_found = 0
        errors = []
        for index, row in df.iterrows():
            try:
                chef_name = row.get('chef_name')
                item_name = row.get('item_name')
                clover_item_id = row.get('clover_id') if 'clover_id' in row else None
                logger.debug(f"Row {index}: chef_name='{chef_name}', item_name='{item_name}', clover_id='{clover_item_id}'")
                # Skip rows with NaN or empty values
                if pd.isna(chef_name) or pd.isna(item_name) or not chef_name or not item_name:
                    logger.warning(f"Skipping row {index}: chef_name='{chef_name}', item_name='{item_name}' (empty or NaN)")
                    continue
                chef_name_clean = chef_name.strip().lower()
                item_name_clean = item_name.strip().lower()
                # Find or create chef (case-insensitive)
                chef = Chef.query.filter(db.func.lower(Chef.name) == chef_name_clean, Chef.tenant_id == tenant_id).first()
                if not chef:
                    chef_clover_id = f"CHEF_{chef_name_clean}_{tenant_id[:8]}_{index}_{int(datetime.now().timestamp())}"
                    chef = Chef(name=chef_name, tenant_id=tenant_id, clover_id=chef_clover_id)
                    db.session.add(chef)
                    db.session.flush()
                    logger.info(f"Created new chef: {chef_name} with ID: {chef.id}")
                # Find item (prefer clover_id, fallback to name) - DO NOT CREATE NEW ITEMS
                item = None
                if clover_item_id and not pd.isna(clover_item_id):
                    logger.debug(f"Looking up item by clover_id='{clover_item_id}' for tenant_id='{tenant_id}'")
                    item = Item.query.filter_by(clover_id=str(clover_item_id), tenant_id=tenant_id).first()
                    if item:
                        logger.info(f"Found item by clover_id: {clover_item_id} -> {item.name}")
                    else:
                        logger.warning(f"No item found by clover_id: {clover_item_id} for tenant_id={tenant_id}")
                if not item:
                    logger.debug(f"Looking up item by name='{item_name_clean}' for tenant_id='{tenant_id}'")
                    item = Item.query.filter(db.func.lower(Item.name) == item_name_clean, Item.tenant_id == tenant_id).first()
                    if item:
                        logger.info(f"Found item by name: {item_name}")
                    else:
                        logger.warning(f"No item found by name: {item_name_clean} for tenant_id={tenant_id}")
                if not item:
                    # Item not found - skip this mapping and log it
                    items_not_found += 1
                    logger.warning(f"Item not found for mapping: {item_name} (clover_id: {clover_item_id}) - skipping")
                    continue
                # Always update or create the mapping
                mapping = ChefDishMapping.query.filter_by(chef_id=chef.id, item_id=item.id, tenant_id=tenant_id).first()
                if not mapping:
                    mapping = ChefDishMapping(chef_id=chef.id, item_id=item.id, tenant_id=tenant_id)
                    db.session.add(mapping)
                    mappings_created += 1
                    logger.info(f"Created mapping: {chef_name} -> {item_name}")
                else:
                    mapping.is_active = True
                    mappings_updated += 1
                    logger.info(f"Updated mapping: {chef_name} -> {item_name}")
            except Exception as e:
                error_msg = f"Error processing row {index}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue
        try:
            db.session.commit()
            logger.info(f"Successfully committed {mappings_created} new and {mappings_updated} updated chef-dish mappings")
        except Exception as e:
            logger.error(f"Database commit failed: {str(e)}")
            db.session.rollback()
            return jsonify({'error': f'Database error: {str(e)}'}), 500
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Cleaned up temporary file: {filepath}")
        return jsonify({
            'message': f'{mappings_created} new and {mappings_updated} updated chef-dish mappings successfully. {items_not_found} items not found.',
            'errors': errors[:5] if errors else []
        })
    except Exception as e:
        logger.error(f"Unexpected error in chef mapping upload: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@upload_bp.route('/expenses', methods=['POST'])
@tenant_admin_required
def upload_expenses():
    tenant_id = request.tenant_id
    create_upload_folder()

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'No selected file or file type not allowed'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    df = pd.read_excel(filepath)
    clean_column_names(df)
    
    # Check for required columns - date, amount, category are mandatory
    required_cols = ['date', 'amount', 'category']
    if not all(col in df.columns for col in required_cols):
        logger.warning(f"Expenses upload failed for tenant {tenant_id}. Missing required columns. Found: {df.columns.tolist()}")
        return jsonify({'error': f"Upload failed. The file must contain columns for: {', '.join(required_cols)}"}), 400

    # Check for description column - if not present, try to use vendor or invoice
    description_col = None
    if 'description' in df.columns:
        description_col = 'description'
    elif 'vendor' in df.columns:
        description_col = 'vendor'
    elif 'invoice' in df.columns:
        description_col = 'invoice'
    else:
        logger.warning(f"Expenses upload failed for tenant {tenant_id}. No description column found. Available columns: {df.columns.tolist()}")
        return jsonify({'error': "Upload failed. The file must contain a column for description, vendor, or invoice."}), 400

    expenses_added = 0
    for index, row in df.iterrows():
        try:
            # Handle missing or NaN values
            if pd.isna(row['date']) or pd.isna(row['amount']) or pd.isna(row['category']):
                logger.warning(f"Skipping row {index}: missing required data")
                continue
                
            # Create description from available columns
            description_parts = []
            if not pd.isna(row.get(description_col)):
                description_parts.append(str(row[description_col]))
            if 'vendor' in df.columns and not pd.isna(row.get('vendor')) and description_col != 'vendor':
                description_parts.append(f"Vendor: {row['vendor']}")
            if 'invoice' in df.columns and not pd.isna(row.get('invoice')) and description_col != 'invoice':
                description_parts.append(f"Invoice: {row['invoice']}")
            
            description = ' | '.join(description_parts) if description_parts else 'No description'
            
            expense = Expense(
                date=pd.to_datetime(row['date']),
                description=description,
                amount=float(row['amount']),
                category=row['category'],
                tenant_id=tenant_id
            )
            db.session.add(expense)
            expenses_added += 1
        except Exception as e:
            logger.error(f"Could not process expense row {index}: {row.to_dict()}. Error: {e}")
            continue

    db.session.commit()

    if os.path.exists(filepath):
        os.remove(filepath)

    return jsonify({'message': f'{expenses_added} expenses added successfully.'})

@upload_bp.route('/status/<int:file_id>', methods=['GET'])
@tenant_admin_required
def get_upload_status(file_id):
    try:
        file_upload = FileUpload.query.get(file_id)
        if not file_upload:
            return jsonify({'error': 'File upload not found'}), 404
        
        return jsonify(file_upload.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@upload_bp.route('/tenant-data', methods=['POST'])
@tenant_admin_required
def upload_tenant_data():
    """Uploads data for a specific tenant."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400

        tenant_id = request.tenant_id
        if not tenant_id:
            return jsonify({'error': 'User is not associated with a tenant'}), 403

        filename = secure_filename(file.filename)
        # Use a temporary directory for file storage
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = os.path.join(temp_dir, filename)
            file.save(filepath)

            # For now, we only support 'items' from CSV
            # Future implementation could check request.form['data_type']
            try:
                df = pd.read_csv(filepath)
            except Exception as e:
                logger.error(f"Tenant {tenant_id} failed to upload data. Error reading CSV: {str(e)}")
                return jsonify({'error': f'Could not read CSV file: {str(e)}'}), 400

            required_columns = ['name', 'category_name', 'price', 'quantity']
            if not all(col in df.columns for col in required_columns):
                return jsonify({'error': f'CSV must have the following columns: {", ".join(required_columns)}'}), 400

            processed_count = 0
            failed_rows = []

            for index, row in df.iterrows():
                try:
                    category_name = row['category_name'].strip()
                    item_name = row['name'].strip()
                    price = float(row['price'])
                    quantity = int(row['quantity'])

                    # Find or create category for this tenant
                    category = Category.query.filter_by(name=category_name, tenant_id=tenant_id).first()
                    if not category:
                        category = Category(name=category_name, tenant_id=tenant_id)
                        db.session.add(category)
                        db.session.flush() # To get category.id for the item

                    # Find or create item for this tenant
                    item = Item.query.filter_by(name=item_name, tenant_id=tenant_id).first()
                    if not item:
                        item = Item(
                            name=item_name,
                            price=price,
                            quantity=quantity,
                            category_id=category.id,
                            tenant_id=tenant_id
                        )
                        db.session.add(item)
                    else:
                        # Update existing item
                        item.price = price
                        item.quantity = quantity
                        item.category_id = category.id
                        item.tenant_id = tenant_id
                    
                    processed_count += 1

                except Exception as e:
                    db.session.rollback()
                    failed_rows.append({'row': index + 2, 'error': str(e)})
                    logger.warning(f"Tenant {tenant_id} data upload: Failed to process row {index + 2}. Error: {str(e)}")
                    continue
            
            db.session.commit()

            if failed_rows:
                 return jsonify({
                    'message': f'Upload partially completed for tenant {tenant_id}',
                    'processed_count': processed_count,
                    'failed_count': len(failed_rows),
                    'errors': failed_rows
                }), 207
            
            return jsonify({
                'message': f'Successfully uploaded and processed {processed_count} items for tenant {tenant_id}'
            }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Tenant data upload failed for user {g.user.id}. Error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

