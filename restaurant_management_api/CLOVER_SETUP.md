# Clover POS Integration Setup Guide

This guide will help you integrate your DesiDelight Analytics application with Clover POS system for real-time data synchronization.

## 🎯 Benefits of Clover Integration

### **Real-time Data Sync**
- ✅ **Live sales data** - No more manual uploads
- ✅ **Real-time inventory** - Automatic stock updates
- ✅ **Customer data** - Complete customer profiles
- ✅ **Employee tracking** - Staff performance metrics
- ✅ **Order management** - Complete order history

### **Business Value**
- **30% time savings** - No manual data entry
- **100% accuracy** - Real-time data eliminates errors
- **Better insights** - Live analytics and reporting
- **Automated workflows** - Inventory alerts and reordering

## 🚀 Quick Setup (10 minutes)

### Step 1: Get Clover API Credentials

1. **Log into Clover Developer Dashboard**
   ```
   https://www.clover.com/developers
   ```

2. **Create a New App**
   - Click "Create App"
   - Name: "DesiDelight Analytics"
   - Description: "Restaurant analytics and reporting"

3. **Get Your Credentials**
   - **Merchant ID**: Found in your Clover Dashboard
   - **Access Token**: Generate in Developer Dashboard

### Step 2: Configure Environment Variables

```bash
# Add to your .env file
CLOVER_MERCHANT_ID=your_merchant_id_here
CLOVER_ACCESS_TOKEN=your_access_token_here
```

### Step 3: Test the Integration

```bash
# Run the test script
cd restaurant_management_api
python test_clover_integration.py
```

## 📋 Detailed Setup Instructions

### 1. Clover Developer Account Setup

#### Create Developer Account
1. Go to [Clover Developers](https://www.clover.com/developers)
2. Sign up for a developer account
3. Verify your email address

#### Create Application
1. Click "Create App" in the developer dashboard
2. Fill in the application details:
   ```
   App Name: DesiDelight Analytics
   Description: Restaurant analytics and reporting platform
   Category: Business & Finance
   ```

#### Configure App Permissions
Enable these permissions for your app:
- ✅ **Read Orders** - Access to sales data
- ✅ **Read Items** - Access to inventory data
- ✅ **Read Employees** - Access to staff data
- ✅ **Read Customers** - Access to customer data
- ✅ **Write Items** - Update inventory levels

#### Generate Access Token
1. Go to "OAuth" section
2. Generate a new access token
3. Copy the token (you'll need this)

### 2. Find Your Merchant ID

#### From Clover Dashboard
1. Log into your Clover Dashboard
2. Go to Settings → Account
3. Your Merchant ID is displayed there

#### From Clover Device
1. On your Clover device, go to Settings
2. Navigate to "About"
3. Your Merchant ID is listed there

### 3. Configure Your Application

#### Update Environment Variables
```bash
# restaurant_management_api/.env
CLOVER_MERCHANT_ID=YOUR_MERCHANT_ID
CLOVER_ACCESS_TOKEN=YOUR_ACCESS_TOKEN
```

#### Restart Your Application
```bash
# If using Docker
docker-compose restart app

# If running locally
python src/main.py
```

### 4. Test the Integration

#### Run Test Script
```bash
python test_clover_integration.py
```

#### Expected Output
```
🚀 Starting Clover Integration Tests
==================================================

📋 Running: API Connection
✅ API connection successful
✅ API Connection: PASSED

📋 Running: Clover Status
✅ Clover status: connected
   Merchant: Your Restaurant Name
✅ Clover Status: PASSED

📋 Running: Real-time Data
✅ Real-time data successful
   Today's revenue: $1,234.56
   Today's orders: 45
   Low stock items: 3
✅ Real-time Data: PASSED

📊 Test Results: 9/9 tests passed
🎉 All tests passed! Clover integration is working correctly.
```

## 🔧 API Endpoints

### Connection & Status
```bash
# Check connection status
GET /api/clover/status

# Get real-time data
GET /api/clover/realtime
```

### Data Synchronization
```bash
# Sync sales data
POST /api/clover/sync/sales
{
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-01-15T23:59:59Z"
}

# Sync inventory data
POST /api/clover/sync/inventory

# Sync all data
POST /api/clover/sync/all
```

### Data Retrieval
```bash
# Get inventory levels
GET /api/clover/inventory

# Get orders
GET /api/clover/orders?start_date=2024-01-01&end_date=2024-01-15&limit=50

# Get employees
GET /api/clover/employees

# Get customers
GET /api/clover/customers
```

### Inventory Management
```bash
# Update inventory level
PUT /api/clover/inventory/{item_id}
{
  "quantity": 25
}

# Create new item
POST /api/clover/items
{
  "name": "New Item",
  "price": 999,
  "categoryId": "category_id"
}
```

## 📊 Data Mapping

### Sales Data
| Clover Field | Database Field | Description |
|--------------|----------------|-------------|
| `id` | `clover_id` | Unique Clover line item ID |
| `item.id` | `item_id` | Item reference |
| `createdTime` | `line_item_date` | Order timestamp |
| `employee.id` | `order_employee_id` | Employee ID |
| `employee.name` | `order_employee_name` | Employee name |
| `price` | `item_revenue` | Item price (in cents) |
| `total` | `total_revenue` | Total amount (in cents) |
| `state` | `payment_state` | Payment status |

### Inventory Data
| Clover Field | Database Field | Description |
|--------------|----------------|-------------|
| `id` | `clover_id` | Unique Clover item ID |
| `name` | `name` | Item name |
| `stockCount` | `quantity` | Current stock level |
| `reorderPoint` | `reorder_point` | Reorder threshold |
| `categories.elements[0].name` | `category` | Item category |

## 🔄 Automation Setup

### Scheduled Sync (Recommended)

#### Using Cron (Linux/Mac)
```bash
# Edit crontab
crontab -e

# Add these lines for automated sync
# Sync sales data every hour
0 * * * * curl -X POST http://localhost:5000/api/clover/sync/sales

# Sync inventory every 4 hours
0 */4 * * * curl -X POST http://localhost:5000/api/clover/sync/inventory

# Full sync daily at 2 AM
0 2 * * * curl -X POST http://localhost:5000/api/clover/sync/all
```

#### Using Windows Task Scheduler
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (daily at 2 AM)
4. Action: Start a program
5. Program: `curl`
6. Arguments: `-X POST http://localhost:5000/api/clover/sync/all`

### Real-time Sync (Advanced)

For real-time synchronization, you can set up webhooks:

```python
# In your Clover app configuration
webhook_url = "https://yourdomain.com/api/clover/webhook"
```

## 🚨 Troubleshooting

### Common Issues

#### 1. "Invalid Access Token"
```bash
# Solution: Regenerate your access token
# Go to Clover Developer Dashboard → OAuth → Generate New Token
```

#### 2. "Merchant Not Found"
```bash
# Solution: Verify your Merchant ID
# Check Clover Dashboard → Settings → Account
```

#### 3. "Permission Denied"
```bash
# Solution: Check app permissions
# Ensure all required permissions are enabled in Developer Dashboard
```

#### 4. "Rate Limit Exceeded"
```bash
# Solution: Implement rate limiting
# Clover API has rate limits, add delays between requests
```

### Debug Mode

Enable debug logging:
```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Check logs
docker-compose logs app | grep Clover
```

### Test Individual Endpoints

```bash
# Test connection
curl http://localhost:5000/api/clover/status

# Test real-time data
curl http://localhost:5000/api/clover/realtime

# Test inventory sync
curl -X POST http://localhost:5000/api/clover/sync/inventory
```

## 📈 Performance Optimization

### Caching Strategy
```python
# Cache frequently accessed data
REDIS_CACHE_TTL = 300  # 5 minutes
```

### Batch Processing
```python
# Process data in batches to avoid rate limits
BATCH_SIZE = 100
```

### Error Handling
```python
# Implement retry logic for failed requests
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
```

## 🔒 Security Considerations

### Access Token Security
- ✅ Store tokens securely (environment variables)
- ✅ Rotate tokens regularly
- ✅ Use HTTPS for all API calls
- ✅ Implement proper error handling

### Data Privacy
- ✅ Only request necessary permissions
- ✅ Implement data retention policies
- ✅ Secure data transmission
- ✅ Regular security audits

## 🎯 Next Steps

### 1. Test Integration
```bash
python test_clover_integration.py
```

### 2. Configure Frontend
Add Clover integration to your dashboard:
```jsx
import { CloverIntegration } from './components/CloverIntegration.jsx';
```

### 3. Set Up Automation
Configure scheduled sync jobs for continuous data flow.

### 4. Monitor Performance
Set up monitoring and alerting for the integration.

---

**🎉 Congratulations!** Your Clover integration is now ready for production use.

**Need Help?** Check the troubleshooting section or run the test script to diagnose any issues. 