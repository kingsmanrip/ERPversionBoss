"""
Script to safely delete all payroll payment records from the database.
This script uses the same models and database connection as the main application
to ensure data integrity and avoid breaking any system functionality.
"""
from flask import Flask
from models import db, PayrollPayment
import os

# Create a minimal Flask app to use the same database configuration
app = Flask(__name__)
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(instance_path, "erp.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def delete_all_payroll_payments():
    """Delete all payroll payment records and return count of deleted records."""
    with app.app_context():
        # First, get the count of payroll payments to be deleted
        payment_count = PayrollPayment.query.count()
        
        # Begin a transaction to ensure database integrity
        try:
            # Also delete any child records if needed (PayrollDeduction if it exists)
            try:
                # Check if PayrollDeduction model exists in the system
                from models import PayrollDeduction
                deduction_count = db.session.query(PayrollDeduction).delete()
                print(f"Deleted {deduction_count} payroll deduction records.")
            except ImportError:
                print("No PayrollDeduction model found in the system.")
            except Exception as e:
                print(f"No deduction records to delete or error: {str(e)}")
            
            # Delete all records from the payroll_payment table
            deleted = db.session.query(PayrollPayment).delete()
            db.session.commit()
            return deleted, None
        except Exception as e:
            # Rollback in case of error
            db.session.rollback()
            return 0, str(e)

if __name__ == "__main__":
    deleted_count, error = delete_all_payroll_payments()
    
    if error:
        print(f"❌ Error deleting payroll payments: {error}")
    else:
        print(f"✅ Successfully deleted {deleted_count} payroll payment records from the database.")
        print("The system is ready to continue normal operation with a clean payroll history.")
