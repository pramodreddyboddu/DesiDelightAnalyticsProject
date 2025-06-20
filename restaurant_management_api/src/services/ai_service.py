import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

class AIService:
    def __init__(self):
        self.sales_model = None
        self.inventory_model = None
        self.scaler = StandardScaler()
        self.logger = logging.getLogger(__name__)
        
        # Create models directory if it doesn't exist
        self.models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
        os.makedirs(self.models_dir, exist_ok=True)
    
    def prepare_sales_data(self, sales_data: List[Dict]) -> pd.DataFrame:
        """Prepare sales data for ML models"""
        try:
            df = pd.DataFrame(sales_data)
            df['line_item_date'] = pd.to_datetime(df['line_item_date'])
            df['day_of_week'] = df['line_item_date'].dt.dayofweek
            df['month'] = df['line_item_date'].dt.month
            df['quarter'] = df['line_item_date'].dt.quarter
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
            return df
        except Exception as e:
            self.logger.error(f"Error preparing sales data: {str(e)}")
            return pd.DataFrame()
    
    def train_sales_forecast_model(self, sales_data: List[Dict]) -> Dict:
        """Train sales forecasting model"""
        try:
            if not sales_data:
                return {'status': 'error', 'message': 'No sales data provided'}
            
            df = self.prepare_sales_data(sales_data)
            
            if df.empty:
                return {'status': 'error', 'message': 'Failed to prepare sales data'}
            
            # Aggregate daily sales
            daily_sales = df.groupby('line_item_date').agg({
                'total_revenue': 'sum',
                'quantity': 'sum'
            }).reset_index()
            
            # Create features
            daily_sales['day_of_week'] = daily_sales['line_item_date'].dt.dayofweek
            daily_sales['month'] = daily_sales['line_item_date'].dt.month
            daily_sales['is_weekend'] = daily_sales['day_of_week'].isin([5, 6]).astype(int)
            
            # Prepare features and target
            X = daily_sales[['day_of_week', 'month', 'is_weekend']]
            y = daily_sales['total_revenue']
            
            # Train model
            self.sales_model = RandomForestRegressor(n_estimators=100, random_state=42)
            self.sales_model.fit(X, y)
            
            # Save model
            model_path = os.path.join(self.models_dir, 'sales_forecast_model.pkl')
            joblib.dump(self.sales_model, model_path)
            
            # Calculate model score
            model_score = self.sales_model.score(X, y)
            
            self.logger.info(f"Sales forecast model trained successfully with score: {model_score}")
            
            return {
                'status': 'success',
                'message': 'Sales forecast model trained successfully',
                'model_score': round(model_score, 4),
                'training_samples': len(X)
            }
            
        except Exception as e:
            self.logger.error(f"Error training sales model: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def predict_sales(self, days_ahead: int = 7) -> List[Dict]:
        """Predict sales for next N days"""
        try:
            model_path = os.path.join(self.models_dir, 'sales_forecast_model.pkl')
            
            if not os.path.exists(model_path):
                return []
            
            if self.sales_model is None:
                self.sales_model = joblib.load(model_path)
            
            predictions = []
            current_date = datetime.now()
            
            for i in range(days_ahead):
                future_date = current_date + timedelta(days=i)
                features = np.array([[
                    future_date.weekday(),
                    future_date.month,
                    1 if future_date.weekday() in [5, 6] else 0
                ]])
                
                predicted_revenue = self.sales_model.predict(features)[0]
                
                predictions.append({
                    'date': future_date.strftime('%Y-%m-%d'),
                    'predicted_revenue': round(predicted_revenue, 2),
                    'day_of_week': future_date.strftime('%A'),
                    'is_weekend': future_date.weekday() in [5, 6]
                })
            
            return predictions
            
        except Exception as e:
            self.logger.error(f"Error predicting sales: {str(e)}")
            return []
    
    def generate_insights(self, sales_data: List[Dict]) -> List[Dict]:
        """Generate automated insights from sales data"""
        try:
            if not sales_data:
                return []
            
            df = self.prepare_sales_data(sales_data)
            
            if df.empty:
                return []
            
            insights = []
            
            # Top performing items
            if 'item_id' in df.columns and 'total_revenue' in df.columns:
                top_items = df.groupby('item_id')['total_revenue'].sum().nlargest(5)
                if not top_items.empty:
                    insights.append({
                        'type': 'top_performers',
                        'title': 'Top Performing Items',
                        'description': f"Top 5 items generated ${top_items.sum():,.2f} in revenue",
                        'data': top_items.to_dict()
                    })
            
            # Weekend vs weekday analysis
            if 'is_weekend' in df.columns and 'total_revenue' in df.columns:
                weekend_sales = df[df['is_weekend'] == 1]['total_revenue'].sum()
                weekday_sales = df[df['is_weekend'] == 0]['total_revenue'].sum()
                total_sales = weekend_sales + weekday_sales
                
                if total_sales > 0:
                    weekend_percentage = (weekend_sales / total_sales) * 100
                    
                    insights.append({
                        'type': 'weekend_analysis',
                        'title': 'Weekend Performance',
                        'description': f"Weekend sales account for {weekend_percentage:.1f}% of total revenue",
                        'data': {
                            'weekend_sales': float(weekend_sales),
                            'weekday_sales': float(weekday_sales),
                            'weekend_percentage': round(weekend_percentage, 1)
                        }
                    })
            
            # Monthly trends
            if 'month' in df.columns and 'total_revenue' in df.columns:
                monthly_sales = df.groupby('month')['total_revenue'].sum()
                if not monthly_sales.empty:
                    best_month = monthly_sales.idxmax()
                    worst_month = monthly_sales.idxmin()
                    
                    month_names = {
                        1: 'January', 2: 'February', 3: 'March', 4: 'April',
                        5: 'May', 6: 'June', 7: 'July', 8: 'August',
                        9: 'September', 10: 'October', 11: 'November', 12: 'December'
                    }
                    
                    insights.append({
                        'type': 'monthly_trends',
                        'title': 'Monthly Performance',
                        'description': f"Best performing month: {month_names.get(best_month, best_month)}, Lowest: {month_names.get(worst_month, worst_month)}",
                        'data': {str(k): float(v) for k, v in monthly_sales.to_dict().items()}
                    })
            
            # Revenue trends
            if 'line_item_date' in df.columns and 'total_revenue' in df.columns:
                daily_revenue = df.groupby('line_item_date')['total_revenue'].sum()
                if len(daily_revenue) > 1:
                    avg_daily_revenue = daily_revenue.mean()
                    max_daily_revenue = daily_revenue.max()
                    min_daily_revenue = daily_revenue.min()
                    
                    insights.append({
                        'type': 'revenue_trends',
                        'title': 'Revenue Trends',
                        'description': f"Average daily revenue: ${avg_daily_revenue:.2f}",
                        'data': {
                            'average_daily': float(avg_daily_revenue),
                            'max_daily': float(max_daily_revenue),
                            'min_daily': float(min_daily_revenue),
                            'total_days': len(daily_revenue)
                        }
                    })
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating insights: {str(e)}")
            return []
    
    def get_model_status(self) -> Dict:
        """Get status of trained models"""
        try:
            sales_model_path = os.path.join(self.models_dir, 'sales_forecast_model.pkl')
            
            return {
                'sales_model': {
                    'exists': os.path.exists(sales_model_path),
                    'last_modified': os.path.getmtime(sales_model_path) if os.path.exists(sales_model_path) else None,
                    'size': os.path.getsize(sales_model_path) if os.path.exists(sales_model_path) else 0
                },
                'models_directory': self.models_dir
            }
        except Exception as e:
            self.logger.error(f"Error getting model status: {str(e)}")
            return {'error': str(e)} 