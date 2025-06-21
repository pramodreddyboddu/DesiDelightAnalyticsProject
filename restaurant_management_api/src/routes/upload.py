from flask import Blueprint, request, jsonify, g
from ..models import db, Item, Chef, ChefDishMapping, Sale, Expense, UncategorizedItem, FileUpload, Category, Tenant
from ..utils.auth import login_required, admin_required
import pandas as pd
import os
from datetime import datetime
from werkzeug.utils import secure_filename
import tempfile
import logging

upload_bp = Blueprint('upload', __name__)
logger = logging.getLogger(__name__)

UPLOAD_FOLDER = '/tmp/uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_upload_folder():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

@upload_bp.route('/sales', methods=['POST'])
@admin_required
def upload_sales():
    try:
        create_upload_folder()
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload CSV or Excel files.'}), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Create file upload record
        file_upload = FileUpload(
            filename=filename,
            file_type='sales',
            status='processing'
        )
        db.session.add(file_upload)
        db.session.commit()
        
        processed_records = 0
        failed_records = 0
        error_details = []
        
        try:
            # Read CSV file with different encodings
            encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(filepath, encoding=encoding)
                    print(f"Successfully read file with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    print(f"Error reading with {encoding}: {str(e)}")
                    continue
            
            if df is None:
                raise ValueError("Could not read the file with any supported encoding. Please ensure the file is a valid CSV.")
            
            total_records = len(df)
            
            # Process in batches to avoid memory issues
            batch_size = 1000
            for batch_start in range(0, total_records, batch_size):
                batch_end = min(batch_start + batch_size, total_records)
                batch_df = df.iloc[batch_start:batch_end]
                
                for index, row in batch_df.iterrows():
                    try:
                        # Start a new transaction for each row
                        db.session.begin_nested()
                        
                        # Parse date - handle timezone properly
                        date_str = row['Line Item Date']
                        if 'CDT' in date_str:
                            date_str = date_str.replace('CDT', '')  # Remove CDT timezone
                        line_item_date = pd.to_datetime(date_str)
                        
                        # Find or create item
                        item_name = row['Item Name']
                        item = Item.query.filter_by(name=item_name).first()
                        
                        if not item:
                            # Check if item is already in uncategorized list
                            uncategorized = UncategorizedItem.query.filter_by(item_name=item_name).first()
                            if uncategorized:
                                uncategorized.frequency += 1
                            else:
                                uncategorized = UncategorizedItem(item_name=item_name)
                                db.session.add(uncategorized)
                            
                            # Create a temporary item for the sale
                            try:
                                price = float(row.get('Item Revenue', 0.0))
                                if pd.isna(price) or price <= 0:
                                    price = 0.0  # Set a default price if invalid
                            except (ValueError, TypeError):
                                price = 0.0  # Set a default price if conversion fails
                                
                            item = Item(
                                clover_id=row.get('Item ID', f"MANUAL_{item_name}"),
                                name=item_name,
                                price=price,  # Use the validated price
                                category='Uncategorized',
                                is_active=False  # Mark as inactive until properly categorized
                            )
                            db.session.add(item)
                            db.session.flush()  # Get the ID
                        
                        # Generate a unique clover_id for the sale by combining Order ID, Item ID, timestamp, and sequence
                        order_id = row.get('Order ID', '')
                        item_id = row.get('Item ID', '')
                        timestamp = line_item_date.strftime('%Y%m%d%H%M%S')
                        
                        # Get the sequence number for this item in this order
                        sequence = 1
                        existing_sales = Sale.query.filter(
                            Sale.order_id == order_id,
                            Sale.item_id == item.id
                        ).count()
                        sequence = existing_sales + 1
                        
                        sale_clover_id = f"SALE_{order_id}_{item_id}_{timestamp}_{sequence}"
                        
                        # Validate numeric fields with more robust error handling
                        try:
                            quantity = float(row.get('Per Unit Quantity', 1.0)) if pd.notna(row.get('Per Unit Quantity')) else 1.0
                        except (ValueError, TypeError):
                            quantity = 1.0
                            
                        try:
                            item_revenue = float(row.get('Item Revenue', 0.0)) if pd.notna(row.get('Item Revenue')) else 0.0
                        except (ValueError, TypeError):
                            item_revenue = 0.0
                            
                        try:
                            modifiers_revenue = float(row.get('Modifiers Revenue', 0.0)) if pd.notna(row.get('Modifiers Revenue')) else 0.0
                        except (ValueError, TypeError):
                            modifiers_revenue = 0.0
                            
                        try:
                            total_revenue = float(row.get('Total Revenue', 0.0)) if pd.notna(row.get('Total Revenue')) else 0.0
                        except (ValueError, TypeError):
                            total_revenue = item_revenue + modifiers_revenue
                            
                        try:
                            discounts = float(row.get('Total Discount', 0.0)) if pd.notna(row.get('Total Discount')) else 0.0
                        except (ValueError, TypeError):
                            discounts = 0.0
                            
                        try:
                            tax_amount = float(row.get('Tax Amount', 0.0)) if pd.notna(row.get('Tax Amount')) else 0.0
                        except (ValueError, TypeError):
                            tax_amount = 0.0
                            
                        try:
                            item_total_with_tax = float(row.get('Item Total with Tax/Fee Amount', 0.0)) if pd.notna(row.get('Item Total with Tax/Fee Amount')) else 0.0
                        except (ValueError, TypeError):
                            item_total_with_tax = total_revenue + tax_amount
                        
                        # Create sale record
                        sale = Sale(
                            clover_id=sale_clover_id,
                            line_item_date=line_item_date,
                            order_employee_id=row.get('Order Employee ID'),
                            order_employee_name=row.get('Order Employee Name'),
                            item_id=item.id,
                            order_id=row.get('Order ID'),
                            quantity=quantity,
                            item_revenue=item_revenue,
                            modifiers_revenue=modifiers_revenue,
                            total_revenue=total_revenue,
                            discounts=discounts,
                            tax_amount=tax_amount,
                            item_total_with_tax=item_total_with_tax,
                            payment_state=row.get('Order Payment State')
                        )
                        db.session.add(sale)
                        processed_records += 1
                        
                        # Commit the nested transaction
                        db.session.commit()
                        
                    except Exception as e:
                        # Rollback the nested transaction
                        db.session.rollback()
                        error_msg = f"Error processing row {index}: {str(e)}"
                        print(error_msg)
                        print(f"Problematic row data: {row.to_dict()}")
                        error_details.append({
                            'row': index,
                            'error': str(e),
                            'data': row.to_dict()
                        })
                        failed_records += 1
                        continue
                
                # Commit batch
                db.session.commit()
            
            # Update file upload record
            file_upload.processed_records = processed_records
            file_upload.failed_records = failed_records
            file_upload.status = 'completed'
            file_upload.error_message = str(error_details) if error_details else None
            db.session.commit()
            
            return jsonify({
                'message': 'Sales data upload completed',
                'total_records': total_records,
                'processed_records': processed_records,
                'failed_records': failed_records,
                'file_id': file_upload.id,
                'error_details': error_details[:10] if error_details else None  # Return first 10 errors
            }), 200
            
        except Exception as e:
            db.session.rollback()
            file_upload.status = 'failed'
            file_upload.error_message = str(e)
            db.session.commit()
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
        
        finally:
            # Clean up uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@upload_bp.route('/inventory', methods=['POST'])
@admin_required
def upload_inventory():
    try:
        create_upload_folder()
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload CSV or Excel files.'}), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Create file upload record
        file_upload = FileUpload(
            filename=filename,
            file_type='inventory',
            status='processing'
        )
        db.session.add(file_upload)
        db.session.commit()
        
        processed_records = 0
        failed_records = 0
        
        try:
            # Read Excel file - try different sheet names
            df = None
            try:
                df = pd.read_excel(filepath, sheet_name='Items')
            except:
                try:
                    df = pd.read_excel(filepath, sheet_name=0)
                except:
                    df = pd.read_excel(filepath)
            
            for index, row in df.iterrows():
                try:
                    item_name = row.get('Name') or row.get('Item Name')
                    if pd.isna(item_name) or not item_name:
                        continue
                    
                    # Find existing item or create new one
                    item = Item.query.filter_by(name=item_name).first()
                    
                    if item:
                        # Update existing item
                        item.clover_id = row.get('Clover ID') or item.clover_id
                        item.alternate_name = row.get('Alternate Name') or item.alternate_name
                        item.description = row.get('Description') or item.description
                        
                        # Handle price conversion
                        price_value = row.get('Price')
                        if pd.notna(price_value):
                            try:
                                if isinstance(price_value, str):
                                    price_value = price_value.replace('$', '').strip()
                                item.price = float(price_value)
                            except (ValueError, TypeError):
                                pass  # Keep existing price if conversion fails
                        
                        item.price_type = row.get('Price Type') or item.price_type
                        item.price_unit = row.get('Price Unit') or item.price_unit
                        
                        # Handle cost conversion
                        cost_value = row.get('Cost')
                        if pd.notna(cost_value):
                            try:
                                if isinstance(cost_value, str):
                                    cost_value = cost_value.replace('$', '').strip()
                                item.cost = float(cost_value)
                            except (ValueError, TypeError):
                                pass  # Keep existing cost if conversion fails
                        
                        item.product_code = row.get('Product Code') or item.product_code
                        item.sku = row.get('SKU') or item.sku
                        item.quantity = int(row.get('Quantity', 0)) if pd.notna(row.get('Quantity')) else item.quantity
                        item.is_hidden = row.get('Hidden?', 'No').lower() == 'yes' if pd.notna(row.get('Hidden?')) else item.is_hidden
                        item.default_tax_rates = row.get('Default tax rates?', 'Yes').lower() == 'yes' if pd.notna(row.get('Default tax rates?')) else item.default_tax_rates
                        item.non_revenue_item = row.get('Non-revenue item?', 'No').lower() == 'yes' if pd.notna(row.get('Non-revenue item?')) else item.non_revenue_item
                        item.printer_labels = row.get('Printer Labels') or item.printer_labels
                        item.modifier_groups = row.get('Modifier Groups') or item.modifier_groups
                        item.category = row.get('Categories') or item.category
                        item.tax_rates = row.get('Tax Rates') or item.tax_rates
                        item.variant_attribute = row.get('Variant Attribute') or item.variant_attribute
                        item.variant_option = row.get('Variant Option') or item.variant_option
                        item.updated_at = datetime.utcnow()
                    else:
                        # Create new item
                        # Handle price conversion for new item
                        price_value = row.get('Price')
                        price = 0.0
                        if pd.notna(price_value):
                            try:
                                if isinstance(price_value, str):
                                    price_value = price_value.replace('$', '').strip()
                                price = float(price_value)
                            except (ValueError, TypeError):
                                pass
                        
                        # Handle cost conversion for new item
                        cost_value = row.get('Cost')
                        cost = 0.0
                        if pd.notna(cost_value):
                            try:
                                if isinstance(cost_value, str):
                                    cost_value = cost_value.replace('$', '').strip()
                                cost = float(cost_value)
                            except (ValueError, TypeError):
                                pass
                        
                        item = Item(
                            clover_id=row.get('Clover ID', f"MANUAL_{item_name}"),
                            name=item_name,
                            alternate_name=row.get('Alternate Name'),
                            description=row.get('Description'),
                            price=price,
                            price_type=row.get('Price Type'),
                            price_unit=row.get('Price Unit'),
                            cost=cost,
                            product_code=row.get('Product Code'),
                            sku=row.get('SKU'),
                            quantity=int(row.get('Quantity', 0)) if pd.notna(row.get('Quantity')) else 0,
                            is_hidden=row.get('Hidden?', 'No').lower() == 'yes' if pd.notna(row.get('Hidden?')) else False,
                            default_tax_rates=row.get('Default tax rates?', 'Yes').lower() == 'yes' if pd.notna(row.get('Default tax rates?')) else True,
                            non_revenue_item=row.get('Non-revenue item?', 'No').lower() == 'yes' if pd.notna(row.get('Non-revenue item?')) else False,
                            printer_labels=row.get('Printer Labels'),
                            modifier_groups=row.get('Modifier Groups'),
                            category=row.get('Categories', 'Uncategorized'),
                            tax_rates=row.get('Tax Rates'),
                            variant_attribute=row.get('Variant Attribute'),
                            variant_option=row.get('Variant Option')
                        )
                        db.session.add(item)
                    
                    processed_records += 1
                    
                except Exception as e:
                    print(f"Error processing row {index}: {str(e)}")
                    failed_records += 1
                    continue
            
            db.session.commit()
            
            # Update file upload record
            file_upload.processed_records = processed_records
            file_upload.failed_records = failed_records
            file_upload.status = 'completed'
            db.session.commit()
            
            return jsonify({
                'message': 'Inventory data uploaded successfully',
                'processed_records': processed_records,
                'failed_records': failed_records,
                'file_id': file_upload.id
            }), 200
            
        except Exception as e:
            file_upload.status = 'failed'
            file_upload.error_message = str(e)
            db.session.commit()
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
        
        finally:
            # Clean up uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@upload_bp.route('/chef-mapping', methods=['POST'])
@admin_required
def upload_chef_mapping():
    try:
        create_upload_folder()
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload CSV or Excel files.'}), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Create file upload record
        file_upload = FileUpload(
            filename=filename,
            file_type='chef_mapping',
            status='processing'
        )
        db.session.add(file_upload)
        db.session.commit()
        
        processed_records = 0
        failed_records = 0
        error_details = []
        
        try:
            # Try reading as Excel first
            try:
                df = pd.read_excel(filepath)
                print("Successfully read as Excel file")
                print("Columns found:", df.columns.tolist())
                print("First few rows:", df.head().to_dict('records'))
                
                # Clean column names by stripping spaces
                df.columns = [col.strip() for col in df.columns]
                print("Columns after cleaning:", df.columns.tolist())
                
            except Exception as e:
                print(f"Failed to read as Excel: {str(e)}")
                # If Excel fails, try CSV/TSV with different encodings
                encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1', 'utf-16']
                separators = [',', '\t']  # Try both comma and tab
                df = None
                successful_encoding = None
                successful_separator = None
                
                for encoding in encodings:
                    for separator in separators:
                        try:
                            # Try reading with different parameters
                            try:
                                df = pd.read_csv(filepath, encoding=encoding, sep=separator)
                            except:
                                # If that fails, try with different parameters
                                df = pd.read_csv(filepath, encoding=encoding, sep=separator, on_bad_lines='skip')
                            
                            # Verify we can read the data and map columns
                            if not df.empty:
                                # Clean column names by stripping spaces
                                df.columns = [col.strip() for col in df.columns]
                                print("Original columns:", df.columns.tolist())
                                
                                # Map column names (case-insensitive)
                                column_mapping = {
                                    'clover id': 'Clover ID',
                                    'item name': 'Item Name',
                                    'category': 'Category',
                                    'chef name': 'Chef Name'
                                }
                                
                                for old_col, new_col in column_mapping.items():
                                    if old_col.lower() in [col.lower() for col in df.columns]:
                                        df = df.rename(columns={old_col: new_col})
                                
                                print("Columns after mapping:", df.columns.tolist())
                                
                                # Verify required columns exist
                                if 'Item Name' in df.columns and 'Chef Name' in df.columns:
                                    successful_encoding = encoding
                                    successful_separator = separator
                                    print(f"Successfully read file with {encoding} encoding and {separator} separator")
                                    break
                        except Exception as e:
                            print(f"Failed to read with {encoding} and {separator}: {str(e)}")
                            continue
                    if successful_encoding:
                        break
            
            if df is None:
                raise ValueError("Could not read the file. Please ensure the file is a valid Excel (.xlsx) or CSV/TSV file with 'Item Name' and 'Chef Name' columns.")
            
            # Clean the data
            df['Item Name'] = df['Item Name'].str.strip()
            df['Chef Name'] = df['Chef Name'].str.strip()
            if 'Category' in df.columns:
                df['Category'] = df['Category'].str.strip()
            
            # Remove any rows with empty values
            df = df.dropna(subset=['Item Name', 'Chef Name'])
            
            total_records = len(df)
            print(f"Total records to process: {total_records}")
            
            # Process in batches to avoid memory issues
            batch_size = 1000
            for batch_start in range(0, total_records, batch_size):
                batch_end = min(batch_start + batch_size, total_records)
                batch_df = df.iloc[batch_start:batch_end]
                
                for index, row in batch_df.iterrows():
                    try:
                        # Start a new transaction for each row
                        db.session.begin_nested()
                        
                        # Get item and chef details
                        item_name = row['Item Name']
                        chef_name = row['Chef Name']
                        
                        # Find the item
                        item = Item.query.filter_by(name=item_name).first()
                        if not item:
                            raise ValueError(f"Item not found: {item_name}")
                        
                        # Find or create the chef
                        chef = Chef.query.filter_by(name=chef_name).first()
                        if not chef:
                            # Generate a unique clover_id for the chef
                            chef_clover_id = f"CHEF_{chef_name.upper().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                            chef = Chef(
                                name=chef_name,
                                clover_id=chef_clover_id,
                                is_active=True
                            )
                            db.session.add(chef)
                            db.session.flush()
                        
                        # Create or update the chef mapping
                        chef_mapping = ChefDishMapping.query.filter_by(item_id=item.id).first()
                        if chef_mapping:
                            chef_mapping.chef_id = chef.id
                        else:
                            chef_mapping = ChefDishMapping(
                                item_id=item.id,
                                chef_id=chef.id
                            )
                            db.session.add(chef_mapping)
                        
                        processed_records += 1
                        
                        # Commit the nested transaction
                        db.session.commit()
                        
                    except Exception as e:
                        # Rollback the nested transaction
                        db.session.rollback()
                        error_msg = f"Error processing row {index}: {str(e)}"
                        print(error_msg)
                        print(f"Problematic row data: {row.to_dict()}")
                        error_details.append({
                            'row': index,
                            'error': str(e),
                            'data': row.to_dict()
                        })
                        failed_records += 1
                        continue
                
                # Commit batch
                db.session.commit()
                print(f"Processed batch {batch_start//batch_size + 1}, total processed: {processed_records}")
            
            # Update file upload record
            file_upload.processed_records = processed_records
            file_upload.failed_records = failed_records
            file_upload.status = 'completed'
            file_upload.error_message = str(error_details) if error_details else None
            db.session.commit()
            
            return jsonify({
                'message': 'Chef mapping upload completed',
                'total_records': total_records,
                'processed_records': processed_records,
                'failed_records': failed_records,
                'file_id': file_upload.id,
                'error_details': error_details[:10] if error_details else None  # Return first 10 errors
            }), 200
            
        except Exception as e:
            db.session.rollback()
            file_upload.status = 'failed'
            file_upload.error_message = str(e)
            db.session.commit()
            print(f"Error processing file: {str(e)}")
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
        
        finally:
            # Clean up uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@upload_bp.route('/expenses', methods=['POST'])
@admin_required
def upload_expenses():
    try:
        create_upload_folder()
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload CSV or Excel files.'}), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Create file upload record
        file_upload = FileUpload(
            filename=filename,
            file_type='expenses',
            status='processing'
        )
        db.session.add(file_upload)
        db.session.commit()
        
        processed_records = 0
        failed_records = 0
        error_details = []
        
        try:
            # Try reading as Excel first
            try:
                df = pd.read_excel(filepath)
                print("Successfully read as Excel file")
                print("Columns found:", df.columns.tolist())
                print("First few rows:", df.head().to_dict('records'))
                
                # Clean column names by stripping spaces
                df.columns = [col.strip() for col in df.columns]
                print("Columns after cleaning:", df.columns.tolist())
                
            except Exception as e:
                print(f"Failed to read as Excel: {str(e)}")
                # If Excel fails, try CSV/TSV with different encodings
                encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1', 'utf-16']
                separators = [',', '\t']  # Try both comma and tab
                df = None
                successful_encoding = None
                successful_separator = None
                
                for encoding in encodings:
                    for separator in separators:
                        try:
                            # Try reading with different parameters
                            try:
                                df = pd.read_csv(filepath, encoding=encoding, sep=separator)
                            except:
                                # If that fails, try with different parameters
                                df = pd.read_csv(filepath, encoding=encoding, sep=separator, on_bad_lines='skip')
                            
                            # Verify we can read the data and map columns
                            if not df.empty:
                                # Clean column names by stripping spaces
                                df.columns = [col.strip() for col in df.columns]
                                print("Original columns:", df.columns.tolist())
                                
                                # Map column names (case-insensitive)
                                column_mapping = {
                                    'date': 'Date',
                                    'vendor': 'Vendor',
                                    'amount': 'Amount',
                                    'invoice': 'Invoice',
                                    'category': 'Category'
                                }
                                
                                for old_col, new_col in column_mapping.items():
                                    if old_col.lower() in [col.lower() for col in df.columns]:
                                        df = df.rename(columns={old_col: new_col})
                                
                                print("Columns after mapping:", df.columns.tolist())
                                
                                # Verify required columns exist
                                if 'Date' in df.columns and 'Amount' in df.columns and 'Category' in df.columns:
                                    successful_encoding = encoding
                                    successful_separator = separator
                                    print(f"Successfully read file with {encoding} encoding and {separator} separator")
                                    break
                        except Exception as e:
                            print(f"Failed to read with {encoding} and {separator}: {str(e)}")
                            continue
                    if successful_encoding:
                        break
            
            if df is None:
                raise ValueError("Could not read the file. Please ensure the file is a valid Excel (.xlsx) or CSV/TSV file with 'Date', 'Amount', and 'Category' columns.")
            
            # Clean the data
            try:
                print("Sample date values before parsing:", df['Date'].head().tolist())
                
                # Try different date formats
                date_formats = [
                    '%d-%b-%y',  # 01-May-25
                    '%d-%b-%Y',  # 01-May-2025
                    '%d/%b/%y',  # 01/May/25
                    '%d/%b/%Y',  # 01/May/2025
                    '%Y-%m-%d',  # 2025-05-01
                    '%d-%m-%Y',  # 01-05-2025
                    '%d/%m/%Y'   # 01/05/2025
                ]
                
                for date_format in date_formats:
                    try:
                        df['Date'] = pd.to_datetime(df['Date'], format=date_format, errors='coerce')
                        if not df['Date'].isna().all():  # If any dates were successfully parsed
                            print(f"Successfully parsed dates with format: {date_format}")
                            break
                    except:
                        continue
                
                if df['Date'].isna().all():  # If all dates are still NaT
                    print("Falling back to default date parser")
                    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                
                print("Sample date values after parsing:", df['Date'].head().tolist())
                
            except Exception as e:
                print(f"Error parsing dates: {str(e)}")
                raise
            
            try:
                df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
                print("Sample amount values:", df['Amount'].head().tolist())
            except Exception as e:
                print(f"Error parsing amounts: {str(e)}")
                raise
            
            try:
                df['Category'] = df['Category'].str.strip()
                if 'Vendor' in df.columns:
                    df['Vendor'] = df['Vendor'].str.strip()
                if 'Invoice' in df.columns:
                    df['Invoice'] = df['Invoice'].str.strip()
                print("Sample category values:", df['Category'].head().tolist())
            except Exception as e:
                print(f"Error cleaning text fields: {str(e)}")
                raise
            
            # Remove any rows with empty values
            df = df.dropna(subset=['Date', 'Amount', 'Category'])
            print(f"Rows after removing empty values: {len(df)}")
            
            # Print sample of processed data for debugging
            print("Sample of processed data:")
            print(df.head().to_dict('records'))
            
            total_records = len(df)
            print(f"Total records to process: {total_records}")
            
            # Process in batches to avoid memory issues
            batch_size = 1000
            for batch_start in range(0, total_records, batch_size):
                batch_end = min(batch_start + batch_size, total_records)
                batch_df = df.iloc[batch_start:batch_end]
                
                for index, row in batch_df.iterrows():
                    try:
                        # Start a new transaction for each row
                        db.session.begin_nested()
                        
                        # Create expense record
                        expense = Expense(
                            date=row['Date'],
                            amount=float(row['Amount']),
                            category=row['Category'],
                            vendor=row.get('Vendor', ''),
                            invoice=row.get('Invoice', ''),
                            is_active=True
                        )
                        db.session.add(expense)
                        
                        processed_records += 1
                        
                        # Commit the nested transaction
                        db.session.commit()
                        
                    except Exception as e:
                        # Rollback the nested transaction
                        db.session.rollback()
                        error_msg = f"Error processing row {index}: {str(e)}"
                        print(error_msg)
                        print(f"Problematic row data: {row.to_dict()}")
                        error_details.append({
                            'row': index,
                            'error': str(e),
                            'data': row.to_dict()
                        })
                        failed_records += 1
                        continue
                
                # Commit batch
                db.session.commit()
                print(f"Processed batch {batch_start//batch_size + 1}, total processed: {processed_records}")
            
            # Update file upload record
            file_upload.processed_records = processed_records
            file_upload.failed_records = failed_records
            file_upload.status = 'completed'
            file_upload.error_message = str(error_details) if error_details else None
            db.session.commit()
            
            return jsonify({
                'message': 'Expenses upload completed',
                'total_records': total_records,
                'processed_records': processed_records,
                'failed_records': failed_records,
                'file_id': file_upload.id,
                'error_details': error_details[:10] if error_details else None  # Return first 10 errors
            }), 200
            
        except Exception as e:
            db.session.rollback()
            file_upload.status = 'failed'
            file_upload.error_message = str(e)
            db.session.commit()
            print(f"Error processing file: {str(e)}")
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
        
        finally:
            # Clean up uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@upload_bp.route('/status/<int:file_id>', methods=['GET'])
@login_required
def get_upload_status(file_id):
    try:
        file_upload = FileUpload.query.get(file_id)
        if not file_upload:
            return jsonify({'error': 'File upload not found'}), 404
        
        return jsonify(file_upload.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@upload_bp.route('/tenant-data', methods=['POST'])
@admin_required
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

        tenant_id = g.user.tenant_id
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

