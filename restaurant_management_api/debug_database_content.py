#!/usr/bin/env python3
"""
Comprehensive database content debug script
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set required environment variables if not present
if not os.getenv('ADMIN_PASSWORD'):
    os.environ['ADMIN_PASSWORD'] = 'admin123'
if not os.getenv('SECRET_KEY'):
    os.environ['SECRET_KEY'] = 'debug-secret-key'
if not os.getenv('DATABASE_URL'):
    os.environ['DATABASE_URL'] = 'sqlite:///instance/restaurant_management.db'

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.main import app, db
from src.models.item import Item
from src.models.chef import Chef
from src.models.chef_dish_mapping import ChefDishMapping
from src.models.sale import Sale
from src.models.user import User
from src.models.tenant import Tenant
from src.models.data_source_config import DataSourceConfig
from datetime import datetime, timezone
import json

def debug_database_content():
    """Debug all database content"""
    
    with app.app_context():
        print("=== COMPREHENSIVE DATABASE DEBUG ===\n")
        
        # Check all tables
        print("1. ALL TABLES IN DATABASE:")
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        for table in tables:
            print(f"  - {table}")
        
        print(f"\nTotal tables: {len(tables)}")
        
        # 2. Check users
        print("\n2. USERS:")
        users = User.query.all()
        print(f"Total users: {len(users)}")
        for user in users:
            print(f"  - {user.username} (id: {user.id}, role: {user.role})")
        
        # 3. Check tenants
        print("\n3. TENANTS:")
        tenants = Tenant.query.all()
        print(f"Total tenants: {len(tenants)}")
        for tenant in tenants:
            print(f"  - {tenant.name} (id: {tenant.id})")
        
        # 4. Check data source config
        print("\n4. DATA SOURCE CONFIG:")
        configs = DataSourceConfig.query.all()
        print(f"Total configs: {len(configs)}")
        for config in configs:
            print(f"  - {config.data_type}: {config.source_type}")
        
        # 5. Check items
        print("\n5. ITEMS:")
        items = Item.query.all()
        print(f"Total items: {len(items)}")
        
        if items:
            items_with_clover = [item for item in items if item.clover_id]
            print(f"Items with clover_id: {len(items_with_clover)}")
            
            print("\nFirst 10 items:")
            for i, item in enumerate(items[:10]):
                print(f"  {i+1}. {item.name} (id: {item.id}, clover_id: {item.clover_id})")
        
        # 6. Check chefs
        print("\n6. CHEFS:")
        chefs = Chef.query.all()
        print(f"Total chefs: {len(chefs)}")
        for chef in chefs:
            print(f"  - {chef.name} (id: {chef.id}, clover_id: {chef.clover_id})")
        
        # 7. Check chef mappings
        print("\n7. CHEF MAPPINGS:")
        mappings = ChefDishMapping.query.all()
        print(f"Total mappings: {len(mappings)}")
        
        if mappings:
            print("\nFirst 10 mappings:")
            for i, mapping in enumerate(mappings[:10]):
                item = Item.query.get(mapping.item_id)
                chef = Chef.query.get(mapping.chef_id)
                print(f"  {i+1}. Item: {item.name if item else 'Unknown'} (clover_id: {item.clover_id if item else 'None'}) -> Chef: {chef.name if chef else 'Unknown'}")
        
        # 8. Check sales
        print("\n8. SALES:")
        sales = Sale.query.all()
        print(f"Total sales: {len(sales)}")
        
        if sales:
            sales_with_clover = [sale for sale in sales if sale.clover_id]
            print(f"Sales with clover_id: {len(sales_with_clover)}")
            
            print("\nFirst 10 sales:")
            for i, sale in enumerate(sales[:10]):
                item = Item.query.get(sale.item_id)
                print(f"  {i+1}. Sale ID: {sale.id}, Item: {item.name if item else 'Unknown'}, Revenue: ${sale.total_revenue}, Date: {sale.line_item_date}, Clover ID: {sale.clover_id}")
        
        # 9. Check database connection
        print("\n9. DATABASE CONNECTION:")
        try:
            # Test a simple query
            result = db.session.execute("SELECT COUNT(*) FROM item").scalar()
            print(f"Database connection test - Item count: {result}")
        except Exception as e:
            print(f"Database connection error: {str(e)}")
        
        # 10. Check if we're using the right database
        print("\n10. DATABASE URL:")
        print(f"Current DATABASE_URL: {os.getenv('DATABASE_URL')}")
        
        print("\n=== DEBUG COMPLETE ===")

if __name__ == "__main__":
    debug_database_content() 