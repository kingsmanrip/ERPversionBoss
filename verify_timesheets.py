"""
Script to verify that all timesheet records have been deleted.
"""
from app import app
from models import db, Timesheet

def verify_timesheets():
    with app.app_context():
        count = Timesheet.query.count()
        print(f"Timesheet count: {count}")
        if count == 0:
            print("✅ All timesheet records have been successfully deleted.")
        else:
            print(f"⚠️ There are still {count} timesheet records in the database.")

if __name__ == "__main__":
    verify_timesheets()
