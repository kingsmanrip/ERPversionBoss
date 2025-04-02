"""
Test script for verifying the employee dropdown search feature works correctly.
"""
from app import app
from models import db, Employee, PayrollPayment, Timesheet

def test_employee_dropdown():
    """Test the employee dropdown search functionality"""
    with app.app_context():
        # 1. Check that employees exist in the system
        total_employees = Employee.query.count()
        print(f'\n1. EMPLOYEE COUNT TEST:')
        print(f'Total employees in system: {total_employees}')
        assert total_employees > 0, "No employees found in database"
        print("✓ Employees exist in database")
        
        # 2. Verify we can get a list of employees for the dropdown
        employees = Employee.query.order_by(Employee.name).all()
        print(f'\n2. EMPLOYEE LIST TEST:')
        print(f'First 5 employees (alphabetical):')
        for idx, emp in enumerate(employees[:5]):
            print(f'- {emp.id}: {emp.name} (Rate: ${emp.pay_rate}/hr)')
        print("✓ Employee list can be retrieved and ordered")
        
        # 3. Test employee filtering by ID
        if employees:
            test_employee = employees[0]  # Use the first employee for testing
            print(f'\n3. EMPLOYEE FILTERING TEST:')
            print(f'Testing with employee: {test_employee.name} (ID: {test_employee.id})')
            
            filtered_employee = Employee.query.filter_by(id=test_employee.id).first()
            assert filtered_employee is not None, f"Could not find employee with ID {test_employee.id}"
            assert filtered_employee.id == test_employee.id, "Employee ID mismatch"
            print(f"✓ Successfully filtered employee by ID")
            
            # 4. Test retrieving employee's payroll data
            payments = PayrollPayment.query.filter_by(employee_id=test_employee.id).all()
            timesheets = Timesheet.query.filter_by(employee_id=test_employee.id).all()
            
            print(f'\n4. EMPLOYEE PAYROLL DATA TEST:')
            print(f'Employee: {test_employee.name}')
            print(f'- Payroll Payments: {len(payments)}')
            print(f'- Timesheet Entries: {len(timesheets)}')
            
            # Calculate totals to ensure calculations work
            total_paid = sum(payment.amount for payment in payments)
            total_hours = sum(ts.calculated_hours for ts in timesheets)
            
            print(f'- Total Amount Paid: ${total_paid:.2f}')
            print(f'- Total Hours Worked: {total_hours:.2f} hours')
            print(f'✓ Successfully retrieved employee payroll data')
            
            if payments:
                print(f'\nSample Payment Details:')
                sample = payments[0]
                print(f'- Date: {sample.payment_date}')
                print(f'- Amount: ${sample.amount:.2f}')
                print(f'- Payment Method: {sample.payment_method.name}')
            
            if timesheets:
                print(f'\nSample Timesheet Details:')
                sample = timesheets[0]
                print(f'- Date: {sample.date}')
                print(f'- Project: {sample.project.name}')
                print(f'- Hours: {sample.calculated_hours:.2f}')
            
            print("\nAll tests passed successfully! ✓")

if __name__ == "__main__":
    test_employee_dropdown()
