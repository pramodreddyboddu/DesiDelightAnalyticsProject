from datetime import datetime, timedelta, timezone
import time
from sqlalchemy import func, and_, or_
from ..models import db, Sale, Expense, Item, Chef, ChefDishMapping, UncategorizedItem, FileUpload
import logging
from flask import current_app
from .clover_service import CloverService, CloverConfig
import os
import json
from src.models.data_source_config import DataSourceConfig
import pytz  # Add this import at the top if not present

class DashboardService:
    def __init__(self):
        clover_config = CloverConfig(
            merchant_id=os.getenv('CLOVER_MERCHANT_ID', ''),
            access_token=os.getenv('CLOVER_ACCESS_TOKEN', '')
        )
        self.clover_service = CloverService(clover_config)
        # Configuration for data sources
        self.data_sources = {
            'sales': 'clover',  # 'clover' or 'local'
            'inventory': 'clover',  # 'clover' or 'local'
            'expenses': 'local',  # Always local since Clover doesn't have expenses
            'chef_mapping': 'local',  # Always local since this is custom data
        }
        
        # Log the configuration
        self.log_data_source_config()
        # In-memory cache for Clover inventory
        self._clover_inventory_cache = None
        self._clover_inventory_cache_time = 0
        self._clover_inventory_cache_ttl = 600  # 10 minutes
    
    def get_data_source(self, data_type, tenant_id=None):
        if data_type == 'inventory':
            return 'clover'
        # Try DB config first
        config = None
        if tenant_id:
            config = DataSourceConfig.query.filter_by(tenant_id=tenant_id, data_type=data_type).first()
        if not config:
            config = DataSourceConfig.query.filter_by(tenant_id=None, data_type=data_type).first()
        if config:
            return config.source
        # Fallback to in-memory config for backward compatibility
        return self.data_sources.get(data_type, 'local')
    
    def get_sales_summary(self, start_date=None, end_date=None, category=None):
        """Get sales summary from configured data source"""
        try:
            data_source = self.get_data_source('sales')
            logging.info(f"Getting sales summary from data source: {data_source} | start_date={start_date}, end_date={end_date}, category={category}")
            
            if data_source == 'clover':
                logging.info("About to call _get_clover_sales_summary")
                result = self._get_clover_sales_summary(start_date, end_date, category)
                logging.info("Successfully called _get_clover_sales_summary")
            else:
                logging.info("About to call _get_local_sales_summary")
                result = self._get_local_sales_summary(start_date, end_date, category)
                logging.info("Successfully called _get_local_sales_summary")
            
            # Extra logging for debugging
            logging.info(f"Sales summary result: {json.dumps(result, default=str)}")
            return result
        except Exception as e:
            logging.error(f"Exception in get_sales_summary: {str(e)}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            # Return empty summary on error
            return self._empty_sales_summary()
    
    def get_inventory_data(self, inventory_enabled=True):
        """Get inventory data from configured data source"""
        data_source = self.get_data_source('inventory')
        logging.info(f"Getting inventory data from data source: {data_source}")
        
        if data_source == 'clover':
            result = self._get_clover_inventory_data(inventory_enabled=inventory_enabled)
        else:
            result = self._get_local_inventory_data()
        
        logging.info(f"Inventory data result: {json.dumps(result, default=str)}")
        return result
    
    def get_expenses_data(self, start_date=None, end_date=None):
        """Get expenses data (always from local database)"""
        result = self._get_local_expenses_data(start_date, end_date)
        logging.info(f"Expenses data result: {json.dumps(result, default=str)}")
        return result
    
    def get_chef_performance_data(self, start_date=None, end_date=None, chef_ids=None):
        """
        Get chef performance data using the configured data source.
        If sales data source is 'clover', use live Clover API for real-time data.
        If sales data source is 'local', use local database.
        """
        print("=== get_chef_performance_data called ===")
        data_source = self.get_data_source('sales')
        print(f"Chef performance data source: {data_source}")
        logging.info(f"Chef performance data source: {data_source}")
        
        if data_source == 'clover':
            print("Using Clover API for chef performance data")
            logging.info("Using Clover API for chef performance data")
            # Use live Clover API for real-time chef performance data
            result = self._get_clover_chef_performance_data(start_date, end_date, chef_ids)
            print(f"Clover API result: {result}")
            return result
        else:
            print("Using local database for chef performance data")
            logging.info("Using local database for chef performance data")
            # Use local database for chef performance data
            result = self._get_local_chef_performance_data(start_date, end_date, chef_ids)
            print(f"Local DB result: {result}")
            return result
    
    def _get_clover_sales_summary(self, start_date=None, end_date=None, category=None):
        """Get sales summary from Clover API"""
        try:
            logging.info("Attempting to get sales data from Clover...")
            # Get orders from Clover
            orders_response = self.clover_service.get_orders(start_date, end_date)
            logging.info(f"Retrieved orders response from Clover: {type(orders_response)}")
            # Handle different response formats from Clover API
            if isinstance(orders_response, dict):
                orders = orders_response.get('orders', [])  # Use 'orders' key, not 'elements'
            elif isinstance(orders_response, list):
                orders = orders_response
            else:
                logging.warning(f"Unexpected orders response format: {type(orders_response)}")
                orders = []
            logging.info(f"Retrieved {len(orders) if orders else 0} orders from Clover")
            if not orders:
                logging.warning("No orders found in Clover, returning empty summary")
                return self._empty_sales_summary()
            # Filter by date range if provided
            if start_date or end_date:
                orders = self._filter_orders_by_date(orders, start_date, end_date)
                logging.info(f"After date filtering: {len(orders)} orders")
            # Parse category filter as list
            category_list = None
            if category and category != 'all':
                category_list = [c.strip() for c in category.split(',') if c.strip()]
            # Process orders and apply category filter
            return self._process_clover_orders(orders, category_list)
        except Exception as e:
            logging.error(f"Exception in _get_clover_sales_summary: {str(e)}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            return self._empty_sales_summary()
    
    def _get_clover_inventory_data(self, inventory_enabled=True):
        """Get inventory data from Clover API, mapping categories by item ID using item category IDs."""
        try:
            now = time.time()
            if (
                self._clover_inventory_cache is not None and
                (now - self._clover_inventory_cache_time) < self._clover_inventory_cache_ttl
            ):
                logging.info("Using cached Clover inventory data.")
                return self._clover_inventory_cache
            logging.info("Refreshing Clover inventory cache...")
            
            # For tenants without inventory management, get items without stockCount
            if not inventory_enabled:
                logging.info("Tenant has no inventory management - skipping stockCount/quantity")
                # Get items directly without inventory levels
                items = self.clover_service.get_items()
                logging.info(f"Retrieved {len(items) if items else 0} items from Clover (no inventory)")
                
                # Process items without stockCount
                inventory_data = self._process_clover_items_no_inventory(items)
                logging.info(f"Processed inventory data: {inventory_data.get('total', 0)} items")
                self._clover_inventory_cache = inventory_data
                self._clover_inventory_cache_time = now
                return inventory_data
            
            # Step 1: Fetch all categories and build id->name mapping
            categories = self.clover_service.get_categories()
            cat_id_to_name = {cat.get('id'): cat.get('name', 'Uncategorized') for cat in categories if cat.get('id')}
            # Step 2: Fetch all items (all pages)
            items = self.clover_service.get_items()
            logging.info(f"Retrieved {len(items) if items else 0} items from Clover")
            # Step 3: Process items, using the mapping
            inventory_data = self._process_clover_items(items, cat_id_to_name)
            logging.info(f"Processed inventory data: {inventory_data.get('total', 0)} items")
            self._clover_inventory_cache = inventory_data
            self._clover_inventory_cache_time = now
            return inventory_data
        except Exception as e:
            logging.error(f"Error getting Clover inventory data: {str(e)}")
            logging.info("Falling back to local inventory data...")
            return self._get_local_inventory_data()
    
    def _get_local_sales_summary(self, start_date=None, end_date=None, category=None):
        """Get sales summary from local database"""
        try:
            # Build base query
            query = db.session.query(Sale).join(Item, Sale.item_id == Item.id)
            
            # Apply filters
            if start_date:
                query = query.filter(Sale.line_item_date >= start_date)
            if end_date:
                query = query.filter(Sale.line_item_date <= end_date)
            if category and category != 'all':
                query = query.filter(Item.category == category)
            
            # Get total revenue
            total_revenue = query.with_entities(func.sum(Sale.total_revenue)).scalar() or 0
            
            # Get unique order count (for category: only orders with at least one item in that category)
            if category and category != 'all':
                unique_order_ids = set([row[0] for row in db.session.query(Sale.order_id).join(Item, Sale.item_id == Item.id)
                                        .filter(Sale.line_item_date >= start_date if start_date else True)
                                        .filter(Sale.line_item_date <= end_date if end_date else True)
                                        .filter(Item.category == category)
                                        .distinct()])
                unique_order_count = len(unique_order_ids)
            else:
                unique_order_count = query.with_entities(func.count(func.distinct(Sale.order_id))).scalar() or 0
            
            # Get category-wise breakdown
            category_breakdown = db.session.query(
                Item.category,
                func.sum(Sale.total_revenue).label('revenue'),
                func.count(Sale.id).label('count')
            ).join(Item, Sale.item_id == Item.id)
            
            if start_date:
                category_breakdown = category_breakdown.filter(Sale.line_item_date >= start_date)
            if end_date:
                category_breakdown = category_breakdown.filter(Sale.line_item_date <= end_date)
            
            category_breakdown = category_breakdown.group_by(Item.category).all()
            
            # Get top selling items
            top_items = db.session.query(
                Item.name,
                Item.category,
                func.sum(Sale.total_revenue).label('revenue'),
                func.count(Sale.id).label('count')
            ).join(Item, Sale.item_id == Item.id)
            
            if start_date:
                top_items = top_items.filter(Sale.line_item_date >= start_date)
            if end_date:
                top_items = top_items.filter(Sale.line_item_date <= end_date)
            if category and category != 'all':
                top_items = top_items.filter(Item.category == category)
            
            top_items = top_items.group_by(Item.id, Item.name, Item.category)\
                                .order_by(func.sum(Sale.total_revenue).desc())\
                                .limit(10).all()
            
            # Get daily sales trend
            daily_sales = db.session.query(
                func.date(Sale.line_item_date).label('date'),
                func.sum(Sale.total_revenue).label('revenue')
            ).join(Item, Sale.item_id == Item.id)
            
            if start_date:
                daily_sales = daily_sales.filter(Sale.line_item_date >= start_date)
            if end_date:
                daily_sales = daily_sales.filter(Sale.line_item_date <= end_date)
            if category and category != 'all':
                daily_sales = daily_sales.filter(Item.category == category)
            
            daily_sales = daily_sales.group_by(func.date(Sale.line_item_date))\
                                    .order_by(func.date(Sale.line_item_date)).all()
            
            return {
                'total_revenue': float(total_revenue),
                'total_transactions': unique_order_count,
                'category_breakdown': [
                    {
                        'category': cat,
                        'revenue': float(rev) if rev is not None else 0,
                        'count': count
                    }
                    for cat, rev, count in category_breakdown
                ],
                'top_items': [
                    {
                        'name': name,
                        'category': cat,
                        'revenue': float(rev) if rev is not None else 0,
                        'count': count
                    }
                    for name, cat, rev, count in top_items
                ],
                'daily_sales': [
                    {
                        'date': date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date) if date else None,
                        'revenue': float(rev) if rev is not None else 0
                    }
                    for date, rev in daily_sales
                ]
            }
            
        except Exception as e:
            logging.error(f"Error getting local sales data: {str(e)}")
            return self._empty_sales_summary()
    
    def _get_local_inventory_data(self):
        """Get inventory data from local database"""
        try:
            items_query = Item.query.filter_by(is_active=True)\
                .with_entities(
                    Item.id,
                    Item.name,
                    Item.category,
                    Item.price,
                    Item.quantity,
                    Item.sku,
                    Item.product_code,
                    Item.updated_at
                )\
                .order_by(Item.category, Item.name)
            
            items = items_query.all()
            
            items_data = [{
                'id': item.id,
                'name': item.name,
                'category': item.category,
                'price': float(item.price) if item.price else 0.0,
                'quantity': item.quantity,
                'sku': item.sku,
                'product_code': item.product_code,
                'last_updated': item.updated_at.isoformat() if item.updated_at else None
            } for item in items]
            
            return {
                'items': items_data,
                'total': len(items_data)
            }
            
        except Exception as e:
            logging.error(f"Error getting local inventory data: {str(e)}")
            return {'items': [], 'total': 0}
    
    def _get_local_expenses_data(self, start_date=None, end_date=None):
        """Get expenses data from local database"""
        try:
            query = Expense.query
            
            if start_date:
                query = query.filter(Expense.date >= start_date)
            if end_date:
                query = query.filter(Expense.date <= end_date)
            
            expenses = query.all()
            
            total_expenses = sum(expense.amount for expense in expenses)
            
            # Group by category
            category_breakdown = {}
            for expense in expenses:
                category = expense.category or 'Uncategorized'
                if category not in category_breakdown:
                    category_breakdown[category] = {'amount': 0, 'count': 0}
                category_breakdown[category]['amount'] += expense.amount
                category_breakdown[category]['count'] += 1
            
            return {
                'total_expenses': float(total_expenses),
                'expense_count': len(expenses),
                'category_breakdown': [
                    {
                        'category': cat,
                        'amount': float(data['amount']),
                        'count': data['count']
                    }
                    for cat, data in category_breakdown.items()
                ],
                'expenses': [
                    {
                        'id': expense.id,
                        'description': expense.description,
                        'amount': float(expense.amount),
                        'category': expense.category,
                        'date': expense.date.isoformat() if expense.date else None
                    }
                    for expense in expenses
                ]
            }
            
        except Exception as e:
            logging.error(f"Error getting expenses data: {str(e)}")
            return {
                'total_expenses': 0.0,
                'expense_count': 0,
                'category_breakdown': [],
                'expenses': []
            }
    
    def _get_local_chef_performance_data(self, start_date=None, end_date=None, chef_ids=None):
        """Get chef performance data from local database, excluding 'Unassigned' chef and reporting unmapped items."""
        try:
            # Get all real chefs (exclude 'Unassigned' and only keep the 4 real chefs)
            allowed_chefs = ["Sarva&Ram", "Savithri", "Wasim", "Chef_miscellanies"]
            real_chefs = {chef.id: chef.name for chef in Chef.query.filter(Chef.name.in_(allowed_chefs)).all()}
            logging.info(f"Found {len(real_chefs)} real chefs: {list(real_chefs.values())}")
            # Build base query for chef performance
            query = (
                db.session.query(
                    Chef.name.label('chef_name'),
                    Item.name.label('item_name'),
                    Item.category,
                    func.sum(Sale.total_revenue).label('revenue'),
                    func.count(Sale.id).label('count')
                )
                .join(ChefDishMapping, Chef.id == ChefDishMapping.chef_id)
                .join(Item, ChefDishMapping.item_id == Item.id)
                .join(Sale, Item.id == Sale.item_id)
                .filter(Chef.id.in_(real_chefs))
            )
            # Apply filters
            if start_date:
                query = query.filter(Sale.line_item_date >= start_date)
            if end_date:
                query = query.filter(Sale.line_item_date <= end_date)
            if chef_ids and chef_ids != 'all':
                try:
                    chef_id_list = [int(id_str) for id_str in chef_ids.split(',')]
                    query = query.filter(Chef.id.in_(chef_id_list))
                except ValueError:
                    logging.error(f"Invalid chef_ids format: {chef_ids}")
                    return {'error': 'Invalid chef_ids format'}
            # Group by chef and item
            chef_performance = query.group_by(Chef.id, Chef.name, Item.id, Item.name, Item.category).all()
            # Get chef summary
            chef_summary = db.session.query(
                Chef.id,
                Chef.name,
                func.sum(Sale.total_revenue).label('total_revenue'),
                func.count(Sale.id).label('total_sales')
            )\
            .join(ChefDishMapping, Chef.id == ChefDishMapping.chef_id)\
            .join(Item, ChefDishMapping.item_id == Item.id)\
            .join(Sale, Item.id == Sale.item_id)\
            .filter(Chef.id.in_(real_chefs))
            # Apply the same filters to summary
            if start_date:
                chef_summary = chef_summary.filter(Sale.line_item_date >= start_date)
            if end_date:
                chef_summary = chef_summary.filter(Sale.line_item_date <= end_date)
            if chef_ids and chef_ids != 'all':
                try:
                    chef_id_list = [int(id_str) for id_str in chef_ids.split(',')]
                    chef_summary = chef_summary.filter(Chef.id.in_(chef_id_list))
                except ValueError:
                    pass
            chef_summary = chef_summary.group_by(Chef.id, Chef.name).all()
            # Find unmapped items with sales
            mapped_item_ids = set(row[0] for row in db.session.query(ChefDishMapping.item_id).all())
            sales_items = set(row[0] for row in db.session.query(Sale.item_id).all())
            unmapped_items = sales_items - mapped_item_ids
            unmapped_items_count = len(unmapped_items)
            warning = None
            if unmapped_items_count > 0:
                warning = f"There are {unmapped_items_count} items with sales that are not mapped to any chef. Please update your chef mapping file."
            return {
                'chef_performance': [
                    {
                        'chef_name': chef_name,
                        'item_name': item_name,
                        'category': category,
                        'revenue': float(revenue) if revenue is not None else 0,
                        'count': count
                    }
                    for chef_name, item_name, category, revenue, count in chef_performance
                ],
                'chef_summary': [
                    {
                        'id': chef_id,
                        'name': chef_name,
                        'total_revenue': float(total_revenue) if total_revenue is not None else 0,
                        'total_sales': total_sales
                    }
                    for chef_id, chef_name, total_revenue, total_sales in chef_summary
                ],
                'unmapped_items_warning': warning,
                'unmapped_items_count': unmapped_items_count
            }
        except Exception as e:
            logging.error(f"Error getting chef performance data: {str(e)}")
            return {
                'chef_performance': [],
                'chef_summary': [],
                'unmapped_items_warning': str(e),
                'unmapped_items_count': 0
            }
    
    def _empty_sales_summary(self):
        """Return empty sales summary structure"""
        return {
            'total_revenue': 0.0,
            'total_transactions': 0,
            'category_breakdown': [],
            'top_items': [],
            'daily_sales': []
        }
    
    def _filter_orders_by_date(self, orders, start_date=None, end_date=None):
        """Filter Clover orders by date range"""
        filtered_orders = []
        
        # Ensure start_date and end_date are timezone-aware (UTC)
        if start_date and start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        if end_date and end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        
        for order in orders:
            order_date = None
            try:
                # Try to parse the order date from Clover data
                if 'createdTime' in order:
                    order_date = datetime.fromtimestamp(order['createdTime'] / 1000, tz=timezone.utc)
                elif 'modifiedTime' in order:
                    order_date = datetime.fromtimestamp(order['modifiedTime'] / 1000, tz=timezone.utc)
            except:
                continue
            
            if order_date:
                if start_date and order_date < start_date:
                    continue
                if end_date and order_date > end_date:
                    continue
            
            filtered_orders.append(order)
        
        return filtered_orders
    
    def calculate_order_revenue(self, order):
        # Try using line items first
        line_items = order.get("lineItems", {}).get("elements", [])
        line_item_revenue = 0
        for item in line_items:
            price = item.get("price", 0)
            quantity = item.get("quantity", 1) if item.get("quantity") is not None else 1
            line_item_revenue += price * quantity
        order_total = order.get("total", 0)
        return max(line_item_revenue, order_total) / 100.0  # Convert cents to dollars

    def _process_clover_orders(self, orders, category=None):
        """Process Clover orders, extract categories correctly, and apply filters"""
        try:
            import json
            logging.warning(f"_process_clover_orders called with {len(orders)} orders. Sample: {json.dumps(orders[0], default=str)[:1000] if orders else 'None'}")
            total_revenue = 0
            order_ids = set()
            category_order_ids = set()
            category_revenue = {}
            item_revenue = {}
            daily_revenue = {}
            for order in orders:
                order_id = order.get('id')
                order_ids.add(order_id)
                order_date = datetime.fromtimestamp(order['createdTime'] / 1000).strftime('%Y-%m-%d')
                line_items = order.get('lineItems', {}).get('elements', [])
                if not isinstance(order.get('lineItems'), dict):
                    logging.error(f"Order {order_id} missing or malformed lineItems: {json.dumps(order, default=str)[:1000]}")
                if not line_items:
                    # Fallback: use order-level total if no line items
                    order_total = float(order.get('total', 0)) / 100
                    logging.warning(f"Order {order_id} has no lineItems, using order total: {order_total}")
                    total_revenue += order_total
                    daily_revenue.setdefault(order_date, 0)
                    daily_revenue[order_date] += order_total
                    continue
                order_has_category = False
                for li in line_items:
                    # Extract category from item.categories
                    cat = 'Uncategorized'
                    item = li.get('item', {})
                    categories = item.get('categories', {}).get('elements', [])
                    if categories and isinstance(categories, list):
                        cat = categories[0].get('name', 'Uncategorized')
                    # Category filter: if category is a list, only include if cat in list
                    if category and isinstance(category, list) and 'all' not in category and cat not in category:
                        continue
                    order_has_category = True
                    # Revenue extraction: use total if present and >0, else price * quantity
                    total_cents = li.get('total', 0)
                    price_cents = li.get('price', 0)
                    quantity = li.get('quantity', 1)
                    if total_cents:
                        revenue = float(total_cents) / 100
                    else:
                        revenue = float(price_cents) * float(quantity) / 100
                    logging.debug(f"Processing line item: {json.dumps(li, default=str)}")
                    logging.debug(f"Line item revenue: {revenue} (raw total: {li.get('total', None)}, price: {price_cents}, quantity: {quantity})")
                    if revenue == 0:
                        logging.warning(f"ZERO revenue line item: {json.dumps(li, default=str)}")
                    total_revenue += revenue
                    category_revenue.setdefault(cat, {'revenue': 0, 'count': 0})
                    category_revenue[cat]['revenue'] += revenue
                    category_revenue[cat]['count'] += quantity
                    item_name = item.get('name', 'Unknown')
                    item_revenue.setdefault(item_name, {'name': item_name, 'category': cat, 'revenue': 0, 'count': 0})
                    item_revenue[item_name]['revenue'] += revenue
                    item_revenue[item_name]['count'] += quantity
                    daily_revenue.setdefault(order_date, 0)
                    daily_revenue[order_date] += revenue
                if category and order_has_category:
                    category_order_ids.add(order_id)
            # For total_transactions: if category filter, use category_order_ids, else all order_ids
            if category:
                total_transactions = len(category_order_ids)
            else:
                total_transactions = len(order_ids)
            category_breakdown = [
                {'category': cat, 'revenue': float(data['revenue']), 'count': data['count']}
                for cat, data in category_revenue.items()
            ]
            top_items = sorted(list(item_revenue.values()), key=lambda x: x['revenue'], reverse=True)[:10]
            daily_sales = [
                {'date': date, 'revenue': float(revenue)}
                for date, revenue in sorted(daily_revenue.items())
            ]
            logging.info(f"Total revenue calculated from Clover orders: {total_revenue}")
            return {
                'total_revenue': float(total_revenue),
                'total_transactions': total_transactions,
                'category_breakdown': category_breakdown,
                'top_items': top_items,
                'daily_sales': daily_sales
            }
        except Exception as e:
            logging.error(f"Error processing Clover orders: {str(e)}")
            return self._empty_sales_summary()
    
    def _process_clover_items_no_inventory(self, items):
        """Process Clover items for tenants without inventory management (no stockCount/quantity)."""
        try:
            processed_items = []
            for idx, item in enumerate(items):
                if idx < 5:
                    import json
                    logging.info(f"Full Clover item (no inventory): {json.dumps(item, indent=2)}")
                
                # Extract category
                category = 'Uncategorized'
                if 'categories' in item and item['categories'] and isinstance(item['categories'], dict):
                    elements = item['categories'].get('elements', [])
                    if elements:
                        category = elements[0].get('name', 'Uncategorized')
                
                processed_item = {
                    'id': item.get('id', ''),
                    'name': item.get('name', 'Unknown Item'),
                    'category': category,
                    'price': float(item.get('price', 0)) / 100,  # Clover prices are in cents
                    'quantity': None,  # No inventory management
                    'sku': item.get('sku', ''),
                    'product_code': item.get('code', ''),
                    'last_updated': None
                }
                if 'modifiedTime' in item:
                    try:
                        modified_time = datetime.fromtimestamp(item['modifiedTime'] / 1000, tz=timezone.utc)
                        processed_item['last_updated'] = modified_time.isoformat()
                    except:
                        pass
                processed_items.append(processed_item)
            return {
                'items': processed_items,
                'total': len(processed_items)
            }
        except Exception as e:
            logging.error(f"Error processing Clover items (no inventory): {str(e)}")
            return {'items': [], 'total': 0}
    
    def _process_clover_items(self, items, cat_id_to_name=None):
        """Process Clover items to match local inventory format, using category ID mapping if provided."""
        try:
            processed_items = []
            for idx, item in enumerate(items):
                if idx < 5:
                    import json
                    logging.info(f"Full Clover item: {json.dumps(item, indent=2)}")
                # Use category ID mapping if available
                category = 'Uncategorized'
                if cat_id_to_name and ('categories' in item or 'categoryIds' in item):
                    # Try both possible fields
                    cat_ids = []
                    if 'categories' in item and item['categories'] and isinstance(item['categories'], dict):
                        elements = item['categories'].get('elements', [])
                        cat_ids = [cat.get('id') for cat in elements if cat.get('id')]
                    elif 'categoryIds' in item and isinstance(item['categoryIds'], list):
                        cat_ids = item['categoryIds']
                    category_names = [cat_id_to_name.get(cid) for cid in cat_ids if cid in cat_id_to_name]
                    if category_names:
                        category = ', '.join(category_names)
                processed_item = {
                    'id': item.get('id', ''),
                    'name': item.get('name', 'Unknown Item'),
                    'category': category,
                    'price': float(item.get('price', 0)) / 100,  # Clover prices are in cents
                    'quantity': item.get('stockCount', 0),
                    'sku': item.get('sku', ''),
                    'product_code': item.get('code', ''),
                    'last_updated': None
                }
                if 'modifiedTime' in item:
                    try:
                        modified_time = datetime.fromtimestamp(item['modifiedTime'] / 1000, tz=timezone.utc)
                        processed_item['last_updated'] = modified_time.isoformat()
                    except:
                        pass
                processed_items.append(processed_item)
            return {
                'items': processed_items,
                'total': len(processed_items)
            }
        except Exception as e:
            logging.error(f"Error processing Clover items: {str(e)}")
            return {'items': [], 'total': 0}
    
    def clear_clover_cache(self):
        """Clear the Clover inventory cache to force a fresh fetch"""
        self._clover_inventory_cache = None
        self._clover_inventory_cache_time = 0
        logging.info("Cleared Clover inventory cache")
    
    def update_data_source_config(self, new_config):
        """Update the data source configuration"""
        self.data_sources.update(new_config)
        # Clear cache when switching data sources
        if 'inventory' in new_config:
            self.clear_clover_cache()
        logging.info(f"Updated data source configuration: {self.data_sources}")
    
    def get_data_source_status(self):
        """Get status of all data sources with proper tenant support and error handling"""
        status = {}
        
        # Get current tenant from session if available
        from flask import session
        tenant_id = session.get('tenant_id')
        
        for data_type in ['sales', 'inventory', 'expenses', 'chef_mapping']:
            try:
                # Get configured source for this data type
                source = self.get_data_source(data_type, tenant_id)
                
                if source == 'clover':
                    # Test Clover connection
                    try:
                        if data_type == 'sales':
                            test_data = self.clover_service.get_orders(limit=1)  # Just test with 1 order
                        elif data_type == 'inventory':
                            test_data = self.clover_service.get_items()  # Remove limit parameter
                        else:
                            test_data = None
                        
                        status[data_type] = {
                            'source': source,
                            'status': 'connected' if test_data is not None else 'error',
                            'last_sync': datetime.now().isoformat(),
                            'tenant_id': tenant_id
                        }
                    except Exception as e:
                        logging.error(f"Clover connection test failed for {data_type}: {str(e)}")
                        status[data_type] = {
                            'source': source,
                            'status': 'error',
                            'error': str(e),
                            'last_sync': None,
                            'tenant_id': tenant_id
                        }
                else:
                    # Local data source - always connected
                    status[data_type] = {
                        'source': source,
                        'status': 'connected',
                        'last_sync': datetime.now().isoformat(),
                        'tenant_id': tenant_id
                    }
                    
            except Exception as e:
                logging.error(f"Error checking status for {data_type}: {str(e)}")
                status[data_type] = {
                    'source': 'unknown',
                    'status': 'error',
                    'error': str(e),
                    'last_sync': None,
                    'tenant_id': tenant_id
                }
        
        return status

    @staticmethod
    def parse_date(date_str):
        """Parse date string to datetime object"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            logging.warning(f"Invalid date format: {date_str}")
            return None

    @staticmethod
    def get_sales_summary_static(start_date, end_date, category=None):
        """Get sales summary data"""
        try:
            # Debug logging
            logging.info(f"get_sales_summary_static called with start_date: {start_date}, end_date: {end_date}, category: {category}")
            
            # Build base query with join to Item
            query = db.session.query(Sale).join(Item)
            
            # Apply date filters
            if start_date:
                query = query.filter(Sale.line_item_date >= start_date)
                logging.info(f"Applied start_date filter: {start_date}")
            if end_date:
                query = query.filter(Sale.line_item_date <= end_date)
                logging.info(f"Applied end_date filter: {end_date}")
            
            # Get total sales
            total_sales = query.with_entities(func.sum(Sale.total_revenue)).scalar() or 0
            logging.info(f"Total sales after date filters: {total_sales}")
            
            # Get total orders
            total_orders = query.count()
            logging.info(f"Total orders after date filters: {total_orders}")
            
            # Get average order value
            avg_order_value = total_sales / total_orders if total_orders > 0 else 0
            
            # Get category-wise breakdown if category filter is applied
            category_breakdown = db.session.query(
                Item.category,
                func.sum(Sale.total_revenue).label('amount'),
                func.count(Sale.id).label('count')
            ).join(Sale, Sale.item_id == Item.id)
            
            if start_date:
                category_breakdown = category_breakdown.filter(Sale.line_item_date >= start_date)
            if end_date:
                category_breakdown = category_breakdown.filter(Sale.line_item_date <= end_date)
            if category and category != 'all':
                category_breakdown = category_breakdown.filter(Item.category == category)
            
            category_breakdown = category_breakdown.group_by(Item.category).all()
            
            # Get daily sales trend
            daily_sales = db.session.query(
                func.date(Sale.line_item_date).label('date'),
                func.sum(Sale.total_revenue).label('amount'),
                func.count(Sale.id).label('orders')
            ).join(Item)
            
            if start_date:
                daily_sales = daily_sales.filter(Sale.line_item_date >= start_date)
            if end_date:
                daily_sales = daily_sales.filter(Sale.line_item_date <= end_date)
            if category and category != 'all':
                daily_sales = daily_sales.filter(Item.category == category)
            
            daily_sales = daily_sales.group_by(func.date(Sale.line_item_date))\
                                   .order_by(func.date(Sale.line_item_date)).all()
            
            return {
                'total_sales': float(total_sales),
                'total_orders': total_orders,
                'avg_order_value': float(avg_order_value),
                'category_breakdown': [
                    {
                        'category': cat,
                        'revenue': float(amt) if amt is not None else 0,
                        'count': count
                    }
                    for cat, amt, count in category_breakdown
                ],
                'daily_sales': [
                    {
                        'date': date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date) if date else None,
                        'amount': float(amt) if amt is not None else 0,
                        'orders': orders
                    }
                    for date, amt, orders in daily_sales
                ]
            }
        except Exception as e:
            logging.error(f"Error in get_sales_summary_static: {str(e)}")
            raise

    @staticmethod
    def get_chef_performance_static(start_date, end_date, chef_ids=None):
        """Get chef performance data"""
        try:
            chef_id_list = None
            if chef_ids:
                try:
                    chef_id_list = [int(id.strip()) for id in chef_ids.split(',')]
                except ValueError:
                    raise ValueError("Invalid chef_ids format. Expected comma-separated integers.")
            
            # Build query with correct relationships: Chef → ChefDishMapping → Item → Sale
            query = db.session.query(
                Chef.id,
                Chef.name,
                func.count(Sale.id).label('orders_handled'),
                func.sum(Sale.total_revenue).label('total_revenue'),
                func.avg(Sale.total_revenue).label('avg_order_value')
            ).join(ChefDishMapping, Chef.id == ChefDishMapping.chef_id)\
             .join(Item, ChefDishMapping.item_id == Item.id)\
             .join(Sale, Item.id == Sale.item_id)
            
            if start_date:
                query = query.filter(Sale.line_item_date >= start_date)
            if end_date:
                query = query.filter(Sale.line_item_date <= end_date)
            if chef_id_list:
                query = query.filter(Chef.id.in_(chef_id_list))
            
            chef_performance = query.group_by(Chef.id, Chef.name).all()
            
            return [
                {
                    'chef_id': chef_id,
                    'chef_name': chef_name,
                    'orders_handled': orders_handled,
                    'total_revenue': float(total_revenue) if total_revenue is not None else 0,
                    'avg_order_value': float(avg_order_value) if avg_order_value is not None else 0
                }
                for chef_id, chef_name, orders_handled, total_revenue, avg_order_value in chef_performance
            ]
        except Exception as e:
            logging.error(f"Error in get_chef_performance_static: {str(e)}")
            raise

    @staticmethod
    def get_profitability_data(start_date, end_date):
        """Get profitability data by category"""
        try:
            # Get sales data by category (join Sale and Item)
            sales_query = db.session.query(
                Item.category,
                func.sum(Sale.total_revenue).label('revenue')
            ).join(Sale, Sale.item_id == Item.id)
            
            if start_date:
                sales_query = sales_query.filter(Sale.line_item_date >= start_date)
            if end_date:
                sales_query = sales_query.filter(Sale.line_item_date <= end_date)
            
            sales_data = sales_query.group_by(Item.category).all()
            
            # Get expenses data by category
            expenses_query = db.session.query(
                Expense.category,
                func.sum(Expense.amount).label('expenses')
            )
            
            if start_date:
                expenses_query = expenses_query.filter(Expense.date >= start_date)
            if end_date:
                expenses_query = expenses_query.filter(Expense.date <= end_date)
            
            expenses_data = expenses_query.group_by(Expense.category).all()
            
            # Create a dictionary for expenses lookup
            expenses_dict = {cat: amt for cat, amt in expenses_data}
            
            # Calculate profitability for each category
            profitability_data = []
            for category, revenue in sales_data:
                expenses = expenses_dict.get(category, 0)
                profit = revenue - expenses
                margin = (profit / revenue * 100) if revenue > 0 else 0
                
                profitability_data.append({
                    'category': category,
                    'revenue': float(revenue),
                    'expenses': float(expenses),
                    'profit': float(profit),
                    'margin': round(margin, 2)
                })
            
            return profitability_data
        except Exception as e:
            logging.error(f"Error in get_profitability_data: {str(e)}")
            raise

    @staticmethod
    def get_recent_activity(limit=10):
        """Get recent activity data"""
        try:
            # Get recent sales
            recent_sales = db.session.query(Sale)\
                .order_by(Sale.line_item_date.desc())\
                .limit(limit//2).all()
            
            # Get recent expenses
            recent_expenses = db.session.query(Expense)\
                .order_by(Expense.date.desc())\
                .limit(limit//2).all()
            
            # Get recent file uploads
            recent_uploads = db.session.query(FileUpload)\
                .order_by(FileUpload.upload_date.desc())\
                .limit(limit//4).all()
            
            # Combine and sort activities
            activities = []
            
            for sale in recent_sales:
                # Get category from related item
                category = sale.item.category if sale.item else 'Unknown'
                activities.append({
                    'type': 'sale',
                    'date': sale.line_item_date,
                    'description': f"Sale of {category} - ${sale.total_revenue}",
                    'amount': sale.total_revenue
                })
            
            for expense in recent_expenses:
                activities.append({
                    'type': 'expense',
                    'date': expense.date,
                    'description': f"Expense: {expense.category} - ${expense.amount}",
                    'amount': -expense.amount
                })
            
            for upload in recent_uploads:
                activities.append({
                    'type': 'upload',
                    'date': upload.upload_date,
                    'description': f"File uploaded: {upload.filename}",
                    'amount': 0
                })
            
            # Sort by date and return top limit
            activities.sort(key=lambda x: x['date'], reverse=True)
            return activities[:limit]
        except Exception as e:
            logging.error(f"Error in get_recent_activity: {str(e)}")
            raise

    def log_data_source_config(self):
        """Log the current data source configuration"""
        logging.info("Current data source configuration:")
        for data_type, source in self.data_sources.items():
            logging.info(f"  {data_type}: {source}")

    def get_dashboard_overview(self, start_date=None, end_date=None):
        """Get restaurant overview metrics using correct data sources"""
        logging.info("Getting dashboard overview with correct data sources")
        try:
            # If no date range is provided, default to today (midnight to now, America/Chicago timezone)
            if not start_date or not end_date:
                tz = pytz.timezone('America/Chicago')
                now = datetime.now(tz)
                start_date = datetime.combine(now.date(), datetime.min.time()).replace(tzinfo=tz)
                end_date = now
            
            # Get sales data from configured source
            sales_data = self.get_sales_summary(start_date, end_date)
            logging.info(f"Sales data retrieved: revenue={sales_data.get('total_revenue', 0)}, transactions={sales_data.get('total_transactions', 0)}")
            
            # Get inventory data from configured source
            inventory_data = self.get_inventory_data()
            logging.info(f"Inventory data retrieved: total items={inventory_data.get('total', 0)}")
            
            # Get staff count from local database (always local)
            staff_count = db.session.query(Chef).count()
            logging.info(f"Staff count: {staff_count}")
            
            # Calculate low stock items (quantity < 10)
            low_stock_items = []
            if inventory_data and 'items' in inventory_data:
                low_stock_items = [
                    item for item in inventory_data['items'] 
                    if item.get('quantity') is not None and item.get('quantity', 0) < 10
                ]
            
            overview = {
                'total_revenue': round(sales_data.get('total_revenue', 0), 2),
                'total_transactions': sales_data.get('total_transactions', 0),
                'staff_count': staff_count,
                'low_stock_items': len(low_stock_items),
                'last_updated': datetime.now().isoformat(),
                'data_sources': {
                    'sales': self.get_data_source('sales'),
                    'inventory': self.get_data_source('inventory'),
                    'staff': 'local'
                }
            }
            
            logging.info(f"Dashboard overview generated: {overview}")
            return overview
            
        except Exception as e:
            logging.error(f"Error getting dashboard overview: {str(e)}")
            # Return fallback data
            return {
                'total_revenue': 0,
                'total_transactions': 0,
                'staff_count': 0,
                'low_stock_items': 0,
                'last_updated': datetime.now().isoformat(),
                'data_sources': {
                    'sales': 'error',
                    'inventory': 'error',
                    'staff': 'local'
                }
            }

    def get_staff_performance(self, start_date=None, end_date=None):
        """Get staff performance using correct sales data source and chef mapping from local DB"""
        data_source = self.get_data_source('sales')
        logging.info(f"Getting staff performance from sales data source: {data_source}")
        if data_source == 'clover':
            # Use the same logic as chef performance data for consistency
            return self._get_clover_chef_performance_data(start_date, end_date)
        else:
            # Use local DB
            return self._get_local_chef_performance_data(start_date, end_date)

    def get_profitability(self, start_date=None, end_date=None):
        """Get profitability using configured sales data source and local expenses, with filters"""
        try:
            logging.info(f"Getting profitability data with date range: {start_date} to {end_date}")
            
            # Get sales data from configured source
            sales_data = self.get_sales_summary(start_date, end_date)
            logging.info(f"Sales data retrieved: revenue={sales_data.get('total_revenue', 0)}")
            
            # Get expenses data (always from local database)
            expenses_data = self.get_expenses_data(start_date, end_date)
            logging.info(f"Expenses data retrieved: total={expenses_data.get('total_expenses', 0)}")
            
            # Calculate totals
            total_sales = sales_data.get('total_revenue', 0)
            total_expenses = expenses_data.get('total_expenses', 0)
            net_profit = total_sales - total_expenses
            profit_margin = (net_profit / total_sales * 100) if total_sales > 0 else 0
            
            # Get category breakdown
            sales_categories = {item['category']: item['revenue'] for item in sales_data.get('category_breakdown', [])}
            expenses_categories = {item['category']: item['amount'] for item in expenses_data.get('category_breakdown', [])}
            all_categories = set(list(sales_categories.keys()) + list(expenses_categories.keys()))
            
            categories = []
            for cat in all_categories:
                sales_amt = sales_categories.get(cat, 0)
                exp_amt = expenses_categories.get(cat, 0)
                profit = sales_amt - exp_amt
                margin = (profit / sales_amt * 100) if sales_amt > 0 else 0
                categories.append({
                    'category': cat, 
                    'sales': sales_amt, 
                    'expenses': exp_amt, 
                    'profit': profit, 
                    'profit_margin': margin
                })
            
            # --- Module mapping for profitability aggregation ---
            CATEGORY_TO_MODULE = {
                "Grocery": "Grocery",
                "Frozen": "Grocery",
                "Snacks": "Grocery",
                "Kaara Snacks": "Grocery",
                "Meat Items": "Meat",
                "Vegetables": "Vegetables",
                # All others will be 'Kitchen'
            }
            MODULES = ["Grocery", "Meat", "Vegetables", "Kitchen"]
            module_agg = {m: {"sales": 0, "expenses": 0, "profit": 0} for m in MODULES}

            # Aggregate by module
            for cat in all_categories:
                sales_amt = sales_categories.get(cat, 0)
                exp_amt = expenses_categories.get(cat, 0)
                profit = sales_amt - exp_amt
                module = CATEGORY_TO_MODULE.get(cat, "Kitchen")
                module_agg[module]["sales"] += sales_amt
                module_agg[module]["expenses"] += exp_amt
                module_agg[module]["profit"] += profit

            # Calculate margin for each module
            modules = []
            for m in MODULES:
                sales = module_agg[m]["sales"]
                profit = module_agg[m]["profit"]
                margin = (profit / sales * 100) if sales > 0 else 0
                modules.append({
                    "module": m,
                    "sales": sales,
                    "expenses": module_agg[m]["expenses"],
                    "profit": profit,
                    "profit_margin": margin
                })

            profitability = {
                'total_sales': total_sales,
                'total_expenses': total_expenses,
                'net_profit': net_profit,
                'profit_margin': profit_margin,
                'categories': categories,
                'modules': modules,
                'data_sources': {
                    'sales': self.get_data_source('sales'),
                    'expenses': 'local'
                }
            }
            
            logging.info(f"Profitability calculated: sales=${total_sales}, expenses=${total_expenses}, profit=${net_profit}")
            return profitability
            
        except Exception as e:
            logging.error(f"Error calculating profitability: {str(e)}")
            return {
                'total_sales': 0,
                'total_expenses': 0,
                'net_profit': 0,
                'profit_margin': 0,
                'categories': [],
                'data_sources': {
                    'sales': 'error',
                    'expenses': 'local'
                }
            }

    def _get_clover_chef_performance_data(self, start_date=None, end_date=None, chef_ids=None, category=None):
        """Get chef performance data using Clover sales data and local chef mappings, with optional category filter, excluding 'Unassigned' chef and reporting unmapped items. Only use clover_id for mapping."""
        try:
            logging.info("Getting chef performance data from Clover sales + local chef mappings (clover_id only)")
            # Get chef mappings from local database (always local)
            chef_mappings = db.session.query(ChefDishMapping).all()
            clover_id_to_chef = {mapping.clover_id: mapping.chef_id for mapping in chef_mappings if mapping.clover_id}
            logging.info(f"Found {len(chef_mappings)} chef mappings with clover_id")
            # Get all real chefs (exclude 'Unassigned' and only keep the 4 real chefs)
            allowed_chefs = ["Sarva&Ram", "Savithri", "Wasim", "Chef_miscellanies"]
            real_chefs = {chef.id: chef.name for chef in Chef.query.filter(Chef.name.in_(allowed_chefs)).all()}
            logging.info(f"Found {len(real_chefs)} real chefs: {list(real_chefs.values())}")
            # Filter chefs if specified
            chefs = real_chefs.copy()
            if chef_ids and chef_ids != 'all':
                try:
                    chef_id_list = [int(id_str) for id_str in chef_ids.split(',')]
                    chefs = {k: v for k, v in real_chefs.items() if k in chef_id_list}
                except ValueError:
                    logging.warning(f"Invalid chef_ids format: {chef_ids}")
            # Get orders from Clover
            orders = self.clover_service.get_orders(start_date, end_date)
            logging.info(f"Retrieved {len(orders) if orders else 0} orders from Clover")
            # Filter orders by date if provided
            if start_date or end_date:
                orders = self._filter_orders_by_date(orders, start_date, end_date)
                logging.info(f"After date filtering: {len(orders)} orders")
            # Parse category filter as list
            category_list = None
            if category and category != 'all':
                category_list = [c.strip() for c in category.split(',') if c.strip()]
            # Process orders to get chef performance
            chef_performance = {}
            chef_summary = {}
            unmapped_items = set()
            processed_orders = 0
            processed_line_items = 0
            mapped_line_items = 0
            for order in orders:
                line_items = order.get('lineItems', {}).get('elements', [])
                processed_orders += 1
                for line_item in line_items:
                    processed_line_items += 1
                    item = line_item.get('item', {})
                    clover_item_id = item.get('id')
                    item_name = item.get('name', 'Unknown')
                    # Only use clover_id for mapping
                    chef_id = clover_id_to_chef.get(clover_item_id)
                    if not chef_id or chef_id not in chefs:
                        unmapped_items.add(f"{clover_item_id}:{item_name}")
                        continue  # Skip items not mapped to chefs or filtered chefs
                    mapped_line_items += 1
                    # Extract category from item.categories
                    cat = 'Uncategorized'
                    categories = item.get('categories', {}).get('elements', [])
                    if categories and isinstance(categories, list):
                        cat = categories[0].get('name', 'Uncategorized')
                    # Category filter: if category_list, only include if cat in list
                    if category_list and cat not in category_list:
                        continue
                    chef_name = chefs[chef_id]
                    # Revenue extraction: use total if present and >0, else price * quantity
                    total_cents = line_item.get('total', 0)
                    price_cents = line_item.get('price', 0)
                    quantity = line_item.get('quantity', 1)
                    if total_cents:
                        revenue = float(total_cents) / 100
                    else:
                        revenue = float(price_cents) * float(quantity) / 100
                    logging.debug(f"Processing line item: {json.dumps(line_item, default=str)}")
                    logging.debug(f"Line item revenue: {revenue} (raw total: {line_item.get('total', None)}, price: {price_cents}, quantity: {quantity})")
                    if revenue == 0:
                        logging.warning(f"ZERO revenue line item: {json.dumps(line_item, default=str)}")
                    # Update chef performance
                    if chef_name not in chef_performance:
                        chef_performance[chef_name] = {}
                    if item_name not in chef_performance[chef_name]:
                        chef_performance[chef_name][item_name] = {
                            'chef_name': chef_name,
                            'item_name': item_name,
                            'category': cat,
                            'revenue': 0,
                            'count': 0
                        }
                    chef_performance[chef_name][item_name]['revenue'] += revenue
                    chef_performance[chef_name][item_name]['count'] += quantity
                    # Update chef summary
                    if chef_id not in chef_summary:
                        chef_summary[chef_id] = {
                            'id': chef_id,
                            'name': chef_name,
                            'total_revenue': 0,
                            'total_sales': 0
                        }
                    chef_summary[chef_id]['total_revenue'] += revenue
                    chef_summary[chef_id]['total_sales'] += quantity
            # Convert to grouped list: one entry per chef, with a list of their dishes
            chef_performance_grouped = []
            for chef_id, chef_name in chefs.items():
                # Find all items for this chef
                dishes = []
                chef_items = chef_performance.get(chef_name, {})
                for item in chef_items.values():
                    dishes.append({
                        'item_name': item['item_name'],
                        'category': item['category'],
                        'revenue': item['revenue'],
                        'count': item['count']
                    })
                chef_performance_grouped.append({
                    'chef_id': chef_id,
                    'chef_name': chef_name,
                    'dishes': dishes
                })
            summary_list = list(chef_summary.values())
            logging.info(f"Clover chef performance processing complete:")
            logging.info(f"  - Processed {processed_orders} orders")
            logging.info(f"  - Processed {processed_line_items} line items")
            logging.info(f"  - Mapped {mapped_line_items} line items to chefs via clover_id")
            logging.info(f"  - Found {len(chef_performance_grouped)} chefs with performance data")
            logging.info(f"  - Total dishes across all chefs: {sum(len(c['dishes']) for c in chef_performance_grouped)}")
            logging.info(f"  - Unmapped items: {len(unmapped_items)}")
            if unmapped_items:
                logging.info(f"  - Sample unmapped items: {list(unmapped_items)[:5]}")
            return {
                'chef_performance': chef_performance_grouped,
                'chef_summary': summary_list
            }
        except Exception as e:
            logging.error(f"Error getting Clover chef performance data: {str(e)}")
            # Fallback to local data
            return self._get_local_chef_performance_data(start_date, end_date, chef_ids) 