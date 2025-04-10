from app import app
from models import PayrollPayment, PaymentMethod, Employee

def check_payment_records():
    with app.app_context():
        print('=== Check Payments in database ===')
        check_payments = PayrollPayment.query.filter_by(payment_method=PaymentMethod.CHECK).all()
        print(f'Total Check Payments: {len(check_payments)}')
        
        if check_payments:
            print("\nSample Check Payments:")
            for p in check_payments[:5]:
                emp = Employee.query.get(p.employee_id)
                print(f'ID: {p.id}, Employee: {emp.name}, Amount: ${p.amount:.2f}')
                print(f'  Check Number: {p.check_number}, Bank: {p.bank_name}')
                print(f'  Payment Date: {p.payment_date}, Method: {p.payment_method.value}')
                print('-' * 50)
        else:
            print("No check payments found in the database.")
            
        # Also check if the PaymentMethod enum values are correct
        print("\nPayment Method Options:")
        for pm in PaymentMethod:
            print(f'{pm.name}: {pm.value}')

if __name__ == "__main__":
    check_payment_records()
