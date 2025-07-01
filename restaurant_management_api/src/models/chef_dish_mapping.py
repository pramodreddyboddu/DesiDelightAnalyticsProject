from datetime import datetime
from . import db

class ChefDishMapping(db.Model):
    __tablename__ = 'chef_dish_mapping'
    __table_args__ = (
        db.UniqueConstraint('chef_id', 'item_id', name='unique_chef_dish'),
        {'extend_existing': True}  # Allow table redefinition
    )

    id = db.Column(db.Integer, primary_key=True)
    chef_id = db.Column(db.Integer, db.ForeignKey('chef.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=True)
    
    # Add tenant_id for multi-tenancy
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=True)

    # New columns for robust mapping
    clover_id = db.Column(db.String(32), nullable=True, index=True)
    item_name = db.Column(db.String(128), nullable=True)

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    chef = db.relationship('Chef', back_populates='dish_mappings')
    item = db.relationship('Item', back_populates='chef_mappings')

    def to_dict(self):
        return {
            'id': self.id,
            'chef_id': self.chef_id,
            'item_id': self.item_id,
            'clover_id': self.clover_id,
            'item_name': self.item_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<ChefDishMapping {self.id}>' 