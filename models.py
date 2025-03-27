from flask_sqlalchemy import SQLAlchemy
from datetime import date, timedelta, datetime
import enum

db = SQLAlchemy()

# --- Enums for Statuses ---
class ProjectStatus(enum.Enum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    INVOICED = "Invoiced"
    PAID = "Paid"

class PaymentStatus(enum.Enum):
    PENDING = "Pending"
    PROCESSED = "Processed"
    PAID = "Paid" # For AP

class PaymentMethod(enum.Enum):
    CASH = "Cash"
    CHECK = "Check"
    OTHER = "Other" # Added for flexibility in expenses

# --- Core Models ---
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    employee_id_str = db.Column(db.String(50), unique=True, nullable=True) # Optional string ID
    contact_details = db.Column(db.String(200))
    pay_rate = db.Column(db.Float, nullable=False)
    payment_method_preference = db.Column(db.Enum(PaymentMethod))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    hire_date = db.Column(db.Date)
    # Add other fields from 4.1 as needed

    timesheets = db.relationship('Timesheet', backref='employee', lazy=True)
    payments = db.relationship('PayrollPayment', backref='employee', lazy=True)

    def __repr__(self):
        return f'<Employee {self.name}>'

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    project_id_str = db.Column(db.String(50), unique=True, nullable=True) # Optional string ID
    client_name = db.Column(db.String(150)) # Simplified Client Info
    location = db.Column(db.String(200))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    contract_value = db.Column(db.Float)
    description = db.Column(db.Text)
    status = db.Column(db.Enum(ProjectStatus), default=ProjectStatus.PENDING, nullable=False)

    timesheets = db.relationship('Timesheet', backref='project', lazy=True)
    materials = db.relationship('Material', backref='project', lazy=True)
    expenses = db.relationship('Expense', backref='project', lazy=True) # Link non-material expenses
    invoices = db.relationship('Invoice', backref='project', lazy=True)

    def __repr__(self):
        return f'<Project {self.name}>'

    @property
    def total_material_cost(self):
        return sum(m.cost for m in self.materials if m.cost)

    @property
    def total_labor_cost(self):
        cost = 0
        for ts in self.timesheets:
            if ts.employee and ts.employee.pay_rate:
                cost += ts.calculated_hours * ts.employee.pay_rate
        return cost

    @property
    def total_other_expenses(self):
         return sum(e.amount for e in self.expenses if e.amount)

    @property
    def total_cost(self):
        return self.total_material_cost + self.total_labor_cost + self.total_other_expenses

    @property
    def profit(self):
        # Simple profit based on contract value vs total cost
        # More complex logic needed for invoiced amounts vs costs
        if self.contract_value:
            return self.contract_value - self.total_cost
        return -self.total_cost # Show loss if no contract value

class Timesheet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    entry_time = db.Column(db.Time, nullable=False)
    exit_time = db.Column(db.Time, nullable=False)
    lunch_duration_minutes = db.Column(db.Integer, default=0, nullable=False) # Store actual break time

    @property
    def raw_hours(self):
        if self.entry_time and self.exit_time:
            # Combine date and time for proper timedelta calculation
            start_dt = datetime.combine(self.date, self.entry_time)
            end_dt = datetime.combine(self.date, self.exit_time)
            if end_dt < start_dt: # Handle overnight shifts if necessary, though unlikely for drywall
                 end_dt += timedelta(days=1)
            duration = end_dt - start_dt
            return duration.total_seconds() / 3600.0
        return 0

    @property
    def calculated_hours(self):
        """Applies lunch break rules"""
        raw = self.raw_hours
        deduction = 0
        if self.lunch_duration_minutes == 60:
            deduction = 0.5 # Deduct 30 mins
        elif self.lunch_duration_minutes > 60:
             # Decide rule for longer breaks, assume deduct only 30 for now
             deduction = 0.5
        # No deduction if lunch <= 30 mins
        
        payable_hours = raw - deduction
        return max(0, payable_hours) # Ensure hours are not negative

    def __repr__(self):
        return f'<Timesheet E:{self.employee_id} P:{self.project_id} D:{self.date} H:{self.calculated_hours:.2f}>'

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    supplier = db.Column(db.String(100))
    cost = db.Column(db.Float, nullable=False)
    purchase_date = db.Column(db.Date, default=date.today)
    category = db.Column(db.String(50)) # e.g., Paint, Drywall, Tools

    def __repr__(self):
        return f'<Material {self.description} Cost:{self.cost}>'

class Expense(db.Model): # For non-material, non-payroll expenses
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False) # Rent, Utilities, Fuel, Subcontractor, etc.
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    supplier_vendor = db.Column(db.String(100))
    payment_method = db.Column(db.Enum(PaymentMethod))
    payment_status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.PENDING)
    due_date = db.Column(db.Date)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=True) # Optional link to project

    def __repr__(self):
        return f'<Expense {self.description} Amt:{self.amount}>'

# --- Simplified Payroll Payment Tracking ---
# This is a basic record of payment made, not a full AP process yet
class PayrollPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    pay_period_start = db.Column(db.Date, nullable=False)
    pay_period_end = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, nullable=False, default=date.today)
    payment_method = db.Column(db.Enum(PaymentMethod), nullable=False)
    status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.PROCESSED) # Assume processed once recorded
    notes = db.Column(db.Text) # For adjustments, etc.

# --- Basic Invoice Tracking ---
class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    invoice_number = db.Column(db.String(50), unique=True)
    invoice_date = db.Column(db.Date, nullable=False, default=date.today)
    due_date = db.Column(db.Date)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_received_date = db.Column(db.Date)
    # Add more details as needed (line items eventually)