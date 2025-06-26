import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.cluster import KMeans
import joblib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import json

class AIService:
    def __init__(self):
        self.sales_model = None
        self.inventory_model = None
        self.anomaly_detector = None
        self.customer_segmentation_model = None
        self.scaler = StandardScaler()
        self.logger = logging.getLogger(__name__)
        
        # Create models directory if it doesn't exist
        self.models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
        os.makedirs(self.models_dir, exist_ok=True)
    
    def prepare_sales_data(self, sales_data: List[Dict]) -> pd.DataFrame:
        """Prepare sales data for ML models"""
        if not sales_data:
            return pd.DataFrame()
            
        df = pd.DataFrame(sales_data)
        df['line_item_date'] = pd.to_datetime(df['line_item_date'])
        df['day_of_week'] = df['line_item_date'].dt.dayofweek
        df['month'] = df['line_item_date'].dt.month
        df['quarter'] = df['line_item_date'].dt.quarter
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        df['day_of_month'] = df['line_item_date'].dt.day
        df['is_month_start'] = df['day_of_month'].isin([1, 2, 3]).astype(int)
        df['is_month_end'] = df['day_of_month'].isin([28, 29, 30, 31]).astype(int)
        return df
    
    def train_sales_forecast_model(self, sales_data: List[Dict]) -> Dict:
        """Train sales forecasting model with all available data"""
        try:
            df = self.prepare_sales_data(sales_data)
            if df.empty:
                return {'status': 'error', 'message': 'No sales data available'}
            # Aggregate daily sales (use all available data)
            daily_sales = df.groupby('line_item_date').agg({
                'total_revenue': 'sum',
                'quantity': 'sum'
            }).reset_index()
            # No limit on number of days
            self.logger.info(f"Training on {len(daily_sales)} days of sales data (full history)")
            # Create features
            daily_sales['day_of_week'] = daily_sales['line_item_date'].dt.dayofweek
            daily_sales['month'] = daily_sales['line_item_date'].dt.month
            daily_sales['is_weekend'] = daily_sales['day_of_week'].isin([5, 6]).astype(int)
            daily_sales['day_of_month'] = daily_sales['line_item_date'].dt.day
            daily_sales['is_month_start'] = daily_sales['day_of_month'].isin([1, 2, 3]).astype(int)
            daily_sales['is_month_end'] = daily_sales['day_of_month'].isin([28, 29, 30, 31]).astype(int)
            daily_sales['recent_7day_avg'] = daily_sales['total_revenue'].rolling(window=7, min_periods=1).mean().shift(1).fillna(0)
            feature_columns = ['day_of_week', 'month', 'is_weekend', 'day_of_month', 'is_month_start', 'is_month_end', 'recent_7day_avg']
            X = daily_sales[feature_columns]
            y = daily_sales['total_revenue']
            self.sales_model = RandomForestRegressor(n_estimators=100, random_state=42)
            self.sales_model.fit(X, y)
            model_path = os.path.join(self.models_dir, 'sales_forecast_model.pkl')
            joblib.dump(self.sales_model, model_path)
            model_score = self.sales_model.score(X, y)
            self.logger.info(f"Sales forecast model trained successfully with score: {model_score}")
            return {
                'status': 'success',
                'message': 'Sales forecast model trained successfully',
                'model_score': round(model_score, 4),
                'feature_importance': dict(zip(feature_columns, self.sales_model.feature_importances_))
            }
        except Exception as e:
            self.logger.error(f"Error training sales model: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def predict_sales_prophet(self, sales_data: List[Dict], days_ahead: int = 7) -> list:
        """Predict sales for next N days using Facebook Prophet time series forecasting."""
        try:
            from prophet import Prophet
            import pandas as pd
            df = self.prepare_sales_data(sales_data)
            if df.empty:
                return []
            # Aggregate daily sales
            daily_sales = df.groupby('line_item_date').agg({'total_revenue': 'sum'}).reset_index()
            daily_sales = daily_sales.rename(columns={'line_item_date': 'ds', 'total_revenue': 'y'})
            # Prophet expects ds as datetime
            daily_sales['ds'] = pd.to_datetime(daily_sales['ds'])
            model = Prophet()
            model.fit(daily_sales)
            future = model.make_future_dataframe(periods=days_ahead)
            forecast = model.predict(future)
            # Only return the forecast for the future days
            forecast = forecast.tail(days_ahead)
            results = []
            for _, row in forecast.iterrows():
                results.append({
                    'date': row['ds'].strftime('%Y-%m-%d'),
                    'predicted_revenue': round(row['yhat'], 2),
                    'lower': round(row['yhat_lower'], 2),
                    'upper': round(row['yhat_upper'], 2),
                    'model': 'Prophet'
                })
            return results
        except ImportError:
            self.logger.warning('Prophet not installed, falling back to RandomForestRegressor.')
            return None
        except Exception as e:
            self.logger.error(f"Error in Prophet prediction: {str(e)}")
            return []

    def predict_sales(self, days_ahead: int = 7) -> list:
        """Predict sales for next N days using Prophet if available, else RandomForest."""
        try:
            # Try Prophet first
            sales_data = None
            try:
                # Use the same data as training
                if hasattr(self, 'last_training_df') and self.last_training_df is not None:
                    sales_data = self.last_training_df.to_dict('records')
            except Exception:
                pass
            if not sales_data:
                # Fallback: get sales data from the unified function
                from src.routes.ai import get_sales_data_for_ai
                sales_data = get_sales_data_for_ai()
            prophet_result = self.predict_sales_prophet(sales_data, days_ahead)
            if prophet_result is not None:
                return prophet_result
            # Fallback to RandomForestRegressor
            model_path = os.path.join(self.models_dir, 'sales_forecast_model.pkl')
            if not os.path.exists(model_path):
                return []
            if self.sales_model is None:
                self.sales_model = joblib.load(model_path)
            # Get recent 7-day average from historical data
            recent_7day_avg = 0
            try:
                if hasattr(self, 'last_training_df') and self.last_training_df is not None:
                    last_df = self.last_training_df
                else:
                    last_df = None
                if last_df is not None and not last_df.empty:
                    recent_7day_avg = last_df['total_revenue'].rolling(window=7, min_periods=1).mean().iloc[-1]
            except Exception:
                pass
            predictions = []
            current_date = datetime.now()
            feature_columns = ['day_of_week', 'month', 'is_weekend', 'day_of_month', 'is_month_start', 'is_month_end', 'recent_7day_avg']
            for i in range(days_ahead):
                future_date = current_date + timedelta(days=i)
                features = pd.DataFrame([
                    [
                        future_date.weekday(),
                        future_date.month,
                        1 if future_date.weekday() in [5, 6] else 0,
                        future_date.day,
                        1 if future_date.day in [1, 2, 3] else 0,
                        1 if future_date.day in [28, 29, 30, 31] else 0,
                        recent_7day_avg
                    ]
                ], columns=feature_columns)
                predicted_revenue = self.sales_model.predict(features)[0]
                predictions.append({
                    'date': future_date.strftime('%Y-%m-%d'),
                    'predicted_revenue': round(predicted_revenue, 2),
                    'day_of_week': future_date.strftime('%A'),
                    'is_weekend': future_date.weekday() in [5, 6],
                    'confidence': 0.85,
                    'model': 'RandomForest'
                })
            return predictions
        except Exception as e:
            self.logger.error(f"Error predicting sales: {str(e)}")
            return []
    
    def detect_anomalies(self, sales_data: List[Dict]) -> List[Dict]:
        """Detect anomalies in sales data"""
        try:
            df = self.prepare_sales_data(sales_data)
            if df.empty:
                return []
            # Aggregate daily sales
            daily_sales = df.groupby('line_item_date').agg({
                'total_revenue': 'sum',
                'quantity': 'sum'
            }).reset_index()
            # Prepare features for anomaly detection
            features = daily_sales[['total_revenue', 'quantity']].values
            # Train anomaly detector
            self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
            anomaly_scores = self.anomaly_detector.fit_predict(features)
            # Calculate average daily revenue for context
            avg_daily_revenue = daily_sales['total_revenue'].mean() if not daily_sales.empty else 0
            # Find anomalies
            anomalies = []
            for i, score in enumerate(anomaly_scores):
                if score == -1:  # Anomaly detected
                    revenue = float(daily_sales.iloc[i]['total_revenue'])
                    if revenue > avg_daily_revenue * 1.5:
                        anomaly_type = 'High'
                        explanation = 'Unusually high sales—check for events, promotions, or data entry errors.'
                    elif revenue < avg_daily_revenue * 0.5:
                        anomaly_type = 'Low'
                        explanation = 'Unusually low sales—check for supply issues, low demand, or missed business.'
                    else:
                        anomaly_type = 'Other'
                        explanation = 'Unusual sales pattern detected.'
                    anomalies.append({
                        'date': daily_sales.iloc[i]['line_item_date'].strftime('%Y-%m-%d'),
                        'revenue': revenue,
                        'quantity': int(daily_sales.iloc[i]['quantity']),
                        'anomaly_score': float(score),
                        'type': 'unusual_sales_pattern',
                        'anomaly_type': anomaly_type,
                        'explanation': explanation
                    })
            return anomalies
        except Exception as e:
            self.logger.error(f"Error detecting anomalies: {str(e)}")
            return []
    
    def optimize_inventory(self, sales_data: List[Dict], inventory_data: List[Dict]) -> List[Dict]:
        """Generate inventory optimization recommendations"""
        try:
            df = self.prepare_sales_data(sales_data)
            
            if df.empty:
                return []
            
            # Calculate demand patterns
            item_demand = df.groupby('item_id').agg({
                'quantity': ['sum', 'mean', 'std'],
                'total_revenue': 'sum'
            }).reset_index()
            
            item_demand.columns = ['item_id', 'total_quantity', 'avg_daily_quantity', 'quantity_std', 'total_revenue']
            
            recommendations = []
            
            for _, item in item_demand.iterrows():
                # Calculate safety stock (2 standard deviations)
                safety_stock = max(0, item['quantity_std'] * 2)
                
                # Calculate reorder point
                reorder_point = item['avg_daily_quantity'] * 7 + safety_stock  # 7 days lead time
                
                # Find current inventory level
                current_inventory = next((inv['quantity'] for inv in inventory_data if inv['id'] == item['item_id']), 0)
                
                # Generate recommendation
                if current_inventory <= reorder_point:
                    recommendations.append({
                        'item_id': item['item_id'],
                        'current_stock': current_inventory,
                        'recommended_order': max(0, reorder_point - current_inventory),
                        'reorder_point': round(reorder_point, 2),
                        'safety_stock': round(safety_stock, 2),
                        'urgency': 'high' if current_inventory == 0 else 'medium',
                        'reason': 'Low stock - reorder needed'
                    })
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error optimizing inventory: {str(e)}")
            return []
    
    def segment_customers(self, sales_data: List[Dict]) -> Dict:
        """Segment customers based on purchasing behavior"""
        try:
            df = self.prepare_sales_data(sales_data)
            
            if df.empty:
                return {}
            
            # Aggregate customer behavior (using order_employee_id as customer proxy)
            customer_behavior = df.groupby('order_employee_id').agg({
                'total_revenue': ['sum', 'mean', 'count'],
                'quantity': 'sum'
            }).reset_index()
            
            customer_behavior.columns = ['customer_id', 'total_spent', 'avg_order_value', 'order_count', 'total_items']
            
            # Prepare features for clustering
            features = customer_behavior[['total_spent', 'avg_order_value', 'order_count']].values
            
            # Normalize features
            features_scaled = self.scaler.fit_transform(features)
            
            # Perform clustering
            kmeans = KMeans(n_clusters=4, random_state=42)
            clusters = kmeans.fit_predict(features_scaled)
            
            # Add cluster labels
            customer_behavior['segment'] = clusters
            
            # Define segment names
            segment_names = {
                0: 'Budget Customers',
                1: 'Regular Customers', 
                2: 'Premium Customers',
                3: 'VIP Customers'
            }
            
            # Analyze segments
            segment_analysis = {}
            for cluster_id in range(4):
                segment_data = customer_behavior[customer_behavior['segment'] == cluster_id]
                segment_analysis[segment_names[cluster_id]] = {
                    'count': len(segment_data),
                    'avg_total_spent': float(segment_data['total_spent'].mean()),
                    'avg_order_value': float(segment_data['avg_order_value'].mean()),
                    'avg_order_count': float(segment_data['order_count'].mean()),
                    'total_revenue': float(segment_data['total_spent'].sum())
                }
            
            return segment_analysis
            
        except Exception as e:
            self.logger.error(f"Error segmenting customers: {str(e)}")
            return {}
    
    def _make_json_serializable(self, obj):
        """Recursively convert numpy/pandas types in obj to native Python types."""
        if isinstance(obj, dict):
            return {self._make_json_serializable(k): self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(v) for v in obj]
        elif isinstance(obj, (np.integer, np.int32, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float32, np.float64)):
            return float(obj)
        elif hasattr(obj, 'item') and callable(obj.item):
            return obj.item()
        else:
            return obj

    def generate_insights(self, sales_data: List[Dict]) -> List[Dict]:
        """Generate advanced, actionable insights from sales data for restaurant owners."""
        import pandas as pd
        from datetime import datetime, timedelta
        try:
            if not sales_data:
                return []
            df = pd.DataFrame(sales_data)
            if df.empty:
                return []
            insights = []
            # --- 1. Top Performing Items (real item names) ---
            if 'item_id' in df.columns and 'item_name' in df.columns and 'total_revenue' in df.columns:
                item_sales = df.groupby(['item_id', 'item_name'])['total_revenue'].sum().sort_values(ascending=False)
                top_items = item_sales.head(5)
                insights.append({
                    'type': 'top_performers',
                    'title': 'Top Performing Items',
                    'description': f"Top {len(top_items)} items generated ${top_items.sum():,.2f} in revenue in the last 90 days.",
                    'data': {name: float(rev) for (_, name), rev in top_items.items()},
                    'priority': 'high',
                    'owner_explanation': (
                        f"These are your bestsellers for the last 90 days. "
                        "Consider promoting them or ensuring they're always in stock. "
                        "If you see fewer than 5 items, it means only those items were sold in this period."
                    )
                })
            # --- 2. Hero Day for Each Top Item ---
            if 'item_id' in df.columns and 'item_name' in df.columns and 'day_of_week' in df.columns and 'total_revenue' in df.columns:
                df['day_of_week'] = pd.to_datetime(df['line_item_date']).dt.dayofweek
                dow_map = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                for (item_id, item_name), group in df.groupby(['item_id', 'item_name']):
                    day_sales = group.groupby('day_of_week')['total_revenue'].sum()
                    if not day_sales.empty:
                        best_day = day_sales.idxmax()
                        if day_sales[best_day] > day_sales.mean() * 1.5:
                            insights.append({
                                'type': 'hero_day',
                                'title': f"Hero Day for {item_name}",
                                'description': f"{item_name} sells best on {dow_map[best_day]} (over {day_sales[best_day]:.2f} in sales, {day_sales[best_day]/(day_sales.mean()+1e-6):.1f}x average)",
                                'priority': 'high',
                                'data': {'item_name': item_name, 'best_day': dow_map[best_day], 'sales': float(day_sales[best_day])},
                                'owner_explanation': (
                                    f"{item_name} performs exceptionally well on {dow_map[best_day]}. "
                                    "Consider special offers or promotions on this day to maximize sales."
                                )
                            })
            # --- 3. Trend Detection (Rising/Falling Items) ---
            if 'item_id' in df.columns and 'item_name' in df.columns and 'line_item_date' in df.columns and 'total_revenue' in df.columns:
                df['line_item_date'] = pd.to_datetime(df['line_item_date'])
                last_week = df[df['line_item_date'] >= (df['line_item_date'].max() - pd.Timedelta(days=7))]
                prev_week = df[(df['line_item_date'] < (df['line_item_date'].max() - pd.Timedelta(days=7))) & (df['line_item_date'] >= (df['line_item_date'].max() - pd.Timedelta(days=14)))]
                rising = []
                falling = []
                for (item_id, item_name) in df.groupby(['item_id', 'item_name']).groups.keys():
                    last = last_week[(last_week['item_id'] == item_id)]['total_revenue'].sum()
                    prev = prev_week[(prev_week['item_id'] == item_id)]['total_revenue'].sum()
                    if prev > 0 and last > prev * 1.2:
                        rising.append((item_name, last, prev))
                    elif prev > 0 and last < prev * 0.8:
                        falling.append((item_name, last, prev))
                if rising:
                    insights.append({
                        'type': 'rising_items',
                        'title': 'Rising Star Items',
                        'description': 'Items with rapidly increasing sales this week',
                        'data': [{ 'item': name, 'last_week': float(last), 'prev_week': float(prev) } for name, last, prev in rising],
                        'priority': 'medium',
                        'owner_explanation': (
                            "These items saw a significant sales increase this week compared to last week. "
                            "Consider featuring them in your menu or promotions."
                        )
                    })
                else:
                    insights.append({
                        'type': 'rising_items',
                        'title': 'Rising Star Items',
                        'description': 'No items had a significant sales increase this week compared to last week.',
                        'data': [],
                        'priority': 'medium',
                        'owner_explanation': (
                            "No items had a significant sales increase this week. "
                            "Keep an eye on your menu for emerging trends."
                        )
                    })
                if falling:
                    insights.append({
                        'type': 'falling_items',
                        'title': 'At Risk Items',
                        'description': 'Items with declining sales this week',
                        'data': [{ 'item': name, 'last_week': float(last), 'prev_week': float(prev) } for name, last, prev in falling],
                        'priority': 'medium',
                        'owner_explanation': (
                            "These items saw a significant sales drop this week compared to last week. "
                            "Investigate possible reasons (supply, quality, demand) and consider action."
                        )
                    })
                else:
                    insights.append({
                        'type': 'falling_items',
                        'title': 'At Risk Items',
                        'description': 'No items had a significant sales drop this week.',
                        'data': [],
                        'priority': 'medium',
                        'owner_explanation': (
                            "No items had a significant sales drop this week. "
                            "Monitor your menu for any underperforming items."
                        )
                    })
            # --- 4. Festival/Holiday Calendar Alerts ---
            # Simple static list for demo; in production, use a real calendar API
            festivals = [
                {'name': 'Diwali', 'date': '2025-10-20'},
                {'name': 'Holi', 'date': '2025-03-14'},
                {'name': 'Independence Day (US)', 'date': '2025-07-04'},
                {'name': 'Thanksgiving', 'date': '2025-11-27'},
                {'name': 'Christmas', 'date': '2025-12-25'}
            ]
            today = datetime.now().date()
            for fest in festivals:
                fest_date = pd.to_datetime(fest['date']).date()
                days_until = (fest_date - today).days
                if 0 <= days_until <= 14:
                    insights.append({
                        'type': 'festival_alert',
                        'title': f"Upcoming Festival: {fest['name']}",
                        'description': f"{fest['name']} is in {days_until} days. Plan a themed menu or promotion!",
                        'priority': 'high',
                        'data': {'festival': fest['name'], 'date': fest['date'], 'days_until': days_until},
                        'owner_explanation': (
                            f"{fest['name']} is coming up soon. Special menus or promotions can boost sales during festivals."
                        )
                    })
            # --- 5. Social Media Plan ---
            # Suggest a post for each of the next 7 days, featuring the top item or a festival
            social_plan = []
            if not item_sales.empty:
                top_item_name = item_sales.index[0][1]
                for i in range(7):
                    plan_date = today + timedelta(days=i)
                    # Check for festival
                    fest_today = [fest for fest in festivals if pd.to_datetime(fest['date']).date() == plan_date]
                    if fest_today:
                        social_plan.append({
                            'date': plan_date.strftime('%Y-%m-%d'),
                            'suggestion': f"Post about {fest_today[0]['name']} specials!"
                        })
                    else:
                        social_plan.append({
                            'date': plan_date.strftime('%Y-%m-%d'),
                            'suggestion': f"Feature your top item: {top_item_name} in today's post."
                        })
                insights.append({
                    'type': 'social_media_plan',
                    'title': 'Social Media Plan',
                    'description': 'Suggested posts for the next 7 days based on trends and festivals.',
                    'data': social_plan,
                    'priority': 'high',
                    'owner_explanation': (
                        "Use these suggestions to engage your customers on social media. "
                        "Highlight top items and upcoming festivals to attract more attention."
                    )
                })
            # --- 6. Existing Insights (Revenue Trends, Anomalies, etc.) ---
            # (Keep as fallback for backward compatibility)
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
                        'description': f"Average daily revenue: ${avg_daily_revenue:.2f} (last {len(daily_revenue)} days)",
                        'data': {
                            'average_daily': float(avg_daily_revenue),
                            'max_daily': float(max_daily_revenue),
                            'min_daily': float(min_daily_revenue),
                            'total_days': len(daily_revenue)
                        },
                        'priority': 'high',
                        'owner_explanation': (
                            f"This shows your actual daily revenue for the last {len(daily_revenue)} days. "
                            "For future sales, see the Sales Forecast section."
                        )
                    })
            # Anomaly detection
            anomalies = self.detect_anomalies(sales_data)
            if anomalies:
                insights.append({
                    'type': 'anomalies',
                    'title': 'Sales Anomalies Detected',
                    'description': f"Found {len(anomalies)} unusual sales patterns that may need attention",
                    'data': anomalies,
                    'priority': 'high',
                    'owner_explanation': (
                        "These are days with sales much higher or lower than usual. "
                        "Review these days for possible causes (events, errors, etc.)."
                    )
                })
            return self._make_json_serializable(insights)
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