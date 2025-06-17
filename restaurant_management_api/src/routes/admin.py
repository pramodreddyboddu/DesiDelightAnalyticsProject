from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
from ..models import db
from ..models.sale import Sale
from ..models.item import Item
from ..models.expense import Expense
from ..models.chef_dish_mapping import ChefDishMapping
from ..models.file_upload import FileUpload
from ..utils.auth import admin_required
from sqlalchemy import func, case
import logging
import pytz

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/data-stats', methods=['GET'])
@admin_required
def get_data_stats():
    """Get statistics about the data in the system"""
    try:
        # Get counts for each data type
        sales_count = db.session.query(func.count(Sale.id)).scalar()
        inventory_count = db.session.query(func.count(Item.id)).filter(Item.is_active == True).scalar()
        expenses_count = db.session.query(func.count(Expense.id)).scalar()
        chef_mapping_count = db.session.query(func.count(ChefDishMapping.id)).scalar()

        # Get last updated times
        last_sales_update = db.session.query(func.max(Sale.line_item_date)).scalar()
        last_inventory_update = db.session.query(func.max(Item.updated_at)).scalar()
        last_expenses_update = db.session.query(func.max(Expense.date)).scalar()
        last_chef_mapping_update = db.session.query(func.max(ChefDishMapping.created_at)).scalar()

        # Log the raw timestamp values
        current_app.logger.info(f"Raw timestamps - Sales: {last_sales_update}, Inventory: {last_inventory_update}, Expenses: {last_expenses_update}, Chef Mapping: {last_chef_mapping_update}")

        # Format timestamps
        def format_timestamp(ts):
            if ts is None:
                return None
            if isinstance(ts, str):
                return ts
            try:
                # Convert to CST timezone
                cst = pytz.timezone('America/Chicago')
                if ts.tzinfo is None:
                    ts = pytz.utc.localize(ts)
                cst_ts = ts.astimezone(cst)
                return cst_ts.strftime('%Y-%m-%dT%H:%M:%S')
            except Exception as e:
                current_app.logger.error(f"Error formatting timestamp {ts}: {str(e)}")
                return None

        # Log formatted timestamps
        formatted_sales = format_timestamp(last_sales_update)
        formatted_inventory = format_timestamp(last_inventory_update)
        formatted_expenses = format_timestamp(last_expenses_update)
        formatted_chef = format_timestamp(last_chef_mapping_update)
        
        current_app.logger.info(f"Formatted timestamps - Sales: {formatted_sales}, Inventory: {formatted_inventory}, Expenses: {formatted_expenses}, Chef Mapping: {formatted_chef}")

        return jsonify({
            'sales': {
                'count': sales_count,
                'last_updated': formatted_sales
            },
            'inventory': {
                'count': inventory_count,
                'last_updated': formatted_inventory
            },
            'expenses': {
                'count': expenses_count,
                'last_updated': formatted_expenses
            },
            'chef_mapping': {
                'count': chef_mapping_count,
                'last_updated': formatted_chef
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error getting data stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/diagnostic/inventory', methods=['GET'])
@admin_required
def get_inventory_diagnostic():
    """Get detailed diagnostic information about inventory items"""
    try:
        # Get counts by status
        status_counts = db.session.query(
            Item.is_active,
            func.count(Item.id).label('count')
        ).group_by(Item.is_active).all()
        
        # Get items with sales
        items_with_sales = db.session.query(
            Item.id,
            Item.name,
            Item.is_active,
            func.count(Sale.id).label('sales_count')
        ).join(Sale, Item.id == Sale.item_id)\
         .group_by(Item.id, Item.name, Item.is_active)\
         .having(func.count(Sale.id) > 0)\
         .all()
        
        # Get items with chef mappings
        items_with_chef_mappings = db.session.query(
            Item.id,
            Item.name,
            Item.is_active,
            func.count(ChefDishMapping.id).label('mapping_count')
        ).join(ChefDishMapping, Item.id == ChefDishMapping.item_id)\
         .group_by(Item.id, Item.name, Item.is_active)\
         .having(func.count(ChefDishMapping.id) > 0)\
         .all()
        
        return jsonify({
            'status_counts': [
                {'is_active': status, 'count': count}
                for status, count in status_counts
            ],
            'items_with_sales': [
                {
                    'id': item.id,
                    'name': item.name,
                    'is_active': item.is_active,
                    'sales_count': item.sales_count
                }
                for item in items_with_sales
            ],
            'items_with_chef_mappings': [
                {
                    'id': item.id,
                    'name': item.name,
                    'is_active': item.is_active,
                    'mapping_count': item.mapping_count
                }
                for item in items_with_chef_mappings
            ]
        })
    except Exception as e:
        current_app.logger.error(f"Error in inventory diagnostic: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/force-delete-inventory', methods=['DELETE'])
@admin_required
def force_delete_inventory():
    """Force delete all inventory items"""
    try:
        # Start transaction
        db.session.begin_nested()
        
        # First, get count of items
        total_items = db.session.query(func.count(Item.id)).scalar()
        current_app.logger.info(f"Found {total_items} total inventory items")
        
        # Delete all items in batches
        batch_size = 1000
        deleted = 0
        
        while deleted < total_items:
            # Get batch of items
            items = db.session.query(Item).limit(batch_size).offset(deleted).all()
            if not items:
                break
                
            # Delete each item
            for item in items:
                try:
                    db.session.delete(item)
                except Exception as e:
                    current_app.logger.error(f"Error deleting item {item.id}: {str(e)}")
                    continue
            
            # Commit batch
            db.session.commit()
            deleted += len(items)
            current_app.logger.info(f"Deleted {deleted} items so far")
        
        # Verify deletion
        remaining = db.session.query(func.count(Item.id)).scalar()
        if remaining > 0:
            current_app.logger.warning(f"Found {remaining} items still remaining, trying direct delete")
            # Try direct delete
            db.session.query(Item).delete(synchronize_session=False)
            db.session.commit()
        
        # Final verification
        final_count = db.session.query(func.count(Item.id)).scalar()
        current_app.logger.info(f"Final item count: {final_count}")
        
        return jsonify({
            'message': f'Successfully deleted {deleted} inventory items',
            'deleted_count': deleted,
            'remaining_count': final_count
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error during force delete: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/delete-data', methods=['DELETE'])
@admin_required
def delete_data():
    """Delete data within a specified date range"""
    try:
        data = request.get_json()
        if not data:
            current_app.logger.error("No JSON data received")
            return jsonify({'error': 'No data provided. Please provide data_type, start_date, and end_date in JSON format'}), 400
            
        data_type = data.get('data_type')
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        # Validate required fields
        missing_fields = []
        if not data_type:
            missing_fields.append('data_type')
        if not start_date:
            missing_fields.append('start_date')
        if not end_date:
            missing_fields.append('end_date')
            
        if missing_fields:
            error_msg = f"Missing required fields: {', '.join(missing_fields)}"
            current_app.logger.error(error_msg)
            return jsonify({'error': error_msg}), 400

        # Validate data type
        valid_data_types = ['sales', 'inventory', 'expenses', 'chef_mapping']
        if data_type not in valid_data_types:
            error_msg = f"Invalid data_type. Must be one of: {', '.join(valid_data_types)}"
            current_app.logger.error(error_msg)
            return jsonify({'error': error_msg}), 400

        try:
            # Handle timezone-aware dates by removing 'Z' and converting to UTC
            start_date = start_date.replace('Z', '+00:00')
            end_date = end_date.replace('Z', '+00:00')
            start_date = datetime.fromisoformat(start_date)
            end_date = datetime.fromisoformat(end_date)
        except ValueError as e:
            current_app.logger.error(f"Invalid date format: {str(e)}")
            return jsonify({'error': 'Invalid date format. Please use ISO format (YYYY-MM-DDTHH:MM:SS.SSSZ)'}), 400

        # Map data types to their corresponding models and date fields
        model_map = {
            'sales': (Sale, 'line_item_date'),
            'inventory': (Item, 'created_at'),
            'expenses': (Expense, 'date'),
            'chef_mapping': (ChefDishMapping, 'created_at')
        }

        model, date_field = model_map[data_type]
        
        # Special handling for inventory items
        if data_type == 'inventory':
            try:
                # Start transaction
                db.session.begin_nested()
                
                # Get total count before deletion
                total_items = db.session.query(func.count(Item.id)).filter(
                    getattr(model, date_field) >= start_date,
                    getattr(model, date_field) <= end_date
                ).scalar()
                
                current_app.logger.info(f"Found {total_items} items to process in date range")
                
                # Try direct delete first
                result = db.session.query(Item).filter(
                    getattr(model, date_field) >= start_date,
                    getattr(model, date_field) <= end_date
                ).delete(synchronize_session=False)
                
                db.session.commit()
                current_app.logger.info(f"Direct delete affected {result} items")
                
                # Verify deletion
                remaining_items = db.session.query(func.count(Item.id)).filter(
                    getattr(model, date_field) >= start_date,
                    getattr(model, date_field) <= end_date
                ).scalar()
                
                if remaining_items > 0:
                    current_app.logger.warning(f"Found {remaining_items} items still remaining, trying batch delete")
                    # Try batch delete
                    batch_size = 1000
                    deleted = 0
                    
                    while deleted < remaining_items:
                        # Get batch of items
                        items = db.session.query(Item).filter(
                            getattr(model, date_field) >= start_date,
                            getattr(model, date_field) <= end_date
                        ).limit(batch_size).offset(deleted).all()
                        
                        if not items:
                            break
                            
                        # Delete each item
                        for item in items:
                            try:
                                db.session.delete(item)
                            except Exception as e:
                                current_app.logger.error(f"Error deleting item {item.id}: {str(e)}")
                                continue
                        
                        # Commit batch
                        db.session.commit()
                        deleted += len(items)
                        current_app.logger.info(f"Deleted {deleted} items so far")
                    
                    result += deleted
                
                # Final verification
                final_count = db.session.query(func.count(Item.id)).filter(
                    getattr(model, date_field) >= start_date,
                    getattr(model, date_field) <= end_date
                ).scalar()
                
                message = f"Successfully deleted {result} inventory items"
                if final_count > 0:
                    message += f" ({final_count} items still remaining)"
                
                current_app.logger.info(f"Final state - Remaining items in range: {final_count}")
                
                return jsonify({
                    'message': message,
                    'deleted_count': result,
                    'remaining_count': final_count,
                    'data_type': data_type,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                })
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error during inventory deletion: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        # For other data types, use bulk delete
        try:
            # Start transaction
            db.session.begin_nested()
            
            # Get the date column dynamically
            date_column = getattr(model, date_field)
            
            # Perform bulk delete
            result = db.session.query(model).filter(
                date_column >= start_date,
                date_column <= end_date
            ).delete(synchronize_session=False)
            
            # Commit the transaction
            db.session.commit()
            
            current_app.logger.info(f"Successfully deleted {result} records of type {data_type}")
            
            return jsonify({
                'message': f'Successfully deleted {result} records',
                'deleted_count': result,
                'data_type': data_type,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            })
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error during bulk delete: {str(e)}")
            
            # Fallback to batch processing if bulk delete fails
            try:
                # Get total count first
                date_column = getattr(model, date_field)
                total_records = db.session.query(func.count(model.id)).filter(
                    date_column >= start_date,
                    date_column <= end_date
                ).scalar()
                
                if total_records == 0:
                    return jsonify({
                        'message': 'No records found in the specified date range',
                        'deleted_count': 0,
                        'data_type': data_type,
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat()
                    })
                
                # Use larger batch size for better performance
                batch_size = 5000
                deleted = 0
                
                while deleted < total_records:
                    # Get and delete batch in a single query
                    batch = db.session.query(model.id).filter(
                        date_column >= start_date,
                        date_column <= end_date
                    ).limit(batch_size).offset(deleted).all()
                    
                    if not batch:
                        break
                    
                    batch_ids = [id[0] for id in batch]
                    db.session.query(model).filter(model.id.in_(batch_ids)).delete(synchronize_session=False)
                    db.session.commit()
                    
                    deleted += len(batch_ids)
                
                return jsonify({
                    'message': f'Successfully deleted {deleted} records',
                    'deleted_count': deleted,
                    'data_type': data_type,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                })
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error during batch delete: {str(e)}")
                return jsonify({'error': str(e)}), 500
                
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in delete_data: {str(e)}")
        return jsonify({'error': str(e)}), 500 