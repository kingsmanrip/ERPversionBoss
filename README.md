# Mauricio PDQ ERP System

A comprehensive Enterprise Resource Planning (ERP) system designed specifically for Mauricio PDQ Paint & Drywall. This application helps manage employees, projects, timesheets, materials, expenses, invoices, and payroll in a single integrated platform.

## Features

- **Employee Management**: Track employee information, pay rates, and contact details
- **Project Management**: Manage client projects with status tracking and financial details
- **Time Tracking**: Record employee hours worked on specific projects
- **Materials Management**: Track materials used for each project
- **Expense Tracking**: Monitor business expenses with or without project association
- **Invoicing**: Generate and track invoices for completed projects
- **Payroll Reporting**: Calculate payroll based on recorded timesheets

## Tech Stack

- **Backend**: Python with Flask framework
- **Database**: SQLite (via SQLAlchemy)
- **Frontend**: Bootstrap 5 for responsive design
- **Forms**: WTForms for form handling and validation

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

## Project Structure

- `app.py` - Main application file with routes and configuration
- `models.py` - Database models and relationships
- `forms.py` - Form definitions using WTForms
- `templates/` - HTML templates for the web interface
- `instance/` - Contains the SQLite database file
- `static/` - Static files (CSS, JavaScript)

## Database Schema

The application uses the following main models:
- Employee
- Project
- Timesheet
- Material
- Expense
- PayrollPayment
- Invoice

## Security Notes

This basic version doesn't include user authentication. For production use, consider:
- Adding user authentication
- Using environment variables for sensitive configuration
- Implementing proper backup procedures for the database

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
