from flask import Blueprint, request, jsonify
from src.models.user import db, Item, Chef, ChefDishMapping, Sale, Expense, UncategorizedItem, FileUpload
from src.routes.auth import login_required, admin_required
import pandas as pd
import os
from datetime import datetime
from werkzeug.utils import secure_filename
import tempfile

upload_bp = Blueprint('upload', __name__)

UPLOAD_FOLDER = '/tmp/uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_upload_folder():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

@upload_bp.route('/upload/sales', methods=['POST'])
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
        
        # Process the file
        processed_records = 0
        failed_records = 0
        
        try:
            # Read CSV file
            df = pd.read_csv(filepath)
            
            for index, row in df.iterrows():
                try:
                    # Parse date
                    line_item_date = pd.to_datetime(row['Line Item Date'])
                    
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
                        
                        # Create item with uncategorized status
                        item = Item(
                            clover_id=row.get('Item ID'),
                            name=item_name,
                            sku=row.get('Item SKU'),
                            product_code=str(row.get('Item Product Code')) if pd.notna(row.get('Item Product Code')) else None,
                            category='Uncategorized'
                        )
                        db.session.add(item)
                        db.session.flush()  # Get the ID
                    
                    # Create sale record
                    sale = Sale(
                        line_item_date=line_item_date,
                        order_employee_id=row.get('Order Employee ID'),
                        order_employee_name=row.get('Order Employee Name'),
                        item_id=item.id,
                        order_id=row.get('Order ID'),
                        quantity=float(row.get('Per Unit Quantity', 1.0)) if pd.notna(row.get('Per Unit Quantity')) else 1.0,
                        item_revenue=float(row.get('Item Revenue', 0.0)),
                        modifiers_revenue=float(row.get('Modifiers Revenue', 0.0)) if pd.notna(row.get('Modifiers Revenue')) else 0.0,
                        total_revenue=float(row.get('Total Revenue', 0.0)),
                        discounts=float(row.get('Total Discount', 0.0)),
                        tax_amount=float(row.get('Tax Amount', 0.0)),
                        item_total_with_tax=float(row.get('Item Total with Tax/Fee Amount', 0.0)),
                        payment_state=row.get('Order Payment State')
                    )
                    db.session.add(sale)
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
                'message': 'Sales data uploaded successfully',
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

@upload_bp.route('/upload/inventory', methods=['POST'])
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
                        item.sku = row.get('SKU') or item.sku
                        item.product_code = row.get('Product Code') or item.product_code
                        item.category = row.get('Category') or item.category
                        item.updated_at = datetime.utcnow()
                    else:
                        # Create new item
                        item = Item(
                            name=item_name,
                            sku=row.get('SKU'),
                            product_code=row.get('Product Code'),
                            category=row.get('Category', 'Uncategorized')
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

@upload_bp.route('/upload/chef-mapping', methods=['POST'])
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
        
        try:
            # Read Excel file
            df = pd.read_excel(filepath)
            
            for index, row in df.iterrows():
                try:
                    chef_name = row.get('Chef Name')
                    item_name = row.get('Item Name')
                    
                    if pd.isna(chef_name) or pd.isna(item_name):
                        continue
                    
                    # Find or create chef
                    chef = Chef.query.filter_by(name=chef_name).first()
                    if not chef:
                        chef = Chef(
                            name=chef_name,
                            clover_id=row.get('Clover ID')
                        )
                        db.session.add(chef)
                        db.session.flush()
                    
                    # Find or create item
                    item = Item.query.filter_by(name=item_name).first()
                    if not item:
                        item = Item(
                            name=item_name,
                            clover_id=row.get('Clover ID'),
                            category=row.get('Category', 'Uncategorized')
                        )
                        db.session.add(item)
                        db.session.flush()
                    
                    # Create or update mapping
                    mapping = ChefDishMapping.query.filter_by(chef_id=chef.id, item_id=item.id).first()
                    if not mapping:
                        mapping = ChefDishMapping(chef_id=chef.id, item_id=item.id)
                        db.session.add(mapping)
                    
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
                'message': 'Chef mapping data uploaded successfully',
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

@upload_bp.route('/upload/expenses', methods=['POST'])
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
        
        try:
            # Read Excel file
            df = pd.read_excel(filepath)
            
            for index, row in df.iterrows():
                try:
                    date = pd.to_datetime(row['Date']).date()
                    vendor = row['Vendor']
                    amount = float(row['Amount'])
                    invoice = row.get('Invoice', '')
                    
                    # Create expense record
                    expense = Expense(
                        date=date,
                        vendor=vendor,
                        amount=amount,
                        invoice=invoice,
                        category='Kitchen'  # Default category, can be updated later
                    )
                    db.session.add(expense)
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
                'message': 'Expenses data uploaded successfully',
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

@upload_bp.route('/upload/status/<int:file_id>', methods=['GET'])
@login_required
def get_upload_status(file_id):
    try:
        file_upload = FileUpload.query.get(file_id)
        if not file_upload:
            return jsonify({'error': 'File upload not found'}), 404
        
        return jsonify(file_upload.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

