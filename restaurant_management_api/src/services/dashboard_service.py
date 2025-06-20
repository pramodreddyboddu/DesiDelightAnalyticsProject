from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from ..models import db, Sale, Expense, Item, Chef, ChefDishMapping, UncategorizedItem, FileUpload
import logging

class DashboardService:
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
    def get_sales_summary(start_date, end_date, category=None):
        """Get sales summary data"""
        try:
            # Debug logging
            logging.info(f"get_sales_summary called with start_date: {start_date}, end_date: {end_date}, category: {category}")
            
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
            logging.error(f"Error in get_sales_summary: {str(e)}")
            raise

    @staticmethod
    def get_chef_performance(start_date, end_date, chef_ids=None):
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
            logging.error(f"Error in get_chef_performance: {str(e)}")
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