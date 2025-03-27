# Mauricio PDQ ERP System Documentation

## Overview

The Mauricio PDQ ERP System is a comprehensive Enterprise Resource Planning solution designed specifically for Mauricio PDQ Paint & Drywall. This web-based application helps streamline business operations by managing employees, projects, timesheets, materials, expenses, invoices, and payroll in a single integrated platform.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Installation and Setup](#installation-and-setup)
3. [Data Models](#data-models)
4. [Features and Modules](#features-and-modules)
5. [Application Workflows](#application-workflows)
6. [User Interface](#user-interface)
7. [Testing](#testing)
8. [Security Considerations](#security-considerations)
9. [System Administration](#system-administration)
10. [Troubleshooting](#troubleshooting)
11. [Future Enhancements](#future-enhancements)

## System Architecture

### Technology Stack

- **Backend**: Python 3.7+ with Flask Framework
- **Database**: SQLite via SQLAlchemy ORM
- **Frontend**: HTML/CSS with Bootstrap 5 for responsive design
- **Form Handling**: WTForms for form creation and validation
- **Testing**: pytest with flask-pytest extension
- **Additional Libraries**:
  - Flask-SQLAlchemy: Database ORM integration
  - Flask-WTF: Form handling with CSRF protection
  - Flask-Bootstrap: UI components and styling

### Directory Structure

```
mauricioERP/
│
├── app.py                 # Main application with routes and configuration
├── models.py              # Database models and relationships
├── forms.py               # Form definitions using WTForms
├── requirements.txt       # Python dependencies
├── README.md              # Basic project information
├── STRUCTURE.md           # Detailed structure documentation
├── DOCUMENTATION.md       # This comprehensive documentation file
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
├── tests/                 # Test directory
│   ├── test_models.py     # Tests for data models
│   ├── test_forms.py      # Tests for form validation
│   ├── test_routes.py     # Tests for route functionality
│   ├── test_integration.py # Integration tests
│   ├── test_complex_scenarios.py # Tests for complex business flows
│   ├── test_edge_cases.py # Tests for boundary conditions
│   └── test_security_and_validation.py # Security and validation tests
```

## Installation and Setup

### Prerequisites

- Python 3.7 or higher
- Git (for cloning the repository)
- Windows, macOS, or Linux operating system

### Installation Steps

1. **Clone the repository**:
   ```
   git clone https://github.com/kingsmanrip/mauricioERP.git
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

4. **Initialize the database**:
   ```
   # Option 1 - Using the built-in command
   flask init-db

   # Option 2 - Using Python directly
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

5. **Run the application**:
   ```
   python app.py
   ```

6. **Run tests**:
   ```
   python -m pytest
   ```

## Data Models

### Model Relationships and Cascade Behavior

The database schema uses SQLAlchemy relationships with proper cascade behavior to ensure data integrity. Key relationship features include:

- **Foreign keys with ondelete='CASCADE'**: Ensures that when a parent record is deleted, all related child records are automatically deleted
- **Backref configuration**: Properly configured to avoid conflicts and circular references
- **Relationship indexes**: Added for performance optimization on common queries

### Core Models

#### Employee

- **Key fields**:
  - `id` (Primary Key)
  - `name`
  - `employee_id_str` (Unique identifier string)
  - `pay_rate`
  - `contact_details`
  - `hire_date`
  - `is_active` (Status flag)

- **Relationships**: 
  - One-to-many with Timesheet
  - One-to-many with PayrollPayment

- **Business logic**:
  - Validates employee status changes
  - Ensures active employees for timesheet entry

#### Project

- **Key fields**:
  - `id` (Primary Key)
  - `name`
  - `project_id_str` (Unique identifier string)
  - `client_name`
  - `location`
  - `start_date` and `end_date`
  - `contract_value`
  - `status` (Using ProjectStatus enum)

- **Relationships**:
  - One-to-many with Timesheet
  - One-to-many with Material
  - One-to-many with Expense
  - One-to-many with Invoice

- **Properties**:
  - `total_material_cost`: Calculated sum of all material costs
  - `total_labor_cost`: Calculated sum of timesheet hours multiplied by employee pay rates
  - `total_other_expenses`: Calculated sum of all expenses
  - `total_cost`: Sum of materials, labor, and expenses
  - `profit`: Contract value minus total cost

#### Timesheet

- **Key fields**:
  - `id` (Primary Key)
  - `employee_id` (Foreign Key with CASCADE)
  - `project_id` (Foreign Key with CASCADE)
  - `date`
  - `entry_time` and `exit_time`
  - `lunch_duration_minutes`: Lunch break duration

- **Properties**:
  - `raw_hours`: Calculated raw hours between entry and exit times
  - `calculated_hours`: Working hours after lunch break adjustments, with special handling for different lunch durations

- **Validation**:
  - Prevents timesheets for inactive employees
  - Ensures valid time entries

#### Material

- **Key fields**:
  - `id` (Primary Key)
  - `project_id` (Foreign Key with CASCADE)
  - `description`
  - `supplier`
  - `cost`
  - `purchase_date`
  - `category`

#### Expense

- **Key fields**:
  - `id` (Primary Key)
  - `description`
  - `category`
  - `amount`
  - `date`
  - `supplier_vendor`
  - `project_id` (Foreign Key with CASCADE, nullable)
  - `payment_method` (Using PaymentMethod enum)
  - `payment_status` (Using PaymentStatus enum)

#### PayrollPayment

- **Key fields**:
  - `id` (Primary Key)
  - `employee_id` (Foreign Key with CASCADE)
  - `payment_date`
  - `pay_period_start` and `pay_period_end`
  - `amount`
  - `payment_method` (Using PaymentMethod enum)
  - `notes`

#### Invoice

- **Key fields**:
  - `id` (Primary Key)
  - `project_id` (Foreign Key with CASCADE)
  - `invoice_number` (Unique)
  - `date`
  - `due_date`
  - `amount`
  - `status` (Using PaymentStatus enum)
  - `paid_date`
  - `payment_method` (Using PaymentMethod enum)

## Features and Modules

### Dashboard

- Summary of active projects
- Quick statistics on finances
- Links to key actions

### Employee Management

- Comprehensive employee information tracking
- Status management (active/inactive)
- Payroll rate tracking

### Project Management

- Full project lifecycle handling
- Status tracking (Pending → In Progress → Completed → Invoiced → Paid)
- Financial analysis with real-time cost and profit calculations

### Time Tracking

- Daily timesheet entry by employee and project
- Automatic calculation of hours with lunch break handling
- Special handling for overnight shifts

### Materials Management

- Record materials used in projects
- Track suppliers and costs
- Categorize materials for reporting

### Expense Tracking

- Record business expenses with or without project association
- Track payment methods and status
- Categorization for financial reporting

### Invoicing

- Generate invoices for completed projects
- Track payment status
- Record payment information

### Payroll Management

- Calculate payroll based on recorded timesheets
- Generate payroll reports
- Record payments to employees

## Testing

### Test Framework

The application includes a comprehensive test suite using pytest with the following main components:

1. **Unit Tests**:
   - Model validation tests
   - Form validation tests
   - Route functionality tests

2. **Integration Tests**:
   - Project workflow tests
   - Payroll workflow tests

3. **Edge Case Tests**:
   - Time boundary tests
   - Date boundary tests
   - Data validation tests

4. **Complex Scenario Tests**:
   - Complete project lifecycle
   - Multiple project resource allocation
   - Employee status change impacts
   - Project status changes

5. **Security and Validation Tests**:
   - Input sanitization
   - Numeric input validation
   - Data consistency
   - Performance with large queries
   - Transaction integrity

### Running Tests

To run the complete test suite:
```
python -m pytest
```

To run specific test categories:
```
python -m pytest tests/test_models.py  # Run only model tests
python -m pytest -v  # Run with verbose output
```

## Security Considerations

Current security features:
- CSRF protection via Flask-WTF
- Input validation and sanitization
- Business rule enforcement

Recommended additions for production:
- User authentication system
- Role-based access control
- HTTPS configuration
- Environment variables for sensitive information
- Regular database backups

## Troubleshooting

### Common Issues

#### Database Issues
- If database errors occur, check file permissions on the instance directory
- For a fresh start, delete the instance/erp.db file and reinitialize

#### Application Errors
- Check the Flask debug output for error messages
- Ensure all dependencies are installed correctly
- Verify that the database migrations are up to date

#### Form Submission Problems
- Ensure all required fields are properly filled
- Check validation rules in forms.py
- Enable debug mode for detailed error messages

## Future Enhancements

Potential improvements for future versions:
- User authentication system
- PDF generation for invoices and reports
- Email notifications
- Mobile-responsive improvements
- Advanced reporting and analytics
- Integration with accounting software
- Client portal for project status viewing
