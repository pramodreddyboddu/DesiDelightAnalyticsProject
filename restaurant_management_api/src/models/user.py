from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class User(db.Model):
    __tablename__ = 'user'
    __table_args__ = {'extend_existing': True}  # Allow table redefinition
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    role = db.Column(db.String(20), default='user')
    is_admin = db.Column(db.Boolean, default=False)
    
    # Multi-tenant support (nullable for backward compatibility)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        tenant_info = None
        if self.tenant:
            tenant_info = {
                'id': self.tenant.id,
                'name': self.tenant.name
            }
            
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'is_admin': self.is_admin,
            'tenant_id': self.tenant_id,
            'tenant': tenant_info,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def is_super_admin(self):
        """Check if user is a super admin (system-wide admin)"""
        return self.is_admin and self.tenant_id is None
    
    @property
    def is_tenant_admin(self):
        """Check if user is a tenant admin"""
        return self.is_admin and self.tenant_id is not None

