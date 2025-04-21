"""
Add job_location column to the invoice table.
"""
from models import db
import sqlalchemy as sa

def migrate_job_location():
    """Add the job_location column to the invoice table."""
    with db.engine.connect() as conn:
        inspector = sa.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('invoice')]
        
        if 'job_location' not in columns:
            try:
                db.session.execute(sa.text('ALTER TABLE invoice ADD COLUMN job_location VARCHAR(200)'))
                db.session.commit()
                print("Successfully added 'job_location' column to the invoice table.")
            except Exception as e:
                db.session.rollback()
                print(f"Error adding 'job_location' column: {e}")
        else:
            print("The 'job_location' column already exists in the invoice table.")

if __name__ == "__main__":
    from app import app
    with app.app_context():
        migrate_job_location()
