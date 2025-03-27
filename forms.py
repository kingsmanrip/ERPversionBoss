from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, DateField, SelectField, TextAreaField, SubmitField, TimeField, BooleanField
from wtforms.validators import DataRequired, Optional, NumberRange, Email
from models import ProjectStatus, PaymentMethod, PaymentStatus

# --- Form Definitions ---

class EmployeeForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    employee_id_str = StringField('Employee ID (Optional)')
    contact_details = TextAreaField('Contact Details')
    pay_rate = FloatField('Pay Rate (per hour)', validators=[DataRequired(), NumberRange(min=0)])
    payment_method_preference = SelectField('Preferred Payment Method', choices=[(pm.name, pm.value) for pm in PaymentMethod if pm != PaymentMethod.OTHER], coerce=str, validators=[Optional()])
    is_active = BooleanField('Active Employee', default=True)
    hire_date = DateField('Hire Date', validators=[Optional()])
    submit = SubmitField('Save Employee')

class ProjectForm(FlaskForm):
    name = StringField('Project Name', validators=[DataRequired()])
    project_id_str = StringField('Project ID (Optional)')
    client_name = StringField('Client Name')
    location = StringField('Location')
    start_date = DateField('Start Date', validators=[Optional()])
    end_date = DateField('End Date', validators=[Optional()])
    contract_value = FloatField('Contract Value ($)', validators=[Optional(), NumberRange(min=0)])
    description = TextAreaField('Description')
    status = SelectField('Status', choices=[(ps.name, ps.value) for ps in ProjectStatus], default=ProjectStatus.PENDING.name, validators=[DataRequired()])
    submit = SubmitField('Save Project')

class TimesheetForm(FlaskForm):
    employee_id = SelectField('Employee', coerce=int, validators=[DataRequired()])
    project_id = SelectField('Project', coerce=int, validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    entry_time = TimeField('Entry Time', validators=[DataRequired()], format='%H:%M')
    exit_time = TimeField('Exit Time', validators=[DataRequired()], format='%H:%M')
    lunch_duration_minutes = IntegerField('Lunch Break (minutes)', default=0, validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Save Timesheet Entry')

class MaterialForm(FlaskForm):
    project_id = SelectField('Project', coerce=int, validators=[DataRequired()])
    description = StringField('Material Description', validators=[DataRequired()])
    supplier = StringField('Supplier')
    cost = FloatField('Cost ($)', validators=[DataRequired(), NumberRange(min=0)])
    purchase_date = DateField('Purchase Date', validators=[DataRequired()], format='%Y-%m-%d')
    category = StringField('Category (e.g., Paint, Drywall)')
    submit = SubmitField('Save Material')

class ExpenseForm(FlaskForm):
    description = StringField('Description', validators=[DataRequired()])
    category = StringField('Category (e.g., Rent, Fuel)', validators=[DataRequired()])
    amount = FloatField('Amount ($)', validators=[DataRequired(), NumberRange(min=0)])
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    supplier_vendor = StringField('Supplier/Vendor')
    payment_method = SelectField('Payment Method', choices=[('', '-- Select --')] + [(pm.name, pm.value) for pm in PaymentMethod], validators=[Optional()])
    payment_status = SelectField('Payment Status', choices=[(ps.name, ps.value) for ps in PaymentStatus], default=PaymentStatus.PENDING.name, validators=[DataRequired()])
    due_date = DateField('Due Date', validators=[Optional()])
    project_id = SelectField('Link to Project (Optional)', coerce=lambda x: int(x) if x else None, validators=[Optional()])
    submit = SubmitField('Save Expense')

# Basic form for recording a payroll payment manually
class PayrollPaymentForm(FlaskForm):
    employee_id = SelectField('Employee', coerce=int, validators=[DataRequired()])
    pay_period_start = DateField('Pay Period Start', validators=[DataRequired()], format='%Y-%m-%d')
    pay_period_end = DateField('Pay Period End', validators=[DataRequired()], format='%Y-%m-%d')
    amount = FloatField('Amount Paid ($)', validators=[DataRequired(), NumberRange(min=0)])
    payment_date = DateField('Payment Date', validators=[DataRequired()], format='%Y-%m-%d')
    payment_method = SelectField('Payment Method', choices=[(pm.name, pm.value) for pm in PaymentMethod if pm != PaymentMethod.OTHER], coerce=str, validators=[DataRequired()])
    notes = TextAreaField('Notes (e.g., adjustments)')
    submit = SubmitField('Record Payment')

# Basic form for creating/editing invoices
class InvoiceForm(FlaskForm):
    project_id = SelectField('Project', coerce=int, validators=[DataRequired()])
    invoice_number = StringField('Invoice Number')
    invoice_date = DateField('Invoice Date', validators=[DataRequired()], format='%Y-%m-%d')
    due_date = DateField('Due Date', validators=[Optional()])
    amount = FloatField('Invoice Amount ($)', validators=[DataRequired(), NumberRange(min=0)])
    status = SelectField('Status', choices=[(ps.name, ps.value) for ps in PaymentStatus], default=PaymentStatus.PENDING.name, validators=[DataRequired()])
    payment_received_date = DateField('Payment Received Date', validators=[Optional()])
    submit = SubmitField('Save Invoice')