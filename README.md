# Mauricio PDQ ERP System

A comprehensive Enterprise Resource Planning (ERP) system designed specifically for Mauricio PDQ Paint & Drywall. This application helps manage employees, projects, timesheets, materials, expenses, invoices, and payroll in a single integrated platform.

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Tech Stack](#tech-stack)
4. [Installation and Setup](#installation-and-setup)
5. [Deployment Information](#deployment-information)
6. [Database Structure](#database-structure)
7. [Usage Guide](#usage-guide)
8. [Recent Updates](#recent-updates)
9. [Project Structure](#project-structure)
10. [Development Guidelines](#development-guidelines)
11. [Troubleshooting](#troubleshooting)

## Overview

The Mauricio PDQ ERP System is a web-based application developed to streamline business operations for Mauricio PDQ Paint & Drywall. It provides an integrated solution for managing various aspects of the business, including employee information, project tracking, time management, financial operations, and reporting.

## Features

- **User Authentication**: Secure login system to protect sensitive business data
- **Visual Analytics Dashboard**: Interactive visualizations of key business metrics and trends
- **Employee Management**: Track employee information, pay rates, and contact details
- **Project Management**: Manage client projects with status tracking and financial details
- **Time Tracking**: Record employee hours worked with smart lunch break handling:
  - Lunch breaks ≥ 1 hour: only 30 minutes deducted
  - Lunch breaks < 30 minutes: no deduction
  - Lunch breaks 30-59 minutes: actual time deducted
- **Materials Management**: Track materials used for each project with cost calculations
- **Expense Tracking**: Monitor business expenses with or without project association
- **Invoicing**: Generate and track invoices for completed projects
- **Payroll Management**:
  - Calculate payroll based on recorded timesheets
  - Track detailed breakdowns by payment method (Cash vs Check)
  - Manage payroll deductions (taxes, insurance, retirement, advances, etc.)
  - Calculate gross and net payment amounts
- **Payment Method Tracking**: Record and track payments by method (Cash/Check) with check numbers and bank information
- **Cost Analysis**: Automatic calculation of project costs and profitability
- **Net Profit Tracking**: Real-time calculation of actual net profit (revenue collected minus expenses) for each project and company-wide
- **Financial Management System**: Comprehensive tracking of accounts payable, paid accounts, and monthly expenses
- **Responsive UI Design**: Optimized display of financial data with properly sized elements to ensure readability

## Tech Stack

- **Backend**: Python with Flask framework
- **Database**: SQLite (via SQLAlchemy ORM)
- **Frontend**: Bootstrap 5 for responsive design
- **Forms**: WTForms for form handling and validation
- **PDF Generation**: FPDF for invoice and report generation
- **Testing**: Pytest suite for validation

## Installation and Setup

### Prerequisites

- Python 3.7 or higher
- Git (for cloning the repository)

### Installation Steps

1. **Clone the repository**:
   ```
   git clone <repository-url>
   cd mauricioERP
   ```

2. **Create and activate a virtual environment**:
   ```
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```
   pip install -r requirements.txt
   ```
   
   ⚠️ **Note**: You may need to install additional packages not listed in requirements.txt:
   ```
   pip install bootstrap-flask==2.3.0 flask-excel
   ```

4. **Initialize the database** (if it doesn't exist):
   ```
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

5. **Run the application**:
   ```
   python app.py
   ```

6. **Access the application** in your web browser:
   ```
   http://127.0.0.1:3002
   ```

## Deployment Information

The Mauricio PDQ ERP System is currently deployed on a Hostinger VPS with the following configuration:

### Deployment Details

- **Domain**: [https://mauriciopdq.site/](https://mauriciopdq.site/)
- **Server**: Ubuntu Linux VPS on Hostinger
- **Repository Location**: `/root/finalERP`
- **Default Login Credentials**:
  - Username: `patricia`
  - Password: `Patri2025`

### Web Server Configuration

- **Application Server**: Flask development server on port 3002
- **Reverse Proxy**: Nginx forwarding requests from mauriciopdq.site to localhost:3002
- **SSL**: Configured with Let's Encrypt certificates

### Starting the Application

The application is configured as a systemd service for 24/7 operation:

```bash
# Check service status
systemctl status mauriciopdq-erp.service

# Start the service
systemctl start mauriciopdq-erp.service

# Stop the service
systemctl stop mauriciopdq-erp.service

# Restart the service
systemctl restart mauriciopdq-erp.service
```

The service is configured to start automatically when the server boots up and will automatically restart if it crashes.

If you need to manually start the application without systemd:

```bash
cd /root/finalERP
source venv/bin/activate
python app.py
```

Note: The application is currently using Flask's built-in development server. For improved reliability, consider upgrading to a production WSGI server like Gunicorn.

## Database Structure

The application uses SQLAlchemy ORM with the following main models:

- **User**: Authentication and user management
- **Employee**: Stores employee information and pay rates
- **Project**: Manages project details, status, and relationships
- **Timesheet**: Records work hours with automatic calculation
- **Material**: Tracks materials used in projects with costs
- **Expense**: Tracks expenses with or without project association
- **Invoice**: Manages client invoices and payment status
- **PayrollPayment**: Records payments to employees
- **PayrollDeduction**: Tracks deductions from employee payments
- **AccountsPayable**: Tracks pending payments to vendors
- **PaidAccount**: Records completed payments to vendors
- **MonthlyExpense**: Tracks recurring monthly expenses

## Usage Guide

### Dashboard

The dashboard provides an overview of key business metrics:
- Active projects count and status
- Recent timesheet entries
- Financial summaries
- Quick navigation to common tasks

### Employee Management

1. **View Employees**: Navigate to the Employees section to see all employee records
2. **Add Employee**: Click the "Add Employee" button and fill out the form
3. **Edit Employee**: Use the Edit button next to any employee to update their information
4. **Delete Employee**: The system prevents deletion of employees with associated records

### Project Management

1. **View Projects**: Navigate to the Projects section to see all project records
2. **Add Project**: Click the "Add Project" button and fill out the form
3. **Edit Project**: Use the Edit button next to any project to update its information
4. **Delete Project**: Use the Delete button to remove a project and all associated records
5. **View Project Details**: Click on a project name to see detailed information

### Timesheet Management

1. **View Timesheets**: Navigate to the Timesheets section to see all timesheet entries
2. **Add Timesheet**: Click the "Add Timesheet" button and fill out the form
   - Select an employee
   - Select a project (or "None - No Project")
   - Enter date, entry time, exit time, and lunch duration
3. **Edit Timesheet**: Use the Edit button to modify an existing timesheet entry
4. **Delete Timesheet**: Use the Delete button to remove a timesheet entry

### Payroll Processing

1. **View Payroll Report**: Navigate to the Payroll section
2. **Filter by Employee**: Use the dropdown to select a specific employee
3. **Record Payment**: Click "Record Payment" and fill out the form
4. **Add Deductions**: Use the deduction section to add various deductions

## Recent Updates

- **April 25, 2025**:
  #### System Testing and Validation
  - **Comprehensive Testing**: Conducted thorough testing of the payroll and project management modules
  - **Lunch Break Calculation**: Verified correct implementation of the lunch break deduction rules:
    - Lunch breaks ≥ 1 hour: only 30 minutes deducted
    - Lunch breaks < 30 minutes: no deduction
    - Lunch breaks 30-59 minutes: actual time deducted
  - **Project Financial Calculations**: Confirmed accuracy of all project cost, revenue, and profit calculations
  - **Production Ready**: All tests confirm the system is functioning as designed and ready for production use

- **April 14, 2025**:
   #### Invoice System Improvements
   - **Enhanced Invoice PDFs**: Updated invoice PDF generation to properly display base amount and tax amount values in the payment section
   - **Improved Description Handling**: Modified invoice PDFs to only display the invoice-specific description (not the project description)
   - **Automatic Invoice Numbering**: Added automatic generation of unique invoice numbers (format: INV-YYYYMMDD-XXXX) when creating invoices with empty invoice number fields
   - **Fixed Database Schema**: Resolved issues with invoice table columns to ensure compatibility with the application code

   #### Bug Fixes
   - Fixed internal server error when creating new invoices with empty invoice numbers
   - Resolved issue where amounts entered in the invoice form weren't displaying correctly in the PDF output
   - Improved error handling when working with invoice records

   #### Development Notes
   - The invoice template now properly separates invoice-specific content from project data
   - PDF generation has been optimized for better visual presentation

- **Timesheet Deletion Feature**: Added the ability to delete timesheet entries with a confirmation dialog
- **"No Project" Timesheet Option**: Added ability to record employee hours without associating them to any project
- **Saturday Premium Pay**: Added $5.00/hour premium for Saturday work with visual indicators
- **Payroll Deductions System**: Implemented comprehensive payroll deduction functionality
- **Net Profit Calculation**: Added tracking of actual net profit for each project
- **Financial Management System**: Added modules for accounts payable and financial tracking
- **Enhanced Invoice Template**: Redesigned invoice PDF with professional layout
- **Custom Work Week**: Implemented Friday to Thursday work week definition

## Project Structure

```
mauricioERP/
│
├── app.py                 # Main application with routes and configuration
├── models.py              # Database models and relationships
├── forms.py               # Form definitions using WTForms
├── requirements.txt       # Python dependencies
│
├── instance/              # Database storage (created at runtime)
│   └── erp.db             # SQLite database file
│
├── templates/             # HTML templates
│   ├── layout.html        # Base template with navigation
│   ├── index.html         # Dashboard
│   ├── employees.html     # Employee listing
│   ├── employee_form.html # Add/edit employee
│   └── ... (other templates)
│
├── static/                # Static assets
│   └── (CSS, JS files)    # For styling and scripts
│
├── tests/                 # Test directory
    ├── test_models.py     # Tests for data models
    ├── test_forms.py      # Tests for form validation
    └── ... (other tests)
```

## Development Guidelines

### Adding New Features

1. Create database models in `models.py`
2. Add form classes in `forms.py`
3. Implement routes in `app.py`
4. Create HTML templates in the `templates` directory
5. Write tests for your new functionality

### Database Migrations

The application currently does not use Alembic for migrations. When changing the database schema:

1. Back up the existing database
2. Make changes to the models
3. Use the update_schema.py script or manually recreate the database

### Coding Standards

- Follow PEP 8 style guidelines
- Document functions and classes with docstrings
- Use consistent naming conventions
- Maintain test coverage for new features

## Troubleshooting

### Common Issues

1. **Database Errors**:
   - Check that the database file exists in the instance directory
   - Verify the database schema matches the models

2. **CSRF Token Errors**:
   - Ensure all forms include `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>`

3. **Bootstrap Issues**:
   - Make sure bootstrap-flask is installed with version 2.3.0 or higher

4. **Project Association Errors**:
   - When no project is selected, the system uses project_id = 0 as a placeholder

### Support

For questions or issues, please contact the development team or submit an issue through the appropriate channels.

---

Maintained by Mauricio PDQ Paint & Drywall (2025)
