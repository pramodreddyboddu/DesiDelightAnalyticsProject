import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx';
import { Button } from '@/components/ui/button.jsx';
import { LoadingSpinner } from '@/components/ui/loading-spinner.jsx';
import { useToast } from '@/components/ui/toast.jsx';
import { useApiData, useApiMutation } from '@/hooks/use-api.js';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { TrendingUp, Brain, Lightbulb, Target, RefreshCw } from 'lucide-react';

export const AIDashboard = () => {
  const [predictions, setPredictions] = useState(null);
  const [insights, setInsights] = useState([]);
  const [modelStatus, setModelStatus] = useState(null);
  const { success, error: showError } = useToast();

  // Fetch AI data
  const { data: predictionsData, loading: predictionsLoading, refresh: refreshPredictions } = useApiData('/ai/predictions/sales');
  const { data: insightsData, loading: insightsLoading, refresh: refreshInsights } = useApiData('/ai/insights/automated');
  const { data: statusData, loading: statusLoading, refresh: refreshStatus } = useApiData('/ai/models/status');
  
  // Train models mutation
  const { mutate: trainModels, loading: trainingLoading } = useApiMutation('/ai/models/train', {
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

  const handleTrainModels = () => {
    trainModels();
  };

  const handleRefreshAll = () => {
    refreshPredictions();
    refreshInsights();
    refreshStatus();
  };

  if (predictionsLoading || insightsLoading || statusLoading) {
    return <LoadingSpinner size="lg" text="Loading AI insights..." />;
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">AI-Powered Analytics</h2>
        <div className="flex space-x-2">
          <Button 
            onClick={handleRefreshAll}
            variant="outline"
            disabled={predictionsLoading || insightsLoading || statusLoading}
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
                    <span className={modelStatus.sales_model?.exists ? 'text-green-600' : 'text-red-600'}>
                      {modelStatus.sales_model?.exists ? 'Trained' : 'Not Trained'}
                    </span>
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

      {/* AI Insights */}
      {insights.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {insights.map((insight, index) => (
            <Card key={index}>
              <CardHeader>
                <CardTitle className="flex items-center text-lg">
                  <Lightbulb className="w-4 h-4 mr-2 text-yellow-500" />
                  {insight.title}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-4">
                  {insight.description}
                </p>
                
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