import pytest
from datetime import date, time

def test_index_route(client):
    """Test the index route."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Dashboard' in response.data

def test_employees_route(client, sample_data):
    """Test the employees listing route."""
    response = client.get('/employees')
    assert response.status_code == 200
    assert b'Employees' in response.data
    # Check that sample employees are listed
    assert b'John Doe' in response.data
    assert b'Jane Smith' in response.data

def test_projects_route(client, sample_data):
    """Test the projects listing route."""
    response = client.get('/projects')
    assert response.status_code == 200
    assert b'Projects' in response.data
    # Check that sample projects are listed
    assert b'Office Renovation' in response.data
    assert b'Residential Painting' in response.data

def test_add_employee_route(client):
    """Test adding a new employee."""
    # Get the form page
    response = client.get('/employee/add')
    assert response.status_code == 200
    assert b'Add Employee' in response.data
    
    # Submit the form with valid data
    employee_data = {
        'name': 'New Test Employee',
        'employee_id_str': 'EMP-TEST',
        'contact_details': 'newtest@example.com',
        'pay_rate': 24.50,
        'payment_method_preference': 'CHECK',
        'is_active': True,
        'hire_date': '2025-01-01'
    }
    response = client.post('/employee/add', data=employee_data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Employee New Test Employee added successfully!' in response.data
    assert b'New Test Employee' in response.data

def test_add_project_route(client):
    """Test adding a new project."""
    # Get the form page
    response = client.get('/project/add')
    assert response.status_code == 200
    assert b'Add Project' in response.data
    
    # Submit the form with valid data
    project_data = {
        'name': 'New Test Project',
        'project_id_str': 'PRJ-TEST',
        'client_name': 'Test Client',
        'location': 'Test Location',
        'start_date': '2025-04-01',
        'end_date': '2025-04-30',
        'contract_value': 7500.0,
        'description': 'This is a test project',
        'status': 'PENDING'
    }
    response = client.post('/project/add', data=project_data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Project New Test Project added successfully!' in response.data
    assert b'New Test Project' in response.data

def test_future_enhancements_route(client):
    """Test the future enhancements page."""
    response = client.get('/future-enhancements')
    assert response.status_code == 200
    assert b'Future Enhancements' in response.data
    assert b'User Authentication' in response.data
    assert b'Document Management' in response.data
    assert b'Client Portal' in response.data
    assert b'Suggest an Enhancement' in response.data

def test_suggest_enhancement_route(client):
    """Test submitting an enhancement suggestion."""
    suggestion_data = {
        'title': 'Integration with QuickBooks',
        'description': 'Add integration with QuickBooks for seamless accounting workflows.',
        'priority': 'Medium'
    }
    response = client.post('/suggest-enhancement', data=suggestion_data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Thank you for your enhancement suggestion' in response.data
    assert b'Integration with QuickBooks' in response.data

def test_project_detail_route(client, sample_data):
    """Test the project detail page."""
    # Get a fresh instance of the project within the request context
    with client.application.app_context():
        from models import Project
        project_id = sample_data['project_ids'][0]
        project = Project.query.get(project_id)
        assert project is not None
    
    response = client.get(f'/project/view/{project_id}')
    assert response.status_code == 200
    assert b'Office Renovation' in response.data
    assert b'Project Details' in response.data
    assert b'Contract Value' in response.data

def test_nonexistent_route(client):
    """Test accessing a non-existent route."""
    response = client.get('/nonexistent-page')
    assert response.status_code == 404
