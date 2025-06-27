import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx';
import { Input } from '@/components/ui/input.jsx';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table.jsx';
import { LoadingSpinner } from '@/components/ui/loading-spinner.jsx';
import { useToast } from '@/components/ui/toast.jsx';
import { useApiData } from '@/hooks/use-api.js';
import { Search, Filter, Image as ImageIcon } from 'lucide-react';
import { Switch } from '@/components/ui/switch.jsx';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

export const InventoryManagement = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [categories, setCategories] = useState([]);
  const [showClover, setShowClover] = useState(false);
  const { error: showError } = useToast();

  // Use API hooks for data fetching with caching
  const { data: inventoryData, loading, error, refresh } = useApiData(showClover ? 'clover/inventory' : 'inventory', [showClover]);

  // Debug logging
  useEffect(() => {
    if (inventoryData) {
      console.log('Inventory data received:', inventoryData);
      console.log('Data type:', typeof inventoryData);
      console.log('Is array:', Array.isArray(inventoryData));
      if (inventoryData.items) {
        console.log('Items array:', inventoryData.items);
        console.log('Items is array:', Array.isArray(inventoryData.items));
      }
      if (inventoryData.inventory) {
        console.log('Inventory array:', inventoryData.inventory);
        console.log('Inventory is array:', Array.isArray(inventoryData.inventory));
      }
    }
  }, [inventoryData]);

  // Fetch categories from backend
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/inventory/categories`, { credentials: 'include' });
        const data = await res.json();
        if (data.categories) {
          setCategories(data.categories);
        }
      } catch (err) {
        showError('Failed to load categories', err.message);
      }
    };
    fetchCategories();
  }, [showError]);

  // Show error toast if API call fails, but don't block rendering
  useEffect(() => {
    if (error) {
      showError('Failed to load inventory data', error);
      // Retry after 5 seconds on error
      const timer = setTimeout(() => {
        refresh();
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, showError, refresh]);

  const filteredInventory = (() => {
    // Ensure we have an array to work with
    let items = [];
    
    if (inventoryData) {
      if (Array.isArray(inventoryData)) {
        items = inventoryData;
      } else if (inventoryData.items && Array.isArray(inventoryData.items)) {
        items = inventoryData.items;
      } else if (inventoryData.inventory && Array.isArray(inventoryData.inventory)) {
        items = inventoryData.inventory;
      }
    }
    
    // Now filter the items
    return items.filter(item => {
      const matchesSearch = item.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           item.sku?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           item.product_code?.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesCategory = selectedCategory === 'all' || (item.category && item.category.split(',').map(c => c.trim()).includes(selectedCategory));
      return matchesSearch && matchesCategory;
    });
  })();

  if (loading) {
    return <LoadingSpinner size="lg" text="Loading inventory data..." />;
  }

  // Even if there's an error, try to show data if we have it
  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Inventory Management</h2>
        <div className="flex items-center space-x-2">
          <span className="text-sm">Show Clover Inventory</span>
          <Switch checked={showClover} onCheckedChange={setShowClover} />
          <span className="text-xs text-gray-500">({showClover ? 'Clover' : 'Local'} source)</span>
        </div>
      </div>
      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Filter className="w-4 h-4 mr-2" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent className="flex space-x-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by name, SKU, or product code..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8"
              />
            </div>
          </div>
          <div className="flex-1">
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger>
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                {categories.map(category => (
                  <SelectItem key={category} value={category}>
                    {category}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Inventory Table */}
      <Card>
        <CardHeader>
          <CardTitle>Inventory Items</CardTitle>
          <CardDescription>
            {filteredInventory.length} items found
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Image</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>SKU</TableHead>
                <TableHead>Product Code</TableHead>
                <TableHead>Category</TableHead>
                <TableHead className="text-right">Price</TableHead>
                <TableHead className="text-right">Quantity</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredInventory.map(item => (
                <TableRow key={item.id || item.item_id}>
                  <TableCell>
                    {item.image_url ? (
                      <img 
                        src={item.image_url} 
                        alt={item.name}
                        className="w-12 h-12 object-cover rounded"
                        onError={(e) => {
                          e.target.onerror = null;
                          e.target.src = '/placeholder-food.png';
                        }}
                      />
                    ) : (
                      <div className="w-12 h-12 bg-gray-100 rounded flex items-center justify-center">
                        <ImageIcon className="w-6 h-6 text-gray-400" />
                      </div>
                    )}
                  </TableCell>
                  <TableCell className="font-medium">{item.name}</TableCell>
                  <TableCell>{item.sku || '-'}</TableCell>
                  <TableCell>{item.product_code || '-'}</TableCell>
                  <TableCell>{item.category || 'Uncategorized'}</TableCell>
                  <TableCell className="text-right">${item.price?.toFixed(2) || '0.00'}</TableCell>
                  <TableCell className="text-right">{item.quantity ?? item.current_stock ?? 0}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}; 