"""
Script to safely delete all timesheet records from the database.
This script uses the same models and database connection as the main application
to ensure data integrity and avoid breaking any system functionality.
"""
from flask import Flask
from models import db, Timesheet
import os

# Create a minimal Flask app to use the same database configuration
app = Flask(__name__)
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(instance_path, "erp.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def delete_all_timesheets():
    """Delete all timesheet records and return count of deleted records."""
    with app.app_context():
        # First, get the count of timesheets to be deleted
        timesheet_count = Timesheet.query.count()
        
        # Begin a transaction to ensure database integrity
        try:
            # Delete all records from the timesheet table
            deleted = db.session.query(Timesheet).delete()
            db.session.commit()
            return deleted, None
        except Exception as e:
            # Rollback in case of error
            db.session.rollback()
            return 0, str(e)

if __name__ == "__main__":
    deleted_count, error = delete_all_timesheets()
    
    if error:
        print(f"❌ Error deleting timesheets: {error}")
    else:
        print(f"✅ Successfully deleted {deleted_count} timesheet records from the database.")
        print("The system is ready to continue normal operation.")
