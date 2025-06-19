import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx';
import { Button } from '@/components/ui/button.jsx';
import { DatePickerWithRange } from '@/components/ui/date-picker.jsx';
import { LoadingSpinner } from '@/components/ui/loading-spinner.jsx';
import { useToast } from '@/components/ui/toast.jsx';
import { useApiData, useApiMutation } from '@/hooks/use-api.js';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';
import { Download, Filter, TrendingUp, DollarSign, X, Users, Search } from 'lucide-react';
import { Badge } from '@/components/ui/badge.jsx';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover.jsx';
import { Checkbox } from '@/components/ui/checkbox.jsx';
import { cn } from '@/lib/utils';
import { Input } from '@/components/ui/input.jsx';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export const SalesAnalyticsDashboard = () => {
  const [dateRange, setDateRange] = useState({ from: null, to: null });
  const [selectedCategories, setSelectedCategories] = useState(['all']);
  const [tempSelectedCategories, setTempSelectedCategories] = useState(['all']);
  const [categories, setCategories] = useState([]);
  const [isSelectOpen, setIsSelectOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const { success, error: showError } = useToast();

  // Use API hooks for data fetching with caching
  const { data: salesData, loading, error, refresh } = useApiData('/dashboard/sales-summary', {
    start_date: dateRange.from?.toISOString(),
    end_date: dateRange.to?.toISOString(),
    category: selectedCategories.includes('all') ? undefined : selectedCategories.join(',')
  });
  
  const { data: inventoryData } = useApiData('/inventory', []);

  // Extract categories from inventory data
  useEffect(() => {
    if (inventoryData?.items) {
      const uniqueCategories = [...new Set(inventoryData.items.map(item => item.category))].filter(Boolean);
      setCategories(uniqueCategories);
    }
  }, [inventoryData]);

  // Initialize temp selection when popover opens
  useEffect(() => {
    if (isSelectOpen) {
      setTempSelectedCategories(selectedCategories);
    }
  }, [isSelectOpen]);

  // Handle checkbox change
  const handleCheckboxChange = (categoryId, checked) => {
    if (checked) {
      if (categoryId === 'all') {
        setTempSelectedCategories(['all']);
      } else {
        setTempSelectedCategories(prev => {
          // If 'all' was selected, remove it and add the new category
          if (prev.includes('all')) {
            return [categoryId];
          }
          // Add the new category to selection if not already present
          return prev.includes(categoryId) ? prev : [...prev, categoryId];
        });
      }
    } else {
      if (categoryId === 'all') {
        // When unchecking 'all', select no categories
        setTempSelectedCategories([]);
      } else {
        // Remove the category from selection
        setTempSelectedCategories(prev => {
          const newSelection = prev.filter(id => id !== categoryId);
          return newSelection.length === 0 ? ['all'] : newSelection;
        });
      }
    }
  };

  // Apply the selection when Done is clicked
  const applySelection = () => {
    // Ensure uniqueness in the final selection
    const uniqueCategories = [...new Set(tempSelectedCategories)];
    setSelectedCategories(uniqueCategories);
    setIsSelectOpen(false);
  };

  // Cancel selection
  const cancelSelection = () => {
    setTempSelectedCategories([...new Set(selectedCategories)]);
    setIsSelectOpen(false);
  };

  // Remove a category from selection
  const removeCategory = (categoryId) => {
    const newSelection = selectedCategories.filter(id => id !== categoryId);
    const uniqueSelection = [...new Set(newSelection.length === 0 ? ['all'] : newSelection)];
    setSelectedCategories(uniqueSelection);
    setTempSelectedCategories(uniqueSelection);
  };

  // Filter the sales data based on selected categories
  const filteredSalesData = useMemo(() => {
    if (!salesData) return null;
    
    return {
      ...salesData,
      category_breakdown: selectedCategories.includes('all') 
        ? salesData.category_breakdown
        : salesData.category_breakdown?.filter(item => 
            selectedCategories.includes(item.category)
          ),
      daily_sales: salesData.daily_sales,
      top_items: selectedCategories.includes('all')
        ? salesData.top_items
        : salesData.top_items?.filter(item =>
            selectedCategories.includes(item.category)
          )
    };
  }, [salesData, selectedCategories]);

  const handleExport = async (format) => {
    try {
      const params = new URLSearchParams();
      if (dateRange.from) params.append('start_date', dateRange.from.toISOString());
      if (dateRange.to) params.append('end_date', dateRange.to.toISOString());
      if (!selectedCategories.includes('all')) {
        params.append('category', selectedCategories.join(','));
      }
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
        success('Export Successful', `Sales report downloaded as ${format.toUpperCase()}`);
      } else {
        throw new Error('Export failed');
      }
    } catch (error) {
      showError('Export Failed', 'Failed to download the report. Please try again.');
    }
  };

  // Show error toast if API call fails
  useEffect(() => {
    if (error) {
      showError('Failed to load sales data', error);
    }
  }, [error, showError]);

  // Filter categories based on search query
  const filteredCategories = categories.filter(category =>
    category.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return <LoadingSpinner size="lg" text="Loading sales analytics..." />;
  }

  // Calculate totals based on filtered data
  const totalRevenue = filteredSalesData?.category_breakdown?.reduce((sum, item) => sum + (item.revenue || 0), 0) || 0;
  const totalTransactions = filteredSalesData?.category_breakdown?.reduce((sum, item) => sum + (item.count || 0), 0) || 0;
  const averageTransaction = totalTransactions > 0 ? totalRevenue / totalTransactions : 0;

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Sales Analytics Dashboard</h2>
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
          <CardTitle className="flex items-center">
            <Filter className="w-4 h-4 mr-2" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex-1">
            <label className="text-sm font-medium">Date Range</label>
            <DatePickerWithRange date={dateRange} setDate={setDateRange} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Category</label>
            <div className="flex flex-wrap gap-2 mb-2">
              {selectedCategories.includes('all') ? (
                <Badge variant="secondary" className="bg-blue-50 text-blue-700 hover:bg-blue-100">
                  All Categories
                  <button
                    className="ml-1 hover:text-destructive"
                    onClick={() => setSelectedCategories(['all'])}
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ) : (
                selectedCategories.map(category => (
                  <Badge key={category} variant="secondary" className="bg-blue-50 text-blue-700 hover:bg-blue-100">
                    {category}
                    <button
                      className="ml-1 hover:text-destructive"
                      onClick={() => removeCategory(category)}
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))
              )}
            </div>
            <Popover open={isSelectOpen} onOpenChange={setIsSelectOpen}>
              <PopoverTrigger asChild>
                <Button 
                  variant="outline" 
                  className="w-[200px] justify-between text-left font-normal"
                  role="combobox"
                  aria-expanded={isSelectOpen}
                >
                  {selectedCategories.includes('all') ? (
                    <span className="text-muted-foreground">Change Selection</span>
                  ) : (
                    <span>Select Categories</span>
                  )}
                  <Filter className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-[200px] p-0" align="start">
                {/* Fixed header with "All Categories" */}
                <div className="p-2 border-b">
                  <div 
                    className={cn(
                      "flex items-center space-x-2 p-2 rounded cursor-pointer transition-colors",
                      tempSelectedCategories.includes('all') ? "bg-blue-50" : "hover:bg-gray-100"
                    )}
                    onClick={() => handleCheckboxChange('all', !tempSelectedCategories.includes('all'))}
                  >
                    <Checkbox 
                      id="all"
                      checked={tempSelectedCategories.includes('all')}
                      onCheckedChange={(checked) => handleCheckboxChange('all', checked)}
                      className="border-blue-500 data-[state=checked]:bg-blue-500"
                    />
                    <label 
                      htmlFor="all" 
                      className="flex-1 text-sm font-medium leading-none cursor-pointer select-none"
                    >
                      All Categories
                    </label>
                  </div>
                  {/* Search input */}
                  <div className="mt-2 px-2">
                    <div className="relative">
                      <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                      <Input
                        placeholder="Search categories..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-8 text-sm"
                      />
                    </div>
                  </div>
                </div>
                
                {/* Scrollable container for categories */}
                <div 
                  className="overflow-y-auto max-h-[200px]"
                  style={{
                    scrollbarWidth: 'thin',
                    scrollbarColor: '#E5E7EB transparent',
                  }}
                >
                  <div className="p-2">
                    <div className="space-y-1">
                      {filteredCategories.length === 0 ? (
                        <div className="text-sm text-muted-foreground text-center py-4">
                          No categories found
                        </div>
                      ) : (
                        filteredCategories.map((category) => (
                          <div 
                            key={category} 
                            className={cn(
                              "flex items-center space-x-2 p-2 rounded cursor-pointer transition-colors",
                              tempSelectedCategories.includes(category) ? "bg-blue-50" : "hover:bg-gray-100"
                            )}
                            onClick={() => handleCheckboxChange(category, !tempSelectedCategories.includes(category))}
                          >
                            <Checkbox 
                              id={category}
                              checked={tempSelectedCategories.includes(category) || tempSelectedCategories.includes('all')}
                              onCheckedChange={(checked) => handleCheckboxChange(category, checked)}
                              className="border-blue-500 data-[state=checked]:bg-blue-500"
                            />
                            <label 
                              htmlFor={category} 
                              className="flex-1 text-sm font-medium leading-none cursor-pointer select-none"
                            >
                              {category}
                            </label>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>

                {/* Fixed footer with buttons */}
                <div className="flex items-center justify-end gap-2 p-2 bg-gray-50 border-t">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={cancelSelection}
                    className="text-xs"
                  >
                    Cancel
                  </Button>
                  <Button 
                    size="sm" 
                    onClick={applySelection}
                    className="bg-blue-500 hover:bg-blue-600 text-xs"
                  >
                    Done
                  </Button>
                </div>
              </PopoverContent>
            </Popover>
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
            <div className="text-2xl font-bold">${totalRevenue.toFixed(2)}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Transactions</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalTransactions}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Transaction</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${averageTransaction.toFixed(2)}</div>
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
                  data={filteredSalesData?.category_breakdown || []}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ category, revenue }) => `${category}: $${revenue?.toFixed(0)}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="revenue"
                >
                  {(filteredSalesData?.category_breakdown || []).map((entry, index) => (
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
              <BarChart data={filteredSalesData?.category_breakdown || []}>
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
            <LineChart data={filteredSalesData?.daily_sales || []}>
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
            {(filteredSalesData?.top_items || []).map((item, index) => (
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

