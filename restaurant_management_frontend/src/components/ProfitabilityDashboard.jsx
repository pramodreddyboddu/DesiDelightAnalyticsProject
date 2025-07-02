import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx';
import { Button } from '@/components/ui/button.jsx';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx';
import { DatePickerWithRange } from '@/components/ui/date-picker.jsx';
import { LoadingSpinner } from '@/components/ui/loading-spinner.jsx';
import { useToast } from '@/components/ui/toast.jsx';
import { useApiData } from '@/hooks/use-api.js';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Download, TrendingUp, TrendingDown, DollarSign } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

// Set default dateRange: from = midnight (00:00:00) in America/Chicago, to = same day (today only)
const chicagoTz = 'America/Chicago';
const now = new Date();
const chicagoMidnight = new Date(now.toLocaleString('en-US', { timeZone: chicagoTz }));
chicagoMidnight.setHours(0, 0, 0, 0);

export const ProfitabilityDashboard = () => {
  const [dateRange, setDateRange] = useState({ from: chicagoMidnight, to: chicagoMidnight });
  const { success, error: showError } = useToast();

  // Use API hooks for data fetching with caching
  const { data: profitData, loading, error } = useApiData('dashboard/profitability', {
    start_date: dateRange.from?.toISOString(),
    end_date: dateRange.to?.toISOString()
  });

  // Show error toast if API call fails
  useEffect(() => {
    if (error) {
      showError('Failed to load profitability data', error);
    }
  }, [error, showError]);

  const handleExport = async (format) => {
    try {
      const params = new URLSearchParams();
      if (dateRange.from) params.append('start_date', dateRange.from.toISOString());
      if (dateRange.to) params.append('end_date', dateRange.to.toISOString());
      params.append('format', format);

      const response = await fetch(`${API_BASE_URL}/reports/profitability?${params}`, {
        credentials: 'include'
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `profitability_report.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        success('Export Successful', `Profitability report downloaded as ${format.toUpperCase()}`);
      } else {
        throw new Error('Export failed');
      }
    } catch (error) {
      showError('Export Failed', 'Failed to download the report. Please try again.');
    }
  };

  if (loading) {
    return <LoadingSpinner size="lg" text="Loading profitability data..." />;
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Profitability Analysis</h2>
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

      {/* Date Range Filter */}
      <Card>
        <CardHeader>
          <CardTitle>Date Range</CardTitle>
        </CardHeader>
        <CardContent>
          <DatePickerWithRange date={dateRange} setDate={setDateRange} />
        </CardContent>
      </Card>

      {/* Overall Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Sales</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${profitData?.total_sales?.toFixed(2) || '0.00'}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Expenses</CardTitle>
            <TrendingDown className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${profitData?.total_expenses?.toFixed(2) || '0.00'}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Net Profit</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${((profitData?.total_sales || 0) - (profitData?.total_expenses || 0)) >= 0 ? 'text-green-600' : 'text-red-600'}`}>${((profitData?.total_sales || 0) - (profitData?.total_expenses || 0)).toFixed(2)}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Profit Margin</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${((profitData?.total_sales || 0) - (profitData?.total_expenses || 0)) >= 0 ? 'text-green-600' : 'text-red-600'}`}>{profitData?.total_sales > 0 ? (((profitData?.total_sales - profitData?.total_expenses) / profitData?.total_sales) * 100).toFixed(1) : '0.0'}%</div>
          </CardContent>
        </Card>
      </div>

      {/* Category Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Profit by Category Bar Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Profit by Category</CardTitle>
            <CardDescription>Net profit comparison across business categories</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={profitData?.categories || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="category" />
                <YAxis />
                <Tooltip formatter={(value) => [`$${value?.toFixed(2)}`, 'Amount']} />
                <Legend />
                <Bar dataKey="sales" fill="#8884d8" name="Sales" />
                <Bar dataKey="expenses" fill="#82ca9d" name="Expenses" />
                <Bar dataKey="profit" fill="#ffc658" name="Profit" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Profit Margin Pie Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Profit Margin by Category</CardTitle>
            <CardDescription>Profitability percentage across categories</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={profitData?.categories?.filter(cat => cat.profit_margin > 0) || []}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ category, profit_margin }) => `${category}: ${profit_margin?.toFixed(1)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="profit_margin"
                >
                  {(profitData?.categories?.filter(cat => cat.profit_margin > 0) || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => [`${value?.toFixed(1)}%`, 'Profit Margin']} />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Module Analysis */}
      <Card>
        <CardHeader>
          <CardTitle>Module Analysis</CardTitle>
          <CardDescription>Profitability grouped by Grocery, Meat, Vegetables, and Kitchen</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3">Module</th>
                  <th className="text-right p-3">Sales Revenue</th>
                  <th className="text-right p-3">Expenses</th>
                  <th className="text-right p-3">Net Profit</th>
                  <th className="text-right p-3">Profit Margin</th>
                </tr>
              </thead>
              <tbody>
                {(profitData?.modules || []).map((mod, index) => (
                  <tr key={index} className="border-b hover:bg-gray-50">
                    <td className="p-3 font-medium">{mod.module}</td>
                    <td className="p-3 text-right">${mod.sales?.toFixed(2)}</td>
                    <td className="p-3 text-right">${mod.expenses?.toFixed(2)}</td>
                    <td className={`p-3 text-right font-medium ${mod.profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>${mod.profit?.toFixed(2)}</td>
                    <td className={`p-3 text-right font-medium ${mod.profit_margin >= 0 ? 'text-green-600' : 'text-red-600'}`}>{mod.profit_margin?.toFixed(1)}%</td>
                  </tr>
                ))}
                {/* Totals Row */}
                <tr className="border-t font-bold bg-gray-100">
                  <td className="p-3">Total</td>
                  <td className="p-3 text-right">${profitData?.total_sales?.toFixed(2) || '0.00'}</td>
                  <td className="p-3 text-right">${profitData?.total_expenses?.toFixed(2) || '0.00'}</td>
                  <td className={`p-3 text-right ${((profitData?.total_sales || 0) - (profitData?.total_expenses || 0)) >= 0 ? 'text-green-600' : 'text-red-600'}`}>${((profitData?.total_sales || 0) - (profitData?.total_expenses || 0)).toFixed(2)}</td>
                  <td className={`p-3 text-right ${((profitData?.total_sales || 0) - (profitData?.total_expenses || 0)) >= 0 ? 'text-green-600' : 'text-red-600'}`}>{profitData?.total_sales > 0 ? (((profitData?.total_sales - profitData?.total_expenses) / profitData?.total_sales) * 100).toFixed(1) : '0.0'}%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Detailed Category Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Detailed Category Analysis</CardTitle>
          <CardDescription>Comprehensive breakdown of sales, expenses, and profitability</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3">Category</th>
                  <th className="text-right p-3">Sales Revenue</th>
                  <th className="text-right p-3">Expenses</th>
                  <th className="text-right p-3">Net Profit</th>
                  <th className="text-right p-3">Profit Margin</th>
                </tr>
              </thead>
              <tbody>
                {(profitData?.categories || []).map((category, index) => (
                  <tr key={index} className="border-b hover:bg-gray-50">
                    <td className="p-3 font-medium">{category.category}</td>
                    <td className="p-3 text-right">${category.sales?.toFixed(2)}</td>
                    <td className="p-3 text-right">${category.expenses?.toFixed(2)}</td>
                    <td className={`p-3 text-right font-medium ${category.profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>${category.profit?.toFixed(2)}</td>
                    <td className={`p-3 text-right font-medium ${category.profit_margin >= 0 ? 'text-green-600' : 'text-red-600'}`}>{category.profit_margin?.toFixed(1)}%</td>
                  </tr>
                ))}
                {/* Totals Row */}
                <tr className="border-t font-bold bg-gray-100">
                  <td className="p-3">Total</td>
                  <td className="p-3 text-right">${profitData?.total_sales?.toFixed(2) || '0.00'}</td>
                  <td className="p-3 text-right">${profitData?.total_expenses?.toFixed(2) || '0.00'}</td>
                  <td className={`p-3 text-right ${((profitData?.total_sales || 0) - (profitData?.total_expenses || 0)) >= 0 ? 'text-green-600' : 'text-red-600'}`}>${((profitData?.total_sales || 0) - (profitData?.total_expenses || 0)).toFixed(2)}</td>
                  <td className={`p-3 text-right ${((profitData?.total_sales || 0) - (profitData?.total_expenses || 0)) >= 0 ? 'text-green-600' : 'text-red-600'}`}>{profitData?.total_sales > 0 ? (((profitData?.total_sales - profitData?.total_expenses) / profitData?.total_sales) * 100).toFixed(1) : '0.0'}%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Performance Insights */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Insights</CardTitle>
          <CardDescription>Key findings and recommendations</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {profitData?.categories && (
              <>
                {/* Most Profitable Category */}
                {(() => {
                  const mostProfitable = profitData.categories.reduce((max, cat) => 
                    cat.profit > (max?.profit || 0) ? cat : max, null);
                  return mostProfitable && (
                    <div className="p-4 bg-green-50 rounded-lg">
                      <h4 className="font-medium text-green-800">Most Profitable Category</h4>
                      <p className="text-green-700">
                        {mostProfitable.category} generates the highest profit of ${mostProfitable.profit?.toFixed(2)} 
                        with a {mostProfitable.profit_margin?.toFixed(1)}% margin.
                      </p>
                    </div>
                  );
                })()}

                {/* Least Profitable Category */}
                {(() => {
                  const leastProfitable = profitData.categories.reduce((min, cat) => 
                    cat.profit < (min?.profit || Infinity) ? cat : min, null);
                  return leastProfitable && leastProfitable.profit < 0 && (
                    <div className="p-4 bg-red-50 rounded-lg">
                      <h4 className="font-medium text-red-800">Attention Required</h4>
                      <p className="text-red-700">
                        {leastProfitable.category} is operating at a loss of ${Math.abs(leastProfitable.profit)?.toFixed(2)}. 
                        Consider reviewing pricing or cost structure.
                      </p>
                    </div>
                  );
                })()}

                {/* High Margin Categories */}
                {(() => {
                  const highMarginCategories = profitData.categories.filter(cat => cat.profit_margin > 20);
                  return highMarginCategories.length > 0 && (
                    <div className="p-4 bg-blue-50 rounded-lg">
                      <h4 className="font-medium text-blue-800">High Margin Opportunities</h4>
                      <p className="text-blue-700">
                        {highMarginCategories.map(cat => cat.category).join(', ')} show strong profit margins above 20%. 
                        Consider expanding these categories.
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

