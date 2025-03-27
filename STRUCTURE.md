# PDQ ERP Application Structure

This document provides a comprehensive overview of the PDQ ERP application's structure, including all files and their purposes.

## Directory Structure

```
pdq_erp/
│
├── app.py                 # Main application file with routes and Flask configuration
├── models.py              # Database models and relationships
├── forms.py               # Form definitions using WTForms
├── requirements.txt       # Python dependencies
├── README.md              # Project documentation
├── DOCUMENTATION.md       # Detailed documentation of the system
├── STRUCTURE.md           # This file - detailed structure documentation
│
├── instance/              # Database storage (created at runtime)
│   └── erp.db             # SQLite database file
│
├── static/                # Static assets
│   └── (CSS, JS files)    # For future custom styling and scripts
│
├── templates/             # HTML templates
│   ├── layout.html        # Base template with navigation and structure
│   ├── index.html         # Dashboard/home page
│   │
│   ├── employees.html     # Employee listing page
│   ├── employee_form.html # Add/edit employee form
│   │
│   ├── projects.html      # Project listing page
│   ├── project_form.html  # Add/edit project form
│   ├── project_detail.html # Detailed project view with costs and profit
│   │
│   ├── timesheets.html    # Timesheet listing page
│   ├── timesheet_form.html # Add timesheet entry form
│   │
│   ├── materials.html     # Materials listing page
│   ├── material_form.html # Add material form
│   │
│   ├── expenses.html      # Expenses listing page
│   ├── expense_form.html  # Add expense form
│   │
│   ├── invoices.html      # Invoice listing page
│   ├── invoice_form.html  # Add/edit invoice form
│   │
│   ├── payroll_report.html # Payroll reporting page
│   └── payroll_payment_form.html # Record payroll payment form
│
├── tests/                 # Test directory
│   ├── test_models.py     # Tests for data models
│   ├── test_forms.py      # Tests for form validation
│   ├── test_routes.py     # Tests for route functionality
│   ├── test_integration.py # Integration tests
│   ├── test_complex_scenarios.py # Tests for complex business flows
│   ├── test_edge_cases.py # Tests for boundary conditions
│   └── test_security_and_validation.py # Security and validation tests
│
└── venv/                  # Virtual environment (not included in repository)
```

## Core Files Explained

### Backend Files

#### `app.py`
- **Purpose**: Main application entry point
- **Contents**:
  - Flask application configuration
  - Database connection setup
  - Route definitions for all pages
  - Request handling logic
  - Form processing
  - Helper functions

#### `models.py`
- **Purpose**: Database schema definition
- **Contents**:
  - SQLAlchemy model classes
  - Table relationships with proper cascade behavior
  - Enums for statuses (ProjectStatus, PaymentStatus, PaymentMethod)
  - Business logic methods within models
  - Data validation rules
  - Calculated properties for costs and other derived values
  - Indexes for performance optimization

#### `forms.py`
- **Purpose**: Form definitions and validation
- **Contents**:
  - WTForms form classes
  - Field definitions with validators
  - Custom field coercion for handling special cases
  - Default values and choices for select fields

#### `requirements.txt`
- **Purpose**: Dependency management
- **Contents**: List of required Python packages with versions

### Template Files

#### Base Templates
- **`layout.html`**: Main layout template with navigation, header, and footer
- **`index.html`**: Dashboard with summary information and quick links

#### Employee Management
- **`employees.html`**: Lists all employees with key information
- **`employee_form.html`**: Form for adding/editing employee details

#### Project Management
- **`projects.html`**: Lists all projects with status and key details
- **`project_form.html`**: Form for creating/editing projects
- **`project_detail.html`**: Detailed view of a project with financial analysis

#### Time Tracking
- **`timesheets.html`**: Lists timesheet entries for filtering and viewing
- **`timesheet_form.html`**: Form for recording employee time entries

#### Materials Management
- **`materials.html`**: Lists materials with project associations
- **`material_form.html`**: Form for recording materials purchased

#### Expense Tracking
- **`expenses.html`**: Lists expenses with filtering options
- **`expense_form.html`**: Form for recording business expenses

#### Invoicing
- **`invoices.html`**: Lists invoices with status tracking
- **`invoice_form.html`**: Form for creating and managing invoices

#### Payroll
- **`payroll_report.html`**: Generates payroll reports by date range
- **`payroll_payment_form.html`**: Form for recording payments to employees

## Database Models

### Key Model Relationships

All database relationships are carefully designed with proper cascade behavior to ensure data integrity:

#### Employee
- Has many timesheets (one-to-many)
- Has many payroll payments (one-to-many)
- Enforces validation for employee status changes

#### Project
- Has many timesheets (one-to-many)
- Has many materials (one-to-many)
- Has many expenses (one-to-many)
- Has many invoices (one-to-many)
- Includes properties for cost and profit calculations

#### Timesheet
- Belongs to an employee (many-to-one)
- Belongs to a project (many-to-one)
- Includes hour calculation properties with lunch break handling
- Validates that employee is active

#### Material
- Belongs to a project (many-to-one)
- Configured with cascade delete when project is deleted

#### Expense
- Can belong to a project (many-to-one, optional)
- Includes payment tracking fields

#### PayrollPayment
- Belongs to an employee (many-to-one)
- Records payment information and status

#### Invoice
- Belongs to a project (many-to-one)
- Includes payment tracking fields

## Test Structure

The test suite is organized to ensure comprehensive coverage:

### Unit Tests
- **`test_models.py`**: Tests individual model functionality
- **`test_forms.py`**: Tests form validation rules

### Integration Tests
- **`test_routes.py`**: Tests route functionality
- **`test_integration.py`**: Tests multi-step workflows

### Complex Scenario Tests
- **`test_complex_scenarios.py`**: Tests business process flows
- **`test_edge_cases.py`**: Tests boundary conditions
- **`test_security_and_validation.py`**: Tests security features and validation

### Test Fixtures
- Provides sample data for testing
- Creates test environments with database isolation

## Configuration

The application uses Flask's configuration system:
- Development configuration is the default
- Debug mode is enabled by default
- SQLite database used for simplicity
- Session security with SECRET_KEY
- CSRF protection enabled

## Security Features

- CSRF protection via Flask-WTF
- Input validation through WTForms
- Business rule enforcement in models
- Data integrity through SQLAlchemy relationships
