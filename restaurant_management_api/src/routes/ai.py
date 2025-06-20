from flask import Blueprint, request, jsonify
from src.services.ai_service import AIService
from src.models import db
from src.models.sale import Sale
from src.models.item import Item
from src.utils.auth import login_required
import logging

ai_bp = Blueprint('ai', __name__)
ai_service = AIService()
logger = logging.getLogger(__name__)

@ai_bp.route('/predictions/sales', methods=['GET'])
@login_required
def get_sales_predictions():
    """Get sales predictions for next 7 days"""
    try:
        days_ahead = request.args.get('days', 7, type=int)
        
        # Validate input
        if days_ahead < 1 or days_ahead > 30:
            return jsonify({
                'status': 'error',
                'message': 'Days ahead must be between 1 and 30'
            }), 400
        
        predictions = ai_service.predict_sales(days_ahead)
        
        return jsonify({
            'status': 'success',
            'data': predictions,
            'days_ahead': days_ahead
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting sales predictions: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to generate predictions'
        }), 500

@ai_bp.route('/insights/automated', methods=['GET'])
@login_required
def get_automated_insights():
    """Get automated insights from sales data"""
    try:
        # Get sales data from database
        sales_data = db.session.query(Sale).all()
        sales_list = []
        
        for sale in sales_data:
            sales_list.append({
                'line_item_date': sale.line_item_date.isoformat(),
                'total_revenue': float(sale.total_revenue),
                'quantity': sale.quantity,
                'item_id': sale.item_id
            })
        
        insights = ai_service.generate_insights(sales_list)
        
        return jsonify({
            'status': 'success',
            'data': insights,
            'total_sales_records': len(sales_list)
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating insights: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to generate insights'
        }), 500

@ai_bp.route('/models/train', methods=['POST'])
@login_required
def train_models():
    """Train AI models with current data"""
    try:
        # Get sales data
        sales_data = db.session.query(Sale).all()
        sales_list = []
        
        for sale in sales_data:
            sales_list.append({
                'line_item_date': sale.line_item_date.isoformat(),
                'total_revenue': float(sale.total_revenue),
                'quantity': sale.quantity,
                'item_id': sale.item_id
            })
        
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
    """Get status of trained models"""
    try:
        status = ai_service.get_model_status()
        
        return jsonify({
            'status': 'success',
            'data': status
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting model status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get model status'
        }), 500

@ai_bp.route('/health', methods=['GET'])
def ai_health_check():
    """Health check for AI service"""
    try:
        # Check if AI service is working
        status = ai_service.get_model_status()
        
        return jsonify({
            'status': 'healthy',
            'ai_service': 'operational',
            'models_status': status
        }), 200
        
    except Exception as e:
        logger.error(f"AI health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'ai_service': 'error',
            'error': str(e)
        }), 500 