import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Button } from '@/components/ui/button.jsx';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx';
import { Input } from '@/components/ui/input.jsx';
import { Label } from '@/components/ui/label.jsx';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx';
import { Alert, AlertDescription } from '@/components/ui/alert.jsx';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx';
import { DatePickerWithRange } from '@/components/ui/date-picker.jsx';
import { Download } from 'lucide-react';

// Import the new dashboard components
import { SalesAnalyticsDashboard } from './components/SalesAnalyticsDashboard.jsx';
import { AdminPanel } from './components/AdminPanel.jsx';
import { ProfitabilityDashboard } from './components/ProfitabilityDashboard.jsx';
import { StaffPerformanceDashboard } from './components/StaffPerformanceDashboard.jsx';
import { InventoryManagement } from './components/InventoryManagement.jsx';

import { 
  DollarSign, 
  TrendingUp, 
  TrendingDown, 
  BarChart3, 
  Upload, 
  FileText, 
  Users, 
  Tag,
  CheckCircle,
  AlertCircle,
  LogOut,
  Menu,
  X
} from 'lucide-react';
import './App.css';

// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// Auth Context
const AuthContext = React.createContext();

const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Auth Provider
const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setUser(data);
      } else {
        setUser(null);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        const error = await response.json();
        return { success: false, error: error.message || 'Invalid credentials' };
      }

      const userData = await response.json();
      setUser(userData);
      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: 'Network error' };
    }
  };

  const logout = async () => {
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        credentials: 'include'
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Login Component
const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = await login(username, password);
    
    if (!result.success) {
      setError(result.error);
    }
    
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl text-center">FreshMart Analytics</CardTitle>
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
const Navigation = ({ activeTab, setActiveTab }) => {
  const { user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  console.log('Navigation user:', user); // Debug log

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
    { id: 'sales', label: 'Sales Analytics', icon: DollarSign },
    { id: 'chef-performance', label: 'Chef Performance', icon: Users },
    { id: 'profitability', label: 'Profitability', icon: TrendingUp },
    { id: 'inventory', label: 'Inventory', icon: FileText },
    { id: 'reports', label: 'Reports & Export', icon: FileText },
  ];

  if (user?.role === 'admin') {
    console.log('Adding admin panel tab'); // Debug log
    navItems.push({ id: 'admin', label: 'Admin Panel', icon: Upload });
  }

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <h1 className="text-xl font-bold text-gray-900">FreshMart Analytics</h1>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveTab(item.id)}
                    className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                      activeTab === item.id
                        ? 'border-blue-500 text-gray-900'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                    style={{ minWidth: 0, paddingLeft: '4px', paddingRight: '4px' }}
                  >
                    <Icon className="w-4 h-4 mr-1" />
                    {item.label}
                  </button>
                );
              })}
            </div>
          </div>
          <div className="hidden sm:ml-6 sm:flex sm:items-center">
            <span className="text-sm text-gray-700 mr-4">Welcome, {user?.username}</span>
            <Button variant="outline" size="sm" onClick={logout}>
              <LogOut className="w-4 h-4 mr-2" />
              Logout
            </Button>
          </div>
          <div className="sm:hidden flex items-center">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="sm:hidden">
          <div className="pt-2 pb-3 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setActiveTab(item.id);
                    setMobileMenuOpen(false);
                  }}
                  className={`block pl-3 pr-4 py-2 border-l-4 text-base font-medium w-full text-left ${
                    activeTab === item.id
                      ? 'bg-blue-50 border-blue-500 text-blue-700'
                      : 'border-transparent text-gray-600 hover:text-gray-800 hover:bg-gray-50 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4 inline mr-2" />
                  {item.label}
                </button>
              );
            })}
            <div className="border-t border-gray-200 pt-4 pb-3">
              <div className="flex items-center px-4">
                <div className="text-base font-medium text-gray-800">{user?.username}</div>
              </div>
              <div className="mt-3 space-y-1">
                <button
                  onClick={logout}
                  className="block px-4 py-2 text-base font-medium text-gray-500 hover:text-gray-800 hover:bg-gray-100 w-full text-left"
                >
                  <LogOut className="w-4 h-4 inline mr-2" />
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
};

// Dashboard Overview Component
const DashboardOverview = ({ setActiveTab }) => {
  const [stats, setStats] = useState({
    totalSales: 0,
    totalExpenses: 0,
    netProfit: 0,
    profitMargin: 0
  });
  const [loading, setLoading] = useState(true);
  const [recentActivity, setRecentActivity] = useState([]);
  const [quickActions, setQuickActions] = useState([]);

  useEffect(() => {
    fetchDashboardStats();
    fetchRecentActivity();
    fetchQuickActions();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      // Fetch sales summary
      const salesResponse = await fetch(`${API_BASE_URL}/dashboard/sales-summary`, {
        credentials: 'include'
      });
      const salesData = await salesResponse.json();

      // Fetch expenses
      const expensesResponse = await fetch(`${API_BASE_URL}/dashboard/expenses`, {
        credentials: 'include'
      });
      const expensesData = await expensesResponse.json();

      // Fetch profitability
      const profitResponse = await fetch(`${API_BASE_URL}/dashboard/profitability`, {
        credentials: 'include'
      });
      const profitData = await profitResponse.json();

      // Calculate net profit and margin from new structure
      const totalSales = profitData.total_sales || 0;
      const totalExpenses = profitData.total_expenses || 0;
      const netProfit = totalSales - totalExpenses;
      const profitMargin = totalSales > 0 ? ((netProfit / totalSales) * 100) : 0;

      setStats({
        totalSales: salesData.total_revenue || 0,
        totalExpenses: expensesData.total_expenses || 0,
        netProfit,
        profitMargin
      });
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRecentActivity = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/dashboard/recent-activity`, {
        credentials: 'include'
      });
      const data = await response.json();
      setRecentActivity(data.activities || []);
    } catch (error) {
      console.error('Error fetching recent activity:', error);
    }
  };

  const fetchQuickActions = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/dashboard/quick-actions`, {
        credentials: 'include'
      });
      const data = await response.json();
      setQuickActions(data.actions || []);
    } catch (error) {
      console.error('Error fetching quick actions:', error);
    }
  };

  const handleQuickAction = (action) => {
    switch (action.id) {
      case 'upload':
        // Navigate to admin panel
        setActiveTab('admin');
        break;
      case 'report':
        // Navigate to reports
        setActiveTab('reports');
        break;
      case 'staff':
        // Navigate to staff performance
        setActiveTab('chef-performance');
        break;
      case 'categorize':
        // Navigate to inventory management
        setActiveTab('inventory');
        break;
      default:
        break;
    }
  };

  if (loading) {
    return <div className="p-6">Loading dashboard...</div>;
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

// Placeholder components for other tabs
const SalesTab = () => <SalesAnalyticsDashboard />;

const ChefPerformanceTab = () => <StaffPerformanceDashboard />;

const ProfitabilityTab = () => <ProfitabilityDashboard />;

const InventoryTab = () => <InventoryManagement />;

// Reports Tab Component
const ReportsTab = () => {
  const [dateRange, setDateRange] = useState({ from: null, to: null });
  const [selectedReport, setSelectedReport] = useState('sales');
  const [loading, setLoading] = useState(false);

  const handleExport = async (format) => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (dateRange.from) params.append('start_date', dateRange.from.toISOString());
      if (dateRange.to) params.append('end_date', dateRange.to.toISOString());
      params.append('format', format);

      const response = await fetch(`${API_BASE_URL}/reports/${selectedReport}?${params}`, {
        credentials: 'include'
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `${selectedReport}_report.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Error exporting report:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Reports & Export</h2>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Generate Report</CardTitle>
          <CardDescription>Select report type and date range to generate comprehensive business reports</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label>Report Type</Label>
              <Select value={selectedReport} onValueChange={setSelectedReport}>
                <SelectTrigger>
                  <SelectValue placeholder="Select report type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="sales">Sales Report</SelectItem>
                  <SelectItem value="profitability">Profitability Report</SelectItem>
                  <SelectItem value="chef-performance">Chef Performance Report</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Date Range</Label>
              <DatePickerWithRange date={dateRange} setDate={setDateRange} />
            </div>
          </div>

          <div className="flex space-x-2">
            <Button 
              variant="outline" 
              onClick={() => handleExport('csv')}
              disabled={loading}
            >
              <Download className="w-4 h-4 mr-2" />
              Export CSV
            </Button>
            <Button 
              variant="outline" 
              onClick={() => handleExport('excel')}
              disabled={loading}
            >
              <Download className="w-4 h-4 mr-2" />
              Export Excel
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Report Types</CardTitle>
          <CardDescription>Available report types and their contents</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h3 className="font-semibold">Sales Report</h3>
              <p className="text-sm text-gray-600">
                Comprehensive sales data including item details, quantities, revenue, discounts, and taxes.
              </p>
            </div>
            <div>
              <h3 className="font-semibold">Profitability Report</h3>
              <p className="text-sm text-gray-600">
                Detailed analysis of sales, expenses, and profit margins across different categories.
              </p>
            </div>
            <div>
              <h3 className="font-semibold">Chef Performance Report</h3>
              <p className="text-sm text-gray-600">
                Performance metrics for chefs including sales attribution, dish popularity, and revenue analysis.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

const AdminTab = () => <AdminPanel />;

// Main App Component
const MainApp = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const { user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardOverview setActiveTab={setActiveTab} />;
      case 'sales':
        return <SalesTab />;
      case 'chef-performance':
        return <ChefPerformanceTab />;
      case 'profitability':
        return <ProfitabilityTab />;
      case 'inventory':
        return <InventoryTab />;
      case 'reports':
        return <ReportsTab />;
      case 'admin':
        return <AdminTab />;
      default:
        return <DashboardOverview setActiveTab={setActiveTab} />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation activeTab={activeTab} setActiveTab={setActiveTab} />
      <main className="max-w-7xl mx-auto">
        {renderContent()}
      </main>
    </div>
  );
};

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  return user ? children : <Login />;
};

// Main App
function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/" element={
              <ProtectedRoute>
                <MainApp />
              </ProtectedRoute>
            } />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;

