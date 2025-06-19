import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx';
import { Button } from '@/components/ui/button.jsx';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx';
import { DatePickerWithRange } from '@/components/ui/date-picker.jsx';
import { LoadingSpinner } from '@/components/ui/loading-spinner.jsx';
import { useToast } from '@/components/ui/toast.jsx';
import { useApiData } from '@/hooks/use-api.js';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Download, Users, Award, TrendingUp } from 'lucide-react';

const API_BASE_URL = 'http://localhost:5000/api';
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export const StaffPerformanceDashboard = () => {
  const [dateRange, setDateRange] = useState({ from: null, to: null });
  const [selectedChef, setSelectedChef] = useState('all');
  const { success, error: showError } = useToast();

  // Use API hooks for data fetching with caching
  const { data: performanceData, loading, error } = useApiData('/dashboard/chef-performance', [dateRange, selectedChef]);

  // Show error toast if API call fails
  useEffect(() => {
    if (error) {
      showError('Failed to load staff performance data', error);
    }
  }, [error, showError]);

  const handleExport = async (format) => {
    try {
      const params = new URLSearchParams();
      if (dateRange.from) params.append('start_date', dateRange.from.toISOString());
      if (dateRange.to) params.append('end_date', dateRange.to.toISOString());
      if (selectedChef !== 'all') params.append('chef_id', selectedChef);
      params.append('format', format);

      const response = await fetch(`http://localhost:5000/api/reports/chef-performance?${params}`, {
        credentials: 'include'
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `chef_performance_report.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        success('Export Successful', `Chef performance report downloaded as ${format.toUpperCase()}`);
      } else {
        throw new Error('Export failed');
      }
    } catch (error) {
      showError('Export Failed', 'Failed to download the report. Please try again.');
    }
  };

  if (loading) {
    return <LoadingSpinner size="lg" text="Loading staff performance data..." />;
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Staff Performance Analytics</h2>
        <div className="flex space-x-2">
          <Button variant="outline" onClick={() => handleExport('csv')}>
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </Button>
          <Button variant="outline" onClick={() => handleExport('excel')}>
            <Download className="w-4 h-4 mr-2" />
            Export Excel
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent className="flex space-x-4">
          <div className="flex-1">
            <label className="text-sm font-medium">Date Range</label>
            <DatePickerWithRange date={dateRange} setDate={setDateRange} />
          </div>
          <div className="flex-1">
            <label className="text-sm font-medium">Staff Member</label>
            <Select value={selectedChef} onValueChange={setSelectedChef}>
              <SelectTrigger>
                <SelectValue placeholder="Select staff member" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Staff Members</SelectItem>
                {(performanceData?.chef_summary || []).map((chef) => (
                  <SelectItem key={chef.id} value={chef.id.toString()}>
                    {chef.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Staff Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Staff Members</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{performanceData?.chef_summary?.length || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Revenue Generated</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${(performanceData?.chef_summary?.reduce((sum, chef) => sum + chef.total_revenue, 0) || 0).toFixed(2)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Sales Count</CardTitle>
            <Award className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {performanceData?.chef_summary?.reduce((sum, chef) => sum + chef.total_sales, 0) || 0}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Performance Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue by Staff Member */}
        <Card>
          <CardHeader>
            <CardTitle>Revenue by Staff Member</CardTitle>
            <CardDescription>Total revenue generated by each staff member</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={performanceData?.chef_summary || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip formatter={(value) => [`$${value?.toFixed(2)}`, 'Revenue']} />
                <Legend />
                <Bar dataKey="total_revenue" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Sales Count by Staff Member */}
        <Card>
          <CardHeader>
            <CardTitle>Sales Volume by Staff Member</CardTitle>
            <CardDescription>Number of items sold by each staff member</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={performanceData?.chef_summary || []}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, total_sales }) => `${name}: ${total_sales}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="total_sales"
                >
                  {(performanceData?.chef_summary || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Performance Table */}
      <Card>
        <CardHeader>
          <CardTitle>Staff Performance Leaderboard</CardTitle>
          <CardDescription>Detailed performance metrics for all staff members</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3">Rank</th>
                  <th className="text-left p-3">Staff Member</th>
                  <th className="text-right p-3">Total Revenue</th>
                  <th className="text-right p-3">Total Sales</th>
                  <th className="text-right p-3">Avg. Sale Value</th>
                  <th className="text-right p-3">Performance Score</th>
                </tr>
              </thead>
              <tbody>
                {(performanceData?.chef_summary || [])
                  .sort((a, b) => b.total_revenue - a.total_revenue)
                  .map((chef, index) => {
                    const avgSaleValue = chef.total_sales > 0 ? chef.total_revenue / chef.total_sales : 0;
                    const maxRevenue = Math.max(...(performanceData?.chef_summary || []).map(c => c.total_revenue));
                    const performanceScore = maxRevenue > 0 ? (chef.total_revenue / maxRevenue * 100) : 0;
                    
                    return (
                      <tr key={chef.id} className="border-b hover:bg-gray-50">
                        <td className="p-3">
                          <div className="flex items-center">
                            {index === 0 && <Award className="w-4 h-4 text-yellow-500 mr-1" />}
                            {index === 1 && <Award className="w-4 h-4 text-gray-400 mr-1" />}
                            {index === 2 && <Award className="w-4 h-4 text-orange-500 mr-1" />}
                            #{index + 1}
                          </div>
                        </td>
                        <td className="p-3 font-medium">{chef.name}</td>
                        <td className="p-3 text-right">${chef.total_revenue?.toFixed(2)}</td>
                        <td className="p-3 text-right">{chef.total_sales}</td>
                        <td className="p-3 text-right">${avgSaleValue.toFixed(2)}</td>
                        <td className="p-3 text-right">
                          <div className="flex items-center justify-end">
                            <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                              <div 
                                className="bg-blue-600 h-2 rounded-full" 
                                style={{ width: `${performanceScore}%` }}
                              ></div>
                            </div>
                            {performanceScore.toFixed(0)}%
                          </div>
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Individual Staff Performance Details */}
      {selectedChef !== 'all' && performanceData?.chef_performance && (
        <Card>
          <CardHeader>
            <CardTitle>Individual Performance Details</CardTitle>
            <CardDescription>Detailed breakdown of dishes and performance</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {performanceData.chef_performance
                .filter(chef => chef.chef_name === (performanceData.chef_summary.find(c => c.id.toString() === selectedChef)?.name))
                .map((chef, index) => (
                  <div key={index}>
                    <h4 className="font-medium text-lg mb-4">{chef.chef_name}</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {chef.dishes?.map((dish, dishIndex) => (
                        <div key={dishIndex} className="p-4 border rounded-lg">
                          <h5 className="font-medium">{dish.item_name}</h5>
                          <p className="text-sm text-gray-500">{dish.category}</p>
                          <div className="mt-2">
                            <p className="text-lg font-bold">${dish.revenue?.toFixed(2)}</p>
                            <p className="text-sm text-gray-600">{dish.count} sales</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Performance Insights */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Insights</CardTitle>
          <CardDescription>Key findings and recommendations</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {performanceData?.chef_summary && performanceData.chef_summary.length > 0 && (
              <>
                {/* Top Performer */}
                {(() => {
                  const topPerformer = performanceData.chef_summary.reduce((max, chef) => 
                    chef.total_revenue > (max?.total_revenue || 0) ? chef : max, null);
                  return topPerformer && (
                    <div className="p-4 bg-green-50 rounded-lg">
                      <h4 className="font-medium text-green-800">Top Performer</h4>
                      <p className="text-green-700">
                        {topPerformer.name} leads with ${topPerformer.total_revenue?.toFixed(2)} in revenue 
                        from {topPerformer.total_sales} sales.
                      </p>
                    </div>
                  );
                })()}

                {/* Most Active */}
                {(() => {
                  const mostActive = performanceData.chef_summary.reduce((max, chef) => 
                    chef.total_sales > (max?.total_sales || 0) ? chef : max, null);
                  return mostActive && (
                    <div className="p-4 bg-blue-50 rounded-lg">
                      <h4 className="font-medium text-blue-800">Most Active Staff Member</h4>
                      <p className="text-blue-700">
                        {mostActive.name} completed the most sales with {mostActive.total_sales} transactions.
                      </p>
                    </div>
                  );
                })()}

                {/* Development Opportunity */}
                {(() => {
                  const needsSupport = performanceData.chef_summary.reduce((min, chef) => 
                    chef.total_revenue < (min?.total_revenue || Infinity) ? chef : min, null);
                  return needsSupport && performanceData.chef_summary.length > 1 && (
                    <div className="p-4 bg-yellow-50 rounded-lg">
                      <h4 className="font-medium text-yellow-800">Development Opportunity</h4>
                      <p className="text-yellow-700">
                        {needsSupport.name} may benefit from additional training or support to improve performance.
                      </p>
                    </div>
                  );
                })()}
              </>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

