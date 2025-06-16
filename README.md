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

### Backend
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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.