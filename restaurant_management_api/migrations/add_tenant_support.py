#!/usr/bin/env python3
"""
Database migration script to add multi-tenant support
This script safely adds tenant functionality without breaking existing data
"""

import os
import sys
from datetime import datetime, timedelta
import uuid
from sqlalchemy import text

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.models import db
from src.models.tenant import Tenant
from src.models.user import User
from src.config import config

def create_tenant_table():
    """Create the tenants table"""
    try:
        # Create tenants table
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS tenants (
                id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                business_type VARCHAR(100) NOT NULL,
                contact_email VARCHAR(255) NOT NULL UNIQUE,
                contact_phone VARCHAR(20),
                address TEXT,
                city VARCHAR(100),
                state VARCHAR(100),
                country VARCHAR(100) DEFAULT 'US',
                postal_code VARCHAR(20),
                subscription_plan VARCHAR(50) DEFAULT 'free',
                subscription_status VARCHAR(20) DEFAULT 'active',
                billing_cycle VARCHAR(20) DEFAULT 'monthly',
                next_billing_date DATETIME,
                api_calls_this_month INTEGER DEFAULT 0,
                storage_used_mb FLOAT DEFAULT 0.0,
                max_users INTEGER DEFAULT 5,
                timezone VARCHAR(50) DEFAULT 'UTC',
                currency VARCHAR(3) DEFAULT 'USD',
                language VARCHAR(10) DEFAULT 'en',
                logo_url VARCHAR(500),
                primary_color VARCHAR(7) DEFAULT '#3B82F6',
                custom_domain VARCHAR(255),
                is_active BOOLEAN DEFAULT 1,
                is_trial BOOLEAN DEFAULT 1,
                trial_ends_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        db.session.commit()
        print("✅ Tenants table created successfully")
        
    except Exception as e:
        print(f"❌ Error creating tenants table: {str(e)}")
        raise

def add_tenant_id_to_users():
    """Add tenant_id column to users table"""
    try:
        # Check if tenant_id column already exists
        result = db.session.execute(text("PRAGMA table_info(user)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'tenant_id' not in columns:
            # Add tenant_id column to users table
            db.session.execute(text("""
                ALTER TABLE user 
                ADD COLUMN tenant_id VARCHAR(36) 
                REFERENCES tenants(id)
            """))
            db.session.commit()
            print("✅ Added tenant_id column to users table")
        else:
            print("ℹ️  tenant_id column already exists in users table")
            
    except Exception as e:
        print(f"❌ Error adding tenant_id to users table: {str(e)}")
        raise

def create_default_tenant():
    """Create a default tenant for existing data"""
    try:
        # Check if any tenants exist
        existing_tenants = db.session.execute(text("SELECT COUNT(*) FROM tenants")).fetchone()[0]
        
        if existing_tenants == 0:
            # Create default tenant
            default_tenant_id = str(uuid.uuid4())
            db.session.execute(text("""
                INSERT INTO tenants (
                    id, name, business_type, contact_email, 
                    subscription_plan, subscription_status, 
                    is_trial, trial_ends_at, created_at, updated_at
                ) VALUES (:id, :name, :business_type, :contact_email, :subscription_plan, :subscription_status, :is_trial, :trial_ends_at, :created_at, :updated_at)
            """), {
                'id': default_tenant_id,
                'name': 'Default Restaurant',
                'business_type': 'restaurant',
                'contact_email': 'admin@default-restaurant.com',
                'subscription_plan': 'free',
                'subscription_status': 'active',
                'is_trial': 1,
                'trial_ends_at': datetime.utcnow() + timedelta(days=30),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            })
            db.session.commit()
            print(f"✅ Created default tenant with ID: {default_tenant_id}")
            return default_tenant_id
        else:
            print("ℹ️  Tenants already exist, skipping default tenant creation")
            return None
            
    except Exception as e:
        print(f"❌ Error creating default tenant: {str(e)}")
        raise

def migrate_existing_users():
    """Migrate existing users to the default tenant"""
    try:
        # Get default tenant ID
        default_tenant = db.session.execute(text("SELECT id FROM tenants LIMIT 1")).fetchone()
        
        if default_tenant:
            default_tenant_id = default_tenant[0]
            
            # Update existing users to belong to default tenant
            result = db.session.execute(text("""
                UPDATE user 
                SET tenant_id = :tenant_id 
                WHERE tenant_id IS NULL
            """), {'tenant_id': default_tenant_id})
            db.session.commit()
            updated_count = result.rowcount
            print(f"✅ Migrated {updated_count} existing users to default tenant")
        else:
            print("⚠️  No default tenant found, skipping user migration")
            
    except Exception as e:
        print(f"❌ Error migrating existing users: {str(e)}")
        raise

def create_indexes():
    """Create indexes for better performance"""
    try:
        # Create indexes
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_tenants_email ON tenants(contact_email)"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_tenants_status ON tenants(subscription_status)"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_users_tenant ON user(tenant_id)"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_tenants_plan ON tenants(subscription_plan)"))
        db.session.commit()
        print("✅ Created database indexes")
        
    except Exception as e:
        print(f"❌ Error creating indexes: {str(e)}")
        raise

def main():
    """Main migration function"""
    print("🚀 Starting multi-tenant migration...")
    
    try:
        # Initialize database connection
        from src.main import create_app
        app = create_app()
        
        with app.app_context():
            print("📊 Database connection established")
            
            # Step 1: Create tenants table
            create_tenant_table()
            
            # Step 2: Add tenant_id to users table
            add_tenant_id_to_users()
            
            # Step 3: Create default tenant
            create_default_tenant()
            
            # Step 4: Migrate existing users
            migrate_existing_users()
            
            # Step 5: Create indexes
            create_indexes()
            
            print("🎉 Multi-tenant migration completed successfully!")
            print("\n📋 Migration Summary:")
            print("- Created tenants table with all required fields")
            print("- Added tenant_id column to users table")
            print("- Created default tenant for existing data")
            print("- Migrated existing users to default tenant")
            print("- Created performance indexes")
            print("\n✨ Your application is now ready for multi-tenant SaaS!")
            
    except Exception as e:
        print(f"💥 Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 