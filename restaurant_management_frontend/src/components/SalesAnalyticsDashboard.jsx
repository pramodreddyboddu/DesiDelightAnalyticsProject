import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx';
import { Button } from '@/components/ui/button.jsx';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx';
import { DatePickerWithRange } from '@/components/ui/date-picker.jsx';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';
import { Download, Filter, TrendingUp, DollarSign } from 'lucide-react';

const API_BASE_URL = 'http://localhost:5000/api';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export const SalesAnalyticsDashboard = () => {
  const [salesData, setSalesData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState({ from: null, to: null });
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    fetchSalesData();
    fetchCategories();
  }, [dateRange, selectedCategory]);

  const fetchSalesData = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (dateRange.from) params.append('start_date', dateRange.from.toISOString());
      if (dateRange.to) params.append('end_date', dateRange.to.toISOString());
      if (selectedCategory !== 'all') params.append('category', selectedCategory);

      const response = await fetch(`${API_BASE_URL}/dashboard/sales-summary?${params}`, {
        credentials: 'include'
      });
      const data = await response.json();
      setSalesData(data);
    } catch (error) {
      console.error('Error fetching sales data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/inventory`, {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        // Extract unique categories from inventory items
        const uniqueCategories = [...new Set(data.items.map(item => item.category))].filter(Boolean);
        setCategories(uniqueCategories);
      }
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const exportReport = async (format) => {
    try {
      const params = new URLSearchParams();
      if (dateRange.from) params.append('start_date', dateRange.from.toISOString());
      if (dateRange.to) params.append('end_date', dateRange.to.toISOString());
      if (selectedCategory !== 'all') params.append('category', selectedCategory);
      params.append('format', format);

      const response = await fetch(`${API_BASE_URL}/reports/sales?${params}`, {
        credentials: 'include'
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `sales_report.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Error exporting report:', error);
    }
  };

  if (loading) {
    return <div className="p-6">Loading sales analytics...</div>;
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Sales Analytics Dashboard</h2>
        <div className="flex space-x-2">
          <Button variant="outline" onClick={() => exportReport('csv')}>
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </Button>
          <Button variant="outline" onClick={() => exportReport('excel')}>
            <Download className="w-4 h-4 mr-2" />
            Export Excel
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Filter className="w-4 h-4 mr-2" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent className="flex space-x-4">
          <div className="flex-1">
            <label className="text-sm font-medium">Date Range</label>
            <DatePickerWithRange date={dateRange} setDate={setDateRange} />
          </div>
          <div className="flex-1">
            <label className="text-sm font-medium">Category</label>
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger>
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                {categories.map(category => (
                  <SelectItem key={category} value={category}>
                    {category}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${salesData?.total_revenue?.toFixed(2) || '0.00'}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Transactions</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {salesData?.unique_order_count || 0}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Transaction</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${salesData?.unique_order_count > 0 
                ? (salesData.total_revenue / salesData.unique_order_count).toFixed(2)
                : '0.00'}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Breakdown Pie Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Sales by Category</CardTitle>
            <CardDescription>Revenue distribution across business categories</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={salesData?.category_breakdown || []}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ category, revenue }) => `${category}: $${revenue?.toFixed(0)}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="revenue"
                >
                  {(salesData?.category_breakdown || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => [`$${value?.toFixed(2)}`, 'Revenue']} />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Category Bar Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Revenue by Category</CardTitle>
            <CardDescription>Detailed breakdown of sales performance</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={salesData?.category_breakdown || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="category" />
                <YAxis />
                <Tooltip formatter={(value) => [`$${value?.toFixed(2)}`, 'Revenue']} />
                <Legend />
                <Bar dataKey="revenue" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Daily Trend */}
      <Card>
        <CardHeader>
          <CardTitle>Daily Sales Trend</CardTitle>
          <CardDescription>Revenue performance over time</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={salesData?.daily_sales || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip formatter={(value) => [`$${value?.toFixed(2)}`, 'Revenue']} />
              <Legend />
              <Line type="monotone" dataKey="revenue" stroke="#8884d8" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Top Items */}
      <Card>
        <CardHeader>
          <CardTitle>Top Selling Items</CardTitle>
          <CardDescription>Best performing products across all categories</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {(salesData?.top_items || []).map((item, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium">{item.name}</p>
                  <p className="text-sm text-gray-500">{item.category} • {item.count} sales</p>
                </div>
                <div className="text-right">
                  <p className="font-bold">${item.revenue?.toFixed(2)}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

