"""
Add client_contact_name column to the invoice table.
"""
from models import db
import sqlalchemy as sa

def migrate_client_contact_name():
    """Add the client_contact_name column to the invoice table."""
    with db.engine.connect() as conn:
        inspector = sa.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('invoice')]
        
        if 'client_contact_name' not in columns:
            try:
                db.session.execute(sa.text('ALTER TABLE invoice ADD COLUMN client_contact_name VARCHAR(100)'))
                db.session.commit()
                print("Successfully added 'client_contact_name' column to the invoice table.")
            except Exception as e:
                db.session.rollback()
                print(f"Error adding 'client_contact_name' column: {e}")
        else:
            print("The 'client_contact_name' column already exists in the invoice table.")

if __name__ == "__main__":
    from app import app
    with app.app_context():
        migrate_client_contact_name()
