from app import app, db
from models import (
    Employee, Project, Timesheet, Material, Expense, Invoice, 
    ProjectStatus, PaymentStatus, PaymentMethod, PayrollPayment,
    ExpenseCategory, DeductionType, PayrollDeduction
)
from datetime import datetime, date, timedelta
import random

def add_mock_data():
    with app.app_context():
        # Get existing projects - we won't modify these
        projects = Project.query.all()
        if not projects:
            print("No projects found in database. Please add projects first.")
            return
            
        print("Using existing projects:")
        for p in projects:
            print(f"  - {p.name} (ID: {p.id}, Status: {p.status.name})")
        
        # Check existing employees
        existing_employees = Employee.query.count()
        if existing_employees < 5:
            print("\nAdding sample employees...")
            # Add some employees if there aren't many
            sample_employees = [
                {"name": "Maria Rodriguez", "pay_rate": 22.50, "contact_details": "Phone: 555-1234"},
                {"name": "James Wilson", "pay_rate": 25.00, "contact_details": "Email: jwilson@example.com"},
                {"name": "Sarah Johnson", "pay_rate": 21.00, "contact_details": "Phone: 555-5678"}
            ]
            
            for emp_data in sample_employees:
                emp = Employee(
                    name=emp_data["name"],
                    pay_rate=emp_data["pay_rate"],
                    contact_details=emp_data["contact_details"],
                    is_active=True,
                    hire_date=date.today() - timedelta(days=random.randint(30, 365)),
                    payment_method_preference=random.choice([pm for pm in PaymentMethod if pm != PaymentMethod.OTHER])
                )
                db.session.add(emp)
                print(f"  - Added employee: {emp.name}")
        
        # Get all employees for assigning timesheets
        employees = Employee.query.all()
        
        # Add timesheets
        print("\nAdding sample timesheets...")
        today = date.today()
        for i in range(10):
            entry_date = today - timedelta(days=random.randint(0, 14))
            employee = random.choice(employees)
            project = random.choice(projects)
            
            # Create a reasonable workday (7-9 hours with lunch)
            entry_time = datetime.strptime('08:00', '%H:%M').time()
            hours = random.randint(7, 9)
            exit_time = datetime.strptime(f'{8+hours}:00', '%H:%M').time()
            lunch_duration = random.choice([0, 30, 60])
            
            ts = Timesheet(
                employee_id=employee.id,
                project_id=project.id,
                date=entry_date,
                entry_time=entry_time,
                exit_time=exit_time,
                lunch_duration_minutes=lunch_duration
            )
            db.session.add(ts)
            print(f"  - Added timesheet: {employee.name} worked on {project.name} on {entry_date}")
        
        # Add materials
        print("\nAdding sample materials...")
        material_types = ["Paint", "Lumber", "Drywall", "Electrical", "Plumbing", "Hardware"]
        suppliers = ["Home Depot", "Lowe's", "Ace Hardware", "Local Supply Co."]
        
        for i in range(8):
            project = random.choice(projects)
            material_type = random.choice(material_types)
            material = Material(
                project_id=project.id,
                description=f"{material_type} supplies for {project.name}",
                supplier=random.choice(suppliers),
                cost=round(random.uniform(50, 500), 2),
                purchase_date=date.today() - timedelta(days=random.randint(1, 30)),
                category=material_type
            )
            db.session.add(material)
            print(f"  - Added material: {material.description} (${material.cost:.2f})")
        
        # Add expenses
        print("\nAdding sample expenses...")
        expense_categories = [cat.name for cat in ExpenseCategory]
        expense_descriptions = ["Office supplies", "Fuel", "Equipment rental", "Software subscription", "Tool repair"]
        
        for i in range(6):
            expense = Expense(
                description=random.choice(expense_descriptions),
                category=random.choice(expense_categories),
                amount=round(random.uniform(20, 300), 2),
                date=date.today() - timedelta(days=random.randint(1, 45)),
                supplier_vendor=random.choice(suppliers),
                payment_method=random.choice([pm for pm in PaymentMethod if pm != PaymentMethod.OTHER]),
                payment_status=random.choice([PaymentStatus.PAID, PaymentStatus.PENDING]),
                project_id=random.choice(projects).id if random.random() > 0.3 else None
            )
            if expense.payment_status == PaymentStatus.PAID:
                expense.payment_date = expense.date + timedelta(days=random.randint(1, 7))
            else:
                expense.due_date = expense.date + timedelta(days=random.randint(7, 30))
                
            db.session.add(expense)
            print(f"  - Added expense: {expense.description} (${expense.amount:.2f})")
        
        # Add invoices to projects that don't have them
        print("\nAdding sample invoices...")
        for project in projects:
            # Only create invoices for projects without them
            existing_invoice = Invoice.query.filter_by(project_id=project.id).first()
            if not existing_invoice:
                invoice_date = date.today() - timedelta(days=random.randint(1, 30))
                due_date = invoice_date + timedelta(days=30)
                amount = round(random.uniform(1000, 5000), 2)
                status = random.choice([PaymentStatus.PAID, PaymentStatus.PENDING])
                
                invoice = Invoice(
                    project_id=project.id,
                    invoice_number=f"INV-{project.id}-{invoice_date.strftime('%Y%m')}",
                    invoice_date=invoice_date,
                    due_date=due_date,
                    amount=amount,
                    status=status
                )
                
                if status == PaymentStatus.PAID:
                    invoice.payment_received_date = invoice_date + timedelta(days=random.randint(1, 25))
                
                db.session.add(invoice)
                print(f"  - Added invoice for project: {project.name} (${amount:.2f}, Status: {status.name})")
                
                # Update project status based on invoice status
                if project.status != ProjectStatus.INVOICED and project.status != ProjectStatus.PAID:
                    if status == PaymentStatus.PAID:
                        project.status = ProjectStatus.PAID
                    else:
                        project.status = ProjectStatus.INVOICED
        
        # Add payroll payments
        print("\nAdding sample payroll payments...")
        payment_methods = [PaymentMethod.CASH, PaymentMethod.CHECK]
        
        for employee in employees:
            if random.random() > 0.3:  # 70% chance to create a payment
                pay_period_start = date.today() - timedelta(days=random.randint(14, 28))
                pay_period_end = pay_period_start + timedelta(days=13)  # Two weeks
                payment_date = pay_period_end + timedelta(days=3)  # 3 days after period ends
                
                # Calculate a reasonable gross amount based on pay rate
                hours = random.randint(60, 80)  # Hours in a two-week period
                gross_amount = round(employee.pay_rate * hours, 2)
                
                payment_method = random.choice(payment_methods)
                check_number = None
                bank_name = None
                
                if payment_method == PaymentMethod.CHECK:
                    check_number = str(random.randint(1001, 9999))
                    bank_name = "First National Bank"
                
                payment = PayrollPayment(
                    employee_id=employee.id,
                    pay_period_start=pay_period_start,
                    pay_period_end=pay_period_end,
                    gross_amount=gross_amount,
                    amount=gross_amount,  # Will be updated after deductions
                    payment_date=payment_date,
                    payment_method=payment_method,
                    check_number=check_number,
                    bank_name=bank_name,
                    notes=f"Pay period {pay_period_start.strftime('%m/%d/%Y')} to {pay_period_end.strftime('%m/%d/%Y')}"
                )
                
                db.session.add(payment)
                db.session.flush()  # To get payment ID
                
                # Add deductions randomly
                if random.random() > 0.5:  # 50% chance for deductions
                    deduction_types = list(DeductionType)
                    num_deductions = random.randint(1, 2)
                    total_deductions = 0
                    
                    for j in range(num_deductions):
                        deduction_type = random.choice(deduction_types)
                        deduction_amount = round(gross_amount * random.uniform(0.05, 0.15), 2)  # 5-15% of gross
                        total_deductions += deduction_amount
                        
                        deduction = PayrollDeduction(
                            payroll_payment_id=payment.id,
                            description=f"{deduction_type.value} deduction",
                            amount=deduction_amount,
                            deduction_type=deduction_type,
                            notes="Automatic deduction"
                        )
                        db.session.add(deduction)
                    
                    # Update payment amount after deductions
                    payment.amount = gross_amount - total_deductions
                
                print(f"  - Added payroll payment for {employee.name}: ${payment.amount:.2f} ({payment_method.value})")
        
        # Commit all changes
        db.session.commit()
        print("\nMock data has been added successfully!")

if __name__ == "__main__":
    add_mock_data()
