#!/usr/bin/env python3
"""
Clover Integration Test Script
This script tests the Clover POS integration to ensure it works correctly.
"""

import os
import sys
import requests
import json
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CloverIntegrationTester:
    def __init__(self, base_url="http://localhost:5000/api"):
        self.base_url = base_url
        self.session = requests.Session()
        
        # Test credentials (you'll need to replace these with real ones)
        self.test_config = {
            'merchant_id': os.getenv('CLOVER_MERCHANT_ID', 'test_merchant_id'),
            'access_token': os.getenv('CLOVER_ACCESS_TOKEN', 'test_access_token')
        }
    
    def test_connection(self):
        """Test basic connection to the API"""
        logger.info("Testing API connection...")
        
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                logger.info("✅ API connection successful")
                return True
            else:
                logger.error(f"❌ API connection failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ API connection failed: {e}")
            return False
    
    def test_clover_status(self):
        """Test Clover status endpoint"""
        logger.info("Testing Clover status...")
        
        try:
            response = self.session.get(f"{self.base_url}/clover/status")
            logger.info(f"Status response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Clover status: {data.get('status', 'unknown')}")
                if data.get('status') == 'connected':
                    logger.info(f"   Merchant: {data.get('merchant_name', 'Unknown')}")
                return True
            else:
                logger.error(f"❌ Clover status failed: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Clover status test failed: {e}")
            return False
    
    def test_sales_sync(self):
        """Test sales data synchronization"""
        logger.info("Testing sales sync...")
        
        try:
            # Test with last 7 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            data = {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
            
            response = self.session.post(
                f"{self.base_url}/clover/sync/sales",
                json=data
            )
            
            logger.info(f"Sales sync response: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Sales sync successful")
                logger.info(f"   Synced: {result.get('synced_count', 0)} records")
                logger.info(f"   Errors: {result.get('error_count', 0)}")
                return True
            else:
                logger.error(f"❌ Sales sync failed: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Sales sync test failed: {e}")
            return False
    
    def test_inventory_sync(self):
        """Test inventory data synchronization"""
        logger.info("Testing inventory sync...")
        
        try:
            response = self.session.post(f"{self.base_url}/clover/sync/inventory")
            
            logger.info(f"Inventory sync response: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Inventory sync successful")
                logger.info(f"   Updated: {result.get('updated_count', 0)} items")
                logger.info(f"   Created: {result.get('created_count', 0)} items")
                return True
            else:
                logger.error(f"❌ Inventory sync failed: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Inventory sync test failed: {e}")
            return False
    
    def test_real_time_data(self):
        """Test real-time data endpoint"""
        logger.info("Testing real-time data...")
        
        try:
            response = self.session.get(f"{self.base_url}/clover/realtime")
            
            logger.info(f"Real-time data response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Real-time data successful")
                logger.info(f"   Today's revenue: ${data.get('today_revenue', 0):.2f}")
                logger.info(f"   Today's orders: {data.get('today_orders', 0)}")
                logger.info(f"   Low stock items: {data.get('low_stock_count', 0)}")
                return True
            else:
                logger.error(f"❌ Real-time data failed: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Real-time data test failed: {e}")
            return False
    
    def test_inventory_endpoint(self):
        """Test inventory endpoint"""
        logger.info("Testing inventory endpoint...")
        
        try:
            response = self.session.get(f"{self.base_url}/clover/inventory")
            
            logger.info(f"Inventory endpoint response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Inventory endpoint successful")
                logger.info(f"   Total items: {data.get('count', 0)}")
                return True
            else:
                logger.error(f"❌ Inventory endpoint failed: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Inventory endpoint test failed: {e}")
            return False
    
    def test_orders_endpoint(self):
        """Test orders endpoint"""
        logger.info("Testing orders endpoint...")
        
        try:
            # Test with last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            params = {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'limit': 10
            }
            
            response = self.session.get(f"{self.base_url}/clover/orders", params=params)
            
            logger.info(f"Orders endpoint response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Orders endpoint successful")
                logger.info(f"   Total orders: {data.get('count', 0)}")
                return True
            else:
                logger.error(f"❌ Orders endpoint failed: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Orders endpoint test failed: {e}")
            return False
    
    def test_employees_endpoint(self):
        """Test employees endpoint"""
        logger.info("Testing employees endpoint...")
        
        try:
            response = self.session.get(f"{self.base_url}/clover/employees")
            
            logger.info(f"Employees endpoint response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Employees endpoint successful")
                logger.info(f"   Total employees: {data.get('count', 0)}")
                return True
            else:
                logger.error(f"❌ Employees endpoint failed: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Employees endpoint test failed: {e}")
            return False
    
    def test_customers_endpoint(self):
        """Test customers endpoint"""
        logger.info("Testing customers endpoint...")
        
        try:
            response = self.session.get(f"{self.base_url}/clover/customers")
            
            logger.info(f"Customers endpoint response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Customers endpoint successful")
                logger.info(f"   Total customers: {data.get('count', 0)}")
                return True
            else:
                logger.error(f"❌ Customers endpoint failed: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Customers endpoint test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all integration tests"""
        logger.info("🚀 Starting Clover Integration Tests")
        logger.info("=" * 50)
        
        tests = [
            ("API Connection", self.test_connection),
            ("Clover Status", self.test_clover_status),
            ("Real-time Data", self.test_real_time_data),
            ("Inventory Endpoint", self.test_inventory_endpoint),
            ("Orders Endpoint", self.test_orders_endpoint),
            ("Employees Endpoint", self.test_employees_endpoint),
            ("Customers Endpoint", self.test_customers_endpoint),
            ("Sales Sync", self.test_sales_sync),
            ("Inventory Sync", self.test_inventory_sync),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n📋 Running: {test_name}")
            try:
                if test_func():
                    passed += 1
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    logger.error(f"❌ {test_name}: FAILED")
            except Exception as e:
                logger.error(f"❌ {test_name}: ERROR - {e}")
        
        logger.info("\n" + "=" * 50)
        logger.info(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! Clover integration is working correctly.")
        else:
            logger.error(f"⚠️  {total - passed} tests failed. Please check the configuration.")
        
        return passed == total

def main():
    """Main test function"""
    # Check if environment variables are set
    if not os.getenv('CLOVER_MERCHANT_ID') or not os.getenv('CLOVER_ACCESS_TOKEN'):
        logger.warning("⚠️  Clover credentials not found in environment variables")
        logger.warning("Set CLOVER_MERCHANT_ID and CLOVER_ACCESS_TOKEN for full testing")
        logger.warning("Some tests may fail without valid credentials")
    
    # Run tests
    tester = CloverIntegrationTester()
    success = tester.run_all_tests()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main() 