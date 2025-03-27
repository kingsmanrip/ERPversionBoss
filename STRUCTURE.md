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
  - Table relationships
  - Enums for statuses (ProjectStatus, PaymentStatus, PaymentMethod)
  - Business logic methods within models
  - Data validation rules

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
- **`timesheets.html`**: Lists timesheet entries with filtering options
- **`timesheet_form.html`**: Form for recording time worked on projects

#### Materials Management
- **`materials.html`**: Lists materials purchased for projects
- **`material_form.html`**: Form for adding materials to projects

#### Expense Tracking
- **`expenses.html`**: Lists business expenses with filtering
- **`expense_form.html`**: Form for recording business expenses

#### Invoicing
- **`invoices.html`**: Lists all invoices with status information
- **`invoice_form.html`**: Form for creating and editing invoices

#### Payroll
- **`payroll_report.html`**: Reporting interface for payroll calculations
- **`payroll_payment_form.html`**: Form for recording payments to employees

## Database Models

### `Employee`
- Stores employee information, pay rates, and status

### `Project`
- Tracks project details, client information, and financial data
- Contains methods for calculating costs and profitability

### `Timesheet`
- Records hours worked by employees on specific projects
- Includes logic for calculating billable hours

### `Material`
- Tracks materials purchased for projects
- Records costs for project profitability calculations

### `Expense`
- Records business expenses
- Can be linked to specific projects or kept as general expenses

### `PayrollPayment`
- Tracks payments made to employees
- Links to employee records

### `Invoice`
- Manages client invoicing
- Tracks payment status and due dates

## Key Relationships

- **Employee to Timesheets**: One-to-many (one employee has many timesheet entries)
- **Project to Timesheets**: One-to-many (one project has many timesheet entries)
- **Project to Materials**: One-to-many (one project uses many materials)
- **Project to Expenses**: One-to-many (one project has many expenses)
- **Project to Invoices**: One-to-many (one project has many invoices)

## Enums

### `ProjectStatus`
- PENDING
- IN_PROGRESS
- COMPLETED
- INVOICED
- PAID

### `PaymentStatus`
- PENDING
- PROCESSED
- PAID

### `PaymentMethod`
- CASH
- CHECK
- OTHER

## Application Flow

1. Create employees and projects
2. Record timesheets as work is performed
3. Add materials and expenses as they occur
4. Generate payroll reports and record payments
5. Create invoices for completed projects
6. Update project status as it progresses through the workflow

## Future Extension Points

- User authentication system
- File upload for project documents
- Client portal
- Advanced reporting
- Mobile application integration
- Email notifications
