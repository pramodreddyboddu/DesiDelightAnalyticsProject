import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx';
import { Button } from '@/components/ui/button.jsx';
import { LoadingSpinner } from '@/components/ui/loading-spinner.jsx';
import { useToast } from '@/components/ui/toast.jsx';
import { useApiData, useApiMutation } from '@/hooks/use-api.js';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { TrendingUp, Brain, Lightbulb, Target, RefreshCw, AlertTriangle, Package, Users, Zap } from 'lucide-react';
import { Badge } from '@/components/ui/badge.jsx';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

export const AIDashboard = () => {
  const [predictions, setPredictions] = useState(null);
  const [insights, setInsights] = useState([]);
  const [modelStatus, setModelStatus] = useState(null);
  const [inventoryRecommendations, setInventoryRecommendations] = useState([]);
  const [customerSegments, setCustomerSegments] = useState({});
  const [anomalies, setAnomalies] = useState([]);
  const { success, error: showError } = useToast();
  const [dataWindow, setDataWindow] = useState(90); // default 90 days
  const windowOptions = [30, 60, 90, 180, 365, 'all'];

  // Fetch base data for AI endpoints
  const { data: salesData } = useApiData('/api/dashboard/sales-summary', []);
  const { data: inventoryBaseData } = useApiData('/api/inventory', []);

  // Custom fetch for POST endpoints
  const [anomaliesLoading, setAnomaliesLoading] = useState(false);
  const [anomaliesError, setAnomaliesError] = useState(null);
  const [inventoryLoading, setInventoryLoading] = useState(false);
  const [inventoryError, setInventoryError] = useState(null);

  // Fetch AI data
  const { data: predictionsData, loading: predictionsLoading, refresh: refreshPredictions } = useApiData(`/api/ai/predictions/sales?window=${dataWindow}`, [dataWindow]);
  const { data: insightsData, loading: insightsLoading, refresh: refreshInsights } = useApiData(`/api/ai/insights/automated?window=${dataWindow}`, [dataWindow]);
  const { data: statusData, loading: statusLoading, refresh: refreshStatus } = useApiData('/api/ai/models/status');
  const [segmentsLoading, setSegmentsLoading] = useState(false);
  const [segmentsError, setSegmentsError] = useState(null);

  // Train models mutation
  const { mutate: trainModels, loading: trainingLoading } = useApiMutation('/api/ai/models/train', {
    onSuccess: () => {
      success('Models Trained', 'AI models have been successfully trained with latest data');
      refreshPredictions();
      refreshInsights();
      refreshStatus();
    },
    onError: (error) => {
      showError('Training Failed', error.message || 'Failed to train AI models');
    }
  });

  useEffect(() => {
    if (predictionsData?.data) {
      setPredictions(predictionsData.data);
    }
  }, [predictionsData]);

  useEffect(() => {
    if (insightsData?.data) {
      setInsights(insightsData.data);
    }
  }, [insightsData]);

  useEffect(() => {
    if (statusData?.data) {
      setModelStatus(statusData.data);
    }
  }, [statusData]);

  useEffect(() => {
    const fetchSegments = async () => {
      if (!salesData?.sales) return;
      setSegmentsLoading(true);
      setSegmentsError(null);
      try {
        const res = await fetch(`${API_BASE_URL}/api/ai/customers/segments`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ sales_data: salesData.sales })
        });
        if (!res.ok) throw new Error('Failed to fetch customer segments');
        const data = await res.json();
        setCustomerSegments(data.data || {});
      } catch (err) {
        setSegmentsError(err.message);
        setCustomerSegments({});
      } finally {
        setSegmentsLoading(false);
      }
    };
    if (salesData?.sales) fetchSegments();
  }, [salesData]);

  useEffect(() => {
    // Fetch anomalies via POST
    const fetchAnomalies = async () => {
      if (!salesData?.sales) return;
      setAnomaliesLoading(true);
      setAnomaliesError(null);
      try {
        const res = await fetch(`${API_BASE_URL}/api/ai/anomalies/detect`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ sales_data: salesData.sales })
        });
        if (!res.ok) throw new Error('Failed to fetch anomalies');
        const data = await res.json();
        setAnomalies(data.data || []);
      } catch (err) {
        setAnomaliesError(err.message);
        setAnomalies([]);
      } finally {
        setAnomaliesLoading(false);
      }
    };
    if (salesData?.sales) fetchAnomalies();
  }, [salesData]);

  useEffect(() => {
    // Fetch inventory optimization via POST
    const fetchInventoryOpt = async () => {
      if (!salesData?.sales || !inventoryBaseData?.items) return;
      setInventoryLoading(true);
      setInventoryError(null);
      try {
        const res = await fetch(`${API_BASE_URL}/api/ai/inventory/optimize`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ sales_data: salesData.sales, inventory_data: inventoryBaseData.items })
        });
        if (!res.ok) throw new Error('Failed to fetch inventory optimization');
        const data = await res.json();
        setInventoryRecommendations(data.data || []);
      } catch (err) {
        setInventoryError(err.message);
        setInventoryRecommendations([]);
      } finally {
        setInventoryLoading(false);
      }
    };
    if (salesData?.sales && inventoryBaseData?.items) fetchInventoryOpt();
  }, [salesData, inventoryBaseData]);

  const handleTrainModels = () => {
    trainModels();
  };

  const handleRefreshAll = () => {
    refreshPredictions();
    refreshInsights();
    refreshStatus();
  };

  const isLoading = predictionsLoading || insightsLoading || statusLoading || segmentsLoading;

  if (isLoading) {
    return <LoadingSpinner size="lg" text="Loading AI insights..." />;
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col md:flex-row md:justify-between md:items-center mb-4">
        <h2 className="text-2xl font-bold text-gray-900">AI-Powered Analytics</h2>
        <div className="flex flex-col md:flex-row md:items-center space-y-2 md:space-y-0 md:space-x-4">
          <div className="flex items-center space-x-2">
            <label htmlFor="window-select" className="text-sm font-medium text-gray-700">Data Window:</label>
            <select
              id="window-select"
              className="border rounded px-2 py-1 text-sm"
              value={dataWindow}
              onChange={e => setDataWindow(e.target.value === 'all' ? 'all' : parseInt(e.target.value))}
            >
              {windowOptions.map(opt => (
                <option key={opt} value={opt}>{opt === 'all' ? 'All Data' : `${opt} days`}</option>
              ))}
            </select>
          </div>
          <Button 
            onClick={handleRefreshAll}
            variant="outline"
            disabled={isLoading}
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Button 
            onClick={handleTrainModels} 
            disabled={trainingLoading}
            className="bg-purple-600 hover:bg-purple-700"
          >
            <Brain className="w-4 h-4 mr-2" />
            {trainingLoading ? 'Training...' : 'Train AI Models'}
          </Button>
        </div>
      </div>

      {/* Model Status */}
      {modelStatus && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Brain className="w-4 h-4 mr-2" />
              AI Model Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 border rounded-lg">
                <h4 className="font-semibold mb-2">Sales Forecast Model</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span>Status:</span>
                    <Badge variant={modelStatus.sales_model?.exists ? "default" : "destructive"}>
                      {modelStatus.sales_model?.exists ? 'Trained' : 'Not Trained'}
                    </Badge>
                  </div>
                  {modelStatus.sales_model?.exists && (
                    <>
                      <div className="flex justify-between">
                        <span>Size:</span>
                        <span>{(modelStatus.sales_model.size / 1024).toFixed(1)} KB</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Last Modified:</span>
                        <span>{new Date(modelStatus.sales_model.last_modified * 1000).toLocaleDateString()}</span>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Sales Predictions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <TrendingUp className="w-4 h-4 mr-2" />
            Sales Predictions (Next 7 Days)
          </CardTitle>
          <CardDescription>
            AI-powered sales forecasting based on historical data
          </CardDescription>
        </CardHeader>
        <CardContent>
          {predictions && predictions.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={predictions}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip formatter={(value) => [`$${value}`, 'Predicted Revenue']} />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="predicted_revenue" 
                  stroke="#8884d8" 
                  strokeWidth={2}
                  dot={{ fill: '#8884d8', strokeWidth: 2, r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Brain className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>No predictions available. Train the AI model first.</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Inventory Optimization */}
      {inventoryRecommendations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Package className="w-4 h-4 mr-2" />
              Inventory Optimization
            </CardTitle>
            <CardDescription>
              AI-powered recommendations for inventory management
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {inventoryRecommendations.slice(0, 5).map((rec, index) => (
                <div key={index} className="p-4 border rounded-lg">
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-semibold">Item #{rec.item_id}</h4>
                    <Badge variant={rec.urgency === 'high' ? "destructive" : "secondary"}>
                      {rec.urgency} priority
                    </Badge>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Current Stock:</span>
                      <p className="font-medium">{rec.current_stock}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Reorder Point:</span>
                      <p className="font-medium">{rec.reorder_point}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Recommended Order:</span>
                      <p className="font-medium">{rec.recommended_order}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Safety Stock:</span>
                      <p className="font-medium">{rec.safety_stock}</p>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600 mt-2">{rec.reason}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Customer Segmentation */}
      {Object.keys(customerSegments).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Users className="w-4 h-4 mr-2" />
              Customer Segmentation
            </CardTitle>
            <CardDescription>
              AI-powered customer behavior analysis and segmentation
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold mb-4">Customer Segments</h4>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={Object.entries(customerSegments).map(([segment, data]) => ({
                        name: segment,
                        value: data.count,
                        revenue: data.total_revenue
                      }))}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {Object.entries(customerSegments).map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value, name) => [value, name]} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="space-y-4">
                {Object.entries(customerSegments).map(([segment, data]) => (
                  <div key={segment} className="p-3 border rounded-lg">
                    <h5 className="font-medium mb-2">{segment}</h5>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span>Customers:</span>
                        <span>{data.count}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Avg Order Value:</span>
                        <span>${data.avg_order_value.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Total Revenue:</span>
                        <span>${data.total_revenue.toFixed(2)}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Anomaly Detection */}
      {anomalies.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <AlertTriangle className="w-4 h-4 mr-2 text-orange-500" />
              Sales Anomalies Detected
            </CardTitle>
            <CardDescription>
              Unusual sales patterns that may need attention
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {anomalies.slice(0, 5).map((anomaly, index) => (
                <div key={index} className="p-3 border border-orange-200 rounded-lg bg-orange-50">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-medium text-orange-800">{anomaly.date}</h4>
                      <p className="text-sm text-orange-600">{anomaly.type}</p>
                    </div>
                    <Badge variant="outline" className="text-orange-700">
                      Anomaly
                    </Badge>
                  </div>
                  <div className="mt-2 grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-orange-600">Revenue:</span>
                      <p className="font-medium">${anomaly.revenue.toFixed(2)}</p>
                    </div>
                    <div>
                      <span className="text-orange-600">Quantity:</span>
                      <p className="font-medium">{anomaly.quantity}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* AI Insights */}
      {insights.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {insights.map((insight, index) => (
            <Card key={index}>
              <CardHeader>
                <CardTitle className="flex items-center text-lg">
                  <Lightbulb className="w-4 h-4 mr-2 text-yellow-500" />
                  {insight.title}
                  {insight.priority === 'high' && (
                    <Badge variant="destructive" className="ml-2">High Priority</Badge>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-4">
                  {insight.description}
                </p>
                {insight.owner_explanation && (
                  <div className="p-2 mb-2 bg-yellow-50 border-l-4 border-yellow-400 rounded text-yellow-900 text-xs">
                    <span className="font-semibold">Owner Tip: </span>{insight.owner_explanation}
                  </div>
                )}
                
                {insight.type === 'top_performers' && (
                  <div className="space-y-2">
                    {Object.entries(insight.data).slice(0, 3).map(([itemId, revenue]) => (
                      <div key={itemId} className="flex justify-between text-sm">
                        <span>Item {itemId}</span>
                        <span className="font-semibold">${revenue.toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                )}
                
                {insight.type === 'weekend_analysis' && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Weekend Sales</span>
                      <span className="font-semibold">${insight.data.weekend_sales.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Weekday Sales</span>
                      <span className="font-semibold">${insight.data.weekday_sales.toFixed(2)}</span>
                    </div>
                    <div className="mt-2 p-2 bg-blue-50 rounded">
                      <span className="text-sm font-medium text-blue-800">
                        {insight.data.weekend_percentage.toFixed(1)}% of revenue from weekends
                      </span>
                    </div>
                  </div>
                )}

                {insight.type === 'monthly_trends' && (
                  <div className="space-y-2">
                    <div className="text-sm text-gray-600">
                      Monthly revenue breakdown
                    </div>
                    <div className="h-32">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={Object.entries(insight.data).map(([month, revenue]) => ({
                          month: month,
                          revenue: revenue
                        }))}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="month" />
                          <YAxis />
                          <Tooltip formatter={(value) => [`$${value}`, 'Revenue']} />
                          <Bar dataKey="revenue" fill="#8884d8" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

                {insight.type === 'revenue_trends' && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Average Daily</span>
                      <span className="font-semibold">${insight.data.average_daily.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Max Daily</span>
                      <span className="font-semibold">${insight.data.max_daily.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Min Daily</span>
                      <span className="font-semibold">${insight.data.min_daily.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Total Days</span>
                      <span className="font-semibold">{insight.data.total_days}</span>
                    </div>
                  </div>
                )}

                {insight.type === 'anomalies' && (
                  <div className="space-y-2">
                    <div className="text-sm text-red-600 font-medium">
                      {insight.data.length} anomalies detected
                    </div>
                    {insight.data.slice(0, 2).map((anomaly, idx) => (
                      <div key={idx} className="text-sm text-gray-600">
                        {anomaly.date}: ${anomaly.revenue.toFixed(2)}
                        <span className="ml-2 font-semibold">{anomaly.anomaly_type}</span>
                        <div className="text-xs text-yellow-800">{anomaly.explanation}</div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* AI Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Target className="w-4 h-4 mr-2" />
            AI Recommendations
          </CardTitle>
          <CardDescription>
            Actionable insights to improve your restaurant performance
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <h4 className="font-semibold text-green-800 mb-2">Inventory Optimization</h4>
              <p className="text-sm text-green-700">
                Based on sales patterns, consider increasing stock of top-performing items by 20% 
                to meet predicted demand.
              </p>
            </div>
            
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h4 className="font-semibold text-blue-800 mb-2">Staffing Recommendations</h4>
              <p className="text-sm text-blue-700">
                Weekend sales are typically higher than weekdays. Consider increasing weekend staff 
                to improve service quality and revenue.
              </p>
            </div>
            
            <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
              <h4 className="font-semibold text-purple-800 mb-2">Menu Optimization</h4>
              <p className="text-sm text-purple-700">
                Focus on your top-performing items and consider featuring them prominently 
                in your menu to maximize revenue.
              </p>
            </div>

            <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
              <h4 className="font-semibold text-orange-800 mb-2">Data-Driven Decisions</h4>
              <p className="text-sm text-orange-700">
                Use the AI predictions to plan your inventory, staffing, and marketing strategies 
                for optimal business performance.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}; 