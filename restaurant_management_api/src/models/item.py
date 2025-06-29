from datetime import datetime
from . import db

class Item(db.Model):
    __tablename__ = 'item'
    __table_args__ = {'extend_existing': True}  # Allow table redefinition

    id = db.Column(db.Integer, primary_key=True)
    clover_id = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    alternate_name = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False, default=0.0)
    price_type = db.Column(db.String(50), nullable=True)
    price_unit = db.Column(db.String(50), nullable=True)
    cost = db.Column(db.Float, nullable=True, default=0.0)
    product_code = db.Column(db.String(50), nullable=True)
    sku = db.Column(db.String(50), nullable=True)
    quantity = db.Column(db.Integer, default=0, nullable=False)
    reorder_point = db.Column(db.Integer, default=10, nullable=False)
    is_hidden = db.Column(db.Boolean, nullable=False, default=False)
    default_tax_rates = db.Column(db.Boolean, nullable=False, default=True)
    non_revenue_item = db.Column(db.Boolean, nullable=False, default=False)
    printer_labels = db.Column(db.String(100), nullable=True)
    modifier_groups = db.Column(db.String(100), nullable=True)
    category = db.Column(db.String(50), nullable=True, default='Uncategorized')
    tax_rates = db.Column(db.String(100), nullable=True)
    variant_attribute = db.Column(db.String(100), nullable=True)
    variant_option = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Add tenant_id for multi-tenancy
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=True)

    # Relationships
    sales = db.relationship('Sale', back_populates='item', lazy=True, cascade="all, delete-orphan")
    chef_mappings = db.relationship('ChefDishMapping', back_populates='item', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'clover_id': self.clover_id,
            'name': self.name,
            'alternate_name': self.alternate_name,
            'description': self.description,
            'price': self.price,
            'price_type': self.price_type,
            'price_unit': self.price_unit,
            'cost': self.cost,
            'product_code': self.product_code,
            'sku': self.sku,
            'quantity': self.quantity,
            'reorder_point': self.reorder_point,
            'is_hidden': self.is_hidden,
            'default_tax_rates': self.default_tax_rates,
            'non_revenue_item': self.non_revenue_item,
            'printer_labels': self.printer_labels,
            'modifier_groups': self.modifier_groups,
            'category': self.category,
            'tax_rates': self.tax_rates,
            'variant_attribute': self.variant_attribute,
            'variant_option': self.variant_option,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<Item {self.name}>' 