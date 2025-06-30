#!/usr/bin/env python3
"""
Detailed debug script for chef performance data
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

def debug_chef_performance_detailed():
    """Detailed debug of chef performance data"""
    
    with app.app_context():
        print("=== DETAILED CHEF PERFORMANCE DEBUG ===\n")
        
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
        
        # 4. Test dashboard service with detailed logging
        print("\n4. TESTING DASHBOARD SERVICE WITH DETAILED LOGGING:")
        dashboard_service = DashboardService()
        
        # Test with today's date
        today = datetime.now(timezone.utc)
        start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        print(f"Testing with date range: {start_date} to {end_date}")
        
        try:
            # Test chef performance data
            print("\nCalling get_chef_performance_data...")
            chef_data = dashboard_service.get_chef_performance_data(start_date, end_date)
            print(f"Result type: {type(chef_data)}")
            print(f"Result keys: {list(chef_data.keys()) if isinstance(chef_data, dict) else 'Not a dict'}")
            
            if isinstance(chef_data, dict):
                chef_summary = chef_data.get('chef_summary', [])
                chef_performance = chef_data.get('chef_performance', [])
                
                print(f"\nChef summary count: {len(chef_summary)}")
                print(f"Chef performance count: {len(chef_performance)}")
                
                if chef_summary:
                    print("\nChef summary data:")
                    for chef in chef_summary:
                        print(f"  - {chef.get('name', 'Unknown')}: ${chef.get('total_revenue', 0)} ({chef.get('total_sales', 0)} sales)")
                else:
                    print("❌ No chef summary data")
                    
                if chef_performance:
                    print("\nChef performance data:")
                    for chef in chef_performance:
                        dishes = chef.get('dishes', [])
                        print(f"  - {chef.get('chef_name', 'Unknown')}: {len(dishes)} dishes")
                        for dish in dishes[:3]:  # Show first 3 dishes
                            print(f"    * {dish.get('item_name', 'Unknown')}: ${dish.get('revenue', 0)} ({dish.get('count', 0)} sold)")
                else:
                    print("❌ No chef performance data")
            else:
                print(f"❌ Unexpected result type: {type(chef_data)}")
                print(f"Result: {chef_data}")
            
        except Exception as e:
            print(f"❌ Error testing dashboard service: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # 5. Check data source configuration
        print("\n5. DATA SOURCE CONFIGURATION:")
        data_source = dashboard_service.get_data_source('sales')
        print(f"Sales data source: {data_source}")
        
        # 6. Test Clover service directly
        print("\n6. TESTING CLOVER SERVICE:")
        try:
            clover_service = dashboard_service.clover_service
            print("Getting orders from Clover...")
            orders = clover_service.get_orders(start_date, end_date)
            print(f"Retrieved {len(orders) if orders else 0} orders from Clover")
            
            if orders:
                print("\nFirst order sample:")
                first_order = orders[0]
                print(f"Order ID: {first_order.get('id')}")
                print(f"Created: {first_order.get('createdTime')}")
                line_items = first_order.get('lineItems', {}).get('elements', [])
                print(f"Line items: {len(line_items)}")
                
                if line_items:
                    first_item = line_items[0]
                    item_data = first_item.get('item', {})
                    print(f"First item: {item_data.get('name')} (ID: {item_data.get('id')})")
                    
                    # Check if this item exists in our mapping
                    item_id_map = {item.clover_id: item.id for item in db.session.query(Item).all()}
                    clover_item_id = item_data.get('id')
                    local_item_id = item_id_map.get(clover_item_id)
                    
                    print(f"Clover item ID: {clover_item_id}")
                    print(f"Local item ID: {local_item_id}")
                    
                    if local_item_id:
                        # Check if it's mapped to a chef
                        chef_mapping = ChefDishMapping.query.filter_by(item_id=local_item_id).first()
                        if chef_mapping:
                            chef = Chef.query.get(chef_mapping.chef_id)
                            print(f"✅ Mapped to chef: {chef.name if chef else 'Unknown'}")
                        else:
                            print("❌ Not mapped to any chef")
                    else:
                        print("❌ Not found in local item mapping")
            
        except Exception as e:
            print(f"❌ Error testing Clover service: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n=== DETAILED DEBUG COMPLETE ===")

if __name__ == "__main__":
    debug_chef_performance_detailed() 