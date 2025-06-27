import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx';
import { Button } from '@/components/ui/button.jsx';
import { Input } from '@/components/ui/input.jsx';
import { Label } from '@/components/ui/label.jsx';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx';
import { Alert, AlertDescription } from '@/components/ui/alert.jsx';
import { Progress } from '@/components/ui/progress.jsx';
import { LoadingSpinner } from '@/components/ui/loading-spinner.jsx';
import { useToast } from '@/components/ui/toast.jsx';
import { useApiData, useApiMutation } from '@/hooks/use-api.js';
import { useAuth } from '@/hooks/use-auth.jsx';
import { Upload, FileText, CheckCircle, AlertCircle, X, Trash2, Database, Calendar, RefreshCw, Shield } from 'lucide-react';
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

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

const DataStats = ({ stats }) => {
    const dataPoints = [
        { title: 'Sales Data', value: stats.sales?.count, lastUpdated: stats.sales?.last_updated },
        { title: 'Inventory Items', value: stats.inventory?.count, lastUpdated: stats.inventory?.last_updated },
        { title: 'Expenses', value: stats.expenses?.count, lastUpdated: stats.expenses?.last_updated },
        { title: 'Chef Mappings', value: stats.chef_mapping?.count, lastUpdated: stats.chef_mapping?.last_updated },
    ];

    return (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {dataPoints.map((point, index) => (
                <Card key={index}>
                    <CardHeader>
                        <CardTitle className="text-sm font-medium">{point.title}</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{point.value ?? 0}</div>
                        <p className="text-xs text-muted-foreground">
                            Last updated: {point.lastUpdated ? new Date(point.lastUpdated).toLocaleDateString() : 'N/A'}
                        </p>
                    </CardContent>
                </Card>
            ))}
        </div>
    );
};

export const AdminPanel = () => {
  const [uploadStatus, setUploadStatus] = useState({});
  const [uncategorizedItems, setUncategorizedItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dateRange, setDateRange] = useState({ from: null, to: null });
  const [selectedDataType, setSelectedDataType] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteStatus, setDeleteStatus] = useState({ status: '', message: '' });
  const [isRefreshing, setIsRefreshing] = useState(false);
  let refreshTimeout;
  
  const { success, error: showError, info } = useToast();
  const { user } = useAuth();

  // Determine user permissions
  const isSuperAdmin = user?.is_admin && !user?.tenant_id;
  const isTenantAdmin = user?.is_admin && user?.tenant_id;
  const hasUploadPermissions = isSuperAdmin || isTenantAdmin;
  const hasDeletePermissions = isSuperAdmin || isTenantAdmin;

  const statsUrl = isSuperAdmin ? '/admin/data-stats' : '/tenant-data/stats';
  const { data: dataStats, loading: statsLoading, error: statsError, refresh: refreshStats } = useApiData(
    statsUrl,
    null,
    {
      refreshInterval: isRefreshing ? 0 : 30000,
      showToast: false // Disable generic toast from hook
    }
  );
  
  const { mutate: deleteData, loading: deleteLoading } = useApiMutation('/admin/delete-data', {
    successMessage: 'Data deleted successfully!',
    invalidateCache: '/admin'
  });

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
        
        success('Upload Successful', `Processed ${result.processed_records} records successfully`);
        
        refreshStats();
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
        showError('Upload Failed', result.error || 'Upload failed');
      }
    } catch (error) {
      setUploadStatus(prev => ({
        ...prev,
        [fileType]: {
          status: 'error',
          message: 'Network error occurred'
        }
      }));
      showError('Upload Failed', 'Network error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteData = async () => {
    if (!dateRange.from || !dateRange.to || !selectedDataType) {
      showError('Validation Error', 'Please select both date range and data type');
      return;
    }

    try {
      setLoading(true);
      
      if (selectedDataType === 'all') {
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

        success('Delete Successful', `Successfully deleted ${totalDeleted} records across all data types`);
        refreshStats();
      } else {
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
          success('Delete Successful', `Successfully deleted ${result.deleted_count} records`);
          refreshStats();
        } else {
          throw new Error(result.error || 'Delete operation failed');
        }
      }
    } catch (error) {
      showError('Delete Failed', error.message || 'Delete operation failed');
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
      showError('Failed to load uncategorized items', error.message);
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
        success('Item Categorized', `Item successfully categorized as ${category}`);
      } else {
        throw new Error('Failed to categorize item');
      }
    } catch (error) {
      showError('Categorization Failed', error.message || 'Failed to categorize item');
    }
  };

  const handleRefresh = (refreshFn) => {
    setIsRefreshing(true);
    if (refreshFn) {
      refreshFn();
    }
    if (refreshTimeout) clearTimeout(refreshTimeout);
    refreshTimeout = setTimeout(() => setIsRefreshing(false), 1000);
  };

  const FileUploadCard = ({ title, description, fileType, acceptedTypes }) => (
    <Card className="shadow-sm hover:shadow-md transition-shadow">
      <CardHeader>
        <CardTitle className="flex items-center text-lg">
          <Upload className="mr-3 text-gray-500" />
          {title}
        </CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <Input
            id={`${fileType}-upload`}
            type="file"
            accept={acceptedTypes}
            onChange={(e) => handleFileUpload(fileType, e.target.files[0])}
            className="file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          />
          {uploadStatus[fileType] && (
            <div className="mt-4 p-3 rounded-lg bg-gray-50">
              {uploadStatus[fileType].status === 'uploading' && (
                <div className="flex items-center text-sm text-blue-600">
                  <LoadingSpinner size="sm" className="mr-2" />
                  Uploading...
                </div>
              )}
              {uploadStatus[fileType].status === 'success' && (
                <div className="flex items-center text-sm text-green-600">
                  <CheckCircle className="mr-2" />
                  Success: {uploadStatus[fileType].message}
                </div>
              )}
              {uploadStatus[fileType].status === 'error' && (
                <div className="flex items-center text-sm text-red-600">
                  <AlertCircle className="mr-2" />
                  Error: {uploadStatus[fileType].message}
        </div>
              )}
            </div>
            )}
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="container mx-auto p-6 bg-gray-50 min-h-screen">
      <header className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Admin Panel</h1>
          <p className="text-gray-500">Welcome, {user?.username}. Manage your restaurant data and settings.</p>
        </div>
        <Button onClick={() => handleRefresh(refreshStats)} disabled={isRefreshing} variant="outline" size="sm">
          <RefreshCw className={`mr-2 h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          Refresh Stats
        </Button>
      </header>
      
      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-700 mb-4">Data Management</h2>
        {statsLoading && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {['Sales Data', 'Inventory Items', 'Expenses', 'Chef Mappings'].map(title => (
                    <Card key={title}>
                        <CardHeader>
                            <CardTitle className="text-sm font-medium">{title}</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <LoadingSpinner size="sm" />
                        </CardContent>
                    </Card>
                ))}
            </div>
          )}
        {statsError && !statsLoading && (
            <Alert variant="destructive">
                <AlertDescription>{statsError.error || "An error occurred while fetching data stats."}</AlertDescription>
            </Alert>
        )}
        {dataStats && !statsLoading && !statsError && (
            <DataStats stats={dataStats} />
        )}
      </section>

      {hasUploadPermissions && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-700 mb-4">Upload Center</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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
              acceptedTypes=".xlsx, .xls"
            />
            <FileUploadCard
              title="Chef Mapping Upload"
              description="Upload chef-to-dish mapping data (Excel format)"
              fileType="chef-mapping"
              acceptedTypes=".xlsx, .xls"
            />
            <FileUploadCard
              title="Expenses Data Upload"
              description="Upload expense and spending records (Excel format)"
              fileType="expenses"
              acceptedTypes=".xlsx, .xls"
            />
        </div>
        </section>
      )}

      {(isSuperAdmin || isTenantAdmin) && (
        <>
          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-700 mb-4">Danger Zone</h2>
            <Card className="bg-red-50 border-red-200">
        <CardHeader>
                <CardTitle className="flex items-center text-red-800">
                  <Trash2 className="mr-3" />
                  Delete Tenant Data
          </CardTitle>
                <CardDescription className="text-red-600">
                  Permanently delete data within a specific date range for a data type. This action cannot be undone.
          </CardDescription>
        </CardHeader>
        <CardContent>
              <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
                <DialogTrigger asChild>
                    <Button variant="destructive" className="bg-red-600 hover:bg-red-700">Delete Data</Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                      <DialogTitle>Are you absolutely sure?</DialogTitle>
                    <DialogDescription>
                        This will permanently delete the selected data within the specified date range. This action cannot be undone.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="col-span-2">
                          <Label>Date range</Label>
                          <DatePickerWithRange date={dateRange} setDate={setDateRange} />
                        </div>
                        <div>
                          <Label htmlFor="data-type">Data Type</Label>
                          <Select onValueChange={setSelectedDataType}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select data type" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All Data</SelectItem>
                              <SelectItem value="sales">Sales</SelectItem>
                              <SelectItem value="inventory">Inventory</SelectItem>
                              <SelectItem value="expenses">Expenses</SelectItem>
                              <SelectItem value="chef_mapping">Chef Mappings</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    </div>
                    {deleteStatus.message && (
                        <Alert variant={deleteStatus.status === 'success' ? 'default' : 'destructive'}>
                        <AlertDescription>{deleteStatus.message}</AlertDescription>
                      </Alert>
                    )}
                  </div>
                  <DialogFooter>
                      <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
                      <Button 
                        variant="destructive" 
                        onClick={handleDeleteData} 
                        disabled={deleteLoading || !dateRange.from || !dateRange.to || !selectedDataType}
                      >
                        {deleteLoading ? <LoadingSpinner size="sm" /> : 'Delete Data'}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
        </CardContent>
      </Card>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-700 mb-4">System Diagnostics</h2>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
                  <Shield className="mr-3 text-gray-500" />
                  Uncategorized Items
            </CardTitle>
            <CardDescription>
                  Review items from sales data that do not have a category and assign them one.
            </CardDescription>
          </CardHeader>
          <CardContent>
                {uncategorizedItems.length > 0 ? (
                  <ul className="space-y-2">
                    {uncategorizedItems.map(item => (
                      <li key={item.id} className="flex justify-between items-center p-2 border rounded-lg">
                        <span>{item.name}</span>
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
                      </li>
                ))}
                  </ul>
                ) : (
                  <p className="text-gray-500">No uncategorized items found.</p>
            )}
          </CardContent>
        </Card>
          </section>
        </>
      )}
    </div>
  );
};

