# Development Tools

This directory contains development and testing scripts that are not part of the main application but are useful for development, debugging, and testing purposes.

## Contents

### Debug Scripts
- `debug_clover_inventory.py` - Debug Clover inventory integration
- `debug_revenue.py` - Debug revenue calculations and data

### Test Scripts
- `test_clover_connection.py` - Test Clover API connection
- `test_clover_credentials.py` - Test Clover authentication
- `test_clover_integration.py` - Test Clover integration features
- `test_clover_simple.py` - Simple Clover API tests
- `test_data_source_fixes.py` - Test data source configuration fixes
- `test_inventory.py` - Test inventory management
- `test_new_token.py` - Test new token generation
- `test_sales_fix.py` - Test sales data fixes

### Database Scripts
- `fix_db_table.py` - Fix database table issues
- `fix_database.py` - Database maintenance and fixes
- `migrate_to_postgres.py` - PostgreSQL migration script
- `restore_tenant_data.py` - Restore tenant data

### Setup Scripts
- `create_data_source_config_table.py` - Create data source configuration table
- `create_demo_users.py` - Create demo users for testing
- `set_sales_data_source_clover.py` - Set sales data source to Clover

### Utility Scripts
- `find_merchant.py` - Find Clover merchant information
- `simple_clover_test.py` - Simple Clover API testing

## Usage

These scripts are for development and testing purposes only. They should not be run in production environments.

To use any of these scripts:

1. Navigate to the `restaurant_management_api` directory
2. Run the script with Python: `python dev_tools/script_name.py`

## Notes

- These scripts may require specific environment variables or database connections
- Always review the script before running to understand what it does
- Some scripts may modify database data - use with caution
- These scripts are not part of the main application and are not required for production deployment 