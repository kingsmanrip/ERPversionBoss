from app import app, db
from models import db, Employee, Timesheet, PayrollPayment, PayrollDeduction

def fix_employee_delete():
    """
    Update the database schema to fix employee deletion by ensuring 
    all related tables have ON DELETE CASCADE set for employee foreign keys.
    
    This creates a clean solution that doesn't involve modifying actual data.
    """
    with app.app_context():
        try:
            print("Beginning employee deletion fix...")
            
            # Enable foreign keys
            db.session.execute('PRAGMA foreign_keys = OFF')
            
            # Fix the relationship for timesheets
            print("1. Fixing Timesheet-Employee relationship...")
            db.session.execute('''
                CREATE TABLE timesheet_temp (
                    id INTEGER PRIMARY KEY,
                    employee_id INTEGER NOT NULL,
                    project_id INTEGER,
                    date DATE NOT NULL,
                    entry_time TIME NOT NULL,
                    exit_time TIME NOT NULL,
                    lunch_duration_minutes INTEGER DEFAULT 0,
                    FOREIGN KEY (employee_id) REFERENCES employee(id) ON DELETE CASCADE,
                    FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE
                )
            ''')
            
            db.session.execute('''
                INSERT INTO timesheet_temp 
                SELECT id, employee_id, project_id, date, entry_time, exit_time, lunch_duration_minutes 
                FROM timesheet
            ''')
            
            db.session.execute('DROP TABLE timesheet')
            db.session.execute('ALTER TABLE timesheet_temp RENAME TO timesheet')
            
            # Recreate indexes for timesheet
            db.session.execute('CREATE INDEX idx_timesheet_employee_date ON timesheet(employee_id, date)')
            db.session.execute('CREATE INDEX idx_timesheet_project_date ON timesheet(project_id, date)')
            
            # Fix the relationship for payroll_payment
            print("2. Fixing PayrollPayment-Employee relationship...")
            db.session.execute('''
                CREATE TABLE payroll_payment_temp (
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
            ''')
            
            db.session.execute('''
                INSERT INTO payroll_payment_temp 
                SELECT id, employee_id, pay_period_start, pay_period_end, gross_amount, 
                       amount, payment_date, payment_method, notes, check_number, bank_name
                FROM payroll_payment
            ''')
            
            db.session.execute('DROP TABLE payroll_payment')
            db.session.execute('ALTER TABLE payroll_payment_temp RENAME TO payroll_payment')
            
            # Recreate indexes for payroll_payment
            db.session.execute('CREATE INDEX idx_payroll_emp_date ON payroll_payment(employee_id, payment_date)')
            db.session.execute('CREATE INDEX idx_payroll_method ON payroll_payment(payment_method)')
            db.session.execute('CREATE INDEX idx_payroll_period ON payroll_payment(pay_period_start, pay_period_end)')
            
            # Now, fix the relationship for payroll_deduction 
            # (which depends on payroll_payment that we just fixed)
            print("3. Fixing PayrollDeduction-PayrollPayment relationship...")
            db.session.execute('''
                CREATE TABLE payroll_deduction_temp (
                    id INTEGER PRIMARY KEY,
                    payroll_payment_id INTEGER NOT NULL,
                    description VARCHAR(100) NOT NULL,
                    amount FLOAT NOT NULL,
                    deduction_type VARCHAR NOT NULL,
                    notes TEXT,
                    FOREIGN KEY (payroll_payment_id) REFERENCES payroll_payment(id) ON DELETE CASCADE
                )
            ''')
            
            db.session.execute('''
                INSERT INTO payroll_deduction_temp 
                SELECT id, payroll_payment_id, description, amount, deduction_type, notes
                FROM payroll_deduction
            ''')
            
            db.session.execute('DROP TABLE payroll_deduction')
            db.session.execute('ALTER TABLE payroll_deduction_temp RENAME TO payroll_deduction')
            
            # Recreate indexes for payroll_deduction
            db.session.execute('CREATE INDEX idx_deduction_payroll ON payroll_deduction(payroll_payment_id)')
            db.session.execute('CREATE INDEX idx_deduction_type ON payroll_deduction(deduction_type)')
            
            # Re-enable foreign keys
            db.session.execute('PRAGMA foreign_keys = ON')
            
            db.session.commit()
            print("Successfully fixed employee deletion relationships!")
            print("You should now be able to delete employees without errors.")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error fixing employee deletion: {e}")

if __name__ == "__main__":
    fix_employee_delete()
