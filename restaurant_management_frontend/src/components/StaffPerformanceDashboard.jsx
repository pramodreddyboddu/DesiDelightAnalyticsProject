import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx';
import { Button } from '@/components/ui/button.jsx';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx';
import { DatePickerWithRange } from '@/components/ui/date-picker.jsx';
import { LoadingSpinner } from '@/components/ui/loading-spinner.jsx';
import { useToast } from '@/components/ui/toast.jsx';
import { useApiData } from '@/hooks/use-api.js';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Download, Users, Award, TrendingUp, X } from 'lucide-react';
import { Badge } from '@/components/ui/badge.jsx';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover.jsx';
import { Checkbox } from '@/components/ui/checkbox.jsx';
import { cn } from '@/lib/utils';
import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input.jsx';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export const StaffPerformanceDashboard = () => {
  // Set default dateRange: from = midnight (00:00:00) in America/Chicago, to = same day (today only)
  const chicagoTz = 'America/Chicago';
  const now = new Date();
  const chicagoMidnight = new Date(now.toLocaleString('en-US', { timeZone: chicagoTz }));
  chicagoMidnight.setHours(0, 0, 0, 0);
  const [dateRange, setDateRange] = useState({ from: chicagoMidnight, to: chicagoMidnight });
  const [selectedChefs, setSelectedChefs] = useState(['all']);
  const [tempSelectedChefs, setTempSelectedChefs] = useState(['all']);
  const [isSelectOpen, setIsSelectOpen] = useState(false);
  const [chefList, setChefList] = useState([]);
  const { success, error: showError } = useToast();

  // Use API hooks for data fetching with caching - only depends on dateRange now
  const { data: performanceData, loading, error, refresh } = useApiData('dashboard/chef-performance', {
    start_date: dateRange.from?.toISOString(),
    end_date: dateRange.to?.toISOString()
  });

  // Fetch chef list on mount
  useEffect(() => {
    const fetchChefs = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/dashboard/chefs`, { credentials: 'include' });
        if (response.ok) {
          const data = await response.json();
          setChefList(data);
        } else {
          showError('Failed to load chef list');
        }
      } catch (err) {
        showError('Failed to load chef list', err.message || String(err));
      }
    };
    fetchChefs();
  }, [showError]);

  // Show error toast if API call fails
  useEffect(() => {
    if (error) {
      showError('Failed to load staff performance data', error);
    }
  }, [error, showError]);

  // Initialize temp selection when popover opens
  useEffect(() => {
    if (isSelectOpen) {
      setTempSelectedChefs(selectedChefs);
    }
  }, [isSelectOpen]);

  // Handle temporary chef selection
  const handleToggleChefSelection = (chefId) => {
    setTempSelectedChefs(currentSelection => {
      const isAllSelected = currentSelection.includes('all');

      // Toggle 'all'
      if (chefId === 'all') {
        return isAllSelected ? [] : ['all'];
      }

      // If 'all' is selected, start a new selection with the chosen chef
      if (isAllSelected) {
        return [chefId];
      }

      // Add or remove an individual chef from the selection
      let newSelection;
      if (currentSelection.includes(chefId)) {
        newSelection = currentSelection.filter(id => id !== chefId);
      } else {
        newSelection = [...currentSelection, chefId];
      }

      // If the selection becomes empty, default back to 'all'
      if (newSelection.length === 0) {
        return ['all'];
      }

      return newSelection;
    });
  };

  // Apply the selection when Done is clicked
  const applySelection = () => {
    setSelectedChefs(tempSelectedChefs);
    setIsSelectOpen(false);
  };

  // Cancel selection
  const cancelSelection = () => {
    setTempSelectedChefs(selectedChefs);
    setIsSelectOpen(false);
  };

  // Remove a chef from selection
  const removeChef = (chefId) => {
    const newSelection = selectedChefs.filter(id => id !== chefId);
    setSelectedChefs(newSelection.length === 0 ? ['all'] : newSelection);
    setTempSelectedChefs(newSelection.length === 0 ? ['all'] : newSelection);
  };

  // Filter data based on selected chefs - now uses chefList for filter
  const filteredChefSummary = useMemo(() => {
    if (!performanceData?.chef_summary) return [];
    if (selectedChefs.includes('all')) {
      // Show all chefs from chefList, merging with summary if available
      return chefList.map(chef => {
        const summary = performanceData.chef_summary.find(c => c.id === chef.id);
        return summary ? summary : { id: chef.id, name: chef.name, total_revenue: 0, total_sales: 0 };
      });
    }
    return chefList
      .filter(chef => selectedChefs.includes(chef.id.toString()))
      .map(chef => {
        const summary = performanceData.chef_summary.find(c => c.id === chef.id);
        return summary ? summary : { id: chef.id, name: chef.name, total_revenue: 0, total_sales: 0 };
      });
  }, [performanceData, selectedChefs, chefList]);

  // For Individual Performance Details, use the new grouped chef_performance structure
  const filteredChefPerformance = useMemo(() => {
    if (!performanceData?.chef_performance) return [];
    if (selectedChefs.includes('all')) return performanceData.chef_performance;
    return performanceData.chef_performance.filter(chef => selectedChefs.includes(chef.chef_id.toString()));
  }, [performanceData, selectedChefs]);

  const handleExport = async (format) => {
    try {
      const params = new URLSearchParams();
      if (dateRange.from) params.append('start_date', dateRange.from.toISOString());
      if (dateRange.to) params.append('end_date', dateRange.to.toISOString());
      if (!selectedChefs.includes('all')) {
        params.append('chef_ids', selectedChefs.join(','));
      }
      params.append('format', format);

      const response = await fetch(`${API_BASE_URL}/api/reports/chef-performance?${params}`, {
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

  // Calculate totals based on filtered data
  const totalStaffMembers = filteredChefSummary.length;
  const totalRevenue = filteredChefSummary.reduce((sum, chef) => sum + (chef.total_revenue || 0), 0);
  const totalSales = filteredChefSummary.reduce((sum, chef) => sum + (chef.total_sales || 0), 0);

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
        <CardContent className="space-y-4">
          <div className="flex-1">
            <label className="text-sm font-medium">Date Range</label>
            <DatePickerWithRange date={dateRange} setDate={setDateRange} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Staff Members</label>
            <div className="flex flex-wrap gap-2 mb-2">
              {selectedChefs.includes('all') ? (
                <Badge variant="secondary" className="bg-blue-50 text-blue-700 hover:bg-blue-100">
                  All Staff Members
                  <button
                    className="ml-1 hover:text-destructive"
                    onClick={() => setSelectedChefs(['all'])}
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ) : (
                selectedChefs.map(chefId => {
                  const chef = performanceData?.chef_summary.find(c => c.id.toString() === chefId);
                  return chef ? (
                    <Badge key={chef.id} variant="secondary" className="bg-blue-50 text-blue-700 hover:bg-blue-100">
                      {chef.name}
                      <button
                        className="ml-1 hover:text-destructive"
                        onClick={() => removeChef(chef.id.toString())}
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ) : null;
                })
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
                  {selectedChefs.includes('all') ? (
                    <span className="text-muted-foreground">Change Selection</span>
                  ) : (
                    <span>Select Staff Members</span>
                  )}
                  <Users className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-[200px] p-0" align="start">
                <div className="p-2">
                  <div className="space-y-1">
                    <div 
                      className={cn(
                        "flex items-center space-x-2 p-2 rounded cursor-pointer transition-colors",
                        tempSelectedChefs.includes('all') ? "bg-blue-50" : "hover:bg-gray-100"
                      )}
                      onClick={() => handleToggleChefSelection('all')}
                    >
                      <Checkbox 
                        id="all"
                        checked={tempSelectedChefs.includes('all')}
                      />
                      <label htmlFor="all" className="font-medium w-full cursor-pointer">All Staff Members</label>
                    </div>
                    {chefList.map(chef => (
                      <div 
                        key={chef.id}
                        className={cn(
                          "flex items-center space-x-2 p-2 rounded cursor-pointer transition-colors",
                          tempSelectedChefs.includes(chef.id.toString()) ? "bg-blue-50" : "hover:bg-gray-100"
                        )}
                        onClick={() => handleToggleChefSelection(chef.id.toString())}
                      >
                        <Checkbox 
                          id={chef.id.toString()}
                          checked={tempSelectedChefs.includes(chef.id.toString())}
                        />
                        <label htmlFor={chef.id.toString()} className="w-full cursor-pointer">{chef.name}</label>
                      </div>
                    ))}
                  </div>
                </div>
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

      {/* Staff Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Staff Members</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalStaffMembers}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Revenue Generated</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${totalRevenue.toFixed(2)}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Sales Count</CardTitle>
            <Award className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalSales}</div>
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
              <BarChart data={filteredChefSummary}>
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
                  data={filteredChefSummary}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, total_sales }) => `${name}: ${total_sales}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="total_sales"
                >
                  {filteredChefSummary.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Staff Performance Leaderboard */}
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
                {filteredChefSummary
                  .sort((a, b) => b.total_revenue - a.total_revenue)
                  .map((chef, index) => {
                    const avgSaleValue = chef.total_sales > 0 ? chef.total_revenue / chef.total_sales : 0;
                    const maxRevenue = Math.max(...filteredChefSummary.map(c => c.total_revenue));
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

      {/* Performance Insights */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Insights</CardTitle>
          <CardDescription>Key findings and recommendations</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredChefSummary && filteredChefSummary.length > 0 && (
              <>
                {/* Top Performer */}
                {(() => {
                  const topPerformer = filteredChefSummary.reduce((max, chef) => 
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
                  const mostActive = filteredChefSummary.reduce((max, chef) => 
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
                  const needsSupport = filteredChefSummary.reduce((min, chef) => 
                    chef.total_revenue < (min?.total_revenue || Infinity) ? chef : min, null);
                  return needsSupport && filteredChefSummary.length > 1 && (
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

      {/* Individual Staff Performance Details */}
      {!selectedChefs.includes('all') && performanceData?.chef_performance && (
        <Card>
          <CardHeader>
            <CardTitle>Individual Performance Details</CardTitle>
            <CardDescription>Detailed breakdown of dishes and performance</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {filteredChefPerformance.map((chef, index) => (
                <div key={index}>
                  <h4 className="font-medium text-lg mb-4">{chef.chef_name}</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {chef.dishes.map((dish, dishIndex) => (
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
    </div>
  );
};

