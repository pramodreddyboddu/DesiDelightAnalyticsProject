from flask import Blueprint, request, jsonify
from src.models.user import db, Sale, Expense, Item, Chef, ChefDishMapping
from src.routes.auth import login_required
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
import pandas as pd

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard/sales-summary', methods=['GET'])
@login_required
def get_sales_summary():
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        category = request.args.get('category')
        
        # Build base query
        query = db.session.query(Sale).join(Item, Sale.item_id == Item.id)
        
        # Apply filters
        if start_date:
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(Sale.line_item_date >= start_date)
        
        if end_date:
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(Sale.line_item_date <= end_date)
        
        if category and category != 'all':
            query = query.filter(Item.category == category)
        
        # Get total revenue
        total_revenue = query.with_entities(func.sum(Sale.total_revenue)).scalar() or 0
        
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
        
        return jsonify({
            'total_revenue': float(total_revenue),
            'category_breakdown': [
                {
                    'category': cat.category,
                    'revenue': float(cat.revenue),
                    'count': cat.count
                } for cat in category_breakdown
            ],
            'top_items': [
                {
                    'name': item.name,
                    'category': item.category,
                    'revenue': float(item.revenue),
                    'count': item.count
                } for item in top_items
            ],
            'daily_trend': [
                {
                    'date': day.date.isoformat(),
                    'revenue': float(day.revenue)
                } for day in daily_sales
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/dashboard/chef-performance', methods=['GET'])
@login_required
def get_chef_performance():
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
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
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(Sale.line_item_date >= start_date)
        
        if end_date:
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(Sale.line_item_date <= end_date)
        
        if chef_id:
            query = query.filter(Chef.id == chef_id)
        
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
            
            performance_data[chef_name]['dishes'].append({
                'item_name': perf.item_name,
                'category': perf.category,
                'revenue': float(perf.revenue),
                'count': perf.count
            })
            performance_data[chef_name]['total_revenue'] += float(perf.revenue)
            performance_data[chef_name]['total_sales'] += perf.count
        
        return jsonify({
            'chef_summary': [
                {
                    'id': chef.id,
                    'name': chef.name,
                    'total_revenue': float(chef.total_revenue),
                    'total_sales': chef.total_sales
                } for chef in chef_summary
            ],
            'chef_performance': list(performance_data.values())
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/dashboard/expenses', methods=['GET'])
@login_required
def get_expenses_dashboard():
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        category = request.args.get('category')
        
        # Build base query
        query = db.session.query(Expense)
        
        # Apply filters
        if start_date:
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00')).date()
            query = query.filter(Expense.date >= start_date)
        
        if end_date:
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00')).date()
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
        
        return jsonify({
            'total_expenses': float(total_expenses),
            'category_breakdown': [
                {
                    'category': cat.category,
                    'amount': float(cat.amount),
                    'count': cat.count
                } for cat in category_breakdown
            ],
            'vendor_breakdown': [
                {
                    'vendor': vendor.vendor,
                    'amount': float(vendor.amount),
                    'count': vendor.count
                } for vendor in vendor_breakdown
            ],
            'daily_trend': [
                {
                    'date': day.date.isoformat(),
                    'amount': float(day.amount)
                } for day in daily_expenses
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/dashboard/profitability', methods=['GET'])
@login_required
def get_profitability_dashboard():
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Parse dates
        if start_date:
            start_date_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            start_date_d = start_date_dt.date()
        else:
            start_date_dt = None
            start_date_d = None
            
        if end_date:
            end_date_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            end_date_d = end_date_dt.date()
        else:
            end_date_dt = None
            end_date_d = None
        
        # Get sales by category
        sales_query = db.session.query(
            Item.category,
            func.sum(Sale.total_revenue).label('revenue')
        ).join(Item, Sale.item_id == Item.id)
        
        if start_date_dt:
            sales_query = sales_query.filter(Sale.line_item_date >= start_date_dt)
        if end_date_dt:
            sales_query = sales_query.filter(Sale.line_item_date <= end_date_dt)
        
        sales_by_category = sales_query.group_by(Item.category).all()
        
        # Get expenses by category
        expenses_query = db.session.query(
            Expense.category,
            func.sum(Expense.amount).label('amount')
        )
        
        if start_date_d:
            expenses_query = expenses_query.filter(Expense.date >= start_date_d)
        if end_date_d:
            expenses_query = expenses_query.filter(Expense.date <= end_date_d)
        
        expenses_by_category = expenses_query.group_by(Expense.category).all()
        
        # Calculate profitability
        sales_dict = {sale.category: float(sale.revenue) for sale in sales_by_category}
        expenses_dict = {exp.category: float(exp.amount) for exp in expenses_by_category}
        
        # Map expense categories to sales categories
        category_mapping = {
            'Kitchen': ['Meat', 'Vegetables', 'Grocery', 'Uncategorized'],
            'Meat': ['Meat'],
            'Vegetables': ['Vegetables'],
            'Grocery': ['Grocery']
        }
        
        profitability_data = []
        total_sales = sum(sales_dict.values())
        total_expenses = sum(expenses_dict.values())
        
        for sales_category, sales_amount in sales_dict.items():
            # Find matching expenses
            matching_expenses = 0
            for exp_category, exp_amount in expenses_dict.items():
                if exp_category in category_mapping and sales_category in category_mapping[exp_category]:
                    matching_expenses += exp_amount
                elif exp_category == sales_category:
                    matching_expenses += exp_amount
            
            # If no direct match, allocate Kitchen expenses proportionally
            if matching_expenses == 0 and 'Kitchen' in expenses_dict:
                kitchen_expenses = expenses_dict['Kitchen']
                allocation_ratio = sales_amount / total_sales if total_sales > 0 else 0
                matching_expenses = kitchen_expenses * allocation_ratio
            
            profit = sales_amount - matching_expenses
            profit_margin = (profit / sales_amount * 100) if sales_amount > 0 else 0
            
            profitability_data.append({
                'category': sales_category,
                'sales': sales_amount,
                'expenses': matching_expenses,
                'profit': profit,
                'profit_margin': profit_margin
            })
        
        # Overall profitability
        overall_profit = total_sales - total_expenses
        overall_margin = (overall_profit / total_sales * 100) if total_sales > 0 else 0
        
        return jsonify({
            'overall': {
                'total_sales': total_sales,
                'total_expenses': total_expenses,
                'net_profit': overall_profit,
                'profit_margin': overall_margin
            },
            'by_category': profitability_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

