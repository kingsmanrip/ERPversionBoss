import os
import sys
import random
import datetime
from datetime import timedelta
from faker import Faker
from app import app, db
from models import Employee, Project, Timesheet, Material, Expense, ProjectStatus, PaymentMethod, ExpenseCategory as ExpenseType, PayrollPayment, PaymentStatus

# Initialize faker
fake = Faker()

def create_mock_data():
    """Populate the database with mock data for testing purposes"""
    print("Starting to populate database with mock data...")
    
    # Make sure database exists
    with app.app_context():
        # Create employees
        print("Creating employees...")
        create_employees()
        
        # Create projects
        print("Creating projects...")
        create_projects()
        
        # Create timesheets
        print("Creating timesheets...")
        create_timesheets()
        
        # Create materials
        print("Creating materials...")
        create_materials()
        
        # Create expenses
        print("Creating expenses...")
        create_expenses()
        
        # Create payments
        print("Creating payments...")
        create_payments()
    
    print("Mock data creation complete!")

def create_employees():
    """Create mock employees"""
    # Using Boolean is_active instead of EmployeeStatus enum
    
    with app.app_context():
        # Clear existing employees except the first one (likely the admin)
        existing_count = Employee.query.count()
        if existing_count > 1:
            Employee.query.filter(Employee.id > 1).delete()
            db.session.commit()
        
        # Create 15 employees
        for i in range(15):
            is_active = True if i < 12 else False
            
            # Create contact details as a single text field
            contact_details = f"Phone: {fake.phone_number()}\nEmail: {fake.email()}\nAddress: {fake.address()}"
            
            employee = Employee(
                name=fake.name(),
                employee_id_str=f"EMP{100+i}",
                contact_details=contact_details,
                is_active=is_active,
                pay_rate=random.uniform(15.0, 35.0),
                payment_method_preference=random.choice(list(PaymentMethod)) if random.random() > 0.3 else None,
                hire_date=fake.date_between(start_date="-5y", end_date="today")
            )
            db.session.add(employee)
        
        db.session.commit()
        print(f"Created {15} employees")

def create_projects():
    """Create mock projects"""
    project_statuses = [ProjectStatus.PENDING, ProjectStatus.IN_PROGRESS, ProjectStatus.COMPLETED, ProjectStatus.CANCELLED]
    project_types = ["Residential", "Commercial", "Industrial", "Renovation"]
    
    with app.app_context():
        # Clear existing projects
        Project.query.delete()
        db.session.commit()
        
        # Create 20 projects
        for i in range(20):
            status_weight = [0.2, 0.5, 0.2, 0.1]  # Weights for PENDING, IN_PROGRESS, COMPLETED, CANCELLED
            status = random.choices(project_statuses, weights=status_weight)[0]
            
            start_date = fake.date_between(start_date="-1y", end_date="today")
            end_date = None
            
            if status in [ProjectStatus.COMPLETED, ProjectStatus.CANCELLED]:
                end_date = start_date + timedelta(days=random.randint(14, 90))
            
            # Using actual Project model fields
            project = Project(
                name=f"{fake.company()} {random.choice(project_types)}",
                project_id_str=f"PROJ{2000+i}",
                client_name=fake.company(),
                location=fake.address(),
                start_date=start_date,
                end_date=end_date,
                contract_value=random.uniform(5000, 50000),
                description=fake.text(max_nb_chars=200),
                status=status
            )
            db.session.add(project)
        
        db.session.commit()
        print(f"Created {20} projects")

def create_timesheets():
    """Create mock timesheet entries"""
    with app.app_context():
        # Clear existing timesheets
        Timesheet.query.delete()
        db.session.commit()
        
        employees = Employee.query.all()
        active_projects = Project.query.filter(Project.status.in_([ProjectStatus.PENDING, ProjectStatus.IN_PROGRESS])).all()
        all_projects = Project.query.all()
        
        # Create 200 timesheet entries
        for i in range(200):
            employee = random.choice(employees)
            
            # 80% chance of having a project, 20% chance of no project
            project = random.choice(all_projects) if random.random() < 0.8 else None
            
            # Generate a date within the last 90 days
            date = fake.date_between(start_date="-90d", end_date="today")
            
            # Generate entry and exit times
            entry_hour = random.randint(7, 9)
            entry_minute = random.choice([0, 15, 30, 45])
            entry_time = datetime.time(entry_hour, entry_minute)
            
            # Work between 6-10 hours
            work_hours = random.randint(6, 10)
            exit_hour = entry_hour + work_hours
            if exit_hour > 18:
                exit_hour = 18
            exit_minute = random.choice([0, 15, 30, 45])
            exit_time = datetime.time(exit_hour, exit_minute)
            
            # Generate lunch duration (0, 30, 45, or 60 minutes)
            lunch_duration = random.choice([0, 30, 45, 60])
            
            timesheet = Timesheet(
                employee_id=employee.id,
                project_id=project.id if project else None,
                date=date,
                entry_time=entry_time,
                exit_time=exit_time,
                lunch_duration_minutes=lunch_duration
            )
            db.session.add(timesheet)
        
        db.session.commit()
        print(f"Created {200} timesheet entries")

def create_materials():
    """Create mock material entries"""
    material_types = ["Paint", "Drywall", "Lumber", "Hardware", "Fixtures", "Tools", "Electrical", "Plumbing"]
    
    with app.app_context():
        # Clear existing materials
        Material.query.delete()
        db.session.commit()
        
        projects = Project.query.all()
        
        # Create 150 material entries
        for i in range(150):
            project = random.choice(projects)
            purchase_date = fake.date_between(start_date=project.start_date, end_date=datetime.date.today())
            
            # Using correct Material model fields
            material = Material(
                project_id=project.id,
                description=f"{random.choice(material_types)} - {fake.word()}",
                supplier=fake.company(),
                cost=random.uniform(5.0, 200.0),
                purchase_date=purchase_date,
                category=random.choice(material_types)
            )
            db.session.add(material)
        
        db.session.commit()
        print(f"Created {150} material entries")

def create_expenses():
    """Create mock expense entries"""
    expense_categories = ["Equipment", "Office Supplies", "Transportation", "Meals", "Utilities"]
    
    with app.app_context():
        # Clear existing expenses
        Expense.query.delete()
        db.session.commit()
        
        projects = Project.query.all()
        
        # Create 100 expense entries
        for i in range(100):
            project = random.choice(projects)
            expense_date = fake.date_between(start_date=project.start_date, end_date=datetime.date.today())
            category = random.choice(expense_categories)
            
            # Using correct Expense model fields
            expense = Expense(
                project_id=project.id,
                description=f"{category} expense - {fake.word()}",
                category=category,
                amount=random.uniform(10.0, 500.0),
                date=expense_date,
                supplier_vendor=fake.company(),
                payment_method=random.choice(list(PaymentMethod)),
                payment_status=random.choice(list(PaymentStatus)),
                due_date=expense_date + timedelta(days=random.randint(15, 45)) if random.random() > 0.5 else None
            )
            db.session.add(expense)
        
        db.session.commit()
        print(f"Created {100} expense entries")

def create_payments():
    """Create mock payment entries"""
    payment_methods = list(PaymentMethod)
    
    with app.app_context():
        # Clear existing payments
        PayrollPayment.query.delete()
        db.session.commit()
        
        employees = Employee.query.all()
        
        # Create 80 payment entries
        for i in range(80):
            employee = random.choice(employees)
            payment_date = fake.date_between(start_date="-6m", end_date="today")
            
            # Create payments for a pay period (typically bi-weekly)
            start_date = payment_date - timedelta(days=14)
            end_date = payment_date
            
            # Calculate hours between 50-90 for a two-week period
            hours = random.uniform(50, 90)
            gross_amount = hours * employee.pay_rate
            
            # Some deductions (typically 15-25%)
            deduction_percent = random.uniform(0.15, 0.25)
            net_amount = gross_amount * (1 - deduction_percent)
            
            payment_method = random.choice(payment_methods)
            check_number = f"CHK{5000+i}" if payment_method == PaymentMethod.CHECK else None
            
            # Using correct PayrollPayment model fields
            payment = PayrollPayment(
                employee_id=employee.id,
                payment_date=payment_date,
                pay_period_start=start_date,
                pay_period_end=end_date,
                gross_amount=gross_amount,
                amount=net_amount,
                payment_method=payment_method,
                check_number=check_number,
                notes=fake.text(max_nb_chars=100) if random.random() > 0.7 else None
            )
            db.session.add(payment)
        
        db.session.commit()
        print(f"Created {80} payment entries")

if __name__ == "__main__":
    # Add Faker to requirements if not present
    try:
        import faker
    except ImportError:
        print("Installing required packages...")
        os.system('pip install faker')
        print("Packages installed successfully.")
    
    create_mock_data()
