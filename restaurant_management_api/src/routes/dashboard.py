from flask import Blueprint, request, jsonify
from ..models import db, Sale, Expense, Item, Chef, ChefDishMapping, UncategorizedItem, FileUpload
from ..routes.auth import login_required
from ..services.dashboard_service import DashboardService
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
import pandas as pd
import logging
from src.models.data_source_config import DataSourceConfig
from flask import current_app
import pytz

dashboard_bp = Blueprint('dashboard', __name__)
dashboard_service = DashboardService()

def parse_date(date_str, is_end=False):
    if not date_str:
        return None
    try:
        central = pytz.timezone('America/Chicago')
        # Use only the date part, ignore time and timezone info
        date_only = date_str[:10]  # 'YYYY-MM-DD'
        dt = datetime.strptime(date_only, '%Y-%m-%d')
        dt = central.localize(dt)
        if is_end:
            return dt.replace(hour=23, minute=59, second=59, microsecond=999000)
        else:
            return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    except ValueError as e:
        logging.error(f"Error parsing date {date_str}: {str(e)}")
        return None

@dashboard_bp.route('/sales-summary', methods=['GET'])
@login_required
def get_sales_summary():
    try:
        # Get query parameters
        start_date_raw = request.args.get('start_date')
        end_date_raw = request.args.get('end_date')
        start_date = parse_date(start_date_raw)
        end_date = parse_date(end_date_raw, is_end=True)
        if start_date and not end_date:
            # If end_date is blank, default to end of start_date
            end_date = parse_date(start_date_raw, is_end=True)
        category = request.args.get('category')
        
        # Debug logging
        logging.info(f"Sales summary request - start_date: {start_date_raw}, parsed: {start_date}")
        logging.info(f"Sales summary request - end_date: {end_date_raw}, parsed: {end_date}")
        logging.info(f"Sales summary request - category: {category}")
        
        # Use dashboard service to get sales data from configured source
        sales_data = dashboard_service.get_sales_summary(start_date, end_date, category)
        
        return jsonify(sales_data), 200
        
    except Exception as e:
        logging.error(f"Error in sales summary: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/chef-performance', methods=['GET'])
@login_required
def get_chef_performance():
    logging.info("=== CHEF PERFORMANCE ROUTE CALLED ===")
    try:
        # Get query parameters
        start_date = parse_date(request.args.get('start_date'))
        end_date = parse_date(request.args.get('end_date'), is_end=True)
        chef_ids = request.args.get('chef_ids')
        
        # Debug logging
        logging.info(f"Chef performance request - start_date: {request.args.get('start_date')}, parsed: {start_date}")
        logging.info(f"Chef performance request - end_date: {request.args.get('end_date')}, parsed: {end_date}")
        logging.info(f"Chef performance request - chef_ids: {chef_ids}")
        
        # Use dashboard service to get chef performance data
        logging.info("About to call dashboard_service.get_chef_performance_data")
        chef_data = dashboard_service.get_chef_performance_data(start_date, end_date, chef_ids)
        logging.info(f"Chef performance data returned: {type(chef_data)}")
        
        return jsonify(chef_data), 200
        
    except Exception as e:
        logging.error(f"Error in chef performance: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/expenses', methods=['GET'])
@login_required
def get_expenses_dashboard():
    try:
        # Get query parameters
        start_date = parse_date(request.args.get('start_date'))
        end_date = parse_date(request.args.get('end_date'), is_end=True)
        
        # Debug logging
        logging.info(f"Expenses request - start_date: {request.args.get('start_date')}, parsed: {start_date}")
        logging.info(f"Expenses request - end_date: {request.args.get('end_date')}, parsed: {end_date}")
        
        # Use dashboard service to get expenses data
        expenses_data = dashboard_service.get_expenses_data(start_date, end_date)
        
        return jsonify(expenses_data), 200
        
    except Exception as e:
        logging.error(f"Error in expenses dashboard: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/overview', methods=['GET'])
@login_required
def get_overview():
    try:
        # Get query parameters
        start_date = parse_date(request.args.get('start_date'))
        end_date = parse_date(request.args.get('end_date'), is_end=True)
        logging.info(f"Dashboard overview request - start_date: {start_date}, end_date: {end_date}")
        overview = dashboard_service.get_dashboard_overview(start_date, end_date)
        return jsonify(overview), 200
    except Exception as e:
        logging.error(f"Error in dashboard overview: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/staff-performance', methods=['GET'])
@login_required
def get_staff_performance():
    try:
        start_date = parse_date(request.args.get('start_date'))
        end_date = parse_date(request.args.get('end_date'), is_end=True)
        chef_ids = request.args.get('chef_ids')
        logging.info(f"Staff performance request - start_date: {start_date}, end_date: {end_date}, chef_ids: {chef_ids}")
        staff_perf = dashboard_service.get_chef_performance_data(start_date, end_date, chef_ids)
        return jsonify(staff_perf), 200
    except Exception as e:
        logging.error(f"Error in staff performance: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/profitability', methods=['GET'])
@login_required
def get_profitability():
    try:
        start_date = parse_date(request.args.get('start_date'))
        end_date = parse_date(request.args.get('end_date'), is_end=True)
        logging.info(f"Profitability request - start_date: {start_date}, end_date: {end_date}")
        profitability = dashboard_service.get_profitability(start_date, end_date)
        return jsonify(profitability), 200
    except Exception as e:
        logging.error(f"Error in profitability: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/items/uncategorized', methods=['GET'])
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

@dashboard_bp.route('/items/uncategorized/<int:item_id>/categorize', methods=['PUT'])
@login_required
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
            existing_item.updated_at = datetime.utcnow()
        else:
            # Create new item
            new_item = Item(
                name=uncategorized_item.name,
                category=category,
                price=0.0,  # Default price
                quantity=0,  # Default quantity
                is_active=True
            )
            db.session.add(new_item)
        
        # Delete the uncategorized item
        db.session.delete(uncategorized_item)
        db.session.commit()
        
        return jsonify({'message': 'Item categorized successfully'}), 200
        
    except Exception as e:
        logging.error(f"Error categorizing item: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/recent-activity', methods=['GET'])
@login_required
def get_recent_activity():
    try:
        # Get recent activity from various sources
        activities = []
        
        # Recent sales (from configured source)
        sales_data = dashboard_service.get_sales_summary()
        if sales_data.get('total_transactions', 0) > 0:
            activities.append({
                'type': 'sales',
                'message': f"{sales_data['total_transactions']} transactions processed",
                'timestamp': datetime.now().isoformat(),
                'value': sales_data['total_revenue']
            })
        
        # Recent expenses (from local database)
        expenses_data = dashboard_service.get_expenses_data()
        if expenses_data.get('expense_count', 0) > 0:
            activities.append({
                'type': 'expenses',
                'message': f"{expenses_data['expense_count']} expenses recorded",
                'timestamp': datetime.now().isoformat(),
                'value': expenses_data['total_expenses']
            })
        
        # Recent inventory updates (from configured source)
        inventory_data = dashboard_service.get_inventory_data()
        if inventory_data.get('total', 0) > 0:
            activities.append({
                'type': 'inventory',
                'message': f"{inventory_data['total']} items in inventory",
                'timestamp': datetime.now().isoformat(),
                'value': inventory_data['total']
            })
        
        # Sort by timestamp (most recent first)
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'activities': activities[:10]  # Return last 10 activities
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting recent activity: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/quick-actions', methods=['GET'])
@login_required
def get_quick_actions():
    try:
        # Get quick actions based on current data state
        actions = []
        
        # Check for uncategorized items
        uncategorized_count = UncategorizedItem.query.count()
        if uncategorized_count > 0:
            actions.append({
                'id': 'categorize',
                'title': 'Categorize Items',
                'description': f'{uncategorized_count} items need categorization',
                'action': 'navigate_to_inventory',
                'priority': 'high'
            })
        
        # Check data source status
        data_source_status = dashboard_service.get_data_source_status()
        for data_type, status in data_source_status.items():
            if status['status'] == 'error':
                actions.append({
                    'id': f'fix_{data_type}_connection',
                    'title': f'Fix {data_type.title()} Connection',
                    'description': f'Connection to {status["source"]} data source failed',
                    'action': 'navigate_to_clover',
                    'priority': 'high'
                })
        
        # Add default actions
        actions.extend([
            {
                'id': 'upload',
                'title': 'Upload Data',
                'description': 'Upload new sales, inventory, or expense data',
                'action': 'navigate_to_admin',
                'priority': 'medium'
            },
            {
                'id': 'report',
                'title': 'Generate Report',
                'description': 'Create detailed reports and analytics',
                'action': 'navigate_to_reports',
                'priority': 'medium'
            }
        ])
        
        return jsonify({
            'actions': actions
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting quick actions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/stats', methods=['GET'])
@login_required
def get_dashboard_stats():
    try:
        # Get stats from configured data sources
        sales_data = dashboard_service.get_sales_summary()
        inventory_data = dashboard_service.get_inventory_data()
        expenses_data = dashboard_service.get_expenses_data()
        
        # Get chef mapping count from local database
        chef_mapping_count = ChefDishMapping.query.count()
        
        # Get data source status
        data_source_status = dashboard_service.get_data_source_status()
        
        stats = {
            'sales': {
                'count': sales_data.get('total_transactions', 0),
                'last_updated': datetime.now().isoformat(),
                'source': data_source_status.get('sales', {}).get('source', 'unknown'),
                'status': data_source_status.get('sales', {}).get('status', 'unknown')
            },
            'inventory': {
                'count': inventory_data.get('total', 0),
                'last_updated': datetime.now().isoformat(),
                'source': data_source_status.get('inventory', {}).get('source', 'unknown'),
                'status': data_source_status.get('inventory', {}).get('status', 'unknown')
            },
            'expenses': {
                'count': expenses_data.get('expense_count', 0),
                'last_updated': datetime.now().isoformat(),
                'source': 'local',
                'status': 'connected'
            },
            'chef_mapping': {
                'count': chef_mapping_count,
                'last_updated': datetime.now().isoformat(),
                'source': 'local',
                'status': 'connected'
            }
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        logging.error(f"Error getting dashboard stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/data-source-config', methods=['GET', 'PUT'])
@login_required
def manage_data_source_config():
    from flask import session
    try:
        user = session.get('username', 'unknown')
        is_superadmin = session.get('is_admin', False) and not session.get('tenant_id')
        if request.method == 'GET':
            # Return current configuration from DB if available
            configs = DataSourceConfig.query.all()
            if configs:
                data_sources = {f"{c.data_type}": c.source for c in configs if c.tenant_id is None}
            else:
                data_sources = dashboard_service.data_sources
            return jsonify({
                'data_sources': data_sources,
                'status': dashboard_service.get_data_source_status()
            }), 200
        else:
            # Only superadmins can update
            if not is_superadmin:
                return jsonify({'error': 'Only superadmins can update data source config.'}), 403
            data = request.get_json()
            new_config = data.get('data_sources', {})
            valid_sources = ['clover', 'local']
            valid_types = ['sales', 'inventory']
            for data_type, source in new_config.items():
                if data_type not in valid_types:
                    return jsonify({'error': f'Invalid data type: {data_type}'}), 400
                if source not in valid_sources:
                    return jsonify({'error': f'Invalid data source: {source}'}), 400
                # Upsert config in DB
                config = DataSourceConfig.query.filter_by(tenant_id=None, data_type=data_type).first()
                if config:
                    config.source = source
                    config.updated_by = user
                    config.updated_at = datetime.utcnow()
                else:
                    config = DataSourceConfig(
                        tenant_id=None,
                        data_type=data_type,
                        source=source,
                        updated_by=user,
                        updated_at=datetime.utcnow()
                    )
                    db.session.add(config)
                current_app.logger.info(f"[AUDIT] Data source config updated: {data_type} -> {source} by {user}")
            db.session.commit()
            # Also update in-memory config for backward compatibility
            dashboard_service.data_sources.update(new_config)
            dashboard_service.clear_clover_cache()
            return jsonify({
                'message': 'Data source configuration updated successfully',
                'data_sources': {f"{c.data_type}": c.source for c in DataSourceConfig.query.filter_by(tenant_id=None).all()}
            }), 200
    except Exception as e:
        logging.error(f"Error managing data source config: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/chefs', methods=['GET'])
@login_required
def get_chefs_list():
    try:
        # If multi-tenant, filter by tenant_id from session
        from flask import session
        tenant_id = session.get('tenant_id')
        query = Chef.query.filter_by(is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        chefs = query.all()
        return jsonify([
            {'id': chef.id, 'name': chef.name, 'clover_id': chef.clover_id}
            for chef in chefs
        ]), 200
    except Exception as e:
        logging.error(f"Error fetching chef list: {str(e)}")
        return jsonify({'error': str(e)}), 500

