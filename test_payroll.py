"""
Test script for payroll functionality in the ERP application
"""
from app import app, db
from models import Employee, PayrollPayment, PaymentMethod, PayrollDeduction, DeductionType
from datetime import date, timedelta
import random

def test_payroll_functions():
    with app.app_context():
        # 1. Test employee listing
        employees = Employee.query.all()
        print(f"=== Test 1: Employee Listing ===")
        print(f"Found {len(employees)} employees")
        for e in employees[:5]:  # Show first 5 employees
            print(f"ID: {e.id}, Name: {e.name}, Pay Rate: ${e.pay_rate:.2f}/hour")
        print()

        # 2. Test payroll payment recording and retrieval
        print(f"=== Test 2: Payroll Payment Recording ===")
        # Find a random employee to use for test
        if employees:
            test_employee = random.choice(employees)
            print(f"Selected employee for test: {test_employee.name}")
            
            # Create a test payment
            payment_date = date.today()
            pay_period_start = payment_date - timedelta(days=14)
            pay_period_end = payment_date - timedelta(days=1)
            
            # Test Cash payment
            cash_payment = PayrollPayment(
                employee_id=test_employee.id,
                pay_period_start=pay_period_start,
                pay_period_end=pay_period_end,
                payment_date=payment_date,
                gross_amount=150.00,
                amount=150.00,  # No deductions
                payment_method=PaymentMethod.CASH,
                notes="Test cash payment"
            )
            db.session.add(cash_payment)
            
            # Test Check payment with deduction
            check_payment = PayrollPayment(
                employee_id=test_employee.id,
                pay_period_start=pay_period_start,
                pay_period_end=pay_period_end,
                payment_date=payment_date,
                gross_amount=200.00,
                amount=180.00,  # With $20 deduction
                payment_method=PaymentMethod.CHECK,
                check_number="12345",
                bank_name="Test Bank",
                notes="Test check payment"
            )
            db.session.add(check_payment)
            db.session.flush()  # To get the payment ID
            
            # Add deduction
            deduction = PayrollDeduction(
                payroll_payment_id=check_payment.id,
                description="Test deduction",
                amount=20.00,
                deduction_type=DeductionType.OTHER,
                notes="Test deduction notes"
            )
            db.session.add(deduction)
            
            db.session.commit()
            print(f"Created test payments for {test_employee.name}")
            print(f"  - Cash payment: ${cash_payment.amount:.2f}")
            print(f"  - Check payment: ${check_payment.amount:.2f} (with $20.00 deduction)")
            print(f"  - Check #: {check_payment.check_number}, Bank: {check_payment.bank_name}")
            
            # Verify payments were recorded
            employee_payments = PayrollPayment.query.filter_by(employee_id=test_employee.id).order_by(PayrollPayment.payment_date.desc()).all()
            print(f"\nFound {len(employee_payments)} payments for {test_employee.name}")
            
            for i, payment in enumerate(employee_payments[:5]):  # Show up to 5 most recent payments
                deductions = PayrollDeduction.query.filter_by(payroll_payment_id=payment.id).all()
                total_deductions = sum(d.amount for d in deductions)
                
                print(f"Payment {i+1}:")
                print(f"  - Date: {payment.payment_date}")
                print(f"  - Method: {payment.payment_method.value}")
                print(f"  - Gross Amount: ${payment.gross_amount:.2f}")
                print(f"  - Net Amount: ${payment.amount:.2f}")
                print(f"  - Total Deductions: ${total_deductions:.2f}")
                
                if payment.payment_method == PaymentMethod.CHECK:
                    print(f"  - Check #: {payment.check_number}")
                    print(f"  - Bank: {payment.bank_name}")
                print()
        else:
            print("No employees found for testing")

        # 3. Test payroll report calculation
        print(f"=== Test 3: Payroll Calculation Verification ===")
        if employees:
            test_employee = Employee.query.order_by(db.func.random()).first()
            print(f"Selected employee for test: {test_employee.name} (Pay Rate: ${test_employee.pay_rate:.2f}/hour)")
            
            # Get all payments for this employee
            payments = PayrollPayment.query.filter_by(employee_id=test_employee.id).all()
            total_paid = sum(payment.amount for payment in payments)
            print(f"Total payments recorded: {len(payments)}")
            print(f"Total amount paid: ${total_paid:.2f}")
            
            # Calculate how many hours this would cover
            hours_covered = total_paid / test_employee.pay_rate if test_employee.pay_rate > 0 else 0
            print(f"This amount covers approximately {hours_covered:.2f} hours of work")
        
        print("\nPayroll tests completed successfully!")

if __name__ == "__main__":
    test_payroll_functions()
