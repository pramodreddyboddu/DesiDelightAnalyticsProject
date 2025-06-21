import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button.jsx';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx';
import { Input } from '@/components/ui/input.jsx';
import { Label } from '@/components/ui/label.jsx';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx';
import { Alert, AlertDescription } from '@/components/ui/alert.jsx';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx';
import { DatePickerWithRange } from '@/components/ui/date-picker.jsx';
import { LoadingSpinner } from '@/components/ui/loading-spinner.jsx';
import { ToastProvider, useToast } from '@/components/ui/toast.jsx';
import { Download, Upload, FileText, Users, Tag, DollarSign, TrendingUp } from 'lucide-react';
import { useApiData, useApiMutation } from '@/hooks/use-api.js';
import { useIsMobile } from '@/hooks/use-mobile.js';
import { Toaster } from '@/components/ui/sonner.jsx';
import { AuthProvider, useAuth } from '@/hooks/use-auth.jsx';
import { LoginPage } from '@/components/LoginPage.jsx';
import { SuperAdminConsole } from '@/components/SuperAdminConsole.jsx';
import { TenantDashboard } from '@/components/TenantDashboard.jsx';

// Import the new dashboard components
import { SalesAnalyticsDashboard } from './components/SalesAnalyticsDashboard.jsx';
import { AdminPanel } from './components/AdminPanel.jsx';
import { ProfitabilityDashboard } from './components/ProfitabilityDashboard.jsx';
import { StaffPerformanceDashboard } from './components/StaffPerformanceDashboard.jsx';
import { InventoryManagement } from './components/InventoryManagement.jsx';
import { AIDashboard } from './components/AIDashboard.jsx';
import { TenantManagement } from '@/components/TenantManagement.jsx';
import { ReportsTab } from './components/ReportsTab.jsx';

import './App.css';

// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// Auth Context
const AuthContext = React.createContext();

// Login Component
const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (user) {
      navigate('/dashboard', { replace: true });
    }
  }, [user, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = await login(username, password);
    
    if (!result.success) {
      setError(result.error);
      setLoading(false);
    }
    // No need to set loading to false on success, as the component will unmount
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl text-center">PlateIQ</CardTitle>
          <CardDescription className="text-center">
            Comprehensive Grocery & Restaurant Management System
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign in'}
            </Button>
          </form>
          <div className="mt-4 text-sm text-gray-600 text-center">
            Default credentials: admin / admin123
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Navigation Component
const Navigation = ({ activeTab, onTabChange, isMobile }) => {
  const { user, logout } = useAuth();
  const isAdmin = user?.is_admin === true;

  const tabs = [
    { id: 'sales', label: 'Sales Analytics', icon: '📊' },
    { id: 'profitability', label: 'Profitability', icon: '💰' },
    { id: 'staff', label: 'Staff Performance', icon: '👥' },
    { id: 'inventory', label: 'Inventory', icon: '📦' },
    { id: 'reports', label: 'Reports', icon: '📋' },
    { id: 'ai', label: 'AI Dashboard', icon: '🤖' },
    ...(isAdmin ? [{ id: 'admin', label: 'Admin Panel', icon: '⚙️' }] : []),
    ...(isAdmin ? [{ id: 'tenants', label: 'Tenant Management', icon: '🏢' }] : []),
  ];

  if (isMobile) {
    return (
      <div className="flex flex-col space-y-2 p-4">
        {tabs.map((tab) => (
          <Button
            key={tab.id}
            variant={activeTab === tab.id ? 'default' : 'outline'}
            className="justify-start"
            onClick={() => onTabChange(tab.id)}
          >
            <span className="mr-2">{tab.icon}</span>
            {tab.label}
          </Button>
        ))}
        <Button variant="outline" onClick={logout} className="mt-4">
          Logout
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col space-y-2 p-4">
      {tabs.map((tab) => (
        <Button
          key={tab.id}
          variant={activeTab === tab.id ? 'default' : 'outline'}
          className="justify-start"
          onClick={() => onTabChange(tab.id)}
        >
          <span className="mr-2">{tab.icon}</span>
          {tab.label}
        </Button>
      ))}
      <Button variant="outline" onClick={logout} className="mt-4">
        Logout
      </Button>
    </div>
  );
};

// Dashboard Component
const Dashboard = ({ activeTab }) => {
  switch (activeTab) {
    case 'sales':
      return <SalesAnalyticsDashboard />;
    case 'profitability':
      return <ProfitabilityDashboard />;
    case 'staff':
      return <StaffPerformanceDashboard />;
    case 'inventory':
      return <InventoryManagement />;
    case 'reports':
      return <ReportsTab />;
    case 'ai':
      return <AIDashboard />;
    case 'admin':
      return <AdminPanel />;
    case 'tenants':
      return <TenantManagement />;
    default:
      return <SalesAnalyticsDashboard />;
  }
};

// Dashboard Overview Component
const DashboardOverview = ({ setActiveTab }) => {
  const [stats, setStats] = useState({
    totalSales: 0,
    totalExpenses: 0,
    netProfit: 0,
    profitMargin: 0
  });
  const [recentActivity, setRecentActivity] = useState([]);
  const [quickActions, setQuickActions] = useState([]);
  const { error: showError } = useToast();

  // Use API hooks for data fetching with caching
  const { data: salesData, loading: salesLoading, error: salesError } = useApiData('/dashboard/sales-summary', []);
  const { data: expensesData, loading: expensesLoading, error: expensesError } = useApiData('/dashboard/expenses', []);
  const { data: profitData, loading: profitLoading, error: profitError } = useApiData('/dashboard/profitability', []);
  const { data: activityData, loading: activityLoading, error: activityError } = useApiData('/dashboard/recent-activity', []);
  const { data: actionsData, loading: actionsLoading, error: actionsError } = useApiData('/dashboard/quick-actions', []);

  // Calculate loading state
  const loading = salesLoading || expensesLoading || profitLoading || activityLoading || actionsLoading;

  // Show error toasts if API calls fail
  useEffect(() => {
    if (salesError) showError('Failed to load sales data', salesError);
    if (expensesError) showError('Failed to load expenses data', expensesError);
    if (profitError) showError('Failed to load profitability data', profitError);
    if (activityError) showError('Failed to load recent activity', activityError);
    if (actionsError) showError('Failed to load quick actions', actionsError);
  }, [salesError, expensesError, profitError, activityError, actionsError, showError]);

  // Calculate stats when data is available
  useEffect(() => {
    if (salesData && expensesData && profitData) {
      const totalSales = salesData.total_revenue || 0;
      const totalExpenses = expensesData.total_expenses || 0;
      const netProfit = totalSales - totalExpenses;
      const profitMargin = totalSales > 0 ? ((netProfit / totalSales) * 100) : 0;

      setStats({
        totalSales,
        totalExpenses,
        netProfit,
        profitMargin
      });
    }
  }, [salesData, expensesData, profitData]);

  // Set recent activity and quick actions when data is available
  useEffect(() => {
    if (activityData) {
      setRecentActivity(activityData.activities || []);
    }
  }, [activityData]);

  useEffect(() => {
    if (actionsData) {
      setQuickActions(actionsData.actions || []);
    }
  }, [actionsData]);

  const handleQuickAction = (action) => {
    switch (action.id) {
      case 'upload':
        setActiveTab('admin');
        break;
      case 'report':
        setActiveTab('reports');
        break;
      case 'staff':
        setActiveTab('chef-performance');
        break;
      case 'categorize':
        setActiveTab('inventory');
        break;
      default:
        break;
    }
  };

  if (loading) {
    return <LoadingSpinner size="lg" text="Loading dashboard..." />;
  }

  return (
    <div className="p-6 space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Sales</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${stats.totalSales.toFixed(2)}</div>
            <p className="text-xs text-muted-foreground">Total Revenue</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Expenses</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${stats.totalExpenses.toFixed(2)}</div>
            <p className="text-xs text-muted-foreground">Total Costs</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Net Profit</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${stats.netProfit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              ${stats.netProfit.toFixed(2)}
            </div>
            <p className="text-xs text-muted-foreground">Total Profit</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Profit Margin</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${stats.profitMargin >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {stats.profitMargin.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">Business Efficiency</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Common tasks and operations</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {quickActions.map((action) => (
              <Button
                key={action.id}
                className={`w-full justify-start ${action.status === 'warning' ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200' : ''}`}
                onClick={() => handleQuickAction(action)}
              >
                {action.icon === 'upload' && <Upload className="w-4 h-4 mr-2" />}
                {action.icon === 'file-text' && <FileText className="w-4 h-4 mr-2" />}
                {action.icon === 'users' && <Users className="w-4 h-4 mr-2" />}
                {action.icon === 'tag' && <Tag className="w-4 h-4 mr-2" />}
                {action.label}
                {action.count > 0 && (
                  <span className="ml-2 bg-yellow-200 text-yellow-800 px-2 py-0.5 rounded-full text-xs">
                    {action.count}
                  </span>
                )}
              </Button>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>Latest system updates</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentActivity.map((activity, index) => (
                <div key={index} className="flex items-center space-x-4">
                  <div className={`w-2 h-2 rounded-full ${
                    activity.status === 'success' ? 'bg-green-500' :
                    activity.status === 'warning' ? 'bg-yellow-500' :
                    'bg-blue-500'
                  }`}></div>
                  <div className="flex-1">
                    <p className="text-sm font-medium">{activity.message}</p>
                    <p className="text-xs text-gray-500">
                      {new Date(activity.timestamp).toLocaleString('en-US', { timeZone: 'America/Chicago' })}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  console.log("ProtectedRoute - user:", user, "loading:", loading);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!user) {
    return <Navigate to="/" replace />;
  }

  return children;
};

// Main App Component (Dashboard)
const MainApp = () => {
  const [activeTab, setActiveTab] = useState('sales');
  const isMobile = useIsMobile();

  return (
    <div className={`app-container ${isMobile ? 'mobile' : ''}`}>
      <aside className="sidebar">
        <Navigation activeTab={activeTab} onTabChange={setActiveTab} isMobile={isMobile} />
      </aside>
      <main className="main-content">
        <Dashboard activeTab={activeTab} />
      </main>
    </div>
  );
};

function AppContent() {
  const { user, loading, isAuthenticated } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  const isSuperAdmin = user?.is_admin && !user?.tenant_id;

  return (
    <Router>
      <Routes>
        {/* Define the primary routes for each user type */}
        <Route path="/admin/*" element={<SuperAdminConsole />} />
        <Route path="/dashboard/*" element={<TenantDashboard />} />
        
        {/* 
          This is the key fix: The fallback route now explicitly checks the user's role.
          If a super admin lands on any non-/admin path, they are sent to /admin.
          If any other user lands on a non-/dashboard path, they are sent to /dashboard.
        */}
        <Route
          path="*"
          element={<Navigate to={isSuperAdmin ? "/admin" : "/dashboard"} replace />}
        />
      </Routes>
    </Router>
  );
}

const App = () => {
  return (
    <ToastProvider>
      <AuthProvider>
        <AppContent />
        <Toaster />
      </AuthProvider>
    </ToastProvider>
  );
};

export default App;