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
12. [Technical Implementation Notes](#technical-implementation-notes)
13. [Recent Enhancements](#recent-enhancements)

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
  - `profit`: Contract value minus total cost (estimated profit)
  - `actual_revenue`: Calculated sum of all paid invoices
  - `actual_net_profit`: Actual revenue minus total cost (actual money made)

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
  - `gross_amount` (Total amount before deductions)
  - `amount` (Net amount after deductions)
  - `payment_method` (Using PaymentMethod enum)
  - `notes`
  - `check_number` (For check payments)
  - `bank_name` (For check payments)

- **Properties**:
  - `total_deductions`: Calculated sum of all associated deduction amounts
  - `net_amount`: Calculated as gross_amount minus total_deductions

- **Relationships**:
  - One-to-many with PayrollDeduction

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

- Interactive visual analytics dashboard with key business metrics
- Financial summary cards including:
  - Total and active projects counter
  - Total invoiced amounts
  - Unpaid invoices tracking
  - Weekly hours logged by employees
- Project status distribution chart (doughnut chart with color-coded status visualization)
- Monthly expense trend visualization (line chart showing past 5 months of expense data)
- Top performing projects with color-coded profit margin indicators and visual progress bars
- Quick action buttons for common tasks
- Recent expenses overview with categorization

### Data Export Functionality

- Excel and PDF export options for key data types:
  - Invoices export with project details, amounts, and status
  - Projects export with detailed status, dates, and financial metrics
  - Timesheets export with employee hours, projects, and calculated totals
  - Expenses export with categorization, payment status, and project association
- Export buttons integrated into each list view for easy access
- Excel exports using pandas DataFrames for rich formatting and data handling
- PDF exports using FPDF with temporary file handling for reliable generation
- Proper attachment handling with appropriate MIME types for browser compatibility
- Automatic file naming for downloaded reports

### Employee Management

- Comprehensive employee information tracking
- Status management (active/inactive)
- Payroll rate tracking

### Project Management

- Full project lifecycle handling
- Status tracking (Pending → In Progress → Completed → Invoiced → Paid)
- Financial analysis with real-time cost and profit calculations
- Project deletion functionality with confirmation dialog and cascade delete
- Secure handling of project removal with proper database cleanup

### Time Tracking

- Daily timesheet entry by employee and project
- Option to record time without associating with a project
- Comprehensive timesheet editing with smart project handling:
  - Edit any timesheet field including employee, project, date, times, and lunch duration
  - Intelligent project dropdown retains associated projects even when they're completed
  - Clear visual indication of project status when editing timesheets
  - Prevention of orphaned records when modifying timesheet data
- Automatic calculation of hours with lunch break handling
- Special handling for overnight shifts
- Saturday premium pay:
  - $5.00/hour additional pay for Saturday work
  - Automatic visual indication of premium pay in timesheet listing
  - Premium automatically factored into payroll calculations

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
- Generate payroll reports with detailed breakdowns
- Employee dropdown search feature for filtering payroll reports:
  - Quick selection of employees from alphabetically-sorted dropdown menu
  - Comprehensive view of employee financial information
  - Display of detailed payment history and timesheet entries
  - Calculation of total hours worked and total amount paid
  - Clear interface for toggling between filtered and unfiltered views
- Record payments to employees with comprehensive deduction tracking
- Support for multiple deduction types (taxes, insurance, retirement, advances, etc.)
- Dynamic UI for adding/removing deductions with real-time calculations
- Detailed reporting showing both gross and net amounts
- Tooltips in reports to show deduction breakdowns
- Check payment tracking with check numbers and bank information

## Testing

### Test Framework

The application includes a comprehensive test suite using pytest with the following main components:

1. **Unit Tests**:
   - Model validation tests
   - Form validation tests
   - Route functionality tests

2. **Integration Tests**:
   - Project workflow tests (from creation to completion)
   - Payroll workflow tests (from timesheet entry to payment with deductions)
   - Authentication tests to ensure proper access control

3. **Edge Case Tests**:
   - Time boundary tests
   - Date boundary tests
   - Data validation tests
   - Error handling tests

4. **Complex Scenario Tests**:
   - Complete project lifecycle
   - Multiple project resource allocation
   - Employee status change impacts
   - Project status changes
   - Payroll deduction calculations

5. **Security and Validation Tests**:
   - Input sanitization
   - Numeric input validation
   - Data consistency
   - Performance with large queries
   - Transaction integrity
   - Authentication validation

6. **Payroll Deductions and Cash Flow Tests**:
   - Payroll deduction calculation tests
   - Project labor cost with payroll tests
   - Comprehensive cash flow tests
   - Payroll net amount consistency tests

7. **Net Profit Tests**:
   - Actual revenue calculation tests
   - Actual net profit calculation tests

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
- User authentication with secure password hashing
- Session management for login state
- Route protection with login_required decorator
- CSRF protection via Flask-WTF
- Input validation and sanitization
- Business rule enforcement

Recommended additions for production:
- Role-based access control
- Multi-factor authentication
- Password reset functionality
- User account management
- HTTPS configuration
- Environment variables for sensitive information (especially SECRET_KEY)
- Regular database backups
- Session timeout settings
- Login attempt limiting

## Troubleshooting

### Common Issues

#### Authentication Issues
- If you forget the default password, you can change it by running a Python script in the application context
- Default credentials are username: `patricia` and password: `Patri2025`

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

### Database Backup and Restoration

A robust automated backup and restoration system has been implemented to ensure data integrity and disaster recovery capabilities.

#### Automated Backup System

**Configuration:**
- **Schedule**: Daily backups at 3:00 AM (UTC)
- **Location**: `/root/backups/erp/`
- **Naming Convention**: `erp_db_backup_YYYY-MM-DD.db.gz`
- **Retention Period**: 30 days (older backups are automatically pruned)
- **Compression**: GZip compression to minimize storage requirements

**Components:**
- **Backup Script**: `/root/backup_erp_db.sh` - Creates compressed, date-stamped backups
- **Cron Job**: `/etc/cron.d/erp_backup` - Schedules automatic execution
- **Logging**: Detailed logs stored in `/root/backups/erp/backup_log.txt`

#### Database Restoration

**Restoration Tool:**
- **Script**: `/root/restore_erp_db.sh YYYY-MM-DD`
- **Safety Features**: Creates a pre-restoration backup before proceeding
- **Service Management**: Automatically handles stopping/starting the application

**Restoration Process:**
1. System creates a timestamped safety backup of the current database
2. ERP service is safely stopped
3. Selected backup is decompressed and restored
4. ERP service is restarted
5. Detailed feedback is provided on operation success

**Usage Example:**
```bash
# List available backups
/root/restore_erp_db.sh

# Restore from specific date
/root/restore_erp_db.sh 2025-04-03
```

**Manual Backup:**
To create an on-demand backup at any time:
```bash
/root/backup_erp_db.sh
```

## Financial Management System

The Financial Management System has been implemented to provide comprehensive tracking and analysis of the company's financial operations. This module includes tools for managing accounts payable, recording paid accounts, tracking monthly expenses, and generating financial reports with interactive visualizations.

### Data Models

#### Accounts Payable
- **Description**: Tracks unpaid vendor bills and their status
- **Key Fields**:
  - Vendor name
  - Description
  - Amount
  - Issue date
  - Due date
  - Payment method (Cash, Check, Transfer, Card, Other)
  - Status (Pending, Paid, Overdue)
  - Project association (optional)
- **Key Features**:
  - Status tracking with visual indicators
  - Due date alerts
  - Filtering by vendor, date range, and status
  - Summary statistics with total amounts

#### Paid Accounts
- **Description**: Records all payments made to vendors
- **Key Fields**:
  - Vendor name
  - Amount paid
  - Payment date
  - Payment method
  - Check number (for check payments)
  - Bank information (for check payments)
- **Key Features**:
  - Payment method breakdown
  - Date-based filtering
  - Total payments by method and vendor

#### Monthly Expenses
- **Description**: Tracks recurring business expenses by category
- **Key Fields**:
  - Description
  - Amount
  - Expense date
  - Category (Rent, Utilities, Insurance, Taxes, Materials, Tools, Payroll, Vehicle, Office, Travel, Marketing, Professional Services, Other)
  - Payment method
  - Project association (optional)
- **Key Features**:
  - Category-based filtering and reporting
  - Month-over-month expense comparison
  - Project-specific expense tracking

### Financial Reports

The Financial Reports dashboard provides a comprehensive view of the company's financial status with interactive visualizations and key metrics.

#### Dashboard Components
- **Summary Cards**:
  - Total Accounts Payable
  - Total Paid Accounts (current month)
  - Total Monthly Expenses (current month)
  - Net Cash Flow (income vs expenses)

#### Interactive Charts
- **Payment Status Summary**:
  - Visualization of pending, paid, and overdue amounts
  - Filtering by date range

- **Monthly Expense Categories**:
  - Pie chart showing distribution of expenses by category
  - Percentage breakdown with color coding

- **Cash Flow Analysis**:
  - Line chart comparing income vs expenses over time
  - Month-by-month trend visualization

- **Upcoming Payments**:
  - List of payments due in the next 30 days
  - Days-to-due indicators with color coding

#### Implementation Details
- Uses Chart.js for interactive visualizations
- Implements responsive design with Bootstrap 5
- Data refreshes on page load for real-time accuracy
- Optimized query structure for performance

## Future Enhancements

The following enhancements have been identified as priority items for future development:

### 1. Email Notifications System (HIGH PRIORITY)
- **Description**: Implement automated email notifications for critical business events
- **Key Features**:
  - Invoice due date reminders to clients and staff
  - Project deadline alerts and milestone notifications
  - Weekly summary reports of timesheet entries
  - Material inventory warnings when stock is low
  - Monthly financial summaries for management
- **Technical Approach**: Integrate Flask-Mail with scheduled tasks (using Celery or APScheduler)
- **Expected Benefits**: Proactive business management, improved cash flow, reduced missed deadlines

### 2. Dashboard Filters and Date Ranges (HIGH PRIORITY)
- **Description**: Enhance the analytics dashboard with filtering and date comparison capabilities
- **Key Features**:
  - Date range selection for all dashboard metrics and charts
  - Comparison views (year-over-year, month-over-month)
  - Filter by project, client, employee, or department
  - Save filter presets for commonly used views
- **Technical Approach**: Add JavaScript-based filtering with AJAX dashboard updates
- **Expected Benefits**: More granular business insights, better trend analysis, customized views for different roles

### 3. Client Portal (HIGH PRIORITY)
- **Description**: Create a limited-access portal for clients to view their project information
- **Key Features**:
  - Project status tracking and timeline visibility
  - Invoice viewing and online payment capabilities
  - Document sharing for project deliverables
  - Messaging system for client-team communication
- **Technical Approach**: Create separate client-focused Flask routes with client authentication
- **Expected Benefits**: Increased client satisfaction, reduced administrative overhead for status updates, faster payments

### 4. Data Import Functionality (HIGH PRIORITY)
- **Description**: Add bulk data import capabilities to complement existing export functionality
- **Key Features**:
  - CSV/Excel import for all major data types (projects, clients, expenses, etc.)
  - Data validation during import with error reporting
  - Template downloads for proper formatting
  - Scheduled imports for integration with other systems
- **Technical Approach**: Use pandas for data processing with format validation
- **Expected Benefits**: Faster data entry, reduced manual errors, easier integration with external systems

### Additional Future Enhancements

- Role-based access control
- Mobile optimization for field workers
- Integration with accounting software
- Advanced reporting and analytics
- Multi-factor authentication
- Quick search functionality across all data

## Technical Implementation Notes

### Dashboard Implementation
- Uses Chart.js for interactive data visualizations
- Implements responsive design with Bootstrap 5
- Calculates key metrics in Python code rather than in templates for better reliability
- Pre-processes data for visualizations on the server-side to optimize performance
- Uses appropriate text sizing classes (display-6) to ensure large numbers are displayed properly
- Ensures all financial figures fit within their containers without overflow issues

### UI Design Considerations

- **Numeric Display**: Large numbers (financial amounts, project counts, hours) use `display-6` class in dashboard and `h3` elements in reports to maintain proper layout regardless of value size
- **Responsive Breakpoints**: Layout adapts to different screen sizes with Bootstrap's grid system
- **Color Scheme**: Uses consistent Bootstrap color utilities (primary, success, warning, info) for information hierarchy
- **Card Components**: Cards are used as the primary UI component for displaying grouped information
- **Accessibility**: Maintains proper color contrast and text sizing for readability

### Export Functionality Implementation
- Uses pandas DataFrames for Excel file generation
  - Better handling of data formatting and column headers
  - Improved compatibility with various Excel versions
  - Support for custom column styling and formatting
- Implements PDF generation via FPDF
  - Uses temporary files for reliable PDF output
  - Handles different page orientations based on report complexity
  - Implements proper encoding for special characters
  - Ensures consistent formatting across different report types
- File serving uses appropriate MIME types for browser compatibility
- All export functionality is protected by the same authentication system

### Database Design
- The database schema is designed with normalization principles to minimize data redundancy and improve data integrity.
- Indexes are used on columns used in WHERE and JOIN clauses to improve query performance.
- Relationships between tables are established using foreign keys to maintain data consistency.
- The database is designed to support the application's functionality, including user authentication, project management, time tracking, and invoicing.

## Recent Enhancements

### Enhanced PDF Export with Comprehensive Totals

The PDF export functionality has been enhanced to automatically calculate and display totals for all numerical fields:

```python
def export_to_pdf(data, title, filename):
    """Helper function to export data to PDF with totals for numerical fields"""
    # ...
    # Calculate totals for numerical columns
    totals = {}
    for key in column_keys:
        totals[key] = 0
        
    # Process data and update totals
    for item in data:
        for key, value in item.items():
            # ...
            # Detect numerical values and add to totals
            string_value = str(value)
            if string_value.replace('.', '', 1).replace(',', '', 1).replace('$', '', 1).replace('-', '', 1).isdigit():
                clean_value = string_value.replace('$', '').replace(',', '')
                try:
                    totals[key] += float(clean_value)
                except ValueError:
                    pass
    
    # Display totals row with appropriate formatting
    pdf.set_font('Arial', 'B', 8)
    pdf.set_text_color(*header_blue)
    pdf.cell(0, 7, 'PROJECT SCOPE', 0, 1, 'L')
    # ...
```

Key improvements include:

1. **Intelligent Numerical Detection**: The system identifies numerical values even when formatted with currency symbols, commas, or other non-numeric characters
2. **Format-Aware Display**: Totals are displayed using the same formatting as the source data (currency, decimal places, etc.)
3. **Visual Distinction**: Totals row has a light gray background and bold text for clear separation
4. **Contextual Note**: Includes an explanatory note about the calculation method

### Custom Work Week Definition (Friday-Thursday)

Implemented a company-specific definition of the work week as running from Friday to Thursday instead of the standard Monday-Sunday:

```python
def get_week_start_end(dt=None):
    """Gets the start (Friday) and end (Thursday) dates of the work week for a given date.
    Work weeks are defined as running from Friday through Thursday.
    """
    dt = dt or date.today()
    # Calculate days to go back to reach Friday
    # weekday() returns: Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5, Sun=6
    # So to get to Friday: if today is Mon (0), go back 3 days; if today is Fri (4), go back 0 days, etc.
    days_to_friday = (dt.weekday() - 4) % 7
    start = dt - timedelta(days=days_to_friday)
    end = start + timedelta(days=6)  # 6 days after Friday is Thursday
    return start, end
```

This change affects:

1. **Dashboard Weekly Hours**: Hours displayed on the dashboard now reflect Friday-Thursday periods
2. **Payroll Reports**: All weekly payroll reports use Friday-Thursday as the standard period
3. **Timesheet Calculations**: Weekly timesheet summaries align with the custom work week definition

### Payment Method Summary Visualization

Enhanced the payroll report with a comprehensive payment summary that clearly separates Cash and Check payments and provides a grand total:

```html
<!-- Payment Summary Card -->
<div class="row mb-4">
    <div class="col-12">
        <div class="card border-primary">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0">Payment Summary</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-4">
                        <div class="card h-100 bg-light">
                            <div class="card-body text-center">
                                <h6 class="card-title text-success">Cash Payments</h6>
                                <h3 class="mb-2">${{ "%.2f"|format(payment_method_totals.CASH.total) }}</h3>
                                <!-- Payment count and percentage of total -->
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card h-100 bg-light">
                            <div class="card-body text-center">
                                <h6 class="card-title text-info">Check Payments</h6>
                                <h3 class="mb-2">${{ "%.2f"|format(payment_method_totals.CHECK.total) }}</h3>
                                <!-- Payment count and percentage of total -->
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card h-100 bg-dark text-white">
                            <div class="card-body text-center">
                                <h6 class="card-title">GRAND TOTAL</h6>
                                <h3 class="mb-2">${{ "%.2f"|format(payment_method_totals.CASH.total + payment_method_totals.CHECK.total) }}</h3>
                                <!-- Total payment count and hours -->
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
```

Key features of the payment summary include:

1. **Method-Specific Totals**: Clear separation of Cash and Check payment totals
2. **Payment Counts**: Display of how many payments were made using each method
3. **Percentage Visualization**: Visual indicators showing the proportion of each payment method
4. **Grand Total**: Prominent display of the combined total across all payment methods
5. **Hours Worked Context**: Inclusion of total hours worked during the period for context

### UI Improvements
{{ ... }}

### SQLAlchemy 2.0 Compatibility Updates

All database access patterns have been modernized to align with SQLAlchemy 2.0 best practices:

```python
# Old approach (deprecated)
employee = Employee.query.get(id)
project = Project.query.get_or_404(id)

# New approach
employee = db.session.get(Employee, id)

# With proper error handling for not found items
project = db.session.get(Project, id)
if not project:
    flash('Project not found.', 'danger')
    return redirect(url_for('projects')), 404
```

This update:
- Eliminates deprecation warnings
- Prepares the codebase for future SQLAlchemy 2.0 migration
- Improves error handling patterns
- Provides more explicit database access code

### Comprehensive Payroll Deductions System

A complete payroll deductions system has been implemented with the following features:

1. **PayrollDeduction Model**:
   - Linked to PayrollPayment via foreign key relationship
   - Supports multiple deduction types (taxes, insurance, retirement, advances, etc.)
   - Tracks description, amount, and deduction type
   - Includes notes field for additional context

2. **Enhanced PayrollPayment Model**:
   - Added gross_amount field to track pre-deduction amount
   - Implemented property methods to calculate net amount after deductions
   - Added relationship to PayrollDeduction for easy access to deductions
   - Includes check_number and bank_name fields for check payments
   - Properly initializes amount field to prevent NOT NULL constraint errors
   - Implements read-only properties for total_deductions and net_amount

3. **Dynamic UI for Deduction Management**:
   - JavaScript-powered interface for adding/removing deductions
   - Real-time calculation of net amount as deductions are added
   - User-friendly form with validation
   - Supports multiple deduction types with dropdown selection

4. **Enhanced Payroll Reports**:
   - Display both gross and net amounts
   - Detailed breakdown of deductions
   - Tooltips to show deduction details
   - Safe handling of edge cases where no deductions exist
   - Proper handling of payment method totals

5. **Form Validation Improvements**:
   - Enhanced validate_end_after_start function to work with both start_date and pay_period_start field names
   - Improved error handling for date validation
   - Added validation for check payment details

6. **Bug Fixes**:
   - Fixed NOT NULL constraint errors in PayrollPayment model
   - Fixed issue with total_deductions property being treated as writable
   - Resolved UndefinedError in payroll reports when no payments exist for certain methods
   - Improved error handling throughout the payroll workflow

### UI Improvements
{{ ... }}
