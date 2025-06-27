from flask import Blueprint, request, jsonify
from src.services.ai_service import AIService
from src.services.dashboard_service import DashboardService
from src.models import db
from src.models.sale import Sale
from src.models.item import Item
from src.utils.auth import login_required
import logging
from datetime import datetime, timedelta

# Set logging level to WARNING for production
logging.basicConfig(level=logging.WARNING)

# Simple in-memory cache for AI insights
_ai_insights_cache = {'data': None, 'timestamp': None}
_AI_INSIGHTS_CACHE_TTL = 180  # seconds (3 minutes)

ai_bp = Blueprint('ai', __name__)
ai_service = AIService()
dashboard_service = DashboardService()
logger = logging.getLogger(__name__)

def get_sales_data_for_ai(mode='item'):
    """Get sales data from configured source for AI processing.
    mode='item': return item-level sales (for insights)
    mode='daily': return daily totals (for predictions)
    """
    try:
        data_source = dashboard_service.get_data_source('sales')
        logger.info(f"AI processing using sales data source: {data_source}, mode={mode}")
        if data_source == 'clover':
            logger.info("Fetching Clover orders for AI processing...")
            orders = dashboard_service.clover_service.get_orders()
            summary = dashboard_service._process_clover_orders(orders)
            sales_list = []
            if mode == 'daily':
                for daily in summary.get('daily_sales', []):
                    sales_list.append({
                        'line_item_date': daily['date'],
                        'total_revenue': daily['revenue'],
                        'quantity': 1,
                        'item_id': 'DAILY',
                        'item_name': 'DAILY',
                        'order_employee_id': 'DAILY'
                    })
            else:  # mode == 'item'
                for order in orders:
                    order_date = datetime.fromtimestamp(order['createdTime'] / 1000).strftime('%Y-%m-%d')
                    line_items = order.get('lineItems', {}).get('elements', [])
                    for li in line_items:
                        item = li.get('item', {})
                        item_id = item.get('id', 'unknown')
                        item_name = item.get('name', 'Unknown')
                        quantity = li.get('quantity', 1)
                        total_cents = li.get('total', 0)
                        price_cents = li.get('price', 0)
                        if total_cents:
                            revenue = float(total_cents) / 100
                        else:
                            revenue = float(price_cents) * float(quantity) / 100
                        sales_list.append({
                            'line_item_date': order_date,
                            'total_revenue': revenue,
                            'quantity': quantity,
                            'item_id': item_id,
                            'item_name': item_name,
                            'order_employee_id': order.get('employee', {}).get('id', 'unknown')
                        })
            logger.info(f"Processed {len(sales_list)} sales records from Clover for AI (mode={mode})")
        else:
            logger.info("Fetching local sales data for AI processing...")
            sales_data = db.session.query(Sale).all()
            if mode == 'daily':
                sales_by_date = {}
                for sale in sales_data:
                    date_str = sale.line_item_date.strftime('%Y-%m-%d')
                    sales_by_date.setdefault(date_str, 0)
                    sales_by_date[date_str] += float(sale.total_revenue)
                sales_list = []
                for date_str, revenue in sales_by_date.items():
                    sales_list.append({
                        'line_item_date': date_str,
                        'total_revenue': revenue,
                        'quantity': 1,
                        'item_id': 'DAILY',
                        'item_name': 'DAILY',
                        'order_employee_id': 'DAILY'
                    })
            else:  # mode == 'item'
                sales_list = []
                for sale in sales_data:
                    sales_list.append({
                        'line_item_date': sale.line_item_date.strftime('%Y-%m-%d'),
                        'total_revenue': float(sale.total_revenue),
                        'quantity': sale.quantity,
                        'item_id': sale.item_id,
                        'item_name': getattr(sale, 'item_name', 'Unknown'),
                        'order_employee_id': sale.order_employee_id
                    })
            logger.info(f"Processed {len(sales_list)} sales records from local DB for AI (mode={mode})")
        return sales_list
    except Exception as e:
        logger.error(f"Error getting sales data for AI: {str(e)}")
        return []

def get_inventory_data_for_ai():
    """Get inventory data from configured source for AI processing"""
    try:
        # Get inventory data from configured source
        inventory_data = dashboard_service.get_inventory_data()
        
        if inventory_data and 'items' in inventory_data:
            return inventory_data['items']
        else:
            # Fallback to local database
            inventory_data = db.session.query(Item).all()
            inventory_list = []
            
            for item in inventory_data:
                inventory_list.append({
                    'id': item.id,
                    'name': item.name,
                    'quantity': item.quantity,
                    'reorder_point': item.reorder_point,
                    'category': item.category
                })
            
            return inventory_list
            
    except Exception as e:
        logger.error(f"Error getting inventory data for AI: {str(e)}")
        return []

@ai_bp.route('/predictions/sales', methods=['GET'])
@login_required
def get_sales_predictions():
    """Get sales predictions for next N days"""
    try:
        days_ahead = request.args.get('days', 7, type=int)
        window = request.args.get('window', 90)
        if window == 'all':
            window = 10000
        else:
            try:
                window = int(window)
            except Exception:
                window = 90
        if not isinstance(days_ahead, int) or days_ahead <= 0:
            return jsonify({'status': 'error', 'message': 'Invalid days parameter'}), 400
        # Use daily aggregation for predictions
        sales_list = get_sales_data_for_ai(mode='daily')
        # Filter by window
        now = datetime.now()
        cutoff_date = now - timedelta(days=window)
        filtered_sales_list = []
        for s in sales_list:
            try:
                sale_date = datetime.strptime(s['line_item_date'], '%Y-%m-%d')
            except Exception:
                continue
            if sale_date >= cutoff_date:
                filtered_sales_list.append(s)
        sales_list = filtered_sales_list
        if not sales_list:
            return jsonify({
                'status': 'error',
                'message': 'No sales data available for predictions'
            }), 400
        predictions = ai_service.predict_sales(days_ahead)
        return jsonify({
            'status': 'success',
            'data': predictions,
            'total_sales_records': len(sales_list),
            'data_source': dashboard_service.get_data_source('sales'),
            'window_days': window
        }), 200
    except Exception as e:
        logger.error(f"Error getting sales predictions: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to generate sales predictions: {str(e)}'
        }), 500

@ai_bp.route('/insights/automated', methods=['GET'])
@login_required
def get_automated_insights():
    """Get automated insights from sales data"""
    import time
    start_time = time.time()
    try:
        window = request.args.get('window', 90)
        if window == 'all':
            window = 10000
        else:
            try:
                window = int(window)
            except Exception:
                window = 90
        # Use item-level data for insights
        sales_list = get_sales_data_for_ai(mode='item')
        if not sales_list:
            return jsonify({
                'status': 'error',
                'message': 'No sales data available for insights'
            }), 400
        # Filter by window
        now = datetime.now()
        cutoff_date = now - timedelta(days=window)
        filtered_sales_list = []
        for s in sales_list:
            try:
                sale_date = datetime.strptime(s['line_item_date'], '%Y-%m-%d')
            except Exception:
                continue
            if sale_date >= cutoff_date:
                filtered_sales_list.append(s)
        sales_list = filtered_sales_list
        num_days = len(set(s['line_item_date'] for s in sales_list))
        # Check cache
        cache_key = f"ai_insights_{window}_{num_days}"
        now_ts = time.time()
        if (_ai_insights_cache.get('data') is not None and
            _ai_insights_cache.get('cache_key') == cache_key and
            _ai_insights_cache['timestamp'] is not None and
            now_ts - _ai_insights_cache['timestamp'] < _AI_INSIGHTS_CACHE_TTL):
            logging.info('Returning cached AI insights')
            insights = _ai_insights_cache['data']
        else:
            logging.info('Generating new AI insights')
            insights = ai_service.generate_insights(sales_list)
            # Add fallback messages for missing insights
            if not insights:
                insights = [{
                    'type': 'no_insights',
                    'title': 'Not Enough Data',
                    'description': 'Not enough data for robust insights. Add more sales data for better results.',
                    'priority': 'high',
                    'owner_explanation': 'AI insights require at least 30 days of sales data. Please add more data.'
                }]
            _ai_insights_cache['data'] = insights
            _ai_insights_cache['timestamp'] = now_ts
            _ai_insights_cache['cache_key'] = cache_key
        elapsed = time.time() - start_time
        logging.warning(f"AI insights endpoint took {elapsed:.2f} seconds")
        return jsonify({
            'status': 'success',
            'data': insights,
            'total_sales_records': len(sales_list),
            'data_source': dashboard_service.get_data_source('sales'),
            'elapsed_seconds': elapsed,
            'window_days': window,
            'num_days': num_days
        }), 200
    except Exception as e:
        logger.error(f"Error generating insights: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to generate insights: {str(e)}'
        }), 500

@ai_bp.route('/models/train', methods=['POST'])
@login_required
def train_models():
    """Train AI models with current data"""
    try:
        window = request.args.get('window', 90)
        if window == 'all':
            window = 10000
        else:
            try:
                window = int(window)
            except Exception:
                window = 90
        # Get sales data from configured source
        sales_list = get_sales_data_for_ai()
        # Filter by window
        cutoff_date = datetime.now() - timedelta(days=window)
        filtered_sales_list = []
        for s in sales_list:
            try:
                sale_date = datetime.strptime(s['line_item_date'], '%Y-%m-%d')
            except Exception:
                continue
            if sale_date >= cutoff_date:
                filtered_sales_list.append(s)
        sales_list = filtered_sales_list
        if not sales_list:
            return jsonify({
                'status': 'error',
                'message': 'No sales data available for training'
            }), 400
        # Train sales model
        result = ai_service.train_sales_forecast_model(sales_list)
        return jsonify(result), 200 if result['status'] == 'success' else 500
    except Exception as e:
        logger.error(f"Error training models: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to train models'
        }), 500

@ai_bp.route('/models/status', methods=['GET'])
@login_required
def get_model_status():
    """Get status of trained AI models"""
    try:
        import os
        model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', 'sales_forecast_model.pkl')
        trained = os.path.exists(model_path)
        status = {
            'trained': trained,
            'model_path': model_path,
        }
        if trained:
            # Optionally, add more info (e.g., model score) if available
            try:
                from src.services.ai_service import AIService
                ai_service = AIService()
                # If get_model_status exists, use it
                if hasattr(ai_service, 'get_model_status'):
                    status.update(ai_service.get_model_status())
            except Exception:
                pass
        return jsonify({'status': 'success', 'data': status}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@ai_bp.route('/inventory/optimize', methods=['GET'])
@login_required
def get_inventory_optimization():
    """Get inventory optimization recommendations"""
    try:
        # Get sales data from configured source
        sales_list = get_sales_data_for_ai()
        
        # Get inventory data from configured source
        inventory_list = get_inventory_data_for_ai()
        
        if not sales_list:
            return jsonify({
                'status': 'error',
                'message': 'No sales data available for optimization'
            }), 400
        
        if not inventory_list:
            return jsonify({
                'status': 'error',
                'message': 'No inventory data available for optimization'
            }), 400
        
        recommendations = ai_service.optimize_inventory(sales_list, inventory_list)
        
        return jsonify({
            'status': 'success',
            'data': recommendations,
            'total_items_analyzed': len(inventory_list),
            'sales_data_source': dashboard_service.get_data_source('sales'),
            'inventory_data_source': dashboard_service.get_data_source('inventory')
        }), 200
        
    except Exception as e:
        logger.error(f"Error optimizing inventory: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to optimize inventory'
        }), 500

@ai_bp.route('/customers/segments', methods=['GET'])
@login_required
def get_customer_segments():
    """Get customer segmentation analysis"""
    try:
        # Get sales data from configured source
        sales_list = get_sales_data_for_ai()
        
        if not sales_list:
            return jsonify({
                'status': 'error',
                'message': 'No sales data available for segmentation'
            }), 400
        
        segments = ai_service.segment_customers(sales_list)
        
        return jsonify({
            'status': 'success',
            'data': segments,
            'total_customers_analyzed': len(set(sale['order_employee_id'] for sale in sales_list)),
            'data_source': dashboard_service.get_data_source('sales')
        }), 200
        
    except Exception as e:
        logger.error(f"Error segmenting customers: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to segment customers'
        }), 500

@ai_bp.route('/anomalies/detect', methods=['GET'])
@login_required
def detect_anomalies():
    """Detect anomalies in sales data"""
    try:
        # Get sales data from configured source
        sales_list = get_sales_data_for_ai()
        
        if not sales_list:
            return jsonify({
                'status': 'error',
                'message': 'No sales data available for anomaly detection'
            }), 400
        
        anomalies = ai_service.detect_anomalies(sales_list)
        
        return jsonify({
            'status': 'success',
            'data': anomalies,
            'total_anomalies': len(anomalies),
            'data_source': dashboard_service.get_data_source('sales')
        }), 200
        
    except Exception as e:
        logger.error(f"Error detecting anomalies: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to detect anomalies'
        }), 500

@ai_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for AI service"""
    try:
        return jsonify({
            'status': 'healthy',
            'service': 'ai',
            'timestamp': datetime.utcnow().isoformat(),
            'data_sources': {
                'sales': dashboard_service.get_data_source('sales'),
                'inventory': dashboard_service.get_data_source('inventory')
            }
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'ai',
            'error': str(e)
        }), 500 