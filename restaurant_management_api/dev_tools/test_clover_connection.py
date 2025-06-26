#!/usr/bin/env python3
"""
Simple test script to verify Clover connection and data availability
"""

import os
import sys
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.clover_service import CloverService, CloverConfig

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_clover_connection():
    """Test Clover connection and data retrieval"""
    
    # Get credentials from environment
    merchant_id = os.getenv('CLOVER_MERCHANT_ID')
    access_token = os.getenv('CLOVER_ACCESS_TOKEN')
    
    if not merchant_id or not access_token:
        logger.error("CLOVER_MERCHANT_ID and CLOVER_ACCESS_TOKEN must be set")
        return False
    
    logger.info(f"Testing Clover connection for merchant: {merchant_id}")
    
    try:
        # Create Clover service
        config = CloverConfig(
            merchant_id=merchant_id,
            access_token=access_token
        )
        clover_service = CloverService(config)
        
        # Test merchant info
        logger.info("Testing merchant info...")
        merchant_info = clover_service.get_merchant_info()
        logger.info(f"Merchant name: {merchant_info.get('name', 'Unknown')}")
        
        # Test categories
        logger.info("Testing categories...")
        categories = clover_service.get_categories()
        logger.info(f"Found {len(categories)} categories")
        for cat in categories[:5]:  # Show first 5 categories
            logger.info(f"  - {cat.get('name', 'Unknown')}")
        
        # Test items
        logger.info("Testing items...")
        items = clover_service.get_items()
        logger.info(f"Found {len(items)} items")
        
        if items:
            # Show first few items with their categories
            for item in items[:5]:
                item_name = item.get('name', 'Unknown')
                categories = item.get('categories', {}).get('elements', [])
                category_name = categories[0].get('name', 'Uncategorized') if categories else 'Uncategorized'
                price = item.get('price', 0) / 100  # Convert from cents
                stock = item.get('stockCount', 0)
                logger.info(f"  - {item_name} (Category: {category_name}, Price: ${price}, Stock: {stock})")
        
        # Test orders
        logger.info("Testing orders...")
        orders = clover_service.get_orders()
        logger.info(f"Found {len(orders)} orders")
        
        if orders:
            # Show first few orders
            for order in orders[:3]:
                order_id = order.get('id', 'Unknown')
                created_time = order.get('createdTime', 0)
                state = order.get('state', 'Unknown')
                total = order.get('total', 0) / 100 if order.get('total') else 0
                logger.info(f"  - Order {order_id} (State: {state}, Total: ${total})")
        
        logger.info("✅ All Clover tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Clover test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_clover_connection()
    sys.exit(0 if success else 1) 