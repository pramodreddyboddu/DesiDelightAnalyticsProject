import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx';
import { Button } from '@/components/ui/button.jsx';
import { Input } from '@/components/ui/input.jsx';
import { Label } from '@/components/ui/label.jsx';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx';
import { Alert, AlertDescription } from '@/components/ui/alert.jsx';
import { Progress } from '@/components/ui/progress.jsx';
import { Upload, FileText, CheckCircle, AlertCircle, X } from 'lucide-react';

const API_BASE_URL = 'http://localhost:5000/api';

export const AdminPanel = () => {
  const [uploadStatus, setUploadStatus] = useState({});
  const [uncategorizedItems, setUncategorizedItems] = useState([]);
  const [loading, setLoading] = useState(false);

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
        
        // Refresh uncategorized items if sales data was uploaded
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

  const fetchUncategorizedItems = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/items/uncategorized`, {
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
      const response = await fetch(`${API_BASE_URL}/items/uncategorized/${itemId}/categorize`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ category })
      });

      if (response.ok) {
        // Remove the item from uncategorized list
        setUncategorizedItems(prev => prev.filter(item => item.id !== itemId));
      }
    } catch (error) {
      console.error('Error categorizing item:', error);
    }
  };

  React.useEffect(() => {
    fetchUncategorizedItems();
  }, []);

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

      {/* System Status */}
      <Card>
        <CardHeader>
          <CardTitle>System Status</CardTitle>
          <CardDescription>Current system information and statistics</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <p className="text-2xl font-bold text-green-600">
                {Object.values(uploadStatus).filter(s => s.status === 'success').length}
              </p>
              <p className="text-sm text-green-600">Successful Uploads</p>
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <p className="text-2xl font-bold text-yellow-600">{uncategorizedItems.length}</p>
              <p className="text-sm text-yellow-600">Items Need Categorization</p>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <p className="text-2xl font-bold text-blue-600">
                {Object.values(uploadStatus).reduce((sum, s) => sum + (s.processed || 0), 0)}
              </p>
              <p className="text-sm text-blue-600">Total Records Processed</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

