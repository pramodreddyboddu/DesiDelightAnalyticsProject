from src.models import db
from datetime import datetime
import uuid

class Tenant(db.Model):
    """Tenant model for multi-tenant SaaS architecture"""
    __tablename__ = 'tenants'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    business_type = db.Column(db.String(100), nullable=False)  # restaurant, food_truck, cafe, etc.
    contact_email = db.Column(db.String(255), nullable=False, unique=True)
    contact_phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100), default='US')
    postal_code = db.Column(db.String(20))
    
    # Subscription and billing
    subscription_plan = db.Column(db.String(50), default='free')  # free, basic, premium, enterprise
    subscription_status = db.Column(db.String(20), default='active')  # active, suspended, cancelled
    billing_cycle = db.Column(db.String(20), default='monthly')  # monthly, yearly
    next_billing_date = db.Column(db.DateTime)
    
    # Usage tracking
    api_calls_this_month = db.Column(db.Integer, default=0)
    storage_used_mb = db.Column(db.Float, default=0.0)
    max_users = db.Column(db.Integer, default=5)
    
    # Configuration
    timezone = db.Column(db.String(50), default='UTC')
    currency = db.Column(db.String(3), default='USD')
    language = db.Column(db.String(10), default='en')
    
    # Branding (for white-labeling)
    logo_url = db.Column(db.String(500))
    primary_color = db.Column(db.String(7), default='#3B82F6')  # hex color
    custom_domain = db.Column(db.String(255))
    
    # Status and metadata
    is_active = db.Column(db.Boolean, default=True)
    is_trial = db.Column(db.Boolean, default=True)
    trial_ends_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='tenant', lazy=True)
    
    def __repr__(self):
        return f'<Tenant {self.name}>'
    
    def to_dict(self):
        """Convert tenant to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'business_type': self.business_type,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'postal_code': self.postal_code,
            'subscription_plan': self.subscription_plan,
            'subscription_status': self.subscription_status,
            'billing_cycle': self.billing_cycle,
            'next_billing_date': self.next_billing_date.isoformat() if self.next_billing_date else None,
            'api_calls_this_month': self.api_calls_this_month,
            'storage_used_mb': self.storage_used_mb,
            'max_users': self.max_users,
            'timezone': self.timezone,
            'currency': self.currency,
            'language': self.language,
            'logo_url': self.logo_url,
            'primary_color': self.primary_color,
            'custom_domain': self.custom_domain,
            'is_active': self.is_active,
            'is_trial': self.is_trial,
            'trial_ends_at': self.trial_ends_at.isoformat() if self.trial_ends_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @property
    def is_trial_expired(self):
        """Check if trial has expired"""
        if not self.is_trial or not self.trial_ends_at:
            return False
        return datetime.utcnow() > self.trial_ends_at
    
    @property
    def can_add_users(self):
        """Check if tenant can add more users"""
        if self.subscription_plan == 'enterprise':
            return True
        current_users = len(self.users)
        return current_users < self.max_users
    
    def get_plan_limits(self):
        """Get plan limits based on subscription"""
        limits = {
            'free': {
                'max_users': 3,
                'max_api_calls_per_month': 1000,
                'max_storage_mb': 100,
                'features': ['basic_analytics', 'inventory_management']
            },
            'basic': {
                'max_users': 10,
                'max_api_calls_per_month': 10000,
                'max_storage_mb': 1000,
                'features': ['basic_analytics', 'inventory_management', 'ai_insights', 'basic_reports']
            },
            'premium': {
                'max_users': 25,
                'max_api_calls_per_month': 50000,
                'max_storage_mb': 5000,
                'features': ['basic_analytics', 'inventory_management', 'ai_insights', 'advanced_reports', 'predictive_analytics', 'custom_branding']
            },
            'enterprise': {
                'max_users': -1,  # unlimited
                'max_api_calls_per_month': -1,  # unlimited
                'max_storage_mb': -1,  # unlimited
                'features': ['all_features', 'custom_integrations', 'dedicated_support', 'white_labeling']
            }
        }
        return limits.get(self.subscription_plan, limits['free']) 