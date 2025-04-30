"""
Script to verify that all payroll payment records have been deleted.
"""
from app import app
from models import db, PayrollPayment, PayrollDeduction

def verify_payroll_deletion():
    with app.app_context():
        payment_count = PayrollPayment.query.count()
        print(f"Payroll payment count: {payment_count}")
        
        # Check for any remaining PayrollDeduction records
        try:
            deduction_count = PayrollDeduction.query.count()
            print(f"Payroll deduction count: {deduction_count}")
        except:
            print("No PayrollDeduction model or table found.")
        
        if payment_count == 0:
            print("✅ All payroll payment records have been successfully deleted.")
        else:
            print(f"⚠️ There are still {payment_count} payroll payment records in the database.")

if __name__ == "__main__":
    verify_payroll_deletion()
