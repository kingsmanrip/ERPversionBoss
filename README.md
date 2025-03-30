# Mauricio PDQ ERP System

A comprehensive Enterprise Resource Planning (ERP) system designed specifically for Mauricio PDQ Paint & Drywall. This application helps manage employees, projects, timesheets, materials, expenses, invoices, and payroll in a single integrated platform.

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
- **Payroll Reporting**: Calculate payroll based on recorded timesheets with detailed breakdowns by payment method (Cash vs Check)
- **Payment Method Tracking**: Record and track payments by method (Cash/Check) with check numbers and bank information
- **Cost Analysis**: Automatic calculation of project costs and profitability
- **Responsive UI Design**: Optimized display of financial data with properly sized elements to ensure readability of large numbers

## Tech Stack

- **Backend**: Python with Flask framework
- **Database**: SQLite (via SQLAlchemy)
- **Frontend**: Bootstrap 5 for responsive design
- **Forms**: WTForms for form handling and validation
- **Testing**: Comprehensive pytest suite for validation

## Recent Updates (March 2025)

- **Enhanced Lunch Break Calculations**: Implemented precise rules for lunch break deductions
- **Improved Payment Method Tracking**: Added capabilities to record check numbers and bank names
- **Enhanced Payroll Reporting**: Added detailed breakdowns by payment method (Cash vs Check)
- **UI Improvements**: Optimized display of large financial values in dashboard and reports
- **Comprehensive Testing**: Added extensive test suite with all tests passing
- **Mock Data Generation**: Included a script to populate the system with realistic test data
- **SQLAlchemy 2.0 Compatibility**: Updated all database queries to use modern patterns
- **Enhanced Export Capabilities**: Added comprehensive export options in Excel, PDF, and CSV formats

## Installation

### Prerequisites

- Python 3.7 or higher
- Git (for cloning the repository)

### Setup Instructions

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
   # Option 1
   flask init-db

   # Option 2 (if above doesn't work)
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

5. **Run the application**:
   ```
   python app.py
   ```

6. **Access the application**:
   - Open your browser and navigate to: http://127.0.0.1:5000
   - Login with the default credentials (username: `patricia`, password: `Patri2025`)

7. **Run tests**:
   ```
   python -m pytest
   ```

## Recommended Workflow

### Initial Setup
1. Add employees through the Employees section
2. Create projects in the Projects section

### Daily Operations
1. Record timesheets for employees working on projects
2. Log materials purchased for projects
3. Track business expenses

### Financial Management
1. Generate payroll reports and record payments to employees
2. Create invoices for completed projects
3. Update project statuses as they progress
4. Monitor project profitability through the cost analysis features

## Project Structure

- `app.py` - Main application file with routes and configuration
- `models.py` - Database models and relationships
- `forms.py` - Form definitions using WTForms
- `templates/` - HTML templates for the web interface
- `instance/` - Contains the SQLite database file
- `static/` - Static files (CSS, JavaScript)
- `tests/` - Comprehensive test suite

## Database Schema

The application uses the following main models:
- **Employee**: Stores employee information and pay rates
- **Project**: Manages project details, status, and relationships to other models
- **Timesheet**: Records work hours with automatic calculation of hours and lunch breaks
- **Material**: Tracks materials used in projects with costs
- **Expense**: Records business expenses with categorization
- **PayrollPayment**: Manages employee payment processing
- **Invoice**: Handles client billing for projects

## Key Model Relationships

All relationships are properly set up with cascade behavior for reliable data management:
- Projects have timesheets, materials, expenses, and invoices
- Employees have timesheets and payroll payments
- Proper validation ensures data integrity across all models

## Security Notes

This version includes basic user authentication. For enhanced security in production:
- Enable HTTPS for secure data transmission
- Implement role-based access control for different user types
- Use environment variables for sensitive configuration (including SECRET_KEY)
- Store passwords using strong hashing methods (already implemented)
- Implement multi-factor authentication for sensitive operations
- Implement proper backup procedures for the database

## Troubleshooting

### Database Issues
- If you encounter database errors, check that the `instance` directory exists and has proper permissions
- For a fresh start, you can delete the database file in the `instance` directory and reinitialize it

### Port Already in Use
- If port 5000 is already in use, you can specify a different port:
  ```
  python app.py --port=5001
  ```

## Contributing

To contribute to this project:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is proprietary software developed for Mauricio PDQ Paint & Drywall.

## Contact

For support or inquiries, please contact the repository owner.
