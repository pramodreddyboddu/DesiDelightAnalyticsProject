import requests
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
from dataclasses import dataclass
from src.models import db
from src.models.sale import Sale
from src.models.item import Item
from src.models.user import User
import os
import urllib.parse
import pytz

logger = logging.getLogger(__name__)

@dataclass
class CloverConfig:
    """Clover API configuration"""
    merchant_id: str
    access_token: str
    api_base_url: str = "https://api.clover.com"
    api_version: str = "v3"

class CloverService:
    """Service for integrating with Clover POS system (Read-Only)"""
    
    def __init__(self, config: CloverConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {config.access_token}',
            'Content-Type': 'application/json'
        })
        # Rate limiting: max 10 requests per second
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
    
    def _rate_limit(self):
        """Implement rate limiting to avoid 429 errors"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, data: Optional[list] = None) -> Dict:
        """Make a rate-limited request to the Clover API"""
        self._rate_limit()
        
        url = f"{self.config.api_base_url}/{self.config.api_version}/merchants/{self.config.merchant_id}/{endpoint}"
        
        try:
            if data:
                req = requests.Request('GET', url, params=data)
                prepped = self.session.prepare_request(req)
                logger.info(f"Final Clover URL: {prepped.url}")
                response = self.session.send(prepped)
            else:
                response = self.session.get(url)
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning(f"Rate limit hit, waiting 1 second before retry")
                time.sleep(1)
                # Retry once after waiting
                self._rate_limit()
                if data:
                    req = requests.Request('GET', url, params=data)
                    prepped = self.session.prepare_request(req)
                    logger.info(f"Final Clover URL: {prepped.url}")
                    response = self.session.send(prepped)
                else:
                    response = self.session.get(url)
                response.raise_for_status()
                return response.json()
            else:
                logger.error(f"Clover API request failed: {e}")
                logger.error(f"Response text: {e.response.text}")
                raise
        except Exception as e:
            logger.error(f"Clover API request failed: {e}")
            raise
    
    def get_merchant_info(self) -> Dict:
        """Get merchant information"""
        return self._make_request('')
    
    def get_employees(self) -> List[Dict]:
        """Get all employees"""
        response = self._make_request('employees')
        return response.get('elements', [])
    
    def get_categories(self) -> List[Dict]:
        """Get all categories"""
        response = self._make_request('categories')
        return response.get('elements', [])
    
    def get_items(self, category_id: str = None) -> List[Dict]:
        """Get all items, optionally filtered by category, with full pagination"""
        params = {'limit': 1000, 'expand': 'categories'}
        if category_id:
            params['categoryId'] = category_id
        
        all_items = []
        offset = 0
        while True:
            params['offset'] = offset
            response = self._make_request('items', data=params)
            items = response.get('elements', [])
            all_items.extend(items)
            if len(items) < params['limit']:
                break
            offset += params['limit']
        return all_items
    
    def get_orders(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, limit: int = 100) -> list:
        """Get all orders from Clover for a date range, with pagination and filtering."""
        # Always set start_date to midnight and end_date to end of day in America/Chicago
        if start_date:
            central = pytz.timezone('America/Chicago')
            start_date = start_date.astimezone(central).replace(hour=0, minute=0, second=0, microsecond=0)
        if end_date:
            central = pytz.timezone('America/Chicago')
            end_date = end_date.astimezone(central).replace(hour=23, minute=59, second=59, microsecond=999000)
        # If start_date and end_date are the same day, ensure end_date is end of that day
        if start_date and end_date and start_date.date() == end_date.date():
            end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=999000)
        if not start_date and not end_date:
            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now()
        elif not start_date:
            start_date = end_date - timedelta(days=30)

        # Log the local and UTC times for debugging
        if start_date:
            central = pytz.timezone('America/Chicago')
            start_local = start_date.astimezone(central)
            start_utc = start_local.astimezone(pytz.utc)
            logging.info(f"Clover order fetch: start_date Chicago={start_local}, UTC={start_utc}, ms={int(start_utc.timestamp() * 1000)}")
        if end_date:
            central = pytz.timezone('America/Chicago')
            end_local = end_date.astimezone(central)
            end_utc = end_local.astimezone(pytz.utc)
            logging.info(f"Clover order fetch: end_date Chicago={end_local}, UTC={end_utc}, ms={int(end_utc.timestamp() * 1000)}")

        # Convert to UTC if not already
        central = pytz.timezone('America/Chicago')
        if start_date:
            start_date = start_date.astimezone(pytz.utc)
        if end_date:
            end_date = end_date.astimezone(pytz.utc)

        base_url = f"{self.config.api_base_url}/{self.config.api_version}/merchants/{self.config.merchant_id}/orders"
        all_orders = []
        offset = 0
        page_limit = 100
        start_ms = int(start_date.timestamp() * 1000)
        end_ms = int(end_date.timestamp() * 1000)
        
        while True:
            # Build URL with multiple filter parameters (not comma-separated)
            params = [
                f"limit={page_limit}",
                f"offset={offset}",
                "expand=lineItems",
                "expand=lineItems.item",
                "expand=lineItems.item.categories",
                f"filter=createdTime>={start_ms}",
                f"filter=createdTime<={end_ms}"
            ]
            url = f"{base_url}?{'&'.join(params)}"
            logger.info(f"Debug Clover Orders URL (offset={offset}): {url}")
            try:
                self._rate_limit()
                response = self.session.get(url, headers={
                    "Authorization": f"Bearer {self.config.access_token}",
                    "Content-Type": "application/json"
                })
                logger.info(f"Clover Orders Response (offset={offset}): {response.status_code}")
                response.raise_for_status()
                data = response.json()
                orders = data.get('orders', data.get('elements', []))
                if not orders:
                    logger.info(f"No more orders found at offset {offset}.")
                    break
                all_orders.extend(orders)
                logger.info(f"Fetched {len(orders)} orders at offset {offset} (total so far: {len(all_orders)})")
                if len(orders) < page_limit:
                    logger.info(f"Last page reached at offset {offset}.")
                    break
                offset += page_limit
            except requests.exceptions.HTTPError as e:
                logger.error(f"Clover API request failed at offset {offset}: {e}")
                logger.error(f"Response text: {getattr(e.response, 'text', '')}")
                break
            except Exception as e:
                logger.error(f"Unexpected error in get_orders at offset {offset}: {e}")
                break

        # When filtering orders after fetching, ensure order_date is in America/Chicago and inclusive
        filtered_orders = []
        for order in all_orders:
            order_time_ms = int(order.get('createdTime', 0))
            order_dt_utc = datetime.utcfromtimestamp(order_time_ms / 1000).replace(tzinfo=pytz.utc)
            order_dt_central = order_dt_utc.astimezone(central)
            if start_date <= order_dt_central <= end_date:
                logging.info(f"Including order {order.get('id')} with local date {order_dt_central.date()} and time {order_dt_central}")
                filtered_orders.append(order)
        orders = filtered_orders

        return orders
    
    def get_order_details(self, order_id: str) -> Dict:
        """Get detailed order information including line items"""
        order = self._make_request(f'orders/{order_id}')
        
        # Get line items for this order
        line_items = self._make_request(f'orders/{order_id}/line_items')
        order['line_items'] = line_items.get('elements', [])
        
        # Get payments for this order
        payments = self._make_request(f'orders/{order_id}/payments')
        order['payments'] = payments.get('elements', [])
        
        return order
    
    def get_customers(self) -> List[Dict]:
        """Get all customers"""
        response = self._make_request('customers')
        return response.get('elements', [])
    
    def get_inventory_levels(self, inventory_enabled: bool = True) -> List[Dict]:
        """Get current inventory levels. If inventory_enabled is False, skip stockCount/quantity."""
        params = {'expand': 'categories'}
        response = self._make_request('items', data=params)
        items = response.get('elements', [])
        
        inventory_data = []
        for item in items:
            # If inventory is not enabled for this tenant, skip stockCount/quantity
            if not inventory_enabled:
                inventory_data.append({
                    'item_id': item['id'],
                    'name': item['name'],
                    'current_stock': None,
                    'reorder_point': None,
                    'category': self._extract_category(item)
                })
                continue
            if 'stockCount' in item:
                category = self._extract_category(item)
                inventory_data.append({
                    'item_id': item['id'],
                    'name': item['name'],
                    'current_stock': item.get('stockCount', 0),
                    'reorder_point': item.get('reorderPoint', 0),
                    'category': category
                })
        return inventory_data

    def _extract_category(self, item):
        category = 'Uncategorized'
        if 'categories' in item and item['categories'] and isinstance(item['categories'], dict):
            elements = item['categories'].get('elements', [])
            if elements:
                category = elements[0].get('name', 'Uncategorized')
        return category
    
    def sync_sales_data(self, start_date: datetime = None, end_date: datetime = None) -> Dict:
        """Sync sales data from Clover to local database (Read-Only)"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        try:
            # Get orders from Clover
            orders = self.get_orders(start_date, end_date)
            
            synced_count = 0
            error_count = 0
            
            for order in orders:
                try:
                    # Get detailed order information
                    order_details = self.get_order_details(order['id'])
                    
                    # Process line items
                    for line_item in order_details.get('line_items', []):
                        sale_data = {
                            'clover_id': line_item['id'],
                            'item_id': line_item.get('item', {}).get('id'),
                            'line_item_date': datetime.fromtimestamp(order['createdTime'] / 1000),
                            'order_employee_id': order.get('employee', {}).get('id'),
                            'order_employee_name': order.get('employee', {}).get('name', 'Unknown'),
                            'order_id': order['id'],
                            'quantity': line_item.get('quantity', 0),
                            'item_revenue': float(line_item.get('price', 0)) / 100,  # Clover uses cents
                            'modifiers_revenue': float(line_item.get('modifications', {}).get('total', 0)) / 100,
                            'total_revenue': float(line_item.get('total', 0)) / 100,
                            'discounts': float(line_item.get('discounts', {}).get('total', 0)) / 100,
                            'tax_amount': float(line_item.get('taxRates', {}).get('total', 0)) / 100,
                            'item_total_with_tax': float(line_item.get('total', 0)) / 100,
                            'payment_state': order.get('state', 'unknown')
                        }
                        
                        # Check if sale already exists
                        existing_sale = db.session.query(Sale).filter_by(clover_id=sale_data['clover_id']).first()
                        if not existing_sale:
                            sale = Sale(**sale_data)
                            db.session.add(sale)
                            synced_count += 1
                    
                    db.session.commit()
                    
                except Exception as e:
                    logger.error(f"Error syncing order {order['id']}: {e}")
                    error_count += 1
                    db.session.rollback()
            
            return {
                'status': 'success',
                'synced_count': synced_count,
                'error_count': error_count,
                'total_orders': len(orders)
            }
            
        except Exception as e:
            logger.error(f"Sales sync failed: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def sync_inventory_data(self) -> Dict:
        """Sync inventory data from Clover to local database (Read-Only)"""
        try:
            inventory_data = self.get_inventory_levels()
            
            updated_count = 0
            created_count = 0
            
            for item_data in inventory_data:
                try:
                    # Check if item exists in local database
                    existing_item = db.session.query(Item).filter_by(clover_id=item_data['item_id']).first()
                    
                    if existing_item:
                        # Update existing item
                        existing_item.quantity = item_data['current_stock']
                        existing_item.reorder_point = item_data['reorder_point']
                        existing_item.updated_at = datetime.utcnow()
                        updated_count += 1
                    else:
                        # Create new item in local database
                        new_item = Item(
                            clover_id=item_data['item_id'],
                            name=item_data['name'],
                            category=item_data['category'],
                            quantity=item_data['current_stock'],
                            reorder_point=item_data['reorder_point'],
                            is_active=True
                        )
                        db.session.add(new_item)
                        created_count += 1
                    
                    db.session.commit()
                    
                except Exception as e:
                    logger.error(f"Error syncing item {item_data['item_id']}: {e}")
                    db.session.rollback()
            
            return {
                'status': 'success',
                'updated_count': updated_count,
                'created_count': created_count,
                'total_items': len(inventory_data)
            }
            
        except Exception as e:
            logger.error(f"Inventory sync failed: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_real_time_data(self) -> Dict[str, Any]:
        """Get real-time dashboard data"""
        try:
            # Get today's date range
            today = datetime.now().date()
            today_start = datetime.combine(today, datetime.min.time())
            today_end = datetime.combine(today, datetime.max.time())
            
            # Get today's orders
            today_orders = self.get_orders(today_start, today_end)
            
            # Get inventory levels
            inventory = self.get_inventory_levels()
            
            # Get employees
            employees = self.get_employees()
            
            # Calculate metrics
            total_sales = sum(order.get('total', 0) for order in today_orders)
            order_count = len(today_orders)
            low_stock_items = [item for item in inventory if item.get('current_stock', 0) < 10]
            
            return {
                'today_sales': total_sales,
                'today_orders': order_count,
                'total_employees': len(employees),
                'low_stock_items': len(low_stock_items),
                'last_updated': datetime.now().isoformat(),
                'orders': today_orders[:10],  # Limit to 10 most recent
                'inventory_alerts': low_stock_items[:5]  # Top 5 low stock items
            }
        except Exception as e:
            logger.error(f"Real-time data fetch failed: {e}")
            return {
                'error': str(e),
                'today_sales': 0,
                'today_orders': 0,
                'total_employees': 0,
                'low_stock_items': 0,
                'last_updated': datetime.now().isoformat()
            } 