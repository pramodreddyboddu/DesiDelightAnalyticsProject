import React from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx';
import { Button } from '@/components/ui/button.jsx';
import { Badge } from '@/components/ui/badge.jsx';
import { useAuth } from '@/hooks/use-auth.jsx';
import { useApiData } from '@/hooks/use-api.js';
import { LoadingSpinner } from '@/components/ui/loading-spinner.jsx';
import { 
  BarChart3, 
  Package, 
  Users, 
  FileText, 
  Settings, 
  Building2,
  LogOut,
  Upload,
  TrendingUp,
  DollarSign,
  AlertTriangle
} from 'lucide-react';

// Import existing dashboard components
import { SalesAnalyticsDashboard } from './SalesAnalyticsDashboard.jsx';
import { InventoryManagement } from './InventoryManagement.jsx';
import { StaffPerformanceDashboard } from './StaffPerformanceDashboard.jsx';
import { ReportsTab } from './ReportsTab.jsx';
import { AdminPanel } from './AdminPanel.jsx';
import { AIDashboard } from './AIDashboard.jsx';
import { ProfitabilityDashboard } from './ProfitabilityDashboard.jsx';
import { UserManagement } from './UserManagement.jsx';

const API_BASE_URL = 'http://localhost:5000/api';

export const TenantDashboard = () => {
  const { user, logout, loading: authLoading } = useAuth();
  const location = useLocation();
  
  // Fetch tenant-specific data
  const { data: tenantData, loading: tenantLoading } = useApiData(
    user?.tenant_id ? `/tenant/tenants/${user.tenant_id}` : null
  );
  
  // Fetch tenant-specific statistics
  const { data: tenantStats, loading: statsLoading } = useApiData('/dashboard/stats', {});
  
  // Determine user role and permissions - only after auth is loaded
  const isTenantAdmin = !authLoading && user?.is_admin && user?.tenant_id;
  const isRegularUser = !authLoading && !user?.is_admin && user?.tenant_id;
  
  // Show loading spinner while authentication or tenant data is being checked
  if (authLoading || tenantLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" text="Loading restaurant data..." />
      </div>
    );
  }
  
  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: BarChart3 },
    { name: 'Sales Analytics', href: '/dashboard/sales', icon: TrendingUp },
    { name: 'Inventory', href: '/dashboard/inventory', icon: Package },
    { name: 'Staff Performance', href: '/dashboard/staff', icon: Users },
    { name: 'Reports', href: '/dashboard/reports', icon: FileText },
    { name: 'AI Insights', href: '/dashboard/ai', icon: BarChart3 },
    { name: 'Profitability', href: '/dashboard/profitability', icon: DollarSign },
    // Admin-only features
    ...(isTenantAdmin ? [
      { name: 'Admin Panel', href: '/dashboard/admin', icon: Settings },
      { name: 'User Management', href: '/dashboard/users', icon: Users },
    ] : []),
  ];

  const handleLogout = () => {
    logout();
  };

  if (statsLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" text="Loading dashboard data..." />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <Building2 className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-xl font-semibold text-gray-900">
                  {tenantData?.data?.name ? `${tenantData.data.name} Dashboard` : 'Restaurant Dashboard'}
                </h1>
                <p className="text-sm text-gray-500">
                  {isTenantAdmin ? 'Restaurant Admin' : 'Restaurant Staff'}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant="outline" className={isTenantAdmin ? "bg-blue-50 text-blue-700" : "bg-gray-50 text-gray-700"}>
                {isTenantAdmin ? 'Admin' : 'Staff'}
              </Badge>
              <span className="text-sm text-gray-700">{user?.username}</span>
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                <LogOut className="h-4 w-4 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar Navigation */}
          <div className="lg:col-span-1">
            <nav className="space-y-2">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                      isActive
                        ? 'bg-blue-50 text-blue-700 border border-blue-200'
                        : 'text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <item.icon className="h-5 w-5 mr-3" />
                    {item.name}
                  </Link>
                );
              })}
            </nav>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            <Routes>
              <Route index element={<RestaurantOverview tenantStats={tenantStats} />} />
              <Route path="sales" element={<SalesAnalyticsDashboard />} />
              <Route path="inventory" element={<InventoryManagement />} />
              <Route path="staff" element={<StaffPerformanceDashboard />} />
              <Route path="reports" element={<ReportsTab />} />
              <Route path="ai" element={<AIDashboard />} />
              <Route path="profitability" element={<ProfitabilityDashboard />} />
              {isTenantAdmin && (
                <>
                  <Route path="admin" element={<AdminPanel />} />
                  <Route path="users" element={<UserManagement />} />
                </>
              )}
            </Routes>
          </div>
        </div>
      </div>
    </div>
  );
};

// Restaurant Overview Component
const RestaurantOverview = ({ tenantStats }) => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Restaurant Overview</h2>
        <p className="text-gray-600">Monitor your restaurant's performance and key metrics</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Today's Sales</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${tenantStats?.today_sales || 0}</div>
            <p className="text-xs text-muted-foreground">
              <TrendingUp className="inline h-3 w-3 text-green-500 mr-1" />
              +{tenantStats?.sales_growth || 0}% from yesterday
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Orders Today</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{tenantStats?.today_orders || 0}</div>
            <p className="text-xs text-muted-foreground">
              Average order: ${tenantStats?.avg_order_value || 0}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Staff</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{tenantStats?.active_staff || 0}</div>
            <p className="text-xs text-muted-foreground">
              {tenantStats?.total_staff || 0} total staff members
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Low Stock Items</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{tenantStats?.low_stock_items || 0}</div>
            <p className="text-xs text-muted-foreground">
              Need reordering
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common restaurant management tasks</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button className="w-full" asChild>
              <Link to="/dashboard/inventory">
                <Package className="h-4 w-4 mr-2" />
                Manage Inventory
              </Link>
            </Button>
            <Button variant="outline" className="w-full" asChild>
              <Link to="/dashboard/ai">
                <BarChart3 className="h-4 w-4 mr-2" />
                AI Insights
              </Link>
            </Button>
            <Button variant="outline" className="w-full" asChild>
              <Link to="/dashboard/reports">
                <FileText className="h-4 w-4 mr-2" />
                View Reports
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Latest restaurant activities and updates</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {tenantStats?.recent_activity?.map((activity, index) => (
              <div key={index} className="flex items-center space-x-4">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <div className="flex-1">
                  <p className="text-sm font-medium">{activity.description}</p>
                  <p className="text-xs text-gray-500">{activity.timestamp}</p>
                </div>
                <Badge variant="outline" className="text-xs">
                  {activity.type}
                </Badge>
              </div>
            )) || (
              <p className="text-gray-500 text-center py-4">No recent activity</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}; 