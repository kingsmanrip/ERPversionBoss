from app import app, db
from models import Invoice
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import inspect

def migrate_invoice_description():
    """Add the description column to the invoice table."""
    with app.app_context():
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('invoice')]
        
        if 'description' not in columns:
            # Add the description column if it doesn't exist
            db.session.execute(sa.text('ALTER TABLE invoice ADD COLUMN description TEXT'))
            db.session.commit()
            print("Successfully added 'description' column to the invoice table.")
        else:
            print("The 'description' column already exists in the invoice table.")

if __name__ == "__main__":
    migrate_invoice_description()
