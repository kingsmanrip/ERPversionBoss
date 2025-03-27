import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, Response
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from datetime import date, timedelta, datetime
from dotenv import load_dotenv
from flask_bootstrap import Bootstrap5
from functools import wraps
import flask_excel as excel
from fpdf import FPDF
import tempfile
import io
import pandas as pd

from models import db, Employee, Project, Timesheet, Material, Expense, PayrollPayment, Invoice, ProjectStatus, PaymentMethod, PaymentStatus, User
from forms import EmployeeForm, ProjectForm, TimesheetForm, MaterialForm, ExpenseForm, PayrollPaymentForm, InvoiceForm, LoginForm

load_dotenv()  # Load environment variables if needed

app = Flask(__name__)

# --- Configuration ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-default-hardcoded-secret-key')  # CHANGE THIS in production
# Use instance folder for the database
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(instance_path, "erp.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Initialize Extensions ---
db.init_app(app)
csrf = CSRFProtect(app)
bootstrap = Bootstrap5(app)  # Initialize Bootstrap5
excel.init_excel(app)  # Initialize Excel export

# --- Authentication utilities ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Helper Functions ---
def get_week_start_end(dt=None):
    """Gets the start (Monday) and end (Sunday) dates of the week for a given date."""
    dt = dt or date.today()
    start = dt - timedelta(days=dt.weekday())
    end = start + timedelta(days=6)
    return start, end

# --- Auth Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    # If already logged in, redirect to dashboard
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    """Handle user logout"""
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# --- Routes ---

@app.route('/')
@login_required
def index():
    """Dashboard"""
    # Total projects counter (instead of just active projects)
    total_projects = Project.query.count()
    active_projects = Project.query.filter(Project.status == ProjectStatus.IN_PROGRESS).count()
    
    # Project financial metrics - include all projects
    all_projects = Project.query.all()
    
    # Sort by profit margin (descending)
    sorted_projects = sorted(
        all_projects, 
        key=lambda p: p.profit_margin if p.profit_margin is not None else -999, 
        reverse=True
    )
    
    # Calculate progress bar widths for the top projects
    top_projects = sorted_projects[:5]
    for project in top_projects:
        # Calculate a width between 0-100% for the progress bar
        # Add 40% to profit margin to make small profit margins visible
        # but cap at 100%
        profit_margin = project.profit_margin or 0
        project.progress_width = max(0, min(100, profit_margin + 40))
    
    # Financial summary
    total_invoiced = db.session.query(db.func.sum(Invoice.amount)).scalar() or 0
    unpaid_invoices = db.session.query(db.func.sum(Invoice.amount)).filter(
        Invoice.status != PaymentStatus.PAID
    ).scalar() or 0
    
    # Timesheet summary for current week
    start_of_week, end_of_week = get_week_start_end()
    # Get timesheets directly instead of using the property in SQL
    weekly_timesheets = Timesheet.query.filter(
        Timesheet.date >= start_of_week,
        Timesheet.date <= end_of_week
    ).all()
    
    # Calculate hours in Python logic instead of SQL
    weekly_hours = sum(ts.calculated_hours for ts in weekly_timesheets)
    
    # Project status distribution
    project_status_counts = {}
    for status in ProjectStatus:
        project_status_counts[status.name] = Project.query.filter(Project.status == status).count()
    
    # Recent expenses
    recent_expenses = Expense.query.order_by(Expense.date.desc()).limit(5).all()
    expenses_total = db.session.query(db.func.sum(Expense.amount)).scalar() or 0
    
    # Monthly expense trend (last 5 months)
    today = date.today()
    monthly_expenses = []
    monthly_labels = []
    for i in range(4, -1, -1):
        month_date = today.replace(day=1) - timedelta(days=i*30)  # Approximate
        month_name = month_date.strftime('%b')
        monthly_labels.append(month_name)
        
        next_month = month_date.replace(day=28) + timedelta(days=4)  # Move to next month
        next_month = next_month.replace(day=1)  # First day of next month
        
        month_expenses = db.session.query(db.func.sum(Expense.amount)).filter(
            Expense.date >= month_date,
            Expense.date < next_month
        ).scalar() or 0
        
        monthly_expenses.append(round(month_expenses, 2))
    
    return render_template('index.html',
                          active_projects=active_projects,
                          total_projects=total_projects,
                          top_projects=top_projects,
                          recent_expenses=recent_expenses,
                          total_invoiced=total_invoiced,
                          unpaid_invoices=unpaid_invoices,
                          weekly_hours=weekly_hours,
                          project_status_counts=project_status_counts,
                          expenses_total=expenses_total,
                          monthly_expenses=monthly_expenses,
                          monthly_labels=monthly_labels)

# --- Employee Routes ---
@app.route('/employees')
@login_required
def employees():
    all_employees = Employee.query.order_by(Employee.name).all()
    return render_template('employees.html', employees=all_employees)

@app.route('/employee/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    form = EmployeeForm()
    if form.validate_on_submit():
        # Handle empty employee_id_str by setting it to None instead of empty string
        employee_id_str = form.employee_id_str.data if form.employee_id_str.data else None
        
        new_employee = Employee(
            name=form.name.data,
            employee_id_str=employee_id_str,
            contact_details=form.contact_details.data,
            pay_rate=form.pay_rate.data,
            payment_method_preference=PaymentMethod[form.payment_method_preference.data] if form.payment_method_preference.data else None,
            is_active=form.is_active.data,
            hire_date=form.hire_date.data
        )
        db.session.add(new_employee)
        db.session.commit()
        flash(f'Employee {new_employee.name} added successfully!', 'success')
        return redirect(url_for('employees'))
    return render_template('employee_form.html', form=form, title="Add Employee")

@app.route('/employee/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    employee = Employee.query.get_or_404(id)
    form = EmployeeForm(obj=employee)
    # Ensure correct enum loading for SelectField
    if request.method == 'GET' and employee.payment_method_preference:
        form.payment_method_preference.data = employee.payment_method_preference.name

    if form.validate_on_submit():
        employee.name = form.name.data
        # Handle empty employee_id_str by setting it to None instead of empty string
        employee.employee_id_str = form.employee_id_str.data if form.employee_id_str.data else None
        employee.contact_details = form.contact_details.data
        employee.pay_rate = form.pay_rate.data
        employee.payment_method_preference = PaymentMethod[form.payment_method_preference.data] if form.payment_method_preference.data else None
        employee.is_active = form.is_active.data
        employee.hire_date = form.hire_date.data
        db.session.commit()
        flash(f'Employee {employee.name} updated successfully!', 'success')
        return redirect(url_for('employees'))
    return render_template('employee_form.html', form=form, title="Edit Employee", employee=employee)

@app.route('/employee/delete/<int:id>', methods=['POST'])
@login_required
def delete_employee(id):
    employee = Employee.query.get_or_404(id)
    try:
        db.session.delete(employee)
        db.session.commit()
        flash(f'Employee {employee.name} deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting employee: {e}. They might have associated records.', 'danger')
    return redirect(url_for('employees'))

# --- Project Routes ---
@app.route('/projects')
@login_required
def projects():
    all_projects = Project.query.order_by(Project.start_date.desc()).all()
    return render_template('projects.html', projects=all_projects)

@app.route('/project/add', methods=['GET', 'POST'])
@login_required
def add_project():
    form = ProjectForm()
    if form.validate_on_submit():
        # Handle empty project_id_str by setting it to None instead of empty string
        project_id_str = form.project_id_str.data if form.project_id_str.data else None
        
        new_project = Project(
            name=form.name.data,
            project_id_str=project_id_str,
            client_name=form.client_name.data,
            location=form.location.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            contract_value=form.contract_value.data,
            description=form.description.data,
            status=ProjectStatus[form.status.data]
        )
        
        # Validate that end date is after start date if both are provided
        if not new_project.validate_dates() and form.start_date.data and form.end_date.data:
            flash('Error: End date must be on or after start date.', 'danger')
            return render_template('project_form.html', form=form, title="Add Project")
            
        db.session.add(new_project)
        db.session.commit()
        flash(f'Project {new_project.name} added successfully!', 'success')
        return redirect(url_for('projects'))
    return render_template('project_form.html', form=form, title="Add Project")

@app.route('/project/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_project(id):
    project = Project.query.get_or_404(id)
    form = ProjectForm(obj=project)
    # Handle enum loading for SelectField
    if request.method == 'GET':
        form.status.data = project.status.name

    if form.validate_on_submit():
        project.name = form.name.data
        # Handle empty project_id_str by setting it to None instead of empty string
        project.project_id_str = form.project_id_str.data if form.project_id_str.data else None
        project.client_name = form.client_name.data
        project.location = form.location.data
        project.start_date = form.start_date.data
        project.end_date = form.end_date.data
        project.contract_value = form.contract_value.data
        project.description = form.description.data
        project.status = ProjectStatus[form.status.data]  # Update status from form
        
        # Validate that end date is after start date if both are provided
        if not project.validate_dates() and form.start_date.data and form.end_date.data:
            flash('Error: End date must be on or after start date.', 'danger')
            return render_template('project_form.html', form=form, title="Edit Project", project=project)
            
        db.session.commit()
        flash(f'Project {project.name} updated successfully!', 'success')
        return redirect(url_for('projects'))
    return render_template('project_form.html', form=form, title="Edit Project", project=project)

@app.route('/project/view/<int:id>')
@login_required
def project_detail(id):
    project = Project.query.get_or_404(id)
    # Calculate costs (using properties defined in model)
    labor_cost = project.total_labor_cost
    material_cost = project.total_material_cost
    other_expenses = project.total_other_expenses
    total_cost = project.total_cost
    profit = project.profit

    # Fetch related items
    timesheets = Timesheet.query.filter_by(project_id=id).order_by(Timesheet.date.desc()).all()
    materials = Material.query.filter_by(project_id=id).order_by(Material.purchase_date.desc()).all()
    expenses = Expense.query.filter_by(project_id=id).order_by(Expense.date.desc()).all()
    invoices = Invoice.query.filter_by(project_id=id).order_by(Invoice.invoice_date.desc()).all()

    return render_template('project_detail.html',
                           project=project,
                           labor_cost=labor_cost,
                           material_cost=material_cost,
                           other_expenses=other_expenses,
                           total_cost=total_cost,
                           profit=profit,
                           timesheets=timesheets,
                           materials=materials,
                           expenses=expenses,
                           invoices=invoices)

# --- Timesheet Routes ---
@app.route('/timesheets')
@login_required
def timesheets():
    # Basic view - show all timesheets, maybe filter by week later
    page = request.args.get('page', 1, type=int)
    timesheet_list = Timesheet.query.join(Employee).join(Project)\
                        .order_by(Timesheet.date.desc(), Employee.name)\
                        .paginate(page=page, per_page=20)  # Add pagination
    return render_template('timesheets.html', timesheets=timesheet_list)

@app.route('/timesheet/add', methods=['GET', 'POST'])
@login_required
def add_timesheet():
    form = TimesheetForm()
    
    # Populate the choices for employees and projects
    with app.app_context():
        # Only show active employees in the dropdown
        form.employee_id.choices = [(e.id, e.name) for e in Employee.query.filter_by(is_active=True).order_by(Employee.name).all()]
        form.project_id.choices = [(p.id, p.name) for p in Project.query.filter(Project.status != ProjectStatus.PAID).order_by(Project.name).all()]
    
    if form.validate_on_submit():
        # Create a new timesheet instance
        new_timesheet = Timesheet(
            employee_id=form.employee_id.data,
            project_id=form.project_id.data,
            date=form.date.data,
            entry_time=form.entry_time.data,
            exit_time=form.exit_time.data,
            lunch_duration_minutes=form.lunch_duration_minutes.data
        )
        
        # Validate timesheet entry
        is_valid, message = new_timesheet.is_valid()
        if not is_valid:
            flash(f'Error: {message}', 'danger')
            return render_template('timesheet_form.html', form=form, title="Add Timesheet Entry")
        
        # Check if employee is active
        employee = Employee.query.get(form.employee_id.data)
        if not employee.is_active:
            flash('Cannot create timesheet entry for inactive employee.', 'danger')
            return render_template('timesheet_form.html', form=form, title="Add Timesheet Entry")
        
        # Check for overlapping timesheet entries
        existing_timesheet = Timesheet.query.filter_by(
            employee_id=form.employee_id.data,
            date=form.date.data
        ).filter(
            ((Timesheet.entry_time <= form.entry_time.data) & (Timesheet.exit_time > form.entry_time.data)) |
            ((Timesheet.entry_time < form.exit_time.data) & (Timesheet.exit_time >= form.exit_time.data)) |
            ((Timesheet.entry_time >= form.entry_time.data) & (Timesheet.exit_time <= form.exit_time.data))
        ).first()
        
        if existing_timesheet:
            flash('Warning: This timesheet entry overlaps with an existing entry.', 'warning')
        
        db.session.add(new_timesheet)
        db.session.commit()
        flash('Timesheet entry added successfully!', 'success')
        return redirect(url_for('timesheets'))
    
    return render_template('timesheet_form.html', form=form, title="Add Timesheet Entry")

# --- Material Routes ---
@app.route('/materials')
@login_required
def materials():
    all_materials = Material.query.join(Project).order_by(Material.purchase_date.desc()).all()
    return render_template('materials.html', materials=all_materials)

@app.route('/material/add', methods=['GET', 'POST'])
@login_required
def add_material():
    form = MaterialForm()
    form.project_id.choices = [(p.id, p.name) for p in Project.query.order_by('name')]

    if form.validate_on_submit():
        new_material = Material(
            project_id=form.project_id.data,
            description=form.description.data,
            supplier=form.supplier.data,
            cost=form.cost.data,
            purchase_date=form.purchase_date.data,
            category=form.category.data
        )
        db.session.add(new_material)
        db.session.commit()
        flash('Material added successfully!', 'success')
        return redirect(url_for('materials'))

    if not form.is_submitted():
        form.purchase_date.data = date.today()

    return render_template('material_form.html', form=form, title="Add Material")

# --- Expense Routes ---
@app.route('/expenses')
@login_required
def expenses():
    all_expenses = Expense.query.order_by(Expense.date.desc()).all()
    return render_template('expenses.html', expenses=all_expenses)

@app.route('/expense/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    form = ExpenseForm()
    # Add empty choice + projects
    form.project_id.choices = [('', '-- None --')] + [(p.id, p.name) for p in Project.query.order_by('name')]

    if form.validate_on_submit():
        new_expense = Expense(
            description=form.description.data,
            category=form.category.data,
            amount=form.amount.data,
            date=form.date.data,
            supplier_vendor=form.supplier_vendor.data,
            payment_method=PaymentMethod[form.payment_method.data] if form.payment_method.data else None,
            payment_status=PaymentStatus[form.payment_status.data],
            due_date=form.due_date.data,
            # Handle optional project link
            project_id=form.project_id.data if form.project_id.data else None
        )
        db.session.add(new_expense)
        db.session.commit()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('expenses'))

    if not form.is_submitted():
        form.date.data = date.today()
        form.payment_status.data = PaymentStatus.PENDING.name  # Default status

    return render_template('expense_form.html', form=form, title="Add Expense")

# --- Payroll Routes ---
@app.route('/payroll/record-payment', methods=['GET', 'POST'])
@login_required
def record_payroll_payment():
    form = PayrollPaymentForm()
    # Populate employee choices
    form.employee_id.choices = [(e.id, e.name) for e in Employee.query.order_by(Employee.name).all()]
    
    if form.validate_on_submit():
        new_payment = PayrollPayment(
            employee_id=form.employee_id.data,
            pay_period_start=form.pay_period_start.data,
            pay_period_end=form.pay_period_end.data,
            amount=form.amount.data,
            payment_date=form.payment_date.data,
            payment_method=PaymentMethod[form.payment_method.data],
            notes=form.notes.data
        )
        
        # Validate that end date is after start date
        if not new_payment.validate_dates():
            flash('Error: Pay period end date must be on or after start date.', 'danger')
            return render_template('payroll_payment_form.html', form=form, title="Record Payroll Payment")
            
        db.session.add(new_payment)
        db.session.commit()
        flash('Payment recorded successfully!', 'success')
        return redirect(url_for('payroll_report'))
    
    return render_template('payroll_payment_form.html', form=form, title="Record Payment")

@app.route('/payroll/report')
@login_required
def payroll_report():
    """Basic report showing weekly hours and recorded payments"""
    target_date_str = request.args.get('date')
    target_date = date.today()
    if target_date_str:
        try:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash("Invalid date format. Using today's date.", 'warning')

    start_of_week, end_of_week = get_week_start_end(target_date)

    # 1. Calculate hours worked per employee for the selected week
    employees = Employee.query.filter_by(is_active=True).all()
    weekly_hours_data = {}
    for emp in employees:
        timesheets_this_week = Timesheet.query.filter(
            Timesheet.employee_id == emp.id,
            Timesheet.date >= start_of_week,
            Timesheet.date <= end_of_week
        ).all()
        total_hours = sum(ts.calculated_hours for ts in timesheets_this_week)
        potential_pay = total_hours * emp.pay_rate
        weekly_hours_data[emp.id] = {
            'employee': emp,
            'total_hours': total_hours,
            'potential_pay': potential_pay,
            'timesheets': timesheets_this_week
        }

    # 2. Get recorded payments for that period (or overlapping)
    recorded_payments = PayrollPayment.query.filter(
        # Simple overlap check, might need refinement
        PayrollPayment.pay_period_end >= start_of_week,
        PayrollPayment.pay_period_start <= end_of_week
    ).order_by(PayrollPayment.payment_date.desc()).all()

    # Add payment info to the weekly data
    for payment in recorded_payments:
        if payment.employee_id in weekly_hours_data:
             if 'payments' not in weekly_hours_data[payment.employee_id]:
                 weekly_hours_data[payment.employee_id]['payments'] = []
             weekly_hours_data[payment.employee_id]['payments'].append(payment)

    return render_template('payroll_report.html',
                           weekly_data=weekly_hours_data.values(),
                           recorded_payments=recorded_payments,
                           start_date=start_of_week,
                           end_date=end_of_week,
                           target_date_str=target_date.strftime('%Y-%m-%d'))

# --- Invoice Routes (Basic CRUD) ---
@app.route('/invoices')
@login_required
def invoices():
    all_invoices = Invoice.query.join(Project).order_by(Invoice.invoice_date.desc()).all()
    return render_template('invoices.html', invoices=all_invoices)

@app.route('/invoice/add', methods=['GET', 'POST'])
@login_required
def add_invoice():
    form = InvoiceForm()
    # Populate project choices
    form.project_id.choices = [(p.id, p.name) for p in Project.query.filter(
        Project.status.in_([ProjectStatus.COMPLETED, ProjectStatus.INVOICED])
    ).order_by(Project.name).all()]
    
    if form.validate_on_submit():
        new_invoice = Invoice(
            project_id=form.project_id.data,
            invoice_number=form.invoice_number.data,
            invoice_date=form.invoice_date.data,
            due_date=form.due_date.data,
            amount=form.amount.data,
            status=PaymentStatus[form.status.data],
            payment_received_date=form.payment_received_date.data if form.status.data == PaymentStatus.PAID.name else None
        )
        
        # Validate that due date is after invoice date if provided
        if not new_invoice.validate_dates() and form.invoice_date.data and form.due_date.data:
            flash('Error: Due date must be on or after invoice date.', 'danger')
            return render_template('invoice_form.html', form=form, title="Add Invoice")
            
        # If status is PAID, need payment date
        if form.status.data == PaymentStatus.PAID.name and not form.payment_received_date.data:
            flash('Error: Payment received date is required when status is PAID.', 'danger')
            return render_template('invoice_form.html', form=form, title="Add Invoice")
        
        db.session.add(new_invoice)
        
        # Update project status if invoice is being created
        project = Project.query.get(form.project_id.data)
        if project.status == ProjectStatus.COMPLETED:
            project.status = ProjectStatus.INVOICED
        
        # Update project status if invoice is marked as paid
        if form.status.data == PaymentStatus.PAID.name:
            project.status = ProjectStatus.PAID
            
        db.session.commit()
        flash('Invoice added successfully!', 'success')
        return redirect(url_for('invoices'))
    
    return render_template('invoice_form.html', form=form, title="Add Invoice")

@app.route('/invoice/delete/<int:id>', methods=['POST'])
@login_required
def delete_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    try:
        db.session.delete(invoice)
        db.session.commit()
        flash(f'Invoice {invoice.invoice_number} deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting invoice: {e}', 'danger')
    return redirect(url_for('invoices'))

# --- Export Routes ---
@app.route('/export/<data_type>/<format>')
@login_required
def export_data(data_type, format):
    """Export data to Excel or PDF"""
    if data_type == 'invoices':
        return export_invoices(format)
    elif data_type == 'projects':
        return export_projects(format)
    elif data_type == 'timesheets':
        return export_timesheets(format)
    elif data_type == 'expenses':
        return export_expenses(format)
    else:
        flash(f'Export type {data_type} not supported', 'danger')
        return redirect(url_for('index'))

def export_invoices(format):
    """Export invoices to Excel or PDF"""
    invoices = Invoice.query.all()
    
    if format == 'excel':
        # Prepare data for Excel
        data = []
        for invoice in invoices:
            project = Project.query.get(invoice.project_id)
            data.append({
                'Invoice #': invoice.invoice_number,
                'Date': invoice.date.strftime('%Y-%m-%d'),
                'Project': project.name if project else 'N/A',
                'Client': project.client_name if project else 'N/A',
                'Amount': f"${invoice.amount:.2f}",
                'Status': invoice.status.name
            })
            
        df = pd.DataFrame(data)
        excel_file = io.BytesIO()
        df.to_excel(excel_file, index=False, engine='openpyxl')
        excel_file.seek(0)
        
        return send_file(
            excel_file,
            as_attachment=True,
            download_name='Invoices_Report.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    elif format == 'pdf':
        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Add title
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Invoices Report', 0, 1, 'C')
        pdf.ln(5)
        
        # Add header
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(25, 10, 'Invoice #', 1)
        pdf.cell(25, 10, 'Date', 1)
        pdf.cell(40, 10, 'Project', 1)
        pdf.cell(40, 10, 'Client', 1)
        pdf.cell(30, 10, 'Amount', 1)
        pdf.cell(30, 10, 'Status', 1)
        pdf.ln()
        
        # Add data
        pdf.set_font('Arial', '', 10)
        for invoice in invoices:
            project = Project.query.get(invoice.project_id)
            pdf.cell(25, 10, str(invoice.invoice_number), 1)
            pdf.cell(25, 10, invoice.date.strftime('%Y-%m-%d'), 1)
            pdf.cell(40, 10, (project.name if project else 'N/A')[:20], 1)
            pdf.cell(40, 10, (project.client_name if project else 'N/A')[:20], 1)
            pdf.cell(30, 10, f"${invoice.amount:.2f}", 1)
            pdf.cell(30, 10, invoice.status.name, 1)
            pdf.ln()

        # Create temp file and write PDF to it
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            pdf_path = tmp.name
            pdf.output(pdf_path)
            
        # Return the created PDF file
        return send_file(
            pdf_path,
            as_attachment=True, 
            download_name='Invoices_Report.pdf',
            mimetype='application/pdf'
        )
    
    else:
        flash(f'Export format {format} not supported', 'danger')
        return redirect(url_for('invoices'))

def export_projects(format):
    """Export projects to Excel or PDF"""
    projects = Project.query.all()
    
    if format == 'excel':
        # Prepare data for Excel
        data = []
        for project in projects:
            data.append({
                'Project ID': project.id,
                'Name': project.name,
                'Client': project.client_name,
                'Status': project.status.name,
                'Start Date': project.start_date.strftime('%Y-%m-%d') if project.start_date else 'N/A',
                'End Date': project.end_date.strftime('%Y-%m-%d') if project.end_date else 'N/A',
                'Budget': f"${project.budget:.2f}" if project.budget else 'N/A',
                'Profit Margin': f"{project.profit_margin:.1f}%" if project.profit_margin is not None else 'N/A'
            })
            
        df = pd.DataFrame(data)
        excel_file = io.BytesIO()
        df.to_excel(excel_file, index=False, engine='openpyxl')
        excel_file.seek(0)
        
        return send_file(
            excel_file,
            as_attachment=True,
            download_name='Projects_Report.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    elif format == 'pdf':
        # Create PDF
        pdf = FPDF()
        pdf.add_page('L')  # Landscape mode for more columns
        
        # Add title
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Projects Report', 0, 1, 'C')
        pdf.ln(5)
        
        # Add header
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(15, 10, 'ID', 1)
        pdf.cell(45, 10, 'Name', 1)
        pdf.cell(40, 10, 'Client', 1)
        pdf.cell(25, 10, 'Status', 1)
        pdf.cell(25, 10, 'Start Date', 1)
        pdf.cell(25, 10, 'End Date', 1)
        pdf.cell(25, 10, 'Budget', 1)
        pdf.cell(25, 10, 'Profit Margin', 1)
        pdf.ln()
        
        # Add data
        pdf.set_font('Arial', '', 9)
        for project in projects:
            pdf.cell(15, 10, str(project.id), 1)
            pdf.cell(45, 10, project.name[:22], 1)
            pdf.cell(40, 10, project.client_name[:20], 1)
            pdf.cell(25, 10, project.status.name, 1)
            pdf.cell(25, 10, project.start_date.strftime('%Y-%m-%d') if project.start_date else 'N/A', 1)
            pdf.cell(25, 10, project.end_date.strftime('%Y-%m-%d') if project.end_date else 'N/A', 1)
            pdf.cell(25, 10, f"${project.budget:.2f}" if project.budget else 'N/A', 1)
            pdf.cell(25, 10, f"{project.profit_margin:.1f}%" if project.profit_margin is not None else 'N/A', 1)
            pdf.ln()

        # Create temp file and write PDF to it
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            pdf_path = tmp.name
            pdf.output(pdf_path)
            
        # Return the created PDF file
        return send_file(
            pdf_path,
            as_attachment=True, 
            download_name='Projects_Report.pdf',
            mimetype='application/pdf'
        )
    
    else:
        flash(f'Export format {format} not supported', 'danger')
        return redirect(url_for('projects'))

def export_timesheets(format):
    """Export timesheets to Excel or PDF"""
    timesheets = Timesheet.query.order_by(Timesheet.date.desc()).all()
    
    if format == 'excel':
        # Prepare data for Excel
        data = []
        for timesheet in timesheets:
            employee = Employee.query.get(timesheet.employee_id)
            project = Project.query.get(timesheet.project_id)
            data.append({
                'Date': timesheet.date.strftime('%Y-%m-%d'),
                'Employee': employee.name if employee else 'N/A',
                'Project': project.name if project else 'N/A',
                'Start Time': timesheet.start_time.strftime('%H:%M') if timesheet.start_time else 'N/A',
                'End Time': timesheet.end_time.strftime('%H:%M') if timesheet.end_time else 'N/A',
                'Lunch (hrs)': timesheet.lunch_hours,
                'Total Hours': timesheet.total_hours
            })
            
        df = pd.DataFrame(data)
        excel_file = io.BytesIO()
        df.to_excel(excel_file, index=False, engine='openpyxl')
        excel_file.seek(0)
        
        return send_file(
            excel_file,
            as_attachment=True,
            download_name='Timesheets_Report.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    elif format == 'pdf':
        # Create PDF
        pdf = FPDF()
        pdf.add_page('L')  # Landscape for more columns
        
        # Add title
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Timesheets Report', 0, 1, 'C')
        pdf.ln(5)
        
        # Add header
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(25, 10, 'Date', 1)
        pdf.cell(40, 10, 'Employee', 1)
        pdf.cell(60, 10, 'Project', 1)
        pdf.cell(25, 10, 'Start Time', 1)
        pdf.cell(25, 10, 'End Time', 1)
        pdf.cell(25, 10, 'Lunch (hrs)', 1)
        pdf.cell(25, 10, 'Total Hours', 1)
        pdf.ln()
        
        # Add data
        pdf.set_font('Arial', '', 9)
        for timesheet in timesheets:
            employee = Employee.query.get(timesheet.employee_id)
            project = Project.query.get(timesheet.project_id)
            pdf.cell(25, 10, timesheet.date.strftime('%Y-%m-%d'), 1)
            pdf.cell(40, 10, (employee.name if employee else 'N/A')[:20], 1)
            pdf.cell(60, 10, (project.name if project else 'N/A')[:30], 1)
            pdf.cell(25, 10, timesheet.start_time.strftime('%H:%M') if timesheet.start_time else 'N/A', 1)
            pdf.cell(25, 10, timesheet.end_time.strftime('%H:%M') if timesheet.end_time else 'N/A', 1)
            pdf.cell(25, 10, str(timesheet.lunch_hours), 1)
            pdf.cell(25, 10, str(timesheet.total_hours), 1)
            pdf.ln()
        
        # Create temp file and write PDF to it
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            pdf_path = tmp.name
            pdf.output(pdf_path)
            
        # Return the created PDF file
        return send_file(
            pdf_path,
            as_attachment=True, 
            download_name='Timesheets_Report.pdf',
            mimetype='application/pdf'
        )
    
    else:
        flash(f'Export format {format} not supported', 'danger')
        return redirect(url_for('timesheets'))

def export_expenses(format):
    """Export expenses to Excel or PDF"""
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    
    if format == 'excel':
        # Prepare data for Excel
        data = []
        for expense in expenses:
            project = Project.query.get(expense.project_id) if expense.project_id else None
            data.append({
                'Date': expense.date.strftime('%Y-%m-%d'),
                'Description': expense.description,
                'Category': expense.category,
                'Amount': f"${expense.amount:.2f}",
                'Project': project.name if project else 'N/A',
                'Payment Method': expense.payment_method.name if expense.payment_method else 'N/A',
                'Status': expense.payment_status.name if expense.payment_status else 'N/A'
            })
            
        df = pd.DataFrame(data)
        excel_file = io.BytesIO()
        df.to_excel(excel_file, index=False, engine='openpyxl')
        excel_file.seek(0)
        
        return send_file(
            excel_file,
            as_attachment=True,
            download_name='Expenses_Report.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    elif format == 'pdf':
        # Create PDF
        pdf = FPDF()
        pdf.add_page('L')  # Landscape for more columns
        
        # Add title
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Expenses Report', 0, 1, 'C')
        pdf.ln(5)
        
        # Add header
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(25, 10, 'Date', 1)
        pdf.cell(60, 10, 'Description', 1)
        pdf.cell(30, 10, 'Category', 1)
        pdf.cell(25, 10, 'Amount', 1)
        pdf.cell(60, 10, 'Project', 1)
        pdf.cell(30, 10, 'Payment Method', 1)
        pdf.cell(25, 10, 'Status', 1)
        pdf.ln()
        
        # Add data
        pdf.set_font('Arial', '', 9)
        for expense in expenses:
            project = Project.query.get(expense.project_id) if expense.project_id else None
            pdf.cell(25, 10, expense.date.strftime('%Y-%m-%d'), 1)
            pdf.cell(60, 10, expense.description[:30], 1)
            pdf.cell(30, 10, expense.category[:15], 1)
            pdf.cell(25, 10, f"${expense.amount:.2f}", 1)
            pdf.cell(60, 10, (project.name if project else 'N/A')[:30], 1)
            pdf.cell(30, 10, expense.payment_method.name if expense.payment_method else 'N/A', 1)
            pdf.cell(25, 10, expense.payment_status.name if expense.payment_status else 'N/A', 1)
            pdf.ln()
        
        # Create temp file and write PDF to it
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            pdf_path = tmp.name
            pdf.output(pdf_path)
            
        # Return the created PDF file
        return send_file(
            pdf_path,
            as_attachment=True, 
            download_name='Expenses_Report.pdf',
            mimetype='application/pdf'
        )
    
    else:
        flash(f'Export format {format} not supported', 'danger')
        return redirect(url_for('expenses'))

# --- Future Enhancements Routes ---
@app.route('/future-enhancements')
@login_required
def future_enhancements():
    """Display future enhancement plans and suggestion form"""
    # Predefined enhancements based on documentation
    enhancements = [
        {
            'title': 'Role-Based Authentication',
            'description': 'Expand the existing authentication system to include role-based permissions for administrators, managers, and staff, allowing different access levels to various features.',
            'priority': 'High'
        },
        {
            'title': 'Multi-Factor Authentication',
            'description': 'Enhance security by implementing multi-factor authentication options such as email verification codes or authenticator apps.',
            'priority': 'Medium'
        },
        {
            'title': 'Enhanced Analytics Dashboard',
            'description': 'Expand the current dashboard with more interactive drill-down capabilities, data filtering options, and custom date range selections.',
            'priority': 'Medium'
        },
        {
            'title': 'Document Management',
            'description': 'Upload and store project-related documents such as contracts, designs, and client communications directly in the system.',
            'priority': 'Medium'
        },
        {
            'title': 'Client Portal',
            'description': 'Allow clients to view project status, approve work, and access invoices through a secure client portal.',
            'priority': 'Medium'
        },
        {
            'title': 'PDF Export',
            'description': 'Generate downloadable PDF reports, invoices, and timesheets for offline sharing and record-keeping.',
            'priority': 'Medium'
        },
        {
            'title': 'Email Notifications',
            'description': 'Send automatic updates for key events such as invoice due dates, project milestones, and payment confirmations.',
            'priority': 'Low'
        },
        {
            'title': 'Mobile Application',
            'description': 'Develop a companion app for field use, allowing employees to log time and materials directly from job sites.',
            'priority': 'High'
        },
        {
            'title': 'Inventory Management',
            'description': 'Track inventory levels and automate reordering to ensure materials are always available when needed.',
            'priority': 'Medium'
        },
        {
            'title': 'Integration with Accounting Software',
            'description': 'Connect with accounting and tax software to streamline financial reporting and tax preparation.',
            'priority': 'Medium'
        },
        {
            'title': 'Electronic Signatures',
            'description': 'Enable digital signing of documents for contracts, approvals, and other paperwork.',
            'priority': 'Low'
        },
        {
            'title': 'Password Reset Functionality',
            'description': 'Implement a self-service password reset feature that allows users to reset their passwords via email verification.',
            'priority': 'Medium'
        },
        {
            'title': 'User Profile Management',
            'description': 'Allow users to update their profile information and preferences, including password changes and notification settings.',
            'priority': 'Low'
        }
    ]
    
    # Form for suggesting new enhancements
    from forms import EnhancementSuggestionForm
    form = EnhancementSuggestionForm()
    
    return render_template('future_enhancements.html', enhancements=enhancements, form=form)

@app.route('/suggest-enhancement', methods=['POST'])
@login_required
def suggest_enhancement():
    """Handle enhancement suggestions"""
    from forms import EnhancementSuggestionForm
    form = EnhancementSuggestionForm()
    
    if form.validate_on_submit():
        # In a real implementation, you would save this to a database
        # For now, just show a success message
        flash(f'Thank you for your enhancement suggestion: "{form.title.data}". Our team will review it!', 'success')
        return redirect(url_for('future_enhancements'))
    
    # If form validation fails, return to the page with errors
    enhancements = []  # You would need to repopulate this
    flash('Please correct the errors in your submission.', 'danger')
    return render_template('future_enhancements.html', enhancements=enhancements, form=form)

# --- Create DB tables ---
@app.cli.command('init-db')
def init_db_command():
    """Creates the database tables."""
    with app.app_context():
        db.create_all()
    print('Initialized the database.')

# --- Main execution ---
if __name__ == '__main__':
    with app.app_context():
        # Create database tables if they don't exist
        db.create_all()
        
        # Create default user if it doesn't exist
        if not User.query.filter_by(username='patricia').first():
            default_user = User(username='patricia')
            default_user.set_password('Patri2025')
            db.session.add(default_user)
            db.session.commit()
            print('Created default user: patricia')
            
    app.run(debug=True, host='0.0.0.0')  # Runs on localhost and network IP