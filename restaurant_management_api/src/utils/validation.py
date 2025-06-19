from marshmallow import Schema, fields, validate, ValidationError
from flask import request, jsonify
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Base validation schemas
class LoginSchema(Schema):
    """Schema for login validation."""
    username = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    password = fields.Str(required=True, validate=validate.Length(min=1, max=100))

class DateRangeSchema(Schema):
    """Schema for date range validation."""
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)

class PaginationSchema(Schema):
    """Schema for pagination parameters."""
    page = fields.Int(validate=validate.Range(min=1), load_default=1)
    per_page = fields.Int(validate=validate.Range(min=1, max=100), load_default=20)

class FileUploadSchema(Schema):
    """Schema for file upload validation."""
    file_type = fields.Str(required=True, validate=validate.OneOf(['sales', 'inventory', 'chef-mapping', 'expenses']))

class ItemSchema(Schema):
    """Schema for item validation."""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    sku = fields.Str(validate=validate.Length(max=50))
    product_code = fields.Str(validate=validate.Length(max=50))
    category = fields.Str(validate=validate.Length(max=100))
    is_active = fields.Bool(load_default=True)

class ExpenseSchema(Schema):
    """Schema for expense validation."""
    date = fields.Date(required=True)
    vendor = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    amount = fields.Decimal(required=True, validate=validate.Range(min=0))
    invoice = fields.Str(validate=validate.Length(max=100))
    category = fields.Str(validate=validate.Length(max=100))
    description = fields.Str(validate=validate.Length(max=500))

class SaleSchema(Schema):
    """Schema for sale validation."""
    line_item_date = fields.DateTime(required=True)
    order_employee_id = fields.Str(validate=validate.Length(max=50))
    order_employee_name = fields.Str(validate=validate.Length(max=100))
    item_id = fields.Int(required=True)
    order_id = fields.Str(required=True, validate=validate.Length(max=50))
    quantity = fields.Int(required=True, validate=validate.Range(min=1))
    item_revenue = fields.Decimal(required=True, validate=validate.Range(min=0))
    modifiers_revenue = fields.Decimal(validate=validate.Range(min=0), load_default=0)
    total_revenue = fields.Decimal(required=True, validate=validate.Range(min=0))
    discounts = fields.Decimal(validate=validate.Range(min=0), load_default=0)
    tax_amount = fields.Decimal(validate=validate.Range(min=0), load_default=0)
    item_total_with_tax = fields.Decimal(required=True, validate=validate.Range(min=0))
    payment_state = fields.Str(validate=validate.Length(max=50))

def validate_request_data(schema_class):
    """Decorator to validate request data using Marshmallow schemas."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                schema = schema_class()
                
                # Validate based on request method
                if request.method == 'GET':
                    data = request.args.to_dict()
                else:
                    if request.is_json:
                        data = request.get_json()
                    else:
                        data = request.form.to_dict()
                
                # Validate data
                validated_data = schema.load(data)
                
                # Add validated data to request context
                request.validated_data = validated_data
                
                return f(*args, **kwargs)
                
            except ValidationError as e:
                logger.warning(f"Validation error: {e.messages}")
                return jsonify({
                    'error': 'Validation failed',
                    'details': e.messages
                }), 400
            except Exception as e:
                logger.error(f"Unexpected error during validation: {str(e)}")
                return jsonify({
                    'error': 'Internal server error during validation'
                }), 500
                
        return decorated_function
    return decorator

def validate_file_upload():
    """Decorator to validate file uploads."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Check if file is present
                if 'file' not in request.files:
                    return jsonify({'error': 'No file provided'}), 400
                
                file = request.files['file']
                
                # Check if file is empty
                if file.filename == '':
                    return jsonify({'error': 'No file selected'}), 400
                
                # Check file extension
                allowed_extensions = {'csv', 'xlsx', 'xls'}
                if not file.filename.lower().endswith(tuple('.' + ext for ext in allowed_extensions)):
                    return jsonify({'error': 'Invalid file type. Allowed: CSV, XLSX, XLS'}), 400
                
                # Check file size (16MB limit)
                file.seek(0, 2)  # Seek to end
                file_size = file.tell()
                file.seek(0)  # Reset to beginning
                
                if file_size > 16 * 1024 * 1024:  # 16MB
                    return jsonify({'error': 'File too large. Maximum size: 16MB'}), 400
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"File validation error: {str(e)}")
                return jsonify({'error': 'File validation failed'}), 500
                
        return decorated_function
    return decorator

def sanitize_input(data):
    """Sanitize input data to prevent XSS and injection attacks."""
    if isinstance(data, str):
        # Basic XSS prevention
        data = data.replace('<script>', '').replace('</script>', '')
        data = data.replace('javascript:', '')
        return data.strip()
    elif isinstance(data, dict):
        return {key: sanitize_input(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    else:
        return data

def validate_date_range(start_date, end_date):
    """Validate that start_date is before end_date."""
    if start_date and end_date and start_date > end_date:
        raise ValidationError("Start date must be before end date")
    return True

def validate_pagination(page, per_page):
    """Validate pagination parameters."""
    if page < 1:
        raise ValidationError("Page must be greater than 0")
    if per_page < 1 or per_page > 100:
        raise ValidationError("Per page must be between 1 and 100")
    return True 