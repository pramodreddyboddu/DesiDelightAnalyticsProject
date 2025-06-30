#!/usr/bin/env python3
"""
Debug script to check Clover configuration and connection
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set the Heroku database URL
HEROKU_DATABASE_URL = "postgres://u6rdcevq0gfopc:pb3bc0adf74bb1f42805449de8c3a10e7f791afc9b210dae8e1e94cb0d294e6bb@c2hbg00ac72j9d.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/d8l07ljalqje7p"
os.environ['DATABASE_URL'] = HEROKU_DATABASE_URL

# Set required environment variables if not present
if not os.getenv('ADMIN_PASSWORD'):
    os.environ['ADMIN_PASSWORD'] = 'admin123'
if not os.getenv('SECRET_KEY'):
    os.environ['SECRET_KEY'] = 'debug-secret-key'

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.main import app, db
from src.services.clover_service import CloverService, CloverConfig
from datetime import datetime, timedelta

def debug_clover_config():
    """Debug Clover configuration and connection"""
    
    with app.app_context():
        print("=== CLOVER CONFIGURATION DEBUG ===\n")
        
        # Check environment variables
        print("1. ENVIRONMENT VARIABLES:")
        merchant_id = os.getenv('CLOVER_MERCHANT_ID')
        access_token = os.getenv('CLOVER_ACCESS_TOKEN')
        
        print(f"CLOVER_MERCHANT_ID: {'✅ Set' if merchant_id else '❌ Not set'}")
        print(f"CLOVER_ACCESS_TOKEN: {'✅ Set' if access_token else '❌ Not set'}")
        
        if not merchant_id or not access_token:
            print("\n❌ Clover is not configured. Please set CLOVER_MERCHANT_ID and CLOVER_ACCESS_TOKEN environment variables.")
            return
        
        # Test Clover connection
        print("\n2. TESTING CLOVER CONNECTION:")
        try:
            config = CloverConfig(merchant_id=merchant_id, access_token=access_token)
            clover_service = CloverService(config)
            
            # Test getting items
            print("Testing items fetch...")
            items = clover_service.get_items()
            print(f"Items found: {len(items) if items else 0}")
            
            if items:
                print("First 5 items:")
                for i, item in enumerate(items[:5]):
                    print(f"  {i+1}. {item.get('name', 'Unknown')} (ID: {item.get('id', 'No ID')})")
            
            # Test getting orders
            print("\nTesting orders fetch...")
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            orders = clover_service.get_orders(start_date, end_date)
            print(f"Orders found (last 7 days): {len(orders) if orders else 0}")
            
            if orders:
                print("First 5 orders:")
                for i, order in enumerate(orders[:5]):
                    order_id = order.get('id', 'No ID')
                    total = order.get('total', 0)
                    state = order.get('state', 'Unknown')
                    print(f"  {i+1}. Order {order_id}: ${total/100:.2f} ({state})")
            
            print("\n✅ Clover connection successful!")
            
        except Exception as e:
            print(f"\n❌ Clover connection failed: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n=== DEBUG COMPLETE ===")

if __name__ == "__main__":
    debug_clover_config() 