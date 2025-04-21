"""
Add client_city_state column to the invoice table.
"""
from models import db
import sqlalchemy as sa

def migrate_client_city_state():
    """Add the client_city_state column to the invoice table."""
    with db.engine.connect() as conn:
        inspector = sa.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('invoice')]
        
        if 'client_city_state' not in columns:
            try:
                db.session.execute(sa.text('ALTER TABLE invoice ADD COLUMN client_city_state VARCHAR(100)'))
                db.session.commit()
                print("Successfully added 'client_city_state' column to the invoice table.")
            except Exception as e:
                db.session.rollback()
                print(f"Error adding 'client_city_state' column: {e}")
        else:
            print("The 'client_city_state' column already exists in the invoice table.")

if __name__ == "__main__":
    from app import app
    with app.app_context():
        migrate_client_city_state()
