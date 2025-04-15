from app import app, db
from models import Invoice
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import inspect

def migrate_invoice_amounts():
    """Add the base_amount and tax_amount columns to the invoice table."""
    with app.app_context():
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('invoice')]
        
        changes_made = False
        
        if 'base_amount' not in columns:
            # Add the base_amount column if it doesn't exist
            db.session.execute(sa.text('ALTER TABLE invoice ADD COLUMN base_amount FLOAT DEFAULT 0'))
            changes_made = True
            print("Successfully added 'base_amount' column to the invoice table.")
        else:
            print("The 'base_amount' column already exists in the invoice table.")
            
        if 'tax_amount' not in columns:
            # Add the tax_amount column if it doesn't exist
            db.session.execute(sa.text('ALTER TABLE invoice ADD COLUMN tax_amount FLOAT DEFAULT 0'))
            changes_made = True
            print("Successfully added 'tax_amount' column to the invoice table.")
        else:
            print("The 'tax_amount' column already exists in the invoice table.")
            
        if changes_made:
            # Update the existing records to set base_amount as 95% of amount and tax_amount as 5% of amount
            db.session.execute(sa.text('UPDATE invoice SET base_amount = amount * 0.95, tax_amount = amount * 0.05 WHERE base_amount = 0 AND tax_amount = 0'))
            db.session.commit()
            print("Updated existing invoices with default values (base_amount = 95% of total, tax_amount = 5% of total).")

if __name__ == "__main__":
    migrate_invoice_amounts()
