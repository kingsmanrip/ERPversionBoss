"""
Add client_phone column to the invoice table.
"""
from models import db
import sqlalchemy as sa

def migrate_client_phone():
    """Add the client_phone column to the invoice table."""
    with db.engine.connect() as conn:
        inspector = sa.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('invoice')]
        
        if 'client_phone' not in columns:
            try:
                db.session.execute(sa.text('ALTER TABLE invoice ADD COLUMN client_phone VARCHAR(20)'))
                db.session.commit()
                print("Successfully added 'client_phone' column to the invoice table.")
            except Exception as e:
                db.session.rollback()
                print(f"Error adding 'client_phone' column: {e}")
        else:
            print("The 'client_phone' column already exists in the invoice table.")

if __name__ == "__main__":
    from app import app
    with app.app_context():
        migrate_client_phone()
