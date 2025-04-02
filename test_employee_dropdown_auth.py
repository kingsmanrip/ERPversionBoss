"""
Test script for verifying the employee dropdown search feature works correctly in the UI.
This script uses Flask's test client to simulate browser requests with authentication.
"""
from app import app
from models import db, Employee, User
from flask import url_for
import re

def test_employee_dropdown_ui():
    """Test the employee dropdown search functionality in the UI"""
    # Create a test client with session handling
    client = app.test_client(follow_redirects=True)
    client.testing = True
    
    print("\n===== EMPLOYEE DROPDOWN UI TESTING =====")
    
    # First authenticate the test client
    print("\nAUTHENTICATING TEST CLIENT:")
    with client.session_transaction() as session:
        # In a test environment, we can just fake the login by setting session variables
        # This mimics what Flask-Login would do in a real login
        session['_user_id'] = '1'  # Assuming admin user has ID 1
        session['_fresh'] = True
    
    print("✓ Successfully set authentication session")
    
    # Test 1: Check if the payroll report page loads successfully
    print("\n1. TESTING PAYROLL REPORT PAGE LOAD:")
    response = client.get('/payroll/report')
    assert response.status_code == 200, f"Failed to load payroll report page: {response.status_code}"
    print("✓ Payroll report page loads successfully")
    
    # Test 2: Check if the employee dropdown is present
    print("\n2. TESTING EMPLOYEE DROPDOWN PRESENCE:")
    html_content = response.data.decode('utf-8')
    assert '<select name="employee_id" class="form-select"' in html_content, "Employee dropdown not found in HTML"
    print("✓ Employee dropdown is present in the page")
    
    # Test 3: Check if employees are listed in the dropdown
    print("\n3. TESTING EMPLOYEE OPTIONS IN DROPDOWN:")
    with app.app_context():
        employees = Employee.query.order_by(Employee.name).all()
        if employees:
            for employee in employees[:3]:  # Check first 3 employees
                option_pattern = f'<option value="{employee.id}".*?>{employee.name}</option>'
                assert re.search(option_pattern, html_content, re.DOTALL), f"Employee {employee.name} not found in dropdown"
            print(f"✓ Found employees in dropdown (checked {min(3, len(employees))} examples)")
        else:
            print("No employees found in database - skipping dropdown option check")
    
    # Test 4: Test employee search by ID (choose a random employee)
    print("\n4. TESTING EMPLOYEE SELECTION AND RESULTS:")
    with app.app_context():
        test_employee = Employee.query.first()
        if test_employee:
            employee_id = test_employee.id
            print(f"Testing with employee: {test_employee.name} (ID: {employee_id})")
            
            # Make a request with the employee ID
            response = client.get(f'/payroll/report?employee_id={employee_id}')
            assert response.status_code == 200, f"Failed to load search results: {response.status_code}"
            
            result_html = response.data.decode('utf-8')
            
            # Check if the employee dropdown has the selected employee
            assert f'<option value="{employee_id}" selected>' in result_html, "Selected employee not marked in dropdown"
            
            # Check for employee details section
            assert 'Employee Details:' in result_html, "Employee details section not found"
            assert test_employee.name in result_html, f"Employee name {test_employee.name} not found in results"
            
            # Check for the employee summary card
            assert 'Employee Summary' in result_html, "Employee summary card not found"
            
            # Check for Recent Payments and Recent Timesheets sections
            assert 'Recent Payments' in result_html, "Recent Payments section not found"
            assert 'Recent Timesheets' in result_html, "Recent Timesheets section not found"
            
            print("✓ Employee selection and details display correctly")
        else:
            print("No employees found in database - skipping employee selection test")
    
    # Test 5: Clear button functionality
    print("\n5. TESTING CLEAR BUTTON FUNCTIONALITY:")
    with app.app_context():
        test_employee = Employee.query.first()
        if test_employee:
            # Check if the clear button is present when an employee is selected
            employee_id = test_employee.id
            response = client.get(f'/payroll/report?employee_id={employee_id}')
            result_html = response.data.decode('utf-8')
            
            clear_link_pattern = r'<a href="[^"]*\bpayroll/report[^"]*" class="btn btn-outline-secondary">\s*<i class="bi bi-x"></i>\s*Clear\s*</a>'
            assert re.search(clear_link_pattern, result_html), "Clear button not found when employee is selected"
            
            # Check that the clear button is not present when no employee is selected
            response = client.get('/payroll/report')
            result_html = response.data.decode('utf-8')
            clear_button_present = re.search(clear_link_pattern, result_html)
            assert not clear_button_present, "Clear button found when no employee is selected"
            
            print("✓ Clear button functionality verified")
        else:
            print("No employees found in database - skipping clear button test")
    
    print("\nAll UI tests passed successfully! ✓")

if __name__ == "__main__":
    with app.app_context():
        # Set SERVER_NAME so url_for works in test
        app.config['SERVER_NAME'] = 'localhost:5004'
        test_employee_dropdown_ui()
