"""
Add signature_date column to the invoice table.
"""
from models import db
import sqlalchemy as sa
from datetime import date

def migrate_signature_date():
    """Add the signature_date column to the invoice table."""
    with db.engine.connect() as conn:
        inspector = sa.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('invoice')]
        
        if 'signature_date' not in columns:
            try:
                db.session.execute(sa.text('ALTER TABLE invoice ADD COLUMN signature_date DATE'))
                db.session.commit()
                print("Successfully added 'signature_date' column to the invoice table.")
            except Exception as e:
                db.session.rollback()
                print(f"Error adding 'signature_date' column: {e}")
        else:
            print("The 'signature_date' column already exists in the invoice table.")

if __name__ == "__main__":
    from app import app
    with app.app_context():
        migrate_signature_date()
