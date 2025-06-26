from flask import Blueprint, request, jsonify, make_response
from ..models import db, Item, UncategorizedItem, Sale, Expense, Chef
from ..routes.auth import login_required, admin_required
from ..services.dashboard_service import DashboardService
from sqlalchemy import func, and_, or_
from datetime import datetime
import pandas as pd
import io
import csv
import logging

reports_bp = Blueprint('reports', __name__)
dashboard_service = DashboardService()

def parse_date(date_str):
    """Parse date string with better error handling"""
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

@reports_bp.route('/reports/sales', methods=['GET'])
@login_required
def export_sales_report():
    try:
        # Get query parameters
        start_date = parse_date(request.args.get('start_date'))
        end_date = parse_date(request.args.get('end_date'))
        category = request.args.get('category')
        format_type = request.args.get('format', 'csv')  # csv, excel
        
        # Get sales data from configured source
        data_source = dashboard_service.get_data_source('sales')
        
        if data_source == 'clover':
            # Get sales data from Clover
            sales_summary = dashboard_service.get_sales_summary(start_date, end_date, category)
            
            # For Clover data, we need to get the raw orders for detailed reporting
            orders = dashboard_service.clover_service.get_orders(start_date, end_date)
            
            data = []
            for order in orders:
                line_items = order.get('lineItems', {}).get('elements', [])
                for line_item in line_items:
                    item = line_item.get('item', {})
                    data.append({
                        'Date': datetime.fromtimestamp(order['createdTime'] / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                        'Employee': order.get('employee', {}).get('name', 'Unknown'),
                        'Item Name': item.get('name', 'Unknown'),
                        'Category': item.get('categories', {}).get('elements', [{}])[0].get('name', 'Uncategorized'),
                        'Quantity': line_item.get('quantity', 1),
                        'Item Revenue': float(line_item.get('price', 0)) / 100,
                        'Modifiers Revenue': 0,  # Clover doesn't separate modifiers in this way
                        'Total Revenue': float(line_item.get('total', 0)) / 100,
                        'Discounts': 0,  # Would need to calculate from order level
                        'Tax Amount': 0,  # Would need to calculate from order level
                        'Total with Tax': float(line_item.get('total', 0)) / 100,
                        'Payment State': order.get('state', 'unknown')
                    })
        else:
            # Use local database
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
                query = query.filter(Sale.line_item_date >= start_date)
            if end_date:
                query = query.filter(Sale.line_item_date <= end_date)
            if category and category != 'all':
                query = query.filter(Item.category == category)
            
            # Execute query
            results = query.order_by(Sale.line_item_date.desc()).all()
            
            # Convert to list of dictionaries
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
        logging.error(f"Error exporting sales report: {str(e)}")
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/reports/profitability', methods=['GET'])
@login_required
def export_profitability_report():
    try:
        # Get query parameters
        start_date = parse_date(request.args.get('start_date'))
        end_date = parse_date(request.args.get('end_date'))
        format_type = request.args.get('format', 'csv')
        
        # Get sales data from configured source
        sales_data = dashboard_service.get_sales_summary(start_date, end_date)
        
        # Get expenses data (always from local database)
        expenses_data = dashboard_service.get_expenses_data(start_date, end_date)
        
        # Prepare data for export
        data = []
        
        # Get category breakdown from sales
        sales_categories = {item['category']: item['revenue'] for item in sales_data.get('category_breakdown', [])}
        expenses_categories = {item['category']: item['amount'] for item in expenses_data.get('category_breakdown', [])}
        
        # Combine categories
        all_categories = set(list(sales_categories.keys()) + list(expenses_categories.keys()))
        
        for category in all_categories:
            sales_amount = sales_categories.get(category, 0)
            expenses_amount = expenses_categories.get(category, 0)
            profit = sales_amount - expenses_amount
            profit_margin = (profit / sales_amount * 100) if sales_amount > 0 else 0
            
            data.append({
                'Category': category,
                'Sales Revenue': sales_amount,
                'Expenses': expenses_amount,
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
        logging.error(f"Error exporting profitability report: {str(e)}")
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/reports/chef-performance', methods=['GET'])
@login_required
def export_chef_performance_report():
    try:
        # Get query parameters
        start_date = parse_date(request.args.get('start_date'))
        end_date = parse_date(request.args.get('end_date'))
        format_type = request.args.get('format', 'csv')
        
        # Get chef performance data (always from local database)
        chef_data = dashboard_service.get_chef_performance_data(start_date, end_date)
        
        # Prepare data for export
        data = []
        for chef in chef_data:
            data.append({
                'Chef ID': chef['chef_id'],
                'Chef Name': chef['chef_name'],
                'Orders Handled': chef['orders_handled'],
                'Total Revenue': chef['total_revenue'],
                'Average Order Value': chef['avg_order_value']
            })
        
        df = pd.DataFrame(data)
        
        if format_type == 'excel':
            # Create Excel file
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Chef Performance Report', index=False)
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
        logging.error(f"Error exporting chef performance report: {str(e)}")
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/items/uncategorized', methods=['GET'])
@login_required
def get_uncategorized_items():
    try:
        # Get uncategorized items from local database
        uncategorized_items = UncategorizedItem.query.all()
        
        items_data = [{
            'id': item.id,
            'name': item.name,
            'count': item.count,
            'total_revenue': float(item.total_revenue) if item.total_revenue else 0
        } for item in uncategorized_items]
        
        return jsonify({
            'uncategorized_items': items_data
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting uncategorized items: {str(e)}")
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/items/uncategorized/<int:item_id>/categorize', methods=['PUT'])
@admin_required
def categorize_item(item_id):
    try:
        data = request.get_json()
        category = data.get('category')
        
        if not category:
            return jsonify({'error': 'Category is required'}), 400
        
        # Get the uncategorized item
        uncategorized_item = UncategorizedItem.query.get(item_id)
        if not uncategorized_item:
            return jsonify({'error': 'Item not found'}), 404
        
        # Create or update the item in the main inventory
        existing_item = Item.query.filter_by(name=uncategorized_item.name).first()
        
        if existing_item:
            # Update existing item
            existing_item.category = category
            existing_item.quantity = (existing_item.quantity or 0) + uncategorized_item.count
        else:
            # Create new item
            new_item = Item(
                name=uncategorized_item.name,
                category=category,
                quantity=uncategorized_item.count,
                price=0  # Default price, can be updated later
            )
            db.session.add(new_item)
        
        # Delete the uncategorized item
        db.session.delete(uncategorized_item)
        db.session.commit()
        
        return jsonify({
            'message': 'Item categorized successfully',
            'item_name': uncategorized_item.name,
            'category': category
        }), 200
        
    except Exception as e:
        logging.error(f"Error categorizing item: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

