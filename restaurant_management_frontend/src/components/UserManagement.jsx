import React, { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/use-auth';
import { useApiData, useApiMutation } from '@/hooks/use-api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/components/ui/toast';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { Badge } from '@/components/ui/badge';
import { UserPlus, Users, Trash2 } from 'lucide-react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

const UserForm = ({ onUserAdded, tenantId }) => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('user');
  const { error: showError, success: showSuccess } = useToast();

  const { mutate: createUser, loading, error } = useApiMutation('/auth/register', {
    onSuccess: () => {
      showSuccess('User Created', `User "${username}" has been created successfully.`);
      setUsername('');
      setEmail('');
      setPassword('');
      setRole('user');
      onUserAdded();
    },
    onError: (err) => {
        showError('Error Creating User', err.error || 'An unexpected error occurred.');
    },
    invalidateCache: tenantId ? `/tenant/tenants/${tenantId}/users` : '/admin/users'
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!username || !password || !email) {
      showError('Missing Fields', 'Please fill out all required fields.');
      return;
    }
    createUser({ username, email, password, role });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <UserPlus className="h-5 w-5 mr-2" />
          Create New User
        </CardTitle>
        <CardDescription>Add a new staff member or admin to your restaurant.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input id="username" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="e.g., john.doe" required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="e.g., john.doe@example.com" required />
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Set a temporary password" required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="role">Role</Label>
              <Select value={role} onValueChange={setRole}>
                <SelectTrigger id="role">
                  <SelectValue placeholder="Select a role" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="user">Staff</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          {error && <p className="text-sm text-red-500">{error.error}</p>}
          <div className="flex justify-end">
            <Button type="submit" disabled={loading}>
              {loading ? <LoadingSpinner size="sm" /> : 'Create User'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

const UserList = ({ users, loading, onUserDeleted, tenantId }) => {
    const { user: currentUser } = useAuth();
    const { success: showSuccess, error: showError } = useToast();
    const isSuperAdmin = currentUser?.is_admin && !currentUser?.tenant_id;

    const { mutate: deleteUser, loading: deleteLoading } = useApiMutation(
        (userId) => `/admin/users/${userId}`, // Use the super admin route for deletion
        {
            method: 'DELETE',
            onSuccess: () => {
                showSuccess('User Deleted', 'The user has been successfully deleted.');
                onUserDeleted();
            },
            onError: (err) => {
                showError('Error Deleting User', err.error || 'An unexpected error occurred.');
            },
            invalidateCache: isSuperAdmin ? '/admin/users' : `/tenant/tenants/${tenantId}/users`
        }
    );

    const handleDelete = (userId) => {
        deleteUser(userId);
    };

    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center">
                    <Users className="h-5 w-5 mr-2" />
                    Current Users
                </CardTitle>
                <CardDescription>A list of all users for this {isSuperAdmin ? 'system' : 'restaurant'}.</CardDescription>
            </CardHeader>
            <CardContent>
                {loading ? (
                    <div className="flex justify-center items-center h-40">
                        <LoadingSpinner />
                    </div>
                ) : (
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Username</TableHead>
                                <TableHead>Email</TableHead>
                                {isSuperAdmin && <TableHead>Tenant</TableHead>}
                                <TableHead>Role</TableHead>
                                <TableHead>Date Joined</TableHead>
                                <TableHead className="text-right">Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {users && users.length > 0 ? (
                                users.map((user) => (
                                    <TableRow key={user.id}>
                                        <TableCell className="font-medium">{user.username}</TableCell>
                                        <TableCell>{user.email}</TableCell>
                                        {isSuperAdmin && <TableCell>{user.tenant?.name || 'System'}</TableCell>}
                                        <TableCell>
                                            <Badge variant={user.is_admin ? 'default' : 'secondary'}>
                                                {user.is_admin ? 'Admin' : 'Staff'}
                                            </Badge>
                                        </TableCell>
                                        <TableCell>{new Date(user.created_at).toLocaleDateString()}</TableCell>
                                        <TableCell className="text-right">
                                            {user.id !== currentUser.id && (
                                                <AlertDialog>
                                                    <AlertDialogTrigger asChild>
                                                        <Button variant="ghost" size="icon" disabled={deleteLoading}>
                                                            <Trash2 className="h-4 w-4 text-red-500" />
                                                        </Button>
                                                    </AlertDialogTrigger>
                                                    <AlertDialogContent>
                                                        <AlertDialogHeader>
                                                            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
                                                            <AlertDialogDescription>
                                                                This action cannot be undone. This will permanently delete the user account for <span className="font-bold">{user.username}</span>.
                                                            </AlertDialogDescription>
                                                        </AlertDialogHeader>
                                                        <AlertDialogFooter>
                                                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                                                            <AlertDialogAction
                                                                onClick={() => handleDelete(user.id)}
                                                                className="bg-red-600 hover:bg-red-700"
                                                            >
                                                                {deleteLoading ? <LoadingSpinner size="sm" /> : 'Delete User'}
                                                            </AlertDialogAction>
                                                        </AlertDialogFooter>
                                                    </AlertDialogContent>
                                                </AlertDialog>
                                            )}
                                        </TableCell>
                                    </TableRow>
                                ))
                            ) : (
                                <TableRow>
                                    <TableCell colSpan={isSuperAdmin ? 6 : 5} className="text-center">No users found.</TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                )}
            </CardContent>
        </Card>
    );
};

export const UserManagement = () => {
  const { user } = useAuth();
  const isSuperAdmin = user?.is_admin && !user?.tenant_id;
  const isTenantAdmin = user?.is_admin && !!user?.tenant_id;

  const usersApiUrl = isSuperAdmin
    ? '/admin/users'
    : isTenantAdmin
    ? `/tenant/tenants/${user.tenant_id}/users`
    : null;

  const { data: userData, loading, error, refresh } = useApiData(usersApiUrl);

  const { error: showError } = useToast();
  useEffect(() => {
    if(error) {
        showError('Error fetching users', error.message || 'Could not load user data.');
    }
  }, [error, showError]);

  // Determine the correct data source, which might be nested under 'data' or be the array itself
  const users = userData?.data || userData || [];

  return (
    <div className="space-y-6">
      {/* Only show user creation form for admins. Super admins need a different UI to select a tenant. */}
      {isTenantAdmin && <UserForm onUserAdded={refresh} tenantId={user?.tenant_id} />}
      <UserList users={users} loading={loading} onUserDeleted={refresh} tenantId={user?.tenant_id} />
    </div>
  );
}; 