from flask import Blueprint, request, jsonify
from ..models import db, Sale, Expense, Item, Chef, ChefDishMapping, UncategorizedItem, FileUpload
from ..routes.auth import login_required
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
import pandas as pd
import logging

dashboard_bp = Blueprint('dashboard', __name__)

def parse_date(date_str):
    """Parse date string with better error handling and timezone support"""
    if not date_str:
        return None
    try:
        # Handle ISO format with 'Z' timezone
        if date_str.endswith('Z'):
            date_str = date_str.replace('Z', '+00:00')
        # Handle ISO format without timezone
        elif '+' not in date_str and '-' not in date_str[-6:]:
            date_str = f"{date_str}+00:00"
        return datetime.fromisoformat(date_str)
    except ValueError as e:
        logging.error(f"Error parsing date {date_str}: {str(e)}")
        return None

@dashboard_bp.route('/sales-summary', methods=['GET'])
@login_required
def get_sales_summary():
    try:
        # Get query parameters
        start_date = parse_date(request.args.get('start_date'))
        end_date = parse_date(request.args.get('end_date'))
        category = request.args.get('category')
        
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
        
        # Get unique order count
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
        
        # Format the response
        return jsonify({
            'total_revenue': float(total_revenue),
            'unique_order_count': unique_order_count,
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
        }), 200
        
    except Exception as e:
        logging.error(f"Error in sales summary: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/chef-performance', methods=['GET'])
@login_required
def get_chef_performance():
    try:
        # Get query parameters
        start_date = parse_date(request.args.get('start_date'))
        end_date = parse_date(request.args.get('end_date'))
        chef_id = request.args.get('chef_id')
        
        # Build base query
        query = db.session.query(
            Chef.name.label('chef_name'),
            Item.name.label('item_name'),
            Item.category,
            func.sum(Sale.total_revenue).label('revenue'),
            func.count(Sale.id).label('count')
        ).join(ChefDishMapping, Chef.id == ChefDishMapping.chef_id)\
         .join(Item, ChefDishMapping.item_id == Item.id)\
         .join(Sale, Item.id == Sale.item_id)
        
        # Apply filters
        if start_date:
            query = query.filter(Sale.line_item_date >= start_date)
        
        if end_date:
            query = query.filter(Sale.line_item_date <= end_date)
        
        if chef_id:
            try:
                chef_id = int(chef_id)
                query = query.filter(Chef.id == chef_id)
            except ValueError:
                logging.error(f"Invalid chef_id format: {chef_id}")
                return jsonify({'error': 'Invalid chef_id format'}), 400
        
        # Group by chef and item
        chef_performance = query.group_by(Chef.id, Chef.name, Item.id, Item.name, Item.category).all()
        
        # Get chef summary
        chef_summary = db.session.query(
            Chef.id,
            Chef.name,
            func.sum(Sale.total_revenue).label('total_revenue'),
            func.count(Sale.id).label('total_sales')
        ).join(ChefDishMapping, Chef.id == ChefDishMapping.chef_id)\
         .join(Item, ChefDishMapping.item_id == Item.id)\
         .join(Sale, Item.id == Sale.item_id)
        
        if start_date:
            chef_summary = chef_summary.filter(Sale.line_item_date >= start_date)
        if end_date:
            chef_summary = chef_summary.filter(Sale.line_item_date <= end_date)
        if chef_id:
            chef_summary = chef_summary.filter(Chef.id == chef_id)
        
        chef_summary = chef_summary.group_by(Chef.id, Chef.name)\
                                  .order_by(func.sum(Sale.total_revenue).desc()).all()
        
        # Format response
        performance_data = {}
        for perf in chef_performance:
            chef_name = perf.chef_name
            if chef_name not in performance_data:
                performance_data[chef_name] = {
                    'chef_name': chef_name,
                    'dishes': [],
                    'total_revenue': 0,
                    'total_sales': 0
                }
            
            try:
                revenue = float(perf.revenue) if perf.revenue is not None else 0
                count = int(perf.count) if perf.count is not None else 0
                
                performance_data[chef_name]['dishes'].append({
                    'item_name': perf.item_name,
                    'category': perf.category,
                    'revenue': revenue,
                    'count': count
                })
                performance_data[chef_name]['total_revenue'] += revenue
                performance_data[chef_name]['total_sales'] += count
            except (ValueError, TypeError) as e:
                logging.error(f"Error processing performance data for {chef_name}: {str(e)}")
                continue
        
        return jsonify({
            'chef_summary': [
                {
                    'id': chef.id,
                    'name': chef.name,
                    'total_revenue': float(chef.total_revenue) if chef.total_revenue is not None else 0,
                    'total_sales': int(chef.total_sales) if chef.total_sales is not None else 0
                } for chef in chef_summary
            ],
            'chef_performance': list(performance_data.values())
        }), 200
        
    except Exception as e:
        logging.error(f"Error in chef performance: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/expenses', methods=['GET'])
@login_required
def get_expenses_dashboard():
    try:
        # Get query parameters
        start_date = parse_date(request.args.get('start_date'))
        end_date = parse_date(request.args.get('end_date'))
        category = request.args.get('category')
        
        # Build base query
        query = db.session.query(Expense)
        
        # Apply filters
        if start_date:
            query = query.filter(Expense.date >= start_date)
        
        if end_date:
            query = query.filter(Expense.date <= end_date)
        
        if category and category != 'all':
            query = query.filter(Expense.category == category)
        
        # Get total expenses
        total_expenses = query.with_entities(func.sum(Expense.amount)).scalar() or 0
        
        # Get category-wise breakdown
        category_breakdown = db.session.query(
            Expense.category,
            func.sum(Expense.amount).label('amount'),
            func.count(Expense.id).label('count')
        )
        
        if start_date:
            category_breakdown = category_breakdown.filter(Expense.date >= start_date)
        if end_date:
            category_breakdown = category_breakdown.filter(Expense.date <= end_date)
        
        category_breakdown = category_breakdown.group_by(Expense.category).all()
        
        # Get vendor breakdown
        vendor_breakdown = db.session.query(
            Expense.vendor,
            func.sum(Expense.amount).label('amount'),
            func.count(Expense.id).label('count')
        )
        
        if start_date:
            vendor_breakdown = vendor_breakdown.filter(Expense.date >= start_date)
        if end_date:
            vendor_breakdown = vendor_breakdown.filter(Expense.date <= end_date)
        if category and category != 'all':
            vendor_breakdown = vendor_breakdown.filter(Expense.category == category)
        
        vendor_breakdown = vendor_breakdown.group_by(Expense.vendor)\
                                         .order_by(func.sum(Expense.amount).desc())\
                                         .limit(10).all()
        
        # Get daily expenses trend
        daily_expenses = db.session.query(
            Expense.date,
            func.sum(Expense.amount).label('amount')
        )
        
        if start_date:
            daily_expenses = daily_expenses.filter(Expense.date >= start_date)
        if end_date:
            daily_expenses = daily_expenses.filter(Expense.date <= end_date)
        if category and category != 'all':
            daily_expenses = daily_expenses.filter(Expense.category == category)
        
        daily_expenses = daily_expenses.group_by(Expense.date)\
                                     .order_by(Expense.date).all()
        
        try:
            return jsonify({
                'total_expenses': float(total_expenses),
                'category_breakdown': [
                    {
                        'category': cat.category,
                        'amount': float(cat.amount) if cat.amount is not None else 0,
                        'count': cat.count
                    } for cat in category_breakdown
                ],
                'vendor_breakdown': [
                    {
                        'vendor': vendor.vendor or 'Unknown',
                        'amount': float(vendor.amount) if vendor.amount is not None else 0,
                        'count': vendor.count
                    } for vendor in vendor_breakdown
                ],
                'daily_trend': [
                    {
                        'date': day.date.isoformat(),
                        'amount': float(day.amount) if day.amount is not None else 0
                    } for day in daily_expenses
                ]
            }), 200
        except (ValueError, TypeError) as e:
            logging.error(f"Error formatting expense data: {str(e)}")
            return jsonify({'error': 'Error formatting expense data'}), 500
        
    except Exception as e:
        logging.error(f"Error in expenses dashboard: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/profitability', methods=['GET'])
@login_required
def get_profitability_dashboard():
    try:
        # Get query parameters
        start_date = parse_date(request.args.get('start_date'))
        end_date = parse_date(request.args.get('end_date'))
        
        # Get sales by category
        sales_query = db.session.query(
            Item.category,
            func.sum(Sale.total_revenue).label('revenue')
        ).join(Item, Sale.item_id == Item.id)
        
        if start_date:
            sales_query = sales_query.filter(Sale.line_item_date >= start_date)
        if end_date:
            sales_query = sales_query.filter(Sale.line_item_date <= end_date)
        
        sales_by_category = sales_query.group_by(Item.category).all()
        
        # Get expenses by category
        expenses_query = db.session.query(
            Expense.category,
            func.sum(Expense.amount).label('amount')
        )
        
        if start_date:
            expenses_query = expenses_query.filter(Expense.date >= start_date.date())
        if end_date:
            expenses_query = expenses_query.filter(Expense.date <= end_date.date())
        
        expenses_by_category = expenses_query.group_by(Expense.category).all()
        
        # Calculate profitability
        sales_dict = {}
        for sale in sales_by_category:
            try:
                sales_dict[sale.category] = float(sale.revenue) if sale.revenue is not None else 0
            except (ValueError, TypeError) as e:
                logging.error(f"Error processing sales data for category {sale.category}: {str(e)}")
                sales_dict[sale.category] = 0
        
        expenses_dict = {}
        for exp in expenses_by_category:
            try:
                expenses_dict[exp.category] = float(exp.amount) if exp.amount is not None else 0
            except (ValueError, TypeError) as e:
                logging.error(f"Error processing expense data for category {exp.category}: {str(e)}")
                expenses_dict[exp.category] = 0
        
        # Explicit mapping from inventory category to expense category
        category_expense_map = {
            "Breakfast": "Kitchen",
            "Breakfast Combo": "Kitchen",
            "Veg Appetizers": "Kitchen",
            "Non-Veg Appetizers": "Kitchen",
            "Curries (Veg & Non-Veg)": "Kitchen",
            "Biryani's": "Kitchen",
            "Breads": "Kitchen",
            "Pulav's": "Kitchen",
            "Meat Items": "Meat",
            "Groceries": "Grocery",
            "Kaara Snacks": "Grocery",
            "Vegetables": "Vegetables",
            "Flowers": "Grocery",
            "Frozen": "Grocery",
            "Snacks": "Grocery",
            "SEASONAL": "Kitchen",
            "DD Specials": "Kitchen",
            "Chat Specials": "Kitchen",
            "Evening Specials": "Kitchen",
            "Indo Chinese": "Kitchen",
            "Drinks": "Kitchen",
            "Kitchen Stocking": "Kitchen",
            "Deserts": "Kitchen",
            "SPECIALS": "Kitchen",
            "Parota Specials": "Kitchen",
            "DAILY SPECIALS": "Kitchen",
            "DD Weekend Delight": "Kitchen",
            "DD Family Pack Combos": "Kitchen",
            "Week End Specials": "Kitchen",
            "Monday Specials": "Kitchen",
            "Tuesday Specials": "Kitchen",
            "Wednesday Specials": "Kitchen",
            "Thursday Specials": "Kitchen",
            "Friday Specials": "Kitchen",
            "Saturday Specials": "Kitchen",
            "MELA 2024": "Kitchen",
            "Thali": "Kitchen",
            "Thali Curries": "Kitchen",
            "Sunday Specials": "Kitchen",
            "Diwali Crackers": "Kitchen",
            "Biryani Combo's": "Kitchen",
            "Appetizer Box": "Kitchen",
            "Kids Special": "Kitchen",
            "Unlimited Biryani": "Kitchen",
            "Roll's": "Kitchen",
            "New Year": "Kitchen",
            "Winter Special": "Kitchen",
            "Chef's Special": "Kitchen",
            "Unlimited Dosa": "Kitchen",
            "Desi Burgers": "Kitchen",
            "Mandi": "Kitchen"
        }

        profitability_data = []
        total_sales = sum(sales_dict.values())
        total_expenses = sum(expenses_dict.values())

        # Group sales by expense category using explicit mapping
        expense_category_sales = {}
        for sales_category, sales_amount in sales_dict.items():
            expense_category = category_expense_map.get(sales_category, 'Grocery')  # Default to Grocery if not mapped
            if expense_category not in expense_category_sales:
                expense_category_sales[expense_category] = 0
            expense_category_sales[expense_category] += sales_amount

        # Calculate profitability for each expense category
        for expense_category, sales_amount in expense_category_sales.items():
            expense_amount = expenses_dict.get(expense_category, 0)
            profit = sales_amount - expense_amount
            profit_margin = (profit / sales_amount * 100) if sales_amount > 0 else 0

            profitability_data.append({
                'category': expense_category,
                'sales': sales_amount,
                'expenses': expense_amount,
                'profit': profit,
                'profit_margin': profit_margin,
                'sales_percentage': (sales_amount / total_sales * 100) if total_sales > 0 else 0,
                'expense_percentage': (expense_amount / total_expenses * 100) if total_expenses > 0 else 0
            })
        
        # Overall profitability
        overall_profit = total_sales - total_expenses
        overall_margin = (overall_profit / total_sales * 100) if total_sales > 0 else 0
        
        return jsonify({
            'categories': profitability_data,
            'total_sales': total_sales,
            'total_expenses': total_expenses
        }), 200
        
    except Exception as e:
        logging.error(f"Error in profitability dashboard: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/items/uncategorized', methods=['GET'])
@login_required
def get_uncategorized_items():
    try:
        uncategorized = UncategorizedItem.query.filter_by(status='pending')\
                                              .order_by(UncategorizedItem.frequency.desc()).all()
        
        return jsonify({
            'uncategorized_items': [item.to_dict() for item in uncategorized]
        }), 200
        
    except Exception as e:
        logging.error(f"Error fetching uncategorized items: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/items/uncategorized/<int:item_id>/categorize', methods=['PUT'])
@login_required
def categorize_item(item_id):
    try:
        data = request.get_json()
        category = data.get('category')
        
        if not category:
            return jsonify({'error': 'Category is required'}), 400
        
        # Update uncategorized item
        uncategorized = UncategorizedItem.query.get(item_id)
        if not uncategorized:
            return jsonify({'error': 'Uncategorized item not found'}), 404
        
        uncategorized.status = 'categorized'
        uncategorized.suggested_category = category
        
        # Update or create actual item
        item = Item.query.filter_by(name=uncategorized.item_name).first()
        if item:
            item.category = category
        else:
            item = Item(
                name=uncategorized.item_name,
                category=category,
                clover_id=f"MANUAL_{uncategorized.item_name}",  # Generate a unique clover_id
                price=0.0  # Default price
            )
            db.session.add(item)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Item categorized successfully',
            'item': item.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error categorizing item: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/recent-activity', methods=['GET'])
@login_required
def get_recent_activity():
    try:
        # Get recent file uploads
        recent_uploads = db.session.query(FileUpload)\
            .order_by(FileUpload.upload_date.desc())\
            .limit(5).all()
        
        # Get recent uncategorized items
        recent_uncategorized = db.session.query(UncategorizedItem)\
            .filter_by(status='pending')\
            .order_by(UncategorizedItem.created_at.desc())\
            .limit(5).all()
        
        # Format activities
        activities = []
        
        # Add file upload activities
        for upload in recent_uploads:
            activities.append({
                'type': 'upload',
                'message': f"{upload.file_type.title()} data uploaded",
                'timestamp': upload.upload_date,
                'status': 'success'
            })
        
        # Add uncategorized items activities
        for item in recent_uncategorized:
            activities.append({
                'type': 'uncategorized',
                'message': f"New item '{item.item_name}' needs categorization",
                'timestamp': item.created_at,
                'status': 'warning'
            })
        
        # Sort activities by timestamp
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'activities': activities
        }), 200
        
    except Exception as e:
        logging.error(f"Error fetching recent activity: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/quick-actions', methods=['GET'])
@login_required
def get_quick_actions():
    try:
        # Get counts for quick action status
        uncategorized_count = db.session.query(func.count(UncategorizedItem.id))\
            .filter_by(status='pending').scalar()
        
        # Get recent file uploads
        last_upload = db.session.query(FileUpload)\
            .order_by(FileUpload.upload_date.desc())\
            .first()
        
        # Format quick actions
        actions = [
            {
                'id': 'upload',
                'label': 'Upload Sales & Inventory Data',
                'icon': 'upload',
                'status': 'available',
                'last_updated': last_upload.upload_date if last_upload else None
            },
            {
                'id': 'report',
                'label': 'Generate Business Report',
                'icon': 'file-text',
                'status': 'available',
                'last_updated': None
            },
            {
                'id': 'staff',
                'label': 'View Staff Performance',
                'icon': 'users',
                'status': 'available',
                'last_updated': None
            },
            {
                'id': 'categorize',
                'label': 'Categorize Items',
                'icon': 'tag',
                'status': 'warning' if uncategorized_count > 0 else 'available',
                'count': uncategorized_count
            }
        ]
        
        return jsonify({
            'actions': actions
        }), 200
        
    except Exception as e:
        logging.error(f"Error fetching quick actions: {str(e)}")
        return jsonify({'error': str(e)}), 500

