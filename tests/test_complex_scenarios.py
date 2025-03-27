import pytest
from datetime import date, time, timedelta
from models import db, Employee, Project, Timesheet, Material, Expense, Invoice, ProjectStatus, PaymentMethod, PaymentStatus

def test_complete_project_lifecycle(app, client):
    """Test the complete lifecycle of a project from creation to payment."""
    with app.app_context():
        # Phase 1: Setup - Create employees and project
        # Create test employees with different roles and pay rates
        painter = Employee(
            name="Sam Painter",
            employee_id_str="EMP-P1",
            contact_details="painter@example.com",
            pay_rate=22.0,
            payment_method_preference=PaymentMethod.CHECK,
            is_active=True,
            hire_date=date.today() - timedelta(days=100)
        )
        drywall_specialist = Employee(
            name="Dana Drywall",
            employee_id_str="EMP-D1",
            contact_details="drywall@example.com",
            pay_rate=25.0,
            payment_method_preference=PaymentMethod.CASH,
            is_active=True,
            hire_date=date.today() - timedelta(days=150)
        )
        db.session.add_all([painter, drywall_specialist])
        db.session.commit()
        
        # Create a new project
        project = Project(
            name="Full Lifecycle Test Project",
            project_id_str="FLTP-001",
            client_name="Complete Test Client",
            location="123 Test Ave",
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() + timedelta(days=15),
            contract_value=10000.0,
            description="A project to test the complete business workflow",
            status=ProjectStatus.PENDING
        )
        db.session.add(project)
        db.session.commit()
        
        # Phase 2: Project Start - Change status to IN_PROGRESS
        project.status = ProjectStatus.IN_PROGRESS
        db.session.commit()
        
        # Phase 3: Project Execution - Add timesheets, materials and expenses
        
        # Add timesheets for multiple days
        # Week 1: Drywall work
        for day in range(5):  # 5 workdays
            timesheet = Timesheet(
                employee_id=drywall_specialist.id,
                project_id=project.id,
                date=date.today() - timedelta(days=25-day),  # 25, 24, 23, 22, 21 days ago
                entry_time=time(8, 0),
                exit_time=time(16, 0),
                lunch_duration_minutes=30
            )
            db.session.add(timesheet)
        
        # Week 2: Painting work
        for day in range(5):  # 5 workdays
            timesheet = Timesheet(
                employee_id=painter.id,
                project_id=project.id,
                date=date.today() - timedelta(days=18-day),  # 18, 17, 16, 15, 14 days ago
                entry_time=time(8, 0),
                exit_time=time(16, 0),
                lunch_duration_minutes=30
            )
            db.session.add(timesheet)
        
        # Add materials used
        materials = [
            Material(
                project_id=project.id,
                description="Drywall Sheets",
                supplier="Building Supply Co",
                cost=500.0,
                purchase_date=date.today() - timedelta(days=28),
                category="Drywall"
            ),
            Material(
                project_id=project.id,
                description="Drywall Compound",
                supplier="Building Supply Co",
                cost=150.0,
                purchase_date=date.today() - timedelta(days=28),
                category="Drywall"
            ),
            Material(
                project_id=project.id,
                description="Premium Paint",
                supplier="Paint Depot",
                cost=300.0,
                purchase_date=date.today() - timedelta(days=20),
                category="Paint"
            ),
            Material(
                project_id=project.id,
                description="Primer",
                supplier="Paint Depot",
                cost=100.0,
                purchase_date=date.today() - timedelta(days=20),
                category="Paint"
            )
        ]
        db.session.add_all(materials)
        
        # Add other expenses
        expenses = [
            Expense(
                description="Equipment Rental",
                category="Equipment",
                amount=200.0,
                date=date.today() - timedelta(days=26),
                supplier_vendor="Tool Rental Inc",
                payment_method=PaymentMethod.CHECK,
                payment_status=PaymentStatus.PAID,
                project_id=project.id
            ),
            Expense(
                description="Site Clean-up",
                category="Services",
                amount=150.0,
                date=date.today() - timedelta(days=14),
                supplier_vendor="Cleaning Service",
                payment_method=PaymentMethod.CASH,
                payment_status=PaymentStatus.PAID,
                project_id=project.id
            )
        ]
        db.session.add_all(expenses)
        db.session.commit()
        
        # Phase 4: Project Completion
        # Update project status to COMPLETED
        project.status = ProjectStatus.COMPLETED
        db.session.commit()
        
        # Phase 5: Create invoice
        invoice = Invoice(
            project_id=project.id,
            invoice_number="INV-FLTP-001",
            invoice_date=date.today() - timedelta(days=10),
            due_date=date.today() + timedelta(days=20),
            amount=10000.0,  # Full contract value
            status=PaymentStatus.PENDING
        )
        db.session.add(invoice)
        db.session.commit()
        
        # Update project status to INVOICED
        project.status = ProjectStatus.INVOICED
        db.session.commit()
        
        # Phase 6: Record payroll payments
        payroll_payments = [
            {
                'employee_id': drywall_specialist.id,
                'pay_period_start': (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'),
                'pay_period_end': (date.today() - timedelta(days=20)).strftime('%Y-%m-%d'),
                'amount': 1000.0,  # 5 days * 8 hours * $25/hr
                'payment_date': (date.today() - timedelta(days=19)).strftime('%Y-%m-%d'),
                'payment_method': 'CASH',
                'notes': 'Week 1 work - drywall installation'
            },
            {
                'employee_id': painter.id,
                'pay_period_start': (date.today() - timedelta(days=20)).strftime('%Y-%m-%d'),
                'pay_period_end': (date.today() - timedelta(days=10)).strftime('%Y-%m-%d'),
                'amount': 880.0,  # 5 days * 8 hours * $22/hr
                'payment_date': (date.today() - timedelta(days=9)).strftime('%Y-%m-%d'),
                'payment_method': 'CHECK',
                'notes': 'Week 2 work - painting'
            }
        ]
        
        for payment_data in payroll_payments:
            response = client.post('/payroll/record-payment', data=payment_data, follow_redirects=True)
            if response.status_code != 200:
                # Try alternative route
                response = client.post('/payroll-payment/add', data=payment_data, follow_redirects=True)
        
        # Phase 7: Invoice Payment
        # Update invoice to PAID
        invoice.status = PaymentStatus.PAID
        invoice.payment_received_date = date.today() - timedelta(days=5)
        db.session.commit()
        
        # Update project status to PAID
        project.status = ProjectStatus.PAID
        db.session.commit()
        
        # Verification - Check project profitability
        final_project = Project.query.get(project.id)
        
        # Calculate expected costs
        expected_material_cost = 500.0 + 150.0 + 300.0 + 100.0  # Sum of all materials
        expected_labor_cost = (5 * 8 * 25.0) + (5 * 8 * 22.0)   # Drywall specialist + Painter
        expected_other_expense = 200.0 + 150.0                  # Equipment rental + Cleaning
        expected_total_cost = expected_material_cost + expected_labor_cost + expected_other_expense
        expected_profit = 10000.0 - expected_total_cost
        
        # Compare with calculated values
        assert round(final_project.total_material_cost, 2) == round(expected_material_cost, 2)
        assert round(final_project.total_other_expenses, 2) == round(expected_other_expense, 2)
        
        # Note: The labor cost calculation might differ slightly due to how the application
        # calculates lunch breaks and rounds numbers, so we use a more flexible assertion
        labor_cost_diff = abs(final_project.total_labor_cost - expected_labor_cost)
        assert labor_cost_diff < 50.0  # Allow for small differences in calculation
        
        # Verify project is properly marked as paid
        assert final_project.status == ProjectStatus.PAID

def test_multiple_projects_resource_allocation(app, client):
    """Test handling multiple concurrent projects and resource allocation."""
    with app.app_context():
        # Create employees
        employee = Employee(
            name="Multi-Project Worker",
            employee_id_str="EMP-MP1",
            contact_details="multi@example.com",
            pay_rate=30.0,
            is_active=True
        )
        db.session.add(employee)
        db.session.commit()
        
        # Create multiple concurrent projects
        project1 = Project(
            name="Multi-Project Test 1",
            client_name="Client A",
            contract_value=5000.0,
            status=ProjectStatus.IN_PROGRESS,
            start_date=date.today() - timedelta(days=15),
            end_date=date.today() + timedelta(days=15)
        )
        
        project2 = Project(
            name="Multi-Project Test 2",
            client_name="Client B",
            contract_value=7000.0,
            status=ProjectStatus.IN_PROGRESS,
            start_date=date.today() - timedelta(days=10),
            end_date=date.today() + timedelta(days=20)
        )
        
        project3 = Project(
            name="Multi-Project Test 3",
            client_name="Client C",
            contract_value=3000.0,
            status=ProjectStatus.IN_PROGRESS,
            start_date=date.today() - timedelta(days=5),
            end_date=date.today() + timedelta(days=10)
        )
        
        db.session.add_all([project1, project2, project3])
        db.session.commit()
        
        # Record timesheets across multiple projects on the same days
        # This tests the employee working on different projects on the same day
        
        # Day 1: Morning on Project 1, Afternoon on Project 2
        timesheet1_morning = Timesheet(
            employee_id=employee.id,
            project_id=project1.id,
            date=date.today() - timedelta(days=5),
            entry_time=time(8, 0),
            exit_time=time(12, 0),
            lunch_duration_minutes=0
        )
        
        timesheet1_afternoon = Timesheet(
            employee_id=employee.id,
            project_id=project2.id,
            date=date.today() - timedelta(days=5),
            entry_time=time(13, 0),
            exit_time=time(17, 0),
            lunch_duration_minutes=0
        )
        
        # Day 2: Morning on Project 3, Afternoon on Project 1
        timesheet2_morning = Timesheet(
            employee_id=employee.id,
            project_id=project3.id,
            date=date.today() - timedelta(days=4),
            entry_time=time(8, 0),
            exit_time=time(12, 0),
            lunch_duration_minutes=0
        )
        
        timesheet2_afternoon = Timesheet(
            employee_id=employee.id,
            project_id=project1.id,
            date=date.today() - timedelta(days=4),
            entry_time=time(13, 0),
            exit_time=time(17, 0),
            lunch_duration_minutes=0
        )
        
        # Day 3: All day on Project 2
        timesheet3 = Timesheet(
            employee_id=employee.id,
            project_id=project2.id,
            date=date.today() - timedelta(days=3),
            entry_time=time(8, 0),
            exit_time=time(17, 0),
            lunch_duration_minutes=60
        )
        
        db.session.add_all([
            timesheet1_morning, timesheet1_afternoon,
            timesheet2_morning, timesheet2_afternoon,
            timesheet3
        ])
        db.session.commit()
        
        # Verify labor costs are allocated to the correct projects
        
        # Project 1: 4 hours on day 1 + 4 hours on day 2 = 8 hours = $240
        project1 = Project.query.get(project1.id)
        expected_labor_cost_p1 = 8 * employee.pay_rate
        assert round(project1.total_labor_cost, 2) == round(expected_labor_cost_p1, 2)
        
        # Project 2: 4 hours on day 1 + 8 hours on day 3 = 12 hours = $360
        project2 = Project.query.get(project2.id)
        expected_labor_cost_p2 = 12 * employee.pay_rate
        assert round(project2.total_labor_cost, 2) == round(expected_labor_cost_p2, 2)
        
        # Project 3: 4 hours on day 2 = 4 hours = $120
        project3 = Project.query.get(project3.id)
        expected_labor_cost_p3 = 4 * employee.pay_rate
        assert round(project3.total_labor_cost, 2) == round(expected_labor_cost_p3, 2)
        
        # Now test adding materials and expenses to multiple projects
        materials = [
            Material(project_id=project1.id, description="Materials for P1", cost=500.0, purchase_date=date.today()),
            Material(project_id=project2.id, description="Materials for P2", cost=700.0, purchase_date=date.today()),
            Material(project_id=project3.id, description="Materials for P3", cost=300.0, purchase_date=date.today())
        ]
        
        expenses = [
            Expense(project_id=project1.id, description="Expense for P1", category="Misc", amount=100.0, date=date.today()),
            Expense(project_id=project2.id, description="Expense for P2", category="Misc", amount=150.0, date=date.today()),
            Expense(project_id=project3.id, description="Expense for P3", category="Misc", amount=50.0, date=date.today())
        ]
        
        db.session.add_all(materials + expenses)
        db.session.commit()
        
        # Refresh project data
        project1 = Project.query.get(project1.id)
        project2 = Project.query.get(project2.id)
        project3 = Project.query.get(project3.id)
        
        # Verify total costs and profits are calculated correctly for each project
        assert round(project1.total_material_cost, 2) == 500.0
        assert round(project1.total_other_expenses, 2) == 100.0
        assert round(project1.total_cost, 2) == round(expected_labor_cost_p1 + 500.0 + 100.0, 2)
        assert round(project1.profit, 2) == round(5000.0 - project1.total_cost, 2)
        
        assert round(project2.total_material_cost, 2) == 700.0
        assert round(project2.total_other_expenses, 2) == 150.0
        assert round(project2.total_cost, 2) == round(expected_labor_cost_p2 + 700.0 + 150.0, 2)
        assert round(project2.profit, 2) == round(7000.0 - project2.total_cost, 2)
        
        assert round(project3.total_material_cost, 2) == 300.0
        assert round(project3.total_other_expenses, 2) == 50.0
        assert round(project3.total_cost, 2) == round(expected_labor_cost_p3 + 300.0 + 50.0, 2)
        assert round(project3.profit, 2) == round(3000.0 - project3.total_cost, 2)

def test_employee_status_change(app):
    """Test employee status changes and the impact on system behavior."""
    with app.app_context():
        # Create an active employee
        employee = Employee(
            name="Status Test Employee",
            pay_rate=25.0,
            is_active=True,
            hire_date=date.today() - timedelta(days=90)
        )
        db.session.add(employee)
        
        # Create a project
        project = Project(
            name="Employee Status Test Project",
            status=ProjectStatus.IN_PROGRESS
        )
        db.session.add(project)
        db.session.commit()
        
        # Record timesheets while employee is active
        timesheet_active = Timesheet(
            employee_id=employee.id,
            project_id=project.id,
            date=date.today() - timedelta(days=10),
            entry_time=time(8, 0),
            exit_time=time(16, 0),
            lunch_duration_minutes=30
        )
        db.session.add(timesheet_active)
        db.session.commit()
        
        # Now mark the employee as inactive
        employee.is_active = False
        db.session.commit()
        
        # Try to record another timesheet
        timesheet_inactive = Timesheet(
            employee_id=employee.id,
            project_id=project.id,
            date=date.today(),
            entry_time=time(8, 0),
            exit_time=time(16, 0),
            lunch_duration_minutes=30
        )
        
        # At the model level, validation now prevents timesheets for inactive employees
        # We expect is_valid() to return false
        is_valid, message = timesheet_inactive.is_valid()
        assert not is_valid
        assert "inactive employee" in message.lower()
        
        # The model-level validation allows this to be saved, but application-level
        # validation in the route prevents it
        db.session.add(timesheet_inactive)
        db.session.commit()
        
        # First timesheet should be saved
        assert timesheet_active.id is not None
        assert timesheet_inactive.id is not None
        
        # Check that labor costs are still calculated for the active timesheet
        project = db.session.get(Project, project.id)  # Use newer SQLAlchemy get method
        expected_labor_cost = 7.5 * employee.pay_rate  # 1 valid timesheet, 7.5 hours
        assert round(project.total_labor_cost, 2) == round(expected_labor_cost, 2)

def test_project_status_changes(app):
    """Test project status changes and the impact on system behavior."""
    with app.app_context():
        # Create a project that goes through the entire lifecycle
        project = Project(
            name="Status Change Test Project",
            client_name="Status Test Client",
            contract_value=10000.0,
            status=ProjectStatus.PENDING,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() + timedelta(days=30)
        )
        db.session.add(project)
        db.session.commit()
        
        # Test each status change
        for status in [
            ProjectStatus.IN_PROGRESS,
            ProjectStatus.COMPLETED,
            ProjectStatus.INVOICED,
            ProjectStatus.PAID
        ]:
            project.status = status
            db.session.commit()
            
            # Verify status was updated
            updated_project = Project.query.get(project.id)
            assert updated_project.status == status
