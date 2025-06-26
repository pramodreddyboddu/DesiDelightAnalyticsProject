#!/usr/bin/env python3
"""
Quick script to restore tenant data for testing
"""

import sys
import os
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main import create_app
from src.models import db
from src.models.tenant import Tenant
from src.models.user import User

def restore_tenant_data():
    """Restore DesiDelight tenant and user data"""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if DesiDelight tenant already exists
            desi_delight = Tenant.query.filter_by(name='DesiDelight').first()
            
            if not desi_delight:
                # Create DesiDelight tenant
                desi_delight = Tenant(
                    name='DesiDelight',
                    business_type='restaurant',
                    contact_email='admin@desidelight.com',
                    contact_phone='+1-555-0123',
                    address='123 Main Street',
                    city='Chicago',
                    state='IL',
                    country='US',
                    postal_code='60601',
                    subscription_plan='premium',
                    subscription_status='active',
                    is_active=True,
                    is_trial=False,
                    created_at=datetime.utcnow()
                )
                db.session.add(desi_delight)
                db.session.commit()
                print("✅ DesiDelight tenant created successfully")
            else:
                print("✅ DesiDelight tenant already exists")
            
            # Check if tenant admin user exists
            tenant_admin = User.query.filter_by(username='desidelight_admin').first()
            
            if not tenant_admin:
                # Create tenant admin user
                tenant_admin = User(
                    username='desidelight_admin',
                    email='admin@desidelight.com',
                    role='admin',
                    is_admin=True,
                    tenant_id=desi_delight.id,
                    created_at=datetime.utcnow()
                )
                tenant_admin.set_password('admin123')
                db.session.add(tenant_admin)
                db.session.commit()
                print("✅ DesiDelight tenant admin user created successfully")
            else:
                print("✅ DesiDelight tenant admin user already exists")
            
            # Check if regular tenant user exists
            tenant_user = User.query.filter_by(username='desidelight_user').first()
            
            if not tenant_user:
                # Create regular tenant user
                tenant_user = User(
                    username='desidelight_user',
                    email='user@desidelight.com',
                    role='user',
                    is_admin=False,
                    tenant_id=desi_delight.id,
                    created_at=datetime.utcnow()
                )
                tenant_user.set_password('user123')
                db.session.add(tenant_user)
                db.session.commit()
                print("✅ DesiDelight tenant user created successfully")
            else:
                print("✅ DesiDelight tenant user already exists")
            
            print("\n🎉 Tenant data restored successfully!")
            print("\n📋 Login Credentials:")
            print("Admin User:")
            print("  Username: desidelight_admin")
            print("  Password: admin123")
            print("  Email: admin@desidelight.com")
            print("\nRegular User:")
            print("  Username: desidelight_user")
            print("  Password: user123")
            print("  Email: user@desidelight.com")
            
        except Exception as e:
            print(f"❌ Error restoring tenant data: {e}")
            db.session.rollback()

if __name__ == "__main__":
    restore_tenant_data() 