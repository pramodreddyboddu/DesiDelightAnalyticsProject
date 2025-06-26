#!/usr/bin/env python3
"""
Debug script to check Clover order data and revenue calculation
"""

import requests
import json
from datetime import datetime, timedelta, timezone
import os
import logging
from src.services.clover_service import CloverService, CloverConfig

logging.basicConfig(level=logging.INFO)

BASE_URL = "http://localhost:5000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def login_and_get_session():
    """Login and get authenticated session"""
    session = requests.Session()
    login_data = {
        'username': ADMIN_USERNAME,
        'password': ADMIN_PASSWORD
    }
    response = session.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if response.status_code == 200:
        print("✅ Login successful")
        return session
    else:
        print(f"❌ Login failed: {response.status_code}")
        return None

def debug_clover_orders(session):
    """Debug Clover orders to see revenue data"""
    print("\n" + "="*60)
    print("DEBUGGING CLOVER ORDERS")
    print("="*60)
    
    # Get orders from Clover
    response = session.get(f"{BASE_URL}/api/clover/orders")
    if response.status_code != 200:
        print(f"❌ Failed to get orders: {response.status_code}")
        return
    
    orders_data = response.json()
    print(f"📊 Response structure: {type(orders_data)}")
    print(f"📊 Response keys: {list(orders_data.keys()) if isinstance(orders_data, dict) else 'Not a dict'}")
    
    # Handle different response formats
    if isinstance(orders_data, dict):
        orders = orders_data.get('orders', [])
    elif isinstance(orders_data, list):
        orders = orders_data
    else:
        print(f"❌ Unexpected response format: {type(orders_data)}")
        print(f"Response: {orders_data}")
        return
    
    print(f"📊 Total orders retrieved: {len(orders)}")
    
    if not orders:
        print("❌ No orders found")
        return
    
    # Analyze first few orders
    for i, order in enumerate(orders[:3]):  # Look at first 3 orders
        print(f"\n--- Order {i+1} ---")
        print(f"Order ID: {order.get('id')}")
        print(f"Created Time: {order.get('createdTime')}")
        print(f"State: {order.get('state')}")
        print(f"Total: {order.get('total')}")
        
        # Check line items
        line_items = order.get('lineItems', {}).get('elements', [])
        print(f"Line items count: {len(line_items)}")
        
        total_order_revenue = 0
        for j, line_item in enumerate(line_items):
            print(f"  Line Item {j+1}:")
            print(f"    ID: {line_item.get('id')}")
            print(f"    Quantity: {line_item.get('quantity')}")
            print(f"    Price: {line_item.get('price')}")
            print(f"    Total: {line_item.get('total')}")
            print(f"    Modifications: {line_item.get('modifications')}")
            
            # Check item details
            item = line_item.get('item', {})
            print(f"    Item Name: {item.get('name')}")
            print(f"    Item Price: {item.get('price')}")
            
            # Calculate revenue
            line_total = float(line_item.get('total', 0)) / 100
            total_order_revenue += line_total
            print(f"    Calculated Revenue: ${line_total:.2f}")
        
        print(f"  Total Order Revenue: ${total_order_revenue:.2f}")
        print(f"  Order Total (from Clover): ${float(order.get('total', 0)) / 100:.2f}")

def debug_dashboard_sales(session):
    """Debug dashboard sales summary"""
    print("\n" + "="*60)
    print("DEBUGGING DASHBOARD SALES")
    print("="*60)
    
    # Get sales summary
    response = session.get(f"{BASE_URL}/api/dashboard/sales-summary")
    if response.status_code != 200:
        print(f"❌ Failed to get sales summary: {response.status_code}")
        return
    
    sales_data = response.json()
    print(f"📊 Sales Summary:")
    print(f"  Total Revenue: ${sales_data.get('total_revenue', 0):.2f}")
    print(f"  Total Transactions: {sales_data.get('total_transactions', 0)}")
    
    # Check category breakdown
    categories = sales_data.get('category_breakdown', [])
    print(f"  Categories: {len(categories)}")
    for cat in categories[:3]:  # Show first 3 categories
        print(f"    {cat.get('category')}: ${cat.get('revenue', 0):.2f} ({cat.get('count', 0)} items)")
    
    # Check top items
    top_items = sales_data.get('top_items', [])
    print(f"  Top Items: {len(top_items)}")
    for item in top_items[:3]:  # Show first 3 items
        print(f"    {item.get('name')}: ${item.get('revenue', 0):.2f} ({item.get('count', 0)} sold)")

def debug_revenue():
    print("🔍 Starting Clover Revenue Debug...")
    clover_config = CloverConfig(
        merchant_id=os.getenv("CLOVER_MERCHANT_ID", ""),
        access_token=os.getenv("CLOVER_ACCESS_TOKEN", "")
    )
    clover_service = CloverService(clover_config)
    print("✅ Login successful")

    print("============================================================")
    print("DEBUGGING CLOVER ORDERS")
    print("============================================================")

    # Use the same timestamp range as the successful logs
    start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2025, 6, 24, 14, 36, 33, tzinfo=timezone.utc)  # 02:36:33 PM CDT
    
    print(f"📅 Date Range: {start_date} to {end_date}")
    
    # Use the same method as DashboardService
    orders = clover_service.get_orders(start_date, end_date)
    
    print(f"📊 Total orders retrieved: {len(orders) if orders else 0}")
    
    if not orders:
        print("❌ No orders found")
        return
    
    print(f"✅ Found {len(orders)} orders")
    
    # Show first 3 orders for inspection
    for i, order in enumerate(orders[:3], 1):
        print(f"\n--- Order {i} ---")
        print(f"Order ID: {order.get('id')}")
        print(f"Created Time: {order.get('createdTime')}")
        print(f"Total: ${order.get('total', 0) / 100.0:.2f}")
        
        line_items = order.get('lineItems', {}).get('elements', [])
        print(f"Line items count: {len(line_items)}")
        
        for j, item in enumerate(line_items[:3], 1):  # Show first 3 line items
            print(f"  Line Item {j}:")
            print(f"    ID: {item.get('id')}")
            print(f"    Name: {item.get('name', 'Unknown')}")
            print(f"    Price: ${item.get('price', 0) / 100.0:.2f}")
            print(f"    Quantity: {item.get('quantity', 1)}")
            print(f"    Total: ${item.get('total', 0) / 100.0:.2f}")

    print("\n============================================================")
    print("DEBUGGING DASHBOARD SALES")
    print("============================================================")
    
    # Calculate revenue like DashboardService
    total_revenue = 0
    order_ids = set()
    category_revenue = {}
    
    for order in orders:
        order_id = order.get('id')
        order_ids.add(order_id)
        
        line_items = order.get('lineItems', {}).get('elements', [])
        if not line_items:
            # Fallback: use order-level total if no line items
            order_total = float(order.get('total', 0)) / 100
            total_revenue += order_total
            continue
            
        for li in line_items:
            revenue = float(li.get('total', 0)) / 100
            total_revenue += revenue
            
            # Extract category
            cat = 'Uncategorized'
            item = li.get('item', {})
            categories = item.get('categories', {}).get('elements', [])
            if categories and isinstance(categories, list):
                cat = categories[0].get('name', 'Uncategorized')
            
            category_revenue.setdefault(cat, {'revenue': 0, 'count': 0})
            category_revenue[cat]['revenue'] += revenue
            category_revenue[cat]['count'] += li.get('quantity', 1)
    
    print(f"📊 Sales Summary:")
    print(f"  Total Revenue: ${total_revenue:.2f}")
    print(f"  Total Transactions: {len(order_ids)}")
    print(f"  Categories: {len(category_revenue)}")
    
    # Show top categories
    top_categories = sorted(category_revenue.items(), key=lambda x: x[1]['revenue'], reverse=True)[:5]
    print(f"  Top Categories:")
    for cat, data in top_categories:
        print(f"    {cat}: ${data['revenue']:.2f} ({data['count']} items)")

    print("\n============================================================")
    print("DEBUG COMPLETE")
    print("============================================================")

if __name__ == "__main__":
    debug_revenue() 