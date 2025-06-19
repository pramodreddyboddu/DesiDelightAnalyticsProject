from flask import Blueprint, request, jsonify, make_response
from ..models import db, Item, UncategorizedItem, Sale, Expense, Chef
from ..routes.auth import login_required, admin_required
from sqlalchemy import func, and_, or_
from datetime import datetime
import pandas as pd
import io
import csv

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports/sales', methods=['GET'])
@login_required
def export_sales_report():
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        category = request.args.get('category')
        format_type = request.args.get('format', 'csv')  # csv, excel
        
        # Build query
        query = db.session.query(
            Sale.line_item_date,
            Sale.order_employee_name,
            Item.name.label('item_name'),
            Item.category,
            Sale.quantity,
            Sale.item_revenue,
            Sale.modifiers_revenue,
            Sale.total_revenue,
            Sale.discounts,
            Sale.tax_amount,
            Sale.item_total_with_tax,
            Sale.payment_state
        ).join(Item, Sale.item_id == Item.id)
        
        # Apply filters
        if start_date:
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(Sale.line_item_date >= start_date)
        
        if end_date:
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(Sale.line_item_date <= end_date)
        
        if category and category != 'all':
            query = query.filter(Item.category == category)
        
        # Execute query
        results = query.order_by(Sale.line_item_date.desc()).all()
        
        # Convert to DataFrame
        data = []
        for row in results:
            data.append({
                'Date': row.line_item_date.strftime('%Y-%m-%d %H:%M:%S'),
                'Employee': row.order_employee_name,
                'Item Name': row.item_name,
                'Category': row.category,
                'Quantity': row.quantity,
                'Item Revenue': row.item_revenue,
                'Modifiers Revenue': row.modifiers_revenue,
                'Total Revenue': row.total_revenue,
                'Discounts': row.discounts,
                'Tax Amount': row.tax_amount,
                'Total with Tax': row.item_total_with_tax,
                'Payment State': row.payment_state
            })
        
        df = pd.DataFrame(data)
        
        if format_type == 'excel':
            # Create Excel file
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Sales Report', index=False)
            output.seek(0)
            
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            response.headers['Content-Disposition'] = 'attachment; filename=sales_report.xlsx'
            return response
        else:
            # Create CSV file
            output = io.StringIO()
            df.to_csv(output, index=False)
            
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = 'attachment; filename=sales_report.csv'
            return response
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/reports/profitability', methods=['GET'])
@login_required
def export_profitability_report():
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        format_type = request.args.get('format', 'csv')
        
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
            func.sum(Sale.total_revenue).label('revenue'),
            func.count(Sale.id).label('count')
        ).join(Item, Sale.item_id == Item.id)
        
        if start_date_dt:
            sales_query = sales_query.filter(Sale.line_item_date >= start_date_dt)
        if end_date_dt:
            sales_query = sales_query.filter(Sale.line_item_date <= end_date_dt)
        
        sales_by_category = sales_query.group_by(Item.category).all()
        
        # Get expenses by category
        expenses_query = db.session.query(
            Expense.category,
            func.sum(Expense.amount).label('amount'),
            func.count(Expense.id).label('count')
        )
        
        if start_date_d:
            expenses_query = expenses_query.filter(Expense.date >= start_date_d)
        if end_date_d:
            expenses_query = expenses_query.filter(Expense.date <= end_date_d)
        
        expenses_by_category = expenses_query.group_by(Expense.category).all()
        
        # Prepare data
        sales_dict = {sale.category: {'revenue': float(sale.revenue), 'count': sale.count} for sale in sales_by_category}
        expenses_dict = {exp.category: {'amount': float(exp.amount), 'count': exp.count} for exp in expenses_by_category}
        
        data = []
        total_sales = sum(item['revenue'] for item in sales_dict.values())
        
        for category in set(list(sales_dict.keys()) + list(expenses_dict.keys())):
            sales_amount = sales_dict.get(category, {}).get('revenue', 0)
            sales_count = sales_dict.get(category, {}).get('count', 0)
            
            # Find matching expenses
            expenses_amount = 0
            expenses_count = 0
            
            if category in expenses_dict:
                expenses_amount = expenses_dict[category]['amount']
                expenses_count = expenses_dict[category]['count']
            elif 'Kitchen' in expenses_dict and category in ['Meat', 'Vegetables', 'Grocery', 'Uncategorized']:
                # Allocate Kitchen expenses proportionally
                kitchen_expenses = expenses_dict['Kitchen']['amount']
                allocation_ratio = sales_amount / total_sales if total_sales > 0 else 0
                expenses_amount = kitchen_expenses * allocation_ratio
                expenses_count = expenses_dict['Kitchen']['count']
            
            profit = sales_amount - expenses_amount
            profit_margin = (profit / sales_amount * 100) if sales_amount > 0 else 0
            
            data.append({
                'Category': category,
                'Sales Revenue': sales_amount,
                'Sales Count': sales_count,
                'Expenses': expenses_amount,
                'Expenses Count': expenses_count,
                'Net Profit': profit,
                'Profit Margin (%)': round(profit_margin, 2)
            })
        
        df = pd.DataFrame(data)
        
        if format_type == 'excel':
            # Create Excel file
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Profitability Report', index=False)
            output.seek(0)
            
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            response.headers['Content-Disposition'] = 'attachment; filename=profitability_report.xlsx'
            return response
        else:
            # Create CSV file
            output = io.StringIO()
            df.to_csv(output, index=False)
            
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = 'attachment; filename=profitability_report.csv'
            return response
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/reports/chef-performance', methods=['GET'])
@login_required
def export_chef_performance_report():
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        chef_ids = request.args.get('chef_ids')
        format_type = request.args.get('format', 'csv')
        
        # Build query
        query = db.session.query(
            Chef.name.label('chef_name'),
            Item.name.label('item_name'),
            Item.category,
            func.sum(Sale.total_revenue).label('revenue'),
            func.count(Sale.id).label('count'),
            func.avg(Sale.total_revenue).label('avg_revenue')
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
            
        if chef_ids and chef_ids != 'all':
            try:
                chef_id_list = [int(id_str) for id_str in chef_ids.split(',')]
                query = query.filter(Chef.id.in_(chef_id_list))
            except ValueError:
                return jsonify({'error': 'Invalid chef_ids format'}), 400
        
        # Group and order
        results = query.group_by(Chef.id, Chef.name, Item.id, Item.name, Item.category)\
                      .order_by(Chef.name, func.sum(Sale.total_revenue).desc()).all()
        
        # Convert to DataFrame
        data = []
        for row in results:
            data.append({
                'Chef Name': row.chef_name,
                'Item Name': row.item_name,
                'Category': row.category,
                'Total Revenue': row.revenue,
                'Sales Count': row.count,
                'Average Revenue': round(row.avg_revenue, 2)
            })
        
        df = pd.DataFrame(data)
        
        if format_type == 'excel':
            # Create Excel file
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Chef Performance', index=False)
            output.seek(0)
            
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            response.headers['Content-Disposition'] = 'attachment; filename=chef_performance_report.xlsx'
            return response
        else:
            # Create CSV file
            output = io.StringIO()
            df.to_csv(output, index=False)
            
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = 'attachment; filename=chef_performance_report.csv'
            return response
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/items/uncategorized', methods=['GET'])
@login_required
def get_uncategorized_items():
    try:
        uncategorized = UncategorizedItem.query.filter_by(status='pending')\
                                              .order_by(UncategorizedItem.frequency.desc()).all()
        
        return jsonify({
            'uncategorized_items': [item.to_dict() for item in uncategorized]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/items/uncategorized/<int:item_id>/categorize', methods=['PUT'])
@admin_required
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
            item = Item(name=uncategorized.item_name, category=category)
            db.session.add(item)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Item categorized successfully',
            'item': item.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

