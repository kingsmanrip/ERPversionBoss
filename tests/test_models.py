import pytest
from datetime import date, datetime, time, timedelta
from models import Employee, Project, Timesheet, Material, Expense, Invoice, ProjectStatus, PaymentMethod, PaymentStatus

def test_employee_creation(app):
    """Test that an employee can be created with the correct attributes."""
    with app.app_context():
        employee = Employee(
            name="Test Employee",
            employee_id_str="TEST123",
            contact_details="test@example.com",
            pay_rate=20.0,
            is_active=True
        )
        assert employee.name == "Test Employee"
        assert employee.employee_id_str == "TEST123"
        assert employee.pay_rate == 20.0
        assert employee.is_active is True

def test_project_creation(app):
    """Test that a project can be created with the correct attributes."""
    with app.app_context():
        project = Project(
            name="Test Project",
            project_id_str="PRJ123",
            client_name="Test Client",
            contract_value=10000.0,
            status=ProjectStatus.PENDING
        )
        assert project.name == "Test Project"
        assert project.project_id_str == "PRJ123"
        assert project.client_name == "Test Client"
        assert project.contract_value == 10000.0
        assert project.status == ProjectStatus.PENDING

def test_project_cost_calculations(app, sample_data):
    """Test project cost calculation properties."""
    with app.app_context():
        from models import db, Project, Material, Timesheet, Expense, Employee
        project = Project.query.get(sample_data['project_ids'][0])
        employee = Employee.query.get(sample_data['employee_ids'][0])
        
        # Add some materials
        material1 = Material(
            project_id=project.id,
            description="Paint",
            supplier="Paint Store",
            cost=200.0,
            purchase_date=date.today(),
            category="Paint"
        )
        material2 = Material(
            project_id=project.id,
            description="Drywall",
            supplier="Building Supply",
            cost=300.0,
            purchase_date=date.today(),
            category="Drywall"
        )
        
        # Add a timesheet entry
        timesheet = Timesheet(
            employee_id=employee.id,
            project_id=project.id,
            date=date.today(),
            entry_time=time(8, 0),
            exit_time=time(16, 0),
            lunch_duration_minutes=30
        )
        
        # Add an expense
        expense = Expense(
            description="Rental Equipment",
            category="Equipment",
            amount=150.0,
            date=date.today(),
            supplier_vendor="Equipment Rental",
            project_id=project.id
        )
        
        db.session.add_all([material1, material2, timesheet, expense])
        db.session.commit()
        
        # Refresh the project to ensure all relationships are loaded
        project = Project.query.get(project.id)
        
        # Test cost calculations
        assert project.total_material_cost == 500.0  # 200 + 300
        
        # Employee pay rate is 25.0 from sample_data and worked hours is 7.5 (8 hours - 30 min lunch)
        assert project.total_labor_cost == 200.0  # 25.0 * 8.0
        
        assert project.total_other_expenses == 150.0
        assert project.total_cost == 850.0  # 500 + 200 + 150
        assert project.profit == 4150.0  # 5000 - 850.0

def test_timesheet_hour_calculation(app, sample_data):
    """Test timesheet hour calculations."""
    with app.app_context():
        from models import db, Employee, Project, Timesheet
        employee = Employee.query.get(sample_data['employee_ids'][0])
        project = Project.query.get(sample_data['project_ids'][0])
        
        # 8 hour day with 30 min lunch (should be no deduction)
        timesheet1 = Timesheet(
            employee_id=employee.id,
            project_id=project.id,
            date=date.today(),
            entry_time=time(8, 0),
            exit_time=time(16, 0),
            lunch_duration_minutes=30
        )
        
        # 8 hour day with 60 min lunch (should be 0.5 hour deduction)
        timesheet2 = Timesheet(
            employee_id=employee.id,
            project_id=project.id,
            date=date.today(),
            entry_time=time(8, 0),
            exit_time=time(16, 0),
            lunch_duration_minutes=60
        )
        
        # 8 hour day with 90 min lunch (should be 0.5 hour deduction)
        timesheet3 = Timesheet(
            employee_id=employee.id,
            project_id=project.id,
            date=date.today(),
            entry_time=time(8, 0),
            exit_time=time(16, 0),
            lunch_duration_minutes=90
        )

        db.session.add_all([timesheet1, timesheet2, timesheet3])
        db.session.commit()
        
        assert timesheet1.raw_hours == 8.0
        assert timesheet1.calculated_hours == 8.0  # No deduction for 30 min lunch
        
        assert timesheet2.raw_hours == 8.0
        assert timesheet2.calculated_hours == 7.5  # 0.5 hour deduction for 60 min lunch
        
        assert timesheet3.raw_hours == 8.0
        assert timesheet3.calculated_hours == 7.5  # 0.5 hour deduction for 90 min lunch
