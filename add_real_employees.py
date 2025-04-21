from app import app, db
from models import Employee, PaymentMethod
from datetime import datetime

def add_real_employees():
    """Add real employees to the database."""
    employees_data = [
        {"id": 1, "name": "Daniel ", "employee_id_str": "2", "contact_details": "", "pay_rate": 23, "payment_method_preference": "CASH", "is_active": True, "hire_date": "2025-04-03"},
        {"id": 2, "name": "William", "employee_id_str": "17", "contact_details": "", "pay_rate": 23, "payment_method_preference": "CASH", "is_active": True, "hire_date": "2025-04-03"},
        {"id": 3, "name": "Luis Gerardo Sanchez", "employee_id_str": "10", "contact_details": "", "pay_rate": 18, "payment_method_preference": "CHECK", "is_active": True, "hire_date": "2025-04-03"},
        {"id": 4, "name": "Alfredo Sanchez", "employee_id_str": "1", "contact_details": "", "pay_rate": 18, "payment_method_preference": "CHECK", "is_active": True, "hire_date": "2025-04-03"},
        {"id": 5, "name": "Gerardo Alvarado", "employee_id_str": "5", "contact_details": "", "pay_rate": 23, "payment_method_preference": "CHECK", "is_active": True, "hire_date": "2025-04-03"},
        {"id": 6, "name": "Gerardo Olivera", "employee_id_str": "6", "contact_details": "", "pay_rate": 20, "payment_method_preference": "CHECK", "is_active": True, "hire_date": "2025-04-03"},
        {"id": 7, "name": "Jose Baltazar", "employee_id_str": "8", "contact_details": "", "pay_rate": 20, "payment_method_preference": "CHECK", "is_active": True, "hire_date": "2025-04-03"},
        {"id": 8, "name": "Luis Afonso Rosales Gomes", "employee_id_str": "9", "contact_details": "", "pay_rate": 18, "payment_method_preference": "CHECK", "is_active": True, "hire_date": "2025-04-03"},
        {"id": 9, "name": "Ruata Bezerra ", "employee_id_str": "15", "contact_details": "", "pay_rate": 20, "payment_method_preference": "CHECK", "is_active": True, "hire_date": "2025-04-03"},
        {"id": 10, "name": "Eduardo Bautista Rodrigues", "employee_id_str": "3", "contact_details": "", "pay_rate": 20, "payment_method_preference": "CHECK", "is_active": True, "hire_date": "2025-04-03"},
        {"id": 11, "name": "Nicolasa Gabriela Osorio", "employee_id_str": "11", "contact_details": "", "pay_rate": 17, "payment_method_preference": "CHECK", "is_active": True, "hire_date": "2025-04-03"},
        {"id": 12, "name": "Rodrigo Aguilar ", "employee_id_str": "14", "contact_details": "", "pay_rate": 17, "payment_method_preference": "CHECK", "is_active": True, "hire_date": "2025-04-03"},
        {"id": 13, "name": "Vicente ", "employee_id_str": "16", "contact_details": "", "pay_rate": 17, "payment_method_preference": "CHECK", "is_active": True, "hire_date": "2025-04-03"},
        {"id": 14, "name": "Eugenio Baltazar", "employee_id_str": "4", "contact_details": "", "pay_rate": 16, "payment_method_preference": "CHECK", "is_active": True, "hire_date": "2025-04-03"},
        {"id": 15, "name": "Jordi Omar ", "employee_id_str": "7", "contact_details": "", "pay_rate": 15, "payment_method_preference": "CHECK", "is_active": True, "hire_date": "2025-04-03"},
        {"id": 16, "name": "Rigoberto", "employee_id_str": "13", "contact_details": "", "pay_rate": 15, "payment_method_preference": "CHECK", "is_active": True, "hire_date": "2025-04-03"},
        {"id": 17, "name": "Patricia Silva ", "employee_id_str": "12", "contact_details": "", "pay_rate": 17.5, "payment_method_preference": "CASH", "is_active": True, "hire_date": "2024-12-09"},
        {"id": 18, "name": "Mauricio Santos", "employee_id_str": "owner", "contact_details": "", "pay_rate": 15.98, "payment_method_preference": "CHECK", "is_active": True, "hire_date": "2025-04-03"},
        {"id": 19, "name": "Alessandro Bezerra", "employee_id_str": "18", "contact_details": "", "pay_rate": 20, "payment_method_preference": "CHECK", "is_active": False, "hire_date": "2025-04-03"},
    ]
    
    with app.app_context():
        # Clear existing employees 
        db.session.query(Employee).delete()
        
        # Add employees
        for employee_data in employees_data:
            employee = Employee(
                name=employee_data["name"],
                employee_id_str=employee_data["employee_id_str"],
                contact_details=employee_data["contact_details"],
                pay_rate=employee_data["pay_rate"],
                payment_method_preference=PaymentMethod[employee_data["payment_method_preference"]],
                is_active=employee_data["is_active"],
                hire_date=datetime.strptime(employee_data["hire_date"], "%Y-%m-%d").date()
            )
            db.session.add(employee)
        
        db.session.commit()
        print(f"Successfully added {len(employees_data)} employees to the database.")

if __name__ == "__main__":
    add_real_employees()
