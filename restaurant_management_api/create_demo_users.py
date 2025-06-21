#!/usr/bin/env python3
"""
Script to create demo users with different roles for testing the multi-tenant system.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.main import create_app
from src.models import db
from src.models.user import User
from src.models.tenant import Tenant
from datetime import datetime, timedelta

def create_demo_users():
    app = create_app()
    
    with app.app_context():
        # Check if demo tenant already exists
        demo_tenant = Tenant.query.filter_by(name="Spice Garden Restaurant").first()
        
        if not demo_tenant:
            # Create demo tenant
            demo_tenant = Tenant(
                name="Spice Garden Restaurant",
                business_type="restaurant",
                contact_email="admin@spicegarden.com",
                contact_phone="+1-555-0123",
                address="123 Main Street",
                city="Chicago",
                state="IL",
                country="US",
                postal_code="60601",
                subscription_plan="premium",
                subscription_status="active",
                billing_cycle="monthly",
                next_billing_date=datetime.utcnow() + timedelta(days=30),
                max_users=10,
                timezone="America/Chicago",
                currency="USD",
                language="en",
                is_active=True,
                is_trial=False
            )
            
            # Add tenant to database
            db.session.add(demo_tenant)
            db.session.commit()
            print(f"Created tenant: {demo_tenant.name} (ID: {demo_tenant.id})")
        else:
            print(f"Using existing tenant: {demo_tenant.name} (ID: {demo_tenant.id})")
        
        # Check and create/update super admin user
        super_admin = User.query.filter_by(username="admin").first()
        if not super_admin:
            super_admin = User(
                username="admin",
                email="admin@desidelight.com",
                role="super_admin",
                is_admin=True,
                tenant_id=None  # Super admin has no tenant
            )
            super_admin.set_password("admin123")
            db.session.add(super_admin)
            print("Created super admin user")
        else:
            # Update existing admin to be super admin
            super_admin.role = "super_admin"
            super_admin.is_admin = True
            super_admin.tenant_id = None
            super_admin.set_password("admin123")
            print("Updated existing admin user to super admin")
        
        # Check and create tenant admin user
        tenant_admin = User.query.filter_by(username="restaurant_admin").first()
        if not tenant_admin:
            tenant_admin = User(
                username="restaurant_admin",
                email="admin@spicegarden.com",
                role="admin",
                is_admin=True,
                tenant_id=demo_tenant.id
            )
            tenant_admin.set_password("admin123")
            db.session.add(tenant_admin)
            print("Created tenant admin user")
        else:
            # Update existing tenant admin
            tenant_admin.role = "admin"
            tenant_admin.is_admin = True
            tenant_admin.tenant_id = demo_tenant.id
            tenant_admin.set_password("admin123")
            print("Updated existing tenant admin user")
        
        # Check and create regular staff user
        staff_user = User.query.filter_by(username="staff").first()
        if not staff_user:
            staff_user = User(
                username="staff",
                email="staff@spicegarden.com",
                role="user",
                is_admin=False,
                tenant_id=demo_tenant.id
            )
            staff_user.set_password("staff123")
            db.session.add(staff_user)
            print("Created staff user")
        else:
            # Update existing staff user
            staff_user.role = "user"
            staff_user.is_admin = False
            staff_user.tenant_id = demo_tenant.id
            staff_user.set_password("staff123")
            print("Updated existing staff user")
        
        # Commit all changes
        db.session.commit()
        
        print("\nDemo users setup complete:")
        print(f"  Super Admin: admin / admin123")
        print(f"  Tenant Admin: restaurant_admin / admin123")
        print(f"  Staff User: staff / staff123")
        print(f"\nAll users are associated with tenant: {demo_tenant.name}")

if __name__ == '__main__':
    create_demo_users() 