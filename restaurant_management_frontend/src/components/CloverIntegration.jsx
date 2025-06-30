import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx';
import { Button } from '@/components/ui/button.jsx';
import { Input } from '@/components/ui/input.jsx';
import { Label } from '@/components/ui/label.jsx';
import { LoadingSpinner } from '@/components/ui/loading-spinner.jsx';
import { useToast } from '@/components/ui/toast.jsx';
import { useApiData, useApiMutation } from '@/hooks/use-api.js';
import { Badge } from '@/components/ui/badge.jsx';
import { 
  RefreshCw, 
  Database, 
  TrendingUp, 
  Package, 
  Users, 
  Settings,
  CheckCircle,
  AlertCircle,
  Clock,
  DollarSign,
  ShoppingCart,
  Eye,
  Wifi,
  WifiOff,
  AlertTriangle
} from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert.jsx';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

// Rate limiting hook
const useRateLimitedApi = (url, options = {}) => {
  const [lastCall, setLastCall] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    const now = Date.now();
    const timeSinceLastCall = now - lastCall;
    const minInterval = 2000; // 2 seconds between calls

    if (timeSinceLastCall < minInterval) {
      const waitTime = minInterval - timeSinceLastCall;
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(url, {
        credentials: 'include',
        ...options
      });

      if (!response.ok) {
        if (response.status === 429) {
          throw new Error('Rate limit exceeded. Please wait a moment before trying again.');
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setData(result);
      setLastCall(Date.now());
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [url, lastCall, options]);

  return { data, error, isLoading, fetchData };
};

export const CloverIntegration = () => {
  const [cloverConfig, setCloverConfig] = useState({
    merchant_id: '',
    access_token: ''
  });
  const [isConfiguring, setIsConfiguring] = useState(false);
  const { success, error: showError } = useToast();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(null);

  // Rate-limited API calls
  const { 
    data: statusData, 
    error: statusError, 
    isLoading: statusLoading, 
    fetchData: fetchStatus 
  } = useRateLimitedApi(`${API_BASE_URL}/clover/status`);

  const { 
    data: realtimeData, 
    error: realtimeError, 
    isLoading: realtimeLoading, 
    fetchData: fetchRealtime 
  } = useRateLimitedApi(`${API_BASE_URL}/clover/realtime`);

  const { 
    data: inventoryData, 
    error: inventoryError, 
    isLoading: inventoryLoading, 
    fetchData: fetchInventory 
  } = useRateLimitedApi(`${API_BASE_URL}/clover/inventory`);

  const { 
    data: ordersData, 
    error: ordersError, 
    isLoading: ordersLoading, 
    fetchData: fetchOrders 
  } = useRateLimitedApi(`${API_BASE_URL}/clover/orders?limit=10`);

  const { 
    data: employeesData, 
    error: employeesError, 
    isLoading: employeesLoading, 
    fetchData: fetchEmployees 
  } = useRateLimitedApi(`${API_BASE_URL}/clover/employees`);

  const { 
    data: customersData, 
    error: customersError, 
    isLoading: customersLoading, 
    fetchData: fetchCustomers 
  } = useRateLimitedApi(`${API_BASE_URL}/clover/customers`);
  
  // Sync mutations
  const { mutate: syncSales, loading: salesSyncLoading } = useApiMutation('/api/clover/sync/sales', {
    onSuccess: () => {
      success('Sales Sync Complete', 'Sales data has been successfully synchronized from Clover');
      fetchRealtime();
    },
    onError: (error) => {
      showError('Sales Sync Failed', error.message || 'Failed to sync sales data from Clover');
    }
  });

  const { mutate: syncInventory, loading: inventorySyncLoading } = useApiMutation('/api/clover/sync/inventory', {
    onSuccess: () => {
      success('Inventory Sync Complete', 'Inventory data has been successfully synchronized from Clover');
      fetchInventory();
    },
    onError: (error) => {
      showError('Inventory Sync Failed', error.message || 'Failed to sync inventory data from Clover');
    }
  });

  const { mutate: syncAll, loading: allSyncLoading } = useApiMutation('/api/clover/sync/all', {
    onSuccess: () => {
      success('Full Sync Complete', 'All data has been successfully synchronized from Clover');
      fetchStatus();
      fetchRealtime();
      fetchInventory();
    },
    onError: (error) => {
      showError('Full Sync Failed', error.message || 'Failed to sync all data from Clover');
    }
  });

  const handleConfigureClover = async () => {
    if (!cloverConfig.merchant_id || !cloverConfig.access_token) {
      showError('Configuration Error', 'Please provide both Merchant ID and Access Token');
      return;
    }

    setIsConfiguring(true);
    try {
      // In a real implementation, you'd save this to your backend
      localStorage.setItem('clover_merchant_id', cloverConfig.merchant_id);
      localStorage.setItem('clover_access_token', cloverConfig.access_token);
      
      success('Clover Configured', 'Clover integration has been configured successfully');
      fetchStatus();
    } catch (error) {
      showError('Configuration Failed', error.message || 'Failed to configure Clover');
    } finally {
      setIsConfiguring(false);
    }
  };

  const handleSyncSales = () => {
    syncSales({
      start_date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
      end_date: new Date().toISOString()
    });
  };

  const handleSyncInventory = () => {
    syncInventory();
  };

  const handleSyncAll = () => {
    syncAll();
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    setLastRefresh(new Date());

    try {
      // Fetch all data sequentially to avoid overwhelming the API
      await fetchStatus();
      await new Promise(resolve => setTimeout(resolve, 500)); // Wait 500ms
      
      await fetchRealtime();
      await new Promise(resolve => setTimeout(resolve, 500));
      
      await fetchInventory();
      await new Promise(resolve => setTimeout(resolve, 500));
      
      await fetchOrders();
      await new Promise(resolve => setTimeout(resolve, 500));
      
      await fetchEmployees();
      await new Promise(resolve => setTimeout(resolve, 500));
      
      await fetchCustomers();
      
      success('Data refreshed successfully');
    } catch (err) {
      showError('Failed to refresh data', err.message);
    } finally {
      setIsRefreshing(false);
    }
  };

  const getConnectionStatus = () => {
    if (statusError) return { status: 'error', icon: <WifiOff className="h-4 w-4" />, text: 'Disconnected' };
    if (statusLoading) return { status: 'loading', icon: <LoadingSpinner size="sm" />, text: 'Connecting...' };
    if (statusData) return { status: 'connected', icon: <Wifi className="h-4 w-4" />, text: 'Connected' };
    return { status: 'unknown', icon: <WifiOff className="h-4 w-4" />, text: 'Unknown' };
  };

  const connectionStatus = getConnectionStatus();

  const isLoading = statusLoading || realtimeLoading || inventoryLoading || ordersLoading || employeesLoading || customersLoading;

  return (
    <div className="container mx-auto p-6 bg-gray-50 min-h-screen">
      <header className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Clover POS Integration</h1>
          <p className="text-gray-500">Real-time data synchronization with your Clover POS system</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            {connectionStatus.icon}
            <span className={`text-sm font-medium ${
              connectionStatus.status === 'connected' ? 'text-green-600' : 
              connectionStatus.status === 'error' ? 'text-red-600' : 
              'text-yellow-600'
            }`}>
              {connectionStatus.text}
            </span>
          </div>
          <Button 
            onClick={handleRefresh} 
            disabled={isRefreshing} 
            variant="outline" 
            size="sm"
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button
            onClick={handleSyncSales}
            disabled={salesSyncLoading}
            variant="outline"
            size="sm"
          >
            {salesSyncLoading ? 'Syncing Sales...' : 'Sync Sales'}
          </Button>
          <Button
            onClick={handleSyncAll}
            disabled={allSyncLoading}
            variant="outline"
            size="sm"
          >
            {allSyncLoading ? 'Syncing All...' : 'Sync All'}
          </Button>
        </div>
      </header>

      {lastRefresh && (
        <div className="mb-4 text-sm text-gray-500 flex items-center">
          <Clock className="mr-1 h-4 w-4" />
          Last updated: {lastRefresh.toLocaleTimeString()}
        </div>
      )}

      {/* Error Alerts */}
      {(statusError || realtimeError || inventoryError || ordersError || employeesError || customersError) && (
        <Alert variant="destructive" className="mb-6">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            Some data could not be loaded. This may be due to rate limiting or temporary API issues. 
            Please wait a moment and try refreshing again.
          </AlertDescription>
        </Alert>
      )}

      {/* Real-time Dashboard */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-700 mb-4">Real-time Dashboard</h2>
        {realtimeLoading ? (
          <Card>
            <CardContent className="flex items-center justify-center p-8">
              <LoadingSpinner size="lg" />
            </CardContent>
          </Card>
        ) : realtimeError ? (
          <Alert variant="destructive">
            <AlertDescription>Failed to load real-time data: {realtimeError}</AlertDescription>
          </Alert>
        ) : realtimeData ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Today's Sales</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  ${(realtimeData.today_sales / 100).toFixed(2)}
                </div>
                <p className="text-xs text-muted-foreground">
                  {realtimeData.today_orders} orders today
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Employees</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{realtimeData.total_employees}</div>
                <p className="text-xs text-muted-foreground">Active staff</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Low Stock Items</CardTitle>
                <Package className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{realtimeData.low_stock_items}</div>
                <p className="text-xs text-muted-foreground">Need reordering</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Last Updated</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-sm font-medium">
                  {new Date(realtimeData.last_updated).toLocaleTimeString()}
                </div>
                <p className="text-xs text-muted-foreground">Real-time sync</p>
              </CardContent>
            </Card>
          </div>
        ) : null}
      </section>

      {/* Data Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Orders */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <ShoppingCart className="mr-2 h-5 w-5" />
              Recent Orders
            </CardTitle>
            <CardDescription>Latest orders from your POS system</CardDescription>
          </CardHeader>
          <CardContent>
            {ordersLoading ? (
              <div className="flex items-center justify-center p-4">
                <LoadingSpinner size="sm" />
              </div>
            ) : ordersError ? (
              <Alert variant="destructive">
                <AlertDescription>Failed to load orders: {ordersError}</AlertDescription>
              </Alert>
            ) : ordersData?.orders ? (
              <div className="space-y-2">
                {ordersData.orders.slice(0, 5).map((order, index) => (
                  <div key={index} className="flex justify-between items-center p-2 border rounded">
                    <div>
                      <div className="font-medium">Order #{order.id}</div>
                      <div className="text-sm text-gray-500">
                        ${(order.total / 100).toFixed(2)} • {order.state}
                      </div>
                    </div>
                    <Badge variant={order.state === 'paid' ? 'default' : 'secondary'}>
                      {order.state}
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No recent orders found</p>
            )}
          </CardContent>
        </Card>

        {/* Inventory Alerts */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Package className="mr-2 h-5 w-5" />
              Inventory Alerts
            </CardTitle>
            <CardDescription>Items that need attention</CardDescription>
          </CardHeader>
          <CardContent>
            {inventoryLoading ? (
              <div className="flex items-center justify-center p-4">
                <LoadingSpinner size="sm" />
              </div>
            ) : inventoryError ? (
              <Alert variant="destructive">
                <AlertDescription>Failed to load inventory: {inventoryError}</AlertDescription>
              </Alert>
            ) : realtimeData?.inventory_alerts ? (
              <div className="space-y-2">
                {realtimeData.inventory_alerts.map((item, index) => (
                  <div key={index} className="flex justify-between items-center p-2 border rounded">
                    <div>
                      <div className="font-medium">{item.name}</div>
                      <div className="text-sm text-gray-500">
                        Stock: {item.stockCount || 0}
                      </div>
                    </div>
                    <Badge variant="destructive">Low Stock</Badge>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex items-center text-green-600">
                <CheckCircle className="mr-2 h-4 w-4" />
                <span>All inventory levels are good</span>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Employees */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Users className="mr-2 h-5 w-5" />
              Employees
            </CardTitle>
            <CardDescription>Staff information from POS</CardDescription>
          </CardHeader>
          <CardContent>
            {employeesLoading ? (
              <div className="flex items-center justify-center p-4">
                <LoadingSpinner size="sm" />
              </div>
            ) : employeesError ? (
              <Alert variant="destructive">
                <AlertDescription>Failed to load employees: {employeesError}</AlertDescription>
              </Alert>
            ) : employeesData?.employees ? (
              <div className="space-y-2">
                {employeesData.employees.slice(0, 5).map((employee, index) => (
                  <div key={index} className="flex justify-between items-center p-2 border rounded">
                    <div>
                      <div className="font-medium">{employee.firstName} {employee.lastName}</div>
                      <div className="text-sm text-gray-500">{employee.role}</div>
                    </div>
                    <Badge variant="outline">{employee.status || 'Active'}</Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No employee data available</p>
            )}
          </CardContent>
        </Card>

        {/* Customers */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Users className="mr-2 h-5 w-5" />
              Customers
            </CardTitle>
            <CardDescription>Customer information from POS</CardDescription>
          </CardHeader>
          <CardContent>
            {customersLoading ? (
              <div className="flex items-center justify-center p-4">
                <LoadingSpinner size="sm" />
              </div>
            ) : customersError ? (
              <Alert variant="destructive">
                <AlertDescription>Failed to load customers: {customersError}</AlertDescription>
              </Alert>
            ) : customersData?.customers ? (
              <div className="space-y-2">
                {customersData.customers.slice(0, 5).map((customer, index) => (
                  <div key={index} className="flex justify-between items-center p-2 border rounded">
                    <div>
                      <div className="font-medium">{customer.firstName} {customer.lastName}</div>
                      <div className="text-sm text-gray-500">{customer.email}</div>
                    </div>
                    <Badge variant="outline">Customer</Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No customer data available</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Connection Status Details */}
      <section className="mt-8">
        <Card>
          <CardHeader>
            <CardTitle>Connection Details</CardTitle>
            <CardDescription>Technical information about your Clover integration</CardDescription>
          </CardHeader>
          <CardContent>
            {statusLoading ? (
              <div className="flex items-center justify-center p-4">
                <LoadingSpinner size="sm" />
              </div>
            ) : statusError ? (
              <Alert variant="destructive">
                <AlertDescription>Connection failed: {statusError}</AlertDescription>
              </Alert>
            ) : statusData ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="font-medium mb-2">Merchant Information</h4>
                  <div className="space-y-1 text-sm">
                    <div><span className="font-medium">Name:</span> {statusData.merchant?.name || 'N/A'}</div>
                    <div><span className="font-medium">ID:</span> {statusData.merchant?.id || 'N/A'}</div>
                    <div><span className="font-medium">Status:</span> {statusData.merchant?.status || 'N/A'}</div>
                  </div>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Integration Status</h4>
                  <div className="space-y-1 text-sm">
                    <div><span className="font-medium">Mode:</span> Read-Only</div>
                    <div><span className="font-medium">Last Sync:</span> {statusData.last_sync || 'N/A'}</div>
                    <div><span className="font-medium">API Version:</span> v3</div>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-gray-500">No connection details available</p>
            )}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}; 