import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx';
import { Button } from '@/components/ui/button.jsx';
import { Input } from '@/components/ui/input.jsx';
import { Label } from '@/components/ui/label.jsx';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx';
import { Alert, AlertDescription } from '@/components/ui/alert.jsx';
import { Progress } from '@/components/ui/progress.jsx';
import { Upload, FileText, CheckCircle, AlertCircle, X, Trash2, Database, Calendar, RefreshCw } from 'lucide-react';
import { DatePickerWithRange } from '@/components/ui/date-picker.jsx';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog.jsx";
import debounce from 'lodash/debounce';

const API_BASE_URL = 'http://localhost:5000/api';

export const AdminPanel = () => {
  const [uploadStatus, setUploadStatus] = useState({});
  const [uncategorizedItems, setUncategorizedItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dateRange, setDateRange] = useState({ from: null, to: null });
  const [selectedDataType, setSelectedDataType] = useState('');
  const [dataStats, setDataStats] = useState({
    sales: { count: 0, lastUpdated: null },
    inventory: { count: 0, lastUpdated: null },
    expenses: { count: 0, lastUpdated: null },
    chefMapping: { count: 0, lastUpdated: null }
  });
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteStatus, setDeleteStatus] = useState({ status: '', message: '' });
  const [dataStatsCache, setDataStatsCache] = useState(null);
  const [lastFetchTime, setLastFetchTime] = useState(0);

  // Debounced fetch function
  const debouncedFetchDataStats = useCallback(
    debounce(async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/admin/data-stats`, {
          credentials: 'include'
        });
        if (response.ok) {
          const stats = await response.json();
          console.log('Received data stats:', stats); // Debug log
          
          // Format timestamps before setting state
          const formattedStats = {
            sales: { 
              count: stats.sales?.count || 0, 
              lastUpdated: stats.sales?.last_updated ? new Date(stats.sales.last_updated).toLocaleString('en-US', { timeZone: 'America/Chicago' }) : 'Never'
            },
            inventory: { 
              count: stats.inventory?.count || 0, 
              lastUpdated: stats.inventory?.last_updated ? new Date(stats.inventory.last_updated).toLocaleString('en-US', { timeZone: 'America/Chicago' }) : 'Never'
            },
            expenses: { 
              count: stats.expenses?.count || 0, 
              lastUpdated: stats.expenses?.last_updated ? new Date(stats.expenses.last_updated).toLocaleString('en-US', { timeZone: 'America/Chicago' }) : 'Never'
            },
            chefMapping: { 
              count: stats.chef_mapping?.count || 0, 
              lastUpdated: stats.chef_mapping?.last_updated ? new Date(stats.chef_mapping.last_updated).toLocaleString('en-US', { timeZone: 'America/Chicago' }) : 'Never'
            }
          };
          
          setDataStats(formattedStats);
          setDataStatsCache(stats);
          setLastFetchTime(Date.now());
        }
      } catch (error) {
        console.error('Error fetching data stats:', error);
      }
    }, 1000),
    []
  );

  useEffect(() => {
    // Only fetch if cache is older than 30 seconds
    if (!dataStatsCache || Date.now() - lastFetchTime > 30000) {
      debouncedFetchDataStats();
    }
  }, []);

  const handleFileUpload = async (fileType, file) => {
    if (!file) return;

    setLoading(true);
    setUploadStatus(prev => ({
      ...prev,
      [fileType]: { status: 'uploading', progress: 0 }
    }));

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE_URL}/upload/${fileType}`, {
        method: 'POST',
        credentials: 'include',
        body: formData
      });

      const result = await response.json();

      if (response.ok) {
        setUploadStatus(prev => ({
          ...prev,
          [fileType]: {
            status: 'success',
            message: `Successfully processed ${result.processed_records} records. ${result.failed_records} failed.`,
            processed: result.processed_records,
            failed: result.failed_records
          }
        }));
        
        // Refresh data stats and uncategorized items
        debouncedFetchDataStats();
        if (fileType === 'sales') {
          fetchUncategorizedItems();
        }
      } else {
        setUploadStatus(prev => ({
          ...prev,
          [fileType]: {
            status: 'error',
            message: result.error || 'Upload failed'
          }
        }));
      }
    } catch (error) {
      setUploadStatus(prev => ({
        ...prev,
        [fileType]: {
          status: 'error',
          message: 'Network error occurred'
        }
      }));
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteData = async () => {
    if (!dateRange.from || !dateRange.to || !selectedDataType) {
      setDeleteStatus({
        status: 'error',
        message: 'Please select both date range and data type'
      });
      return;
    }

    try {
      setLoading(true);
      
      if (selectedDataType === 'all') {
        // Delete all data types sequentially
        const dataTypes = ['sales', 'inventory', 'expenses', 'chef_mapping'];
        let totalDeleted = 0;
        
        for (const type of dataTypes) {
          const response = await fetch(`${API_BASE_URL}/admin/delete-data`, {
            method: 'DELETE',
            headers: {
              'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
              data_type: type,
              start_date: dateRange.from.toISOString(),
              end_date: dateRange.to.toISOString()
            })
          });

          const result = await response.json();
          
          if (response.ok) {
            totalDeleted += result.deleted_count || 0;
          } else {
            throw new Error(`Failed to delete ${type}: ${result.error || 'Unknown error'}`);
          }
        }

        setDeleteStatus({
          status: 'success',
          message: `Successfully deleted ${totalDeleted} records across all data types`
        });
      } else {
        // Delete single data type
        const response = await fetch(`${API_BASE_URL}/admin/delete-data`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({
            data_type: selectedDataType,
            start_date: dateRange.from.toISOString(),
            end_date: dateRange.to.toISOString()
          })
        });

        const result = await response.json();

        if (response.ok) {
          setDeleteStatus({
            status: 'success',
            message: `Successfully deleted ${result.deleted_count} records`
          });
        } else {
          throw new Error(result.error || 'Delete operation failed');
        }
      }
      
      // Refresh stats after deletion
      debouncedFetchDataStats();
    } catch (error) {
      setDeleteStatus({
        status: 'error',
        message: error.message || 'Network error occurred'
      });
    } finally {
      setLoading(false);
      setDeleteDialogOpen(false);
    }
  };

  const fetchUncategorizedItems = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/dashboard/items/uncategorized`, {
        credentials: 'include'
      });
      const data = await response.json();
      setUncategorizedItems(data.uncategorized_items || []);
    } catch (error) {
      console.error('Error fetching uncategorized items:', error);
    }
  };

  const categorizeItem = async (itemId, category) => {
    try {
      const response = await fetch(`${API_BASE_URL}/dashboard/items/uncategorized/${itemId}/categorize`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ category })
      });

      if (response.ok) {
        setUncategorizedItems(prev => prev.filter(item => item.id !== itemId));
      }
    } catch (error) {
      console.error('Error categorizing item:', error);
    }
  };

  const FileUploadCard = ({ title, description, fileType, acceptedTypes }) => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <Upload className="w-4 h-4 mr-2" />
          {title}
        </CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label htmlFor={`file-${fileType}`}>Choose File</Label>
          <Input
            id={`file-${fileType}`}
            type="file"
            accept={acceptedTypes}
            onChange={(e) => handleFileUpload(fileType, e.target.files[0])}
            disabled={loading}
          />
        </div>
        
        {uploadStatus[fileType] && (
          <Alert variant={uploadStatus[fileType].status === 'error' ? 'destructive' : 'default'}>
            <div className="flex items-center">
              {uploadStatus[fileType].status === 'success' && <CheckCircle className="w-4 h-4" />}
              {uploadStatus[fileType].status === 'error' && <AlertCircle className="w-4 h-4" />}
              {uploadStatus[fileType].status === 'uploading' && <Upload className="w-4 h-4" />}
              <AlertDescription className="ml-2">
                {uploadStatus[fileType].message}
              </AlertDescription>
            </div>
            {uploadStatus[fileType].status === 'uploading' && (
              <Progress value={50} className="mt-2" />
            )}
          </Alert>
        )}
      </CardContent>
    </Card>
  );

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Admin Panel</h2>
      
      {/* Data Management Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Database className="w-4 h-4 mr-2" />
            Data Management
          </CardTitle>
          <CardDescription>Manage and monitor your data</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <h3 className="font-medium text-blue-800">Sales Data</h3>
              <p className="text-2xl font-bold text-blue-600">{dataStats?.sales?.count || 0}</p>
              <p className="text-sm text-blue-600">
                Last updated: {dataStats?.sales?.lastUpdated}
              </p>
            </div>
            <div className="p-4 bg-green-50 rounded-lg">
              <h3 className="font-medium text-green-800">Inventory Items</h3>
              <p className="text-2xl font-bold text-green-600">{dataStats?.inventory?.count || 0}</p>
              <p className="text-sm text-green-600">
                Last updated: {dataStats?.inventory?.lastUpdated}
              </p>
            </div>
            <div className="p-4 bg-yellow-50 rounded-lg">
              <h3 className="font-medium text-yellow-800">Expenses</h3>
              <p className="text-2xl font-bold text-yellow-600">{dataStats?.expenses?.count || 0}</p>
              <p className="text-sm text-yellow-600">
                Last updated: {dataStats?.expenses?.lastUpdated}
              </p>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg">
              <h3 className="font-medium text-purple-800">Chef Mappings</h3>
              <p className="text-2xl font-bold text-purple-600">{dataStats?.chefMapping?.count || 0}</p>
              <p className="text-sm text-purple-600">
                Last updated: {dataStats?.chefMapping?.lastUpdated}
              </p>
            </div>
          </div>

          <div className="mt-6 flex justify-end space-x-4">
            <Button variant="outline" onClick={debouncedFetchDataStats}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh Stats
            </Button>
            <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="destructive">
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete Data
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Delete Data</DialogTitle>
                  <DialogDescription>
                    Select the data type and date range to delete. This action cannot be undone.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label>Data Type</Label>
                    <Select value={selectedDataType} onValueChange={setSelectedDataType}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select data type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Data</SelectItem>
                        <SelectItem value="sales">Sales Data</SelectItem>
                        <SelectItem value="inventory">Inventory Data</SelectItem>
                        <SelectItem value="expenses">Expenses Data</SelectItem>
                        <SelectItem value="chef_mapping">Chef Mapping Data</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Date Range</Label>
                    <DatePickerWithRange date={dateRange} setDate={setDateRange} />
                  </div>
                  {deleteStatus.message && (
                    <Alert variant={deleteStatus.status === 'error' ? 'destructive' : 'default'}>
                      <AlertDescription>{deleteStatus.message}</AlertDescription>
                    </Alert>
                  )}
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button variant="destructive" onClick={handleDeleteData} disabled={loading}>
                    {loading ? 'Deleting...' : 'Delete'}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </CardContent>
      </Card>

      {/* File Upload Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <FileUploadCard
          title="Sales Data Upload"
          description="Upload monthly sales reports (CSV format)"
          fileType="sales"
          acceptedTypes=".csv"
        />
        
        <FileUploadCard
          title="Inventory Data Upload"
          description="Upload inventory and product information (Excel format)"
          fileType="inventory"
          acceptedTypes=".xlsx,.xls"
        />
        
        <FileUploadCard
          title="Chef Mapping Upload"
          description="Upload chef-to-dish mapping data (Excel format)"
          fileType="chef-mapping"
          acceptedTypes=".xlsx,.xls"
        />
        
        <FileUploadCard
          title="Expenses Data Upload"
          description="Upload expense and spending records (Excel format)"
          fileType="expenses"
          acceptedTypes=".xlsx,.xls"
        />
      </div>

      {/* Uncategorized Items Management */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <FileText className="w-4 h-4 mr-2" />
            Uncategorized Items Management
          </CardTitle>
          <CardDescription>
            Items found in sales data that need manual categorization
          </CardDescription>
        </CardHeader>
        <CardContent>
          {uncategorizedItems.length === 0 ? (
            <p className="text-gray-500">No uncategorized items found.</p>
          ) : (
            <div className="space-y-4">
              {uncategorizedItems.map((item) => (
                <div key={item.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex-1">
                    <p className="font-medium">{item.item_name}</p>
                    <p className="text-sm text-gray-500">
                      Found {item.frequency} times in sales data
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Select onValueChange={(category) => categorizeItem(item.id, category)}>
                      <SelectTrigger className="w-48">
                        <SelectValue placeholder="Select category" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Meat">Meat</SelectItem>
                        <SelectItem value="Vegetables">Vegetables</SelectItem>
                        <SelectItem value="Grocery">Grocery</SelectItem>
                        <SelectItem value="Breakfast">Restaurant - Breakfast</SelectItem>
                        <SelectItem value="Lunch">Restaurant - Lunch</SelectItem>
                        <SelectItem value="Dinner">Restaurant - Dinner</SelectItem>
                        <SelectItem value="Kitchen">Kitchen Supplies</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

