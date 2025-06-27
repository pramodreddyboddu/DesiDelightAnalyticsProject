import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx';
import { Button } from '@/components/ui/button.jsx';
import { Input } from '@/components/ui/input.jsx';
import { Label } from '@/components/ui/label.jsx';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx';
import { LoadingSpinner } from '@/components/ui/loading-spinner.jsx';
import { useToast } from '@/components/ui/toast.jsx';
import { useApiData, useApiMutation } from '@/hooks/use-api.js';
import { Badge } from '@/components/ui/badge.jsx';
import { 
  Building2, 
  Users, 
  CreditCard, 
  TrendingUp, 
  Plus, 
  Edit, 
  Eye,
  Calendar,
  DollarSign,
  AlertTriangle
} from 'lucide-react';
import { Alert, AlertDescription } from "@/components/ui/alert"

export const TenantManagement = () => {
  const [tenants, setTenants] = useState([]);
  const [selectedTenant, setSelectedTenant] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [newTenantCredentials, setNewTenantCredentials] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    business_type: '',
    contact_email: '',
    contact_phone: '',
    address: '',
    city: '',
    state: '',
    country: 'US',
    postal_code: '',
    subscription_plan: 'free'
  });
  
  const { success, error: showError } = useToast();

  // Fetch tenants data
  const { data: tenantsData, loading: tenantsLoading, refresh: refreshTenants } = useApiData('tenant/tenants');
  
  // Create tenant mutation
  const { mutate: createTenant, loading: creatingTenant } = useApiMutation('tenant/tenants', {
    onSuccess: (data) => {
      success('Tenant Created', 'New tenant has been created successfully');
      setShowCreateForm(false);
      setNewTenantCredentials(data.data.admin_credentials);
      resetForm();
      refreshTenants();
    },
    onError: (error) => {
      showError('Creation Failed', error.message || 'Failed to create tenant');
    }
  });

  // Update tenant mutation
  const { mutate: updateTenant, loading: updatingTenant } = useApiMutation(`tenant/tenants/${selectedTenant?.id}`, {
    method: 'PUT',
    onSuccess: () => {
      success('Tenant Updated', 'Tenant has been updated successfully');
      setShowEditForm(false);
      setSelectedTenant(null);
      refreshTenants();
    },
    onError: (error) => {
      showError('Update Failed', error.message || 'Failed to update tenant');
    }
  });

  useEffect(() => {
    if (tenantsData?.data) {
      setTenants(tenantsData.data);
    }
  }, [tenantsData]);

  const resetForm = () => {
    setFormData({
      name: '',
      business_type: '',
      contact_email: '',
      contact_phone: '',
      address: '',
      city: '',
      state: '',
      country: 'US',
      postal_code: '',
      subscription_plan: 'free'
    });
  };

  const handleCreateTenant = () => {
    createTenant(formData);
  };

  const handleUpdateTenant = () => {
    updateTenant(formData);
  };

  const handleEditTenant = (tenant) => {
    setSelectedTenant(tenant);
    setFormData({
      name: tenant.name,
      business_type: tenant.business_type,
      contact_email: tenant.contact_email,
      contact_phone: tenant.contact_phone || '',
      address: tenant.address || '',
      city: tenant.city || '',
      state: tenant.state || '',
      country: tenant.country || 'US',
      postal_code: tenant.postal_code || '',
      subscription_plan: tenant.subscription_plan
    });
    setShowEditForm(true);
  };

  const getPlanBadgeColor = (plan) => {
    switch (plan) {
      case 'free': return 'bg-gray-100 text-gray-800';
      case 'basic': return 'bg-blue-100 text-blue-800';
      case 'premium': return 'bg-purple-100 text-purple-800';
      case 'enterprise': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusBadgeColor = (status) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'suspended': return 'bg-red-100 text-red-800';
      case 'cancelled': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (tenantsLoading) {
    return <LoadingSpinner size="lg" text="Loading tenants..." />;
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Tenant Management</h2>
        <Button 
          onClick={() => setShowCreateForm(true)}
          className="bg-blue-600 hover:bg-blue-700"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add New Tenant
        </Button>
      </div>

      {newTenantCredentials && (
        <Alert>
          <AlertDescription>
            <strong className="font-bold">Tenant Created Successfully!</strong>
            <p>Please save the following credentials for the new tenant administrator:</p>
            <div className="mt-2 p-2 bg-gray-100 rounded">
              <p><strong>Username:</strong> {newTenantCredentials.username}</p>
              <p><strong>Password:</strong> {newTenantCredentials.password}</p>
            </div>
            <Button variant="outline" size="sm" className="mt-2" onClick={() => setNewTenantCredentials(null)}>
              Dismiss
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Tenants</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{tenants.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Tenants</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {tenants.filter(t => t.subscription_status === 'active').length}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Premium Plans</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {tenants.filter(t => ['premium', 'enterprise'].includes(t.subscription_plan)).length}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Trial Users</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {tenants.filter(t => t.is_trial).length}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tenants List */}
      <Card>
        <CardHeader>
          <CardTitle>All Tenants</CardTitle>
          <CardDescription>Manage your SaaS tenants and their subscriptions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {tenants.map((tenant) => (
              <div key={tenant.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-4">
                  <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                    <Building2 className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold">{tenant.name}</h3>
                    <p className="text-sm text-gray-600">{tenant.contact_email}</p>
                    <p className="text-xs text-gray-500 mt-1">ID: {tenant.id}</p>
                    <div className="flex items-center space-x-2 mt-1">
                      <Badge className={getPlanBadgeColor(tenant.subscription_plan)}>
                        {tenant.subscription_plan}
                      </Badge>
                      <Badge className={getStatusBadgeColor(tenant.subscription_status)}>
                        {tenant.subscription_status}
                      </Badge>
                      {tenant.is_trial && (
                        <Badge className="bg-yellow-100 text-yellow-800">
                          Trial
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleEditTenant(tenant)}
                  >
                    <Edit className="w-4 h-4 mr-2" />
                    Edit
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedTenant(tenant)}
                  >
                    <Eye className="w-4 h-4 mr-2" />
                    View
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Create Tenant Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-2xl mx-4">
            <CardHeader>
              <CardTitle>Create New Tenant</CardTitle>
              <CardDescription>Add a new restaurant, food truck, or business to your platform</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="name">Business Name</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    placeholder="Restaurant Name"
                  />
                </div>
                <div>
                  <Label htmlFor="business_type">Business Type</Label>
                  <Select value={formData.business_type} onValueChange={(value) => setFormData({...formData, business_type: value})}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select business type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="restaurant">Restaurant</SelectItem>
                      <SelectItem value="food_truck">Food Truck</SelectItem>
                      <SelectItem value="cafe">Cafe</SelectItem>
                      <SelectItem value="bakery">Bakery</SelectItem>
                      <SelectItem value="catering">Catering</SelectItem>
                      <SelectItem value="other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="contact_email">Contact Email</Label>
                  <Input
                    id="contact_email"
                    type="email"
                    value={formData.contact_email}
                    onChange={(e) => setFormData({...formData, contact_email: e.target.value})}
                    placeholder="contact@business.com"
                  />
                </div>
                <div>
                  <Label htmlFor="contact_phone">Contact Phone</Label>
                  <Input
                    id="contact_phone"
                    value={formData.contact_phone}
                    onChange={(e) => setFormData({...formData, contact_phone: e.target.value})}
                    placeholder="+1 (555) 123-4567"
                  />
                </div>
                <div>
                  <Label htmlFor="subscription_plan">Subscription Plan</Label>
                  <Select value={formData.subscription_plan} onValueChange={(value) => setFormData({...formData, subscription_plan: value})}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select plan" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="free">Free (30-day trial)</SelectItem>
                      <SelectItem value="basic">Basic ($29/month)</SelectItem>
                      <SelectItem value="premium">Premium ($79/month)</SelectItem>
                      <SelectItem value="enterprise">Enterprise (Custom)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setShowCreateForm(false)}>
                  Cancel
                </Button>
                <Button 
                  onClick={handleCreateTenant}
                  disabled={creatingTenant}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {creatingTenant ? 'Creating...' : 'Create Tenant'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Edit Tenant Modal */}
      {showEditForm && selectedTenant && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-2xl mx-4">
            <CardHeader>
              <CardTitle>Edit Tenant</CardTitle>
              <CardDescription>Update tenant information and subscription</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="edit_name">Business Name</Label>
                  <Input
                    id="edit_name"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                  />
                </div>
                <div>
                  <Label htmlFor="edit_business_type">Business Type</Label>
                  <Select value={formData.business_type} onValueChange={(value) => setFormData({...formData, business_type: value})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="restaurant">Restaurant</SelectItem>
                      <SelectItem value="food_truck">Food Truck</SelectItem>
                      <SelectItem value="cafe">Cafe</SelectItem>
                      <SelectItem value="bakery">Bakery</SelectItem>
                      <SelectItem value="catering">Catering</SelectItem>
                      <SelectItem value="other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="edit_contact_email">Contact Email</Label>
                  <Input
                    id="edit_contact_email"
                    type="email"
                    value={formData.contact_email}
                    onChange={(e) => setFormData({...formData, contact_email: e.target.value})}
                  />
                </div>
                <div>
                  <Label htmlFor="edit_contact_phone">Contact Phone</Label>
                  <Input
                    id="edit_contact_phone"
                    value={formData.contact_phone}
                    onChange={(e) => setFormData({...formData, contact_phone: e.target.value})}
                  />
                </div>
                <div>
                  <Label htmlFor="edit_subscription_plan">Subscription Plan</Label>
                  <Select value={formData.subscription_plan} onValueChange={(value) => setFormData({...formData, subscription_plan: value})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="free">Free</SelectItem>
                      <SelectItem value="basic">Basic ($29/month)</SelectItem>
                      <SelectItem value="premium">Premium ($79/month)</SelectItem>
                      <SelectItem value="enterprise">Enterprise (Custom)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setShowEditForm(false)}>
                  Cancel
                </Button>
                <Button 
                  onClick={handleUpdateTenant}
                  disabled={updatingTenant}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {updatingTenant ? 'Updating...' : 'Update Tenant'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}; 