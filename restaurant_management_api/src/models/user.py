from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)  # 'admin' or 'user'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    clover_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(255), nullable=False)
    sku = db.Column(db.String(100))
    product_code = db.Column(db.String(100))
    category = db.Column(db.String(50), default='Uncategorized')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sales = db.relationship('Sale', backref='item', lazy=True)
    chef_mappings = db.relationship('ChefDishMapping', backref='item', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'clover_id': self.clover_id,
            'name': self.name,
            'sku': self.sku,
            'product_code': self.product_code,
            'category': self.category,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Chef(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    clover_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    dish_mappings = db.relationship('ChefDishMapping', backref='chef', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'clover_id': self.clover_id,
            'name': self.name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ChefDishMapping(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chef_id = db.Column(db.Integer, db.ForeignKey('chef.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Unique constraint to prevent duplicate mappings
    __table_args__ = (db.UniqueConstraint('chef_id', 'item_id', name='unique_chef_item'),)

    def to_dict(self):
        return {
            'id': self.id,
            'chef_id': self.chef_id,
            'item_id': self.item_id,
            'chef_name': self.chef.name if self.chef else None,
            'item_name': self.item.name if self.item else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    line_item_date = db.Column(db.DateTime, nullable=False)
    order_employee_id = db.Column(db.String(50))
    order_employee_name = db.Column(db.String(100))
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    order_id = db.Column(db.String(50))
    quantity = db.Column(db.Float, default=1.0)
    item_revenue = db.Column(db.Float, default=0.0)
    modifiers_revenue = db.Column(db.Float, default=0.0)
    total_revenue = db.Column(db.Float, default=0.0)
    discounts = db.Column(db.Float, default=0.0)
    tax_amount = db.Column(db.Float, default=0.0)
    item_total_with_tax = db.Column(db.Float, default=0.0)
    payment_state = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'line_item_date': self.line_item_date.isoformat() if self.line_item_date else None,
            'order_employee_id': self.order_employee_id,
            'order_employee_name': self.order_employee_name,
            'item_id': self.item_id,
            'item_name': self.item.name if self.item else None,
            'order_id': self.order_id,
            'quantity': self.quantity,
            'item_revenue': self.item_revenue,
            'modifiers_revenue': self.modifiers_revenue,
            'total_revenue': self.total_revenue,
            'discounts': self.discounts,
            'tax_amount': self.tax_amount,
            'item_total_with_tax': self.item_total_with_tax,
            'payment_state': self.payment_state,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    vendor = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    invoice = db.Column(db.String(100))
    category = db.Column(db.String(50), default='Kitchen')
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'vendor': self.vendor,
            'amount': self.amount,
            'invoice': self.invoice,
            'category': self.category,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class UncategorizedItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(255), nullable=False)
    frequency = db.Column(db.Integer, default=1)
    suggested_category = db.Column(db.String(50))
    status = db.Column(db.String(20), default='pending')  # 'pending', 'categorized', 'ignored'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'item_name': self.item_name,
            'frequency': self.frequency,
            'suggested_category': self.suggested_category,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class FileUpload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # 'sales', 'inventory', 'chef_mapping', 'expenses'
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    processed_records = db.Column(db.Integer, default=0)
    failed_records = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='processing')  # 'processing', 'completed', 'failed'
    error_message = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'file_type': self.file_type,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'processed_records': self.processed_records,
            'failed_records': self.failed_records,
            'status': self.status,
            'error_message': self.error_message
        }

