import React from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx';
import { Button } from '@/components/ui/button.jsx';
import { Badge } from '@/components/ui/badge.jsx';
import { useAuth } from '@/hooks/use-auth.jsx';
import { useApiData } from '@/hooks/use-api.js';
import { LoadingSpinner } from '@/components/ui/loading-spinner.jsx';
import { 
  Building2, 
  Users, 
  BarChart3, 
  Settings, 
  DollarSign, 
  Shield,
  LogOut,
  Plus,
  TrendingUp,
  AlertTriangle
} from 'lucide-react';

// Import sub-components
import { TenantManagement } from './TenantManagement.jsx';
import { UserManagement } from './UserManagement.jsx';
import { BillingManagement } from './BillingManagement.jsx';
import { SystemSettings } from './SystemSettings.jsx';
import DataSourceConfig from './DataSourceConfig.jsx';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

export const SuperAdminConsole = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  
  // Fetch system-wide statistics
  const { data: systemStats, loading: statsLoading } = useApiData('/api/admin/system-stats', {});
  
  const navigation = [
    { name: 'Dashboard', href: '/admin', icon: BarChart3 },
    { name: 'Tenants', href: '/admin/tenants', icon: Building2 },
    { name: 'Users', href: '/admin/users', icon: Users },
    { name: 'Billing', href: '/admin/billing', icon: DollarSign },
    { name: 'Settings', href: '/admin/settings', icon: Settings },
  ];

  const handleLogout = () => {
    logout();
  };

  if (statsLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
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
              <Shield className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-xl font-semibold text-gray-900">PlateIQ</h1>
                <p className="text-sm text-gray-500">Super Admin Console</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant="outline" className="bg-green-50 text-green-700">
                Super Admin
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
              {user?.is_admin && !user?.tenant_id && (
                <Link
                  to="/admin/data-source-config"
                  className={`flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                    location.pathname === '/admin/data-source-config'
                      ? 'bg-blue-50 text-blue-700 border border-blue-200'
                      : 'text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <Building2 className="h-5 w-5 mr-3" />
                  Data Source Config
                </Link>
              )}
            </nav>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            <Routes>
              <Route index element={<SuperAdminDashboard systemStats={systemStats} />} />
              <Route path="tenants" element={<TenantManagement />} />
              <Route path="users" element={<UserManagement />} />
              <Route path="billing" element={<BillingManagement />} />
              <Route path="settings" element={<SystemSettings />} />
              {user?.is_admin && !user?.tenant_id && (
                <Route path="/admin/data-source-config" element={<DataSourceConfig />} />
              )}
            </Routes>
          </div>
        </div>
      </div>
    </div>
  );
};

// Super Admin Dashboard Component
const SuperAdminDashboard = ({ systemStats }) => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">System Overview</h2>
        <p className="text-gray-600">Monitor all tenants and system performance</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Tenants</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemStats?.total_tenants || 0}</div>
            <p className="text-xs text-muted-foreground">
              {systemStats?.active_tenants || 0} active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemStats?.total_users || 0}</div>
            <p className="text-xs text-muted-foreground">
              {systemStats?.active_users || 0} active this month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Monthly Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${systemStats?.monthly_revenue || 0}</div>
            <p className="text-xs text-muted-foreground">
              <TrendingUp className="inline h-3 w-3 text-green-500 mr-1" />
              +{systemStats?.revenue_growth || 0}% from last month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Health</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">98%</div>
            <p className="text-xs text-muted-foreground">
              Uptime this month
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common administrative tasks</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button className="w-full" asChild>
              <Link to="/admin/tenants">
                <Plus className="h-4 w-4 mr-2" />
                Add New Tenant
              </Link>
            </Button>
            <Button variant="outline" className="w-full" asChild>
              <Link to="/admin/billing">
                <DollarSign className="h-4 w-4 mr-2" />
                Review Billing
              </Link>
            </Button>
            <Button variant="outline" className="w-full" asChild>
              <Link to="/admin/settings">
                <Settings className="h-4 w-4 mr-2" />
                System Settings
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Latest system events and tenant activities</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {systemStats?.recent_activity?.map((activity, index) => (
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