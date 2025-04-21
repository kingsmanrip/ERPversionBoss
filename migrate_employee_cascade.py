from app import app, db
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import inspect
from models import PayrollPayment

def migrate_employee_cascade():
    """Update the employee_id foreign key in the payroll_payment table to include ON DELETE CASCADE."""
    with app.app_context():
        try:
            # For SQLite, we need to recreate the table with the new constraint
            # First, enable foreign keys
            db.session.execute(sa.text('PRAGMA foreign_keys = OFF'))
            
            # Create a temporary table with the new constraint
            db.session.execute(sa.text('''
                CREATE TABLE payroll_payment_new (
                    id INTEGER PRIMARY KEY,
                    employee_id INTEGER NOT NULL,
                    pay_period_start DATE NOT NULL,
                    pay_period_end DATE NOT NULL,
                    gross_amount FLOAT NOT NULL,
                    amount FLOAT NOT NULL,
                    payment_date DATE NOT NULL,
                    payment_method VARCHAR NOT NULL,
                    notes TEXT,
                    check_number VARCHAR(50),
                    bank_name VARCHAR(100),
                    FOREIGN KEY (employee_id) REFERENCES employee(id) ON DELETE CASCADE
                )
            '''))
            
            # Copy data from the old table to the new one
            db.session.execute(sa.text('''
                INSERT INTO payroll_payment_new 
                SELECT id, employee_id, pay_period_start, pay_period_end, gross_amount, 
                       amount, payment_date, payment_method, notes, check_number, bank_name
                FROM payroll_payment
            '''))
            
            # Drop the old table
            db.session.execute(sa.text('DROP TABLE payroll_payment'))
            
            # Rename the new table to the original name
            db.session.execute(sa.text('ALTER TABLE payroll_payment_new RENAME TO payroll_payment'))
            
            # Recreate the indexes
            db.session.execute(sa.text('CREATE INDEX idx_payroll_emp_date ON payroll_payment (employee_id, payment_date)'))
            db.session.execute(sa.text('CREATE INDEX idx_payroll_method ON payroll_payment (payment_method)'))
            db.session.execute(sa.text('CREATE INDEX idx_payroll_period ON payroll_payment (pay_period_start, pay_period_end)'))
            
            # Re-enable foreign keys
            db.session.execute(sa.text('PRAGMA foreign_keys = ON'))
            
            db.session.commit()
            print("Successfully updated payroll_payment table with CASCADE delete.")
        except Exception as e:
            db.session.rollback()
            print(f"Error updating foreign key: {e}")

if __name__ == "__main__":
    migrate_employee_cascade()
