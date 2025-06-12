# Restaurant Sales and Expense Management System - Technical Design Document

## Executive Summary

This document outlines the technical architecture and design specifications for a comprehensive restaurant sales and expense management system. The application is designed to track, categorize, and analyze restaurant sales and expenses, providing automated mapping capabilities, manual correction features for missing inventory items, and comprehensive dashboards for profitability analysis.

The system will handle four primary data sources: monthly sales reports, inventory files, chef-to-dish mapping files, and spending records. It will provide real-time dashboards for sales analysis, expense tracking, profitability assessment, and chef performance monitoring, with robust export capabilities for management reporting.

## System Architecture Overview

The application follows a modern full-stack architecture pattern with clear separation of concerns between the presentation layer, business logic layer, and data persistence layer. The system is designed as a web-based application to ensure accessibility across different devices and platforms while maintaining data consistency and security.

The frontend layer utilizes React.js with Tailwind CSS for responsive design, providing an intuitive user interface for both administrative functions and dashboard viewing. The backend layer is implemented using Flask, a lightweight Python web framework that provides RESTful API endpoints for data operations, file processing, and business logic execution. The data layer employs SQLite for development and testing, with the flexibility to migrate to PostgreSQL for production environments requiring higher concurrency and data volume handling.

Authentication and authorization are implemented using session-based authentication with secure password hashing. The system includes role-based access control to distinguish between administrative users who can upload files and manage categorizations, and regular users who can view dashboards and generate reports.

## Database Schema Design

The database schema is designed to efficiently store and relate the various types of data while maintaining referential integrity and supporting complex analytical queries. The schema consists of several interconnected tables that represent the core entities in the restaurant management domain.

### Core Entity Tables

The `items` table serves as the central repository for all inventory items, containing essential information such as item names, SKUs, product codes, and category classifications. This table includes fields for `id` as the primary key, `name` for the item description, `sku` for stock keeping unit identification, `product_code` for manufacturer identification, `category` for classification purposes, and `is_active` for soft deletion functionality. The category field supports values such as 'Meat', 'Vegetables', 'Grocery', 'Kitchen', and 'Uncategorized' to facilitate proper classification and reporting.

The `chefs` table maintains information about kitchen staff members, including their unique identifiers, names, and employment status. This table contains `id` as the primary key, `name` for the chef's full name, `clover_id` for integration with the point-of-sale system, and `is_active` for employment status tracking.

The `chef_dish_mapping` table establishes the many-to-many relationship between chefs and the dishes they prepare. This table includes `id` as the primary key, `chef_id` as a foreign key referencing the chefs table, `item_id` as a foreign key referencing the items table, and `created_at` for audit trail purposes. This relationship enables accurate attribution of sales to specific chefs for performance analysis.

### Transaction Tables

The `sales` table records all sales transactions with comprehensive details for analytical purposes. Key fields include `id` as the primary key, `line_item_date` for transaction timestamp, `order_employee_id` and `order_employee_name` for staff attribution, `item_id` as a foreign key to the items table, `order_id` for transaction grouping, `quantity` for units sold, `item_revenue` for base revenue, `modifiers_revenue` for additional charges, `total_revenue` for complete transaction value, `discounts` for promotional adjustments, `tax_amount` for tax calculations, `item_total_with_tax` for final amount, and `payment_state` for transaction status tracking.

The `expenses` table captures all spending records with categorization and vendor information. This table includes `id` as the primary key, `date` for expense date, `vendor` for supplier identification, `amount` for expense value, `invoice` for reference documentation, `category` for expense classification, and `description` for additional details. The category field aligns with the item categories to enable accurate profit margin calculations.

### Administrative Tables

The `uncategorized_items` table temporarily stores items that appear in sales data but are not found in the inventory system. This table facilitates the manual categorization process by administrators. Fields include `id` as the primary key, `item_name` for the unrecognized item, `frequency` for occurrence count, `suggested_category` for automated suggestions, `status` for processing state, and `created_at` for tracking purposes.

The `users` table manages system authentication and authorization. Key fields include `id` as the primary key, `username` for login identification, `password_hash` for secure credential storage, `role` for access level determination, `created_at` for account creation tracking, and `is_active` for account status management.

### Audit and Configuration Tables

The `file_uploads` table maintains a record of all data imports for audit and troubleshooting purposes. This table includes `id` as the primary key, `filename` for file identification, `file_type` for categorization, `upload_date` for timing, `processed_records` for success tracking, `failed_records` for error monitoring, and `status` for processing state.

The `categories` table provides a centralized definition of all item categories used throughout the system. This table contains `id` as the primary key, `name` for category identification, `description` for detailed explanation, `is_active` for status management, and `created_at` for audit purposes.

## API Architecture and Endpoints

The RESTful API architecture provides a comprehensive set of endpoints organized by functional domains. Each endpoint follows standard HTTP methods and status codes, with consistent request and response formats using JSON serialization.

### Authentication Endpoints

The authentication system provides secure access control through session-based authentication. The `/api/auth/login` POST endpoint accepts username and password credentials, validates them against the database, and establishes a secure session. The response includes user information and role assignments for frontend authorization decisions.

The `/api/auth/logout` POST endpoint terminates the current session and clears authentication tokens. The `/api/auth/me` GET endpoint returns current user information for session validation and user interface personalization.

### File Upload and Processing Endpoints

The file management system handles various data import formats through specialized endpoints. The `/api/upload/sales` POST endpoint accepts CSV files containing sales data, validates the format against expected columns, processes each record for data integrity, and imports valid records into the sales table while flagging errors for review.

The `/api/upload/inventory` POST endpoint processes Excel files containing inventory information, validates item data including SKUs and categories, updates existing items or creates new entries, and maintains audit trails for all changes.

The `/api/upload/chef-mapping` POST endpoint handles chef-to-dish relationship files, validates chef and item references, establishes or updates mapping relationships, and ensures data consistency across the system.

The `/api/upload/expenses` POST endpoint processes spending data files, validates expense records including vendor and category information, imports financial data for profitability analysis, and maintains proper categorization for reporting purposes.

### Dashboard Data Endpoints

The dashboard system provides real-time data through optimized endpoints that aggregate and analyze transactional data. The `/api/dashboard/sales-summary` GET endpoint returns comprehensive sales analytics including total revenue by date range, category-wise breakdown, top-selling items, and trend analysis. Parameters include date range filters, category selections, and aggregation levels.

The `/api/dashboard/chef-performance` GET endpoint provides chef-specific analytics including individual sales volumes, revenue attribution, dish popularity by chef, and performance comparisons. The endpoint supports filtering by chef, date range, and dish categories.

The `/api/dashboard/profitability` GET endpoint calculates and returns profit margins by category, comparing sales revenue against corresponding expenses. This endpoint performs complex calculations to match expense categories with sales categories, providing accurate profitability analysis.

The `/api/dashboard/expenses` GET endpoint aggregates spending data by category, vendor, and time period, providing insights into cost patterns and vendor performance.

### Item Management Endpoints

The item management system provides comprehensive CRUD operations for inventory management. The `/api/items` GET endpoint returns paginated item lists with filtering and search capabilities. The POST endpoint creates new items with validation and categorization.

The `/api/items/{id}` GET endpoint returns detailed item information including sales history and chef associations. The PUT endpoint updates item details with proper validation and audit logging. The DELETE endpoint performs soft deletion to maintain referential integrity.

The `/api/items/uncategorized` GET endpoint returns items that require manual categorization, sorted by frequency of occurrence. The PUT endpoint allows administrators to assign categories to uncategorized items.

### Reporting and Export Endpoints

The reporting system provides flexible data export capabilities for management reporting. The `/api/reports/sales` GET endpoint generates comprehensive sales reports in multiple formats including CSV, Excel, and PDF. Parameters include date ranges, categories, chefs, and aggregation levels.

The `/api/reports/profitability` GET endpoint creates detailed profitability reports comparing sales and expenses across categories and time periods. The endpoint supports various visualization formats and export options.

The `/api/reports/chef-performance` GET endpoint generates chef-specific performance reports including sales attribution, dish popularity, and comparative analysis.

## Data Processing Logic

The data processing engine handles complex business logic for sales analysis, expense categorization, and profitability calculations. The system implements sophisticated algorithms to ensure accurate data interpretation and meaningful insights generation.

### Sales Data Processing

Sales data processing begins with file validation to ensure proper format and required fields. The system parses each transaction record, validates data types and ranges, and performs lookup operations to match items with inventory records. When items are not found in the inventory, they are flagged as uncategorized and added to the manual review queue.

Revenue calculations account for base item prices, modifier additions, discounts, taxes, and fees to provide accurate total values. The system handles various currency formats and tax calculations based on configurable rules.

Date and time processing converts various timestamp formats to standardized UTC values while preserving local timezone information for reporting purposes. The system supports different date formats commonly used in point-of-sale systems.

### Expense Categorization

Expense processing involves intelligent categorization based on vendor patterns, invoice descriptions, and historical data. The system maintains a learning algorithm that improves categorization accuracy over time by analyzing administrator corrections and establishing pattern recognition rules.

Vendor management includes automatic vendor normalization to handle variations in naming conventions and address formats. The system maintains vendor profiles with category preferences and spending patterns for improved automation.

Amount validation ensures proper currency handling and identifies potential data entry errors through statistical analysis and outlier detection.

### Profitability Analysis

Profitability calculations require sophisticated matching between sales categories and expense categories to ensure accurate margin analysis. The system implements configurable mapping rules that allow administrators to define how expense categories relate to sales categories.

Cost allocation algorithms distribute shared expenses across multiple categories based on sales volume proportions or custom allocation rules. This ensures that overhead costs are properly attributed for accurate profitability assessment.

Trend analysis identifies patterns in profitability over time, highlighting seasonal variations, cost fluctuations, and performance improvements or degradations.

## Security and Authentication

The security framework implements multiple layers of protection to ensure data integrity and user privacy. Authentication uses industry-standard password hashing with salt generation to protect user credentials. Session management employs secure tokens with configurable expiration times and automatic renewal mechanisms.

Authorization is implemented through role-based access control with granular permissions for different system functions. Administrative users have full access to data management and configuration functions, while regular users are restricted to dashboard viewing and report generation.

Data validation occurs at multiple levels including client-side input validation, server-side parameter validation, and database constraint enforcement. The system implements protection against common security vulnerabilities including SQL injection, cross-site scripting, and cross-site request forgery.

File upload security includes format validation, size restrictions, and content scanning to prevent malicious file uploads. The system maintains audit logs for all administrative actions and data modifications.

## Performance Optimization

The system implements various performance optimization strategies to ensure responsive user experience even with large datasets. Database indexing is strategically applied to frequently queried columns including dates, categories, and foreign key relationships.

Query optimization includes the use of database views for complex analytical queries, result caching for frequently accessed data, and pagination for large result sets. The system implements connection pooling and query batching to minimize database overhead.

Frontend optimization includes lazy loading for dashboard components, data virtualization for large tables, and efficient state management to minimize unnecessary re-renders.

File processing optimization includes streaming for large file uploads, background processing for time-intensive operations, and progress tracking for user feedback during long-running processes.

This comprehensive technical design provides the foundation for a robust, scalable, and maintainable restaurant management system that meets all specified requirements while providing room for future enhancements and feature additions.

