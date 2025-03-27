import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from datetime import date, timedelta, datetime
from dotenv import load_dotenv
from flask_bootstrap import Bootstrap5

from models import db, Employee, Project, Timesheet, Material, Expense, PayrollPayment, Invoice, ProjectStatus, PaymentMethod, PaymentStatus
from forms import EmployeeForm, ProjectForm, TimesheetForm, MaterialForm, ExpenseForm, PayrollPaymentForm, InvoiceForm

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

# --- Helper Functions ---
def get_week_start_end(dt=None):
    """Gets the start (Monday) and end (Sunday) dates of the week for a given date."""
    dt = dt or date.today()
    start = dt - timedelta(days=dt.weekday())
    end = start + timedelta(days=6)
    return start, end

# --- Routes ---

@app.route('/')
def index():
    """Dashboard"""
    active_projects = Project.query.filter(Project.status == ProjectStatus.IN_PROGRESS).count()
    # Add more dashboard data queries here (e.g., upcoming payments, cash position simplified)
    recent_expenses = Expense.query.order_by(Expense.date.desc()).limit(5).all()
    return render_template('index.html',
                           active_projects=active_projects,
                           recent_expenses=recent_expenses)

# --- Employee Routes ---
@app.route('/employees')
def employees():
    all_employees = Employee.query.order_by(Employee.name).all()
    return render_template('employees.html', employees=all_employees)

@app.route('/employee/add', methods=['GET', 'POST'])
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
def projects():
    all_projects = Project.query.order_by(Project.start_date.desc()).all()
    return render_template('projects.html', projects=all_projects)

@app.route('/project/add', methods=['GET', 'POST'])
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
        db.session.add(new_project)
        db.session.commit()
        flash(f'Project {new_project.name} added successfully!', 'success')
        return redirect(url_for('projects'))
    return render_template('project_form.html', form=form, title="Add Project")

@app.route('/project/edit/<int:id>', methods=['GET', 'POST'])
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
        db.session.commit()
        flash(f'Project {project.name} updated successfully!', 'success')
        return redirect(url_for('projects'))
    return render_template('project_form.html', form=form, title="Edit Project", project=project)

@app.route('/project/view/<int:id>')
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
def timesheets():
    # Basic view - show all timesheets, maybe filter by week later
    page = request.args.get('page', 1, type=int)
    timesheet_list = Timesheet.query.join(Employee).join(Project)\
                        .order_by(Timesheet.date.desc(), Employee.name)\
                        .paginate(page=page, per_page=20)  # Add pagination
    return render_template('timesheets.html', timesheets=timesheet_list)


@app.route('/timesheet/add', methods=['GET', 'POST'])
def add_timesheet():
    form = TimesheetForm()
    # Populate choices dynamically
    form.employee_id.choices = [(e.id, e.name) for e in Employee.query.filter_by(is_active=True).order_by('name')]
    form.project_id.choices = [(p.id, p.name) for p in Project.query.filter(Project.status.in_([ProjectStatus.PENDING, ProjectStatus.IN_PROGRESS])).order_by('name')]

    if form.validate_on_submit():
        # Simple validation for times
        if form.exit_time.data <= form.entry_time.data:
             flash('Exit time must be after entry time.', 'warning')
             return render_template('timesheet_form.html', form=form, title="Add Timesheet Entry")

        new_entry = Timesheet(
            employee_id=form.employee_id.data,
            project_id=form.project_id.data,
            date=form.date.data,
            entry_time=form.entry_time.data,
            exit_time=form.exit_time.data,
            lunch_duration_minutes=form.lunch_duration_minutes.data
        )
        db.session.add(new_entry)
        db.session.commit()
        flash('Timesheet entry added successfully!', 'success')
        return redirect(url_for('timesheets'))

    # Pre-fill date if not postback
    if not form.is_submitted():
        form.date.data = date.today()

    return render_template('timesheet_form.html', form=form, title="Add Timesheet Entry")

# --- Material Routes ---
@app.route('/materials')
def materials():
    all_materials = Material.query.join(Project).order_by(Material.purchase_date.desc()).all()
    return render_template('materials.html', materials=all_materials)

@app.route('/material/add', methods=['GET', 'POST'])
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
def expenses():
    all_expenses = Expense.query.order_by(Expense.date.desc()).all()
    return render_template('expenses.html', expenses=all_expenses)

@app.route('/expense/add', methods=['GET', 'POST'])
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
@app.route('/payroll/record_payment', methods=['GET', 'POST'])
def record_payroll_payment():
    form = PayrollPaymentForm()
    form.employee_id.choices = [(e.id, e.name) for e in Employee.query.filter_by(is_active=True).order_by('name')]

    if form.validate_on_submit():
        new_payment = PayrollPayment(
            employee_id=form.employee_id.data,
            pay_period_start=form.pay_period_start.data,
            pay_period_end=form.pay_period_end.data,
            amount=form.amount.data,
            payment_date=form.payment_date.data,
            payment_method=PaymentMethod[form.payment_method.data],
            notes=form.notes.data,
            status=PaymentStatus.PROCESSED  # Default status for recorded payment
        )
        db.session.add(new_payment)
        db.session.commit()
        flash('Payroll payment recorded successfully!', 'success')
        return redirect(url_for('payroll_report'))  # Redirect to a report page

    if not form.is_submitted():
        # Pre-fill dates for convenience (e.g., last week)
        today = date.today()
        start_of_week, end_of_week = get_week_start_end(today - timedelta(days=7))
        form.pay_period_start.data = start_of_week
        form.pay_period_end.data = end_of_week
        form.payment_date.data = today

    return render_template('payroll_payment_form.html', form=form, title="Record Payroll Payment")

@app.route('/payroll/report')
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
def invoices():
    all_invoices = Invoice.query.join(Project).order_by(Invoice.invoice_date.desc()).all()
    return render_template('invoices.html', invoices=all_invoices)

@app.route('/invoice/add', methods=['GET', 'POST'])
def add_invoice():
    form = InvoiceForm()
    form.project_id.choices = [(p.id, p.name) for p in Project.query.order_by('name')]

    if form.validate_on_submit():
        # Handle empty invoice_number by setting it to None instead of empty string
        invoice_number = form.invoice_number.data if form.invoice_number.data else None
        
        new_invoice = Invoice(
            project_id=form.project_id.data,
            invoice_number=invoice_number,
            invoice_date=form.invoice_date.data,
            due_date=form.due_date.data,
            amount=form.amount.data,
            status=PaymentStatus[form.status.data],
            payment_received_date=form.payment_received_date.data
        )
        db.session.add(new_invoice)
        db.session.commit()
        flash('Invoice added successfully!', 'success')
        return redirect(url_for('invoices'))

    if not form.is_submitted():
        form.invoice_date.data = date.today()
        form.status.data = PaymentStatus.PENDING.name

    return render_template('invoice_form.html', form=form, title="Add Invoice")

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
    app.run(debug=True, host='0.0.0.0')  # Runs on localhost and network IP