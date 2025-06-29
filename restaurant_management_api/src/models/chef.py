from datetime import datetime
from . import db

class Chef(db.Model):
    __tablename__ = 'chef'
    __table_args__ = {'extend_existing': True}  # Allow table redefinition

    id = db.Column(db.Integer, primary_key=True)
    clover_id = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    dish_mappings = db.relationship('ChefDishMapping', back_populates='chef', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'clover_id': self.clover_id,
            'name': self.name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 