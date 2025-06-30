#!/usr/bin/env python3
"""
Debug script to check staff performance data and mapping
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
from src.services.dashboard_service import DashboardService
from datetime import datetime, timezone
import json

def debug_staff_performance():
    """Debug staff performance data"""
    
    with app.app_context():
        print("=== STAFF PERFORMANCE DEBUG ===\n")
        
        # 1. Check items in database
        print("1. ITEMS IN DATABASE:")
        items = Item.query.all()
        print(f"Total items: {len(items)}")
        items_with_clover_id = [item for item in items if item.clover_id]
        print(f"Items with clover_id: {len(items_with_clover_id)}")
        
        # Show first 10 items with clover_id
        print("\nFirst 10 items with clover_id:")
        for i, item in enumerate(items_with_clover_id[:10]):
            print(f"  {i+1}. {item.name} (clover_id: {item.clover_id})")
        
        # 2. Check chefs in database
        print("\n2. CHEFS IN DATABASE:")
        chefs = Chef.query.all()
        print(f"Total chefs: {len(chefs)}")
        for chef in chefs:
            print(f"  - {chef.name} (id: {chef.id}, clover_id: {chef.clover_id})")
        
        # 3. Check chef mappings
        print("\n3. CHEF MAPPINGS:")
        mappings = ChefDishMapping.query.all()
        print(f"Total mappings: {len(mappings)}")
        
        # Show mappings with item details
        print("\nFirst 10 chef mappings:")
        for i, mapping in enumerate(mappings[:10]):
            item = Item.query.get(mapping.item_id)
            chef = Chef.query.get(mapping.chef_id)
            print(f"  {i+1}. Item: {item.name if item else 'Unknown'} (clover_id: {item.clover_id if item else 'None'}) -> Chef: {chef.name if chef else 'Unknown'}")
        
        # 4. Check sales data
        print("\n4. SALES DATA:")
        sales = Sale.query.all()
        print(f"Total sales: {len(sales)}")
        
        if sales:
            # Check sales with clover_id
            sales_with_clover_id = [sale for sale in sales if sale.clover_id]
            print(f"Sales with clover_id: {len(sales_with_clover_id)}")
            
            # Show first 10 sales
            print("\nFirst 10 sales:")
            for i, sale in enumerate(sales[:10]):
                item = Item.query.get(sale.item_id)
                print(f"  {i+1}. Sale ID: {sale.id}, Item: {item.name if item else 'Unknown'}, Revenue: ${sale.total_revenue}, Date: {sale.line_item_date}")
        
        # 5. Test dashboard service
        print("\n5. TESTING DASHBOARD SERVICE:")
        dashboard_service = DashboardService()
        
        # Test with today's date
        today = datetime.now(timezone.utc)
        start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        print(f"Testing with date range: {start_date} to {end_date}")
        
        try:
            # Test chef performance data
            chef_data = dashboard_service.get_chef_performance_data(start_date, end_date)
            print(f"\nChef performance data result:")
            print(f"  - Chef summary count: {len(chef_data.get('chef_summary', []))}")
            print(f"  - Chef performance count: {len(chef_data.get('chef_performance', []))}")
            
            if chef_data.get('chef_summary'):
                print("\nChef summary:")
                for chef in chef_data['chef_summary']:
                    print(f"  - {chef['name']}: ${chef['total_revenue']} ({chef['total_sales']} sales)")
            
            if chef_data.get('chef_performance'):
                print("\nChef performance details:")
                for chef in chef_data['chef_performance']:
                    print(f"  - {chef['chef_name']}: {len(chef['dishes'])} dishes")
                    for dish in chef['dishes'][:3]:  # Show first 3 dishes
                        print(f"    * {dish['item_name']}: ${dish['revenue']} ({dish['count']} sold)")
            
        except Exception as e:
            print(f"Error testing dashboard service: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # 6. Check data source configuration
        print("\n6. DATA SOURCE CONFIGURATION:")
        data_source = dashboard_service.get_data_source('sales')
        print(f"Sales data source: {data_source}")
        
        print("\n=== DEBUG COMPLETE ===")

if __name__ == "__main__":
    debug_staff_performance() 