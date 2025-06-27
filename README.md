# Desi Delight Analytics Project

A comprehensive restaurant management system with analytics capabilities for Desi Delight restaurant.

## Features

- Sales Analytics Dashboard
- Chef Performance Tracking
- Profitability Analysis
- Inventory Management
- Expense Tracking
- Admin Panel for Data Management
- Uncategorized Items Management

## Tech Stack

### Frontend
- React.js
- Vite
- Tailwind CSS
- Shadcn UI Components
- React Router
- Axios

### Backend ##
- Python Flask
- SQLAlchemy
- SQLite
- Flask-Login
- Flask-CORS

## Prerequisites

- Node.js 16+
- Python 3.8+
- pip
- npm or pnpm

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd restaurant_management_api
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv myenv
   source myenv/bin/activate  # On Windows: myenv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```bash
   flask db upgrade
   ```

5. Start the backend server:
   ```bash
   flask run
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd restaurant_management_frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   # or
   pnpm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   # or
   pnpm dev
   ```

## Usage

1. Access the application at `http://localhost:5173`
2. Login with admin credentials:
   - Username: admin
   - Password: admin123

## API Endpoints

### Authentication
- POST `/api/auth/login` - User login
- POST `/api/auth/logout` - User logout

### Dashboard
- GET `/api/dashboard/sales-summary` - Get sales summary
- GET `/api/dashboard/chef-performance` - Get chef performance data
- GET `/api/dashboard/profitability` - Get profitability data
- GET `/api/dashboard/expenses` - Get expenses data

### Admin
- GET `/api/admin/data-stats` - Get data statistics
- POST `/api/upload/{type}` - Upload data files
- DELETE `/api/admin/delete-data` - Delete data

## Setting Inventory Data Source to Clover

To ensure your inventory data is synced from Clover, you must set the inventory data source to `clover` in the backend configuration.

### Option 1: Using the API Endpoint

Send a PUT request to `/api/dashboard/data-source-config` with the following JSON body:

```json
{
  "data_sources": {
    "sales": "clover",
    "inventory": "clover"
  }
}
```

You can use a tool like `curl` or Postman:

```bash
curl -X PUT https://<your-backend-domain>/api/dashboard/data-source-config \
  -H "Content-Type: application/json" \
  -d '{"data_sources": {"sales": "clover", "inventory": "clover"}}'
```

### Option 2: Using the Admin UI

- Go to the Data Source Configuration section in the admin panel.
- Set both **Sales Source** and **Inventory Source** to `Clover`.
- Save the configuration.

### Why is this important?

If the inventory data source is not set to `clover`, your backend will use local data and not sync inventory from Clover. This is required for real-time and accurate inventory management.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.