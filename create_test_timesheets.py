from app import app, db
from models import Timesheet, Employee, Project
import datetime

def create_test_timesheets():
    with app.app_context():
        # Get the first employee
        employee = Employee.query.first()
        if not employee:
            print("No employees found in database")
            return
            
        print(f"Creating test timesheets for employee: {employee.name}, Pay rate: ${employee.pay_rate}")
        
        # Common timesheet parameters
        entry_time = datetime.time(8, 0)  # 8:00 AM
        exit_time = datetime.time(17, 0)  # 5:00 PM
        lunch_minutes = 60
        
        # Create a Saturday timesheet (April 5, 2025 is a Saturday)
        saturday = datetime.date(2025, 4, 5)
        print(f"Creating Saturday timesheet for {saturday} (weekday: {saturday.weekday()})")
        
        saturday_timesheet = Timesheet(
            employee_id=employee.id,
            date=saturday,
            entry_time=entry_time,
            exit_time=exit_time,
            lunch_duration_minutes=lunch_minutes
        )
        db.session.add(saturday_timesheet)
        
        # Create a regular weekday timesheet (April 3, 2025 is a Thursday)
        thursday = datetime.date(2025, 4, 3)
        print(f"Creating Thursday timesheet for {thursday} (weekday: {thursday.weekday()})")
        
        weekday_timesheet = Timesheet(
            employee_id=employee.id,
            date=thursday,
            entry_time=entry_time,
            exit_time=exit_time,
            lunch_duration_minutes=lunch_minutes
        )
        db.session.add(weekday_timesheet)
        
        # Commit both timesheet records
        db.session.commit()
        
        # Verify the effective hourly rates
        db.session.refresh(saturday_timesheet)
        db.session.refresh(weekday_timesheet)
        
        print("\nTest Results:")
        print(f"Saturday timesheet - Base rate: ${employee.pay_rate}, Effective rate: ${saturday_timesheet.effective_hourly_rate}")
        print(f"  Date: {saturday_timesheet.date}, Is Saturday: {saturday_timesheet.date.weekday() == 5}")
        print(f"  Hours: {saturday_timesheet.calculated_hours:.2f}, Amount: ${saturday_timesheet.calculated_amount:.2f}")
        
        print(f"Weekday timesheet - Base rate: ${employee.pay_rate}, Effective rate: ${weekday_timesheet.effective_hourly_rate}")
        print(f"  Date: {weekday_timesheet.date}, Is Saturday: {weekday_timesheet.date.weekday() == 5}")  
        print(f"  Hours: {weekday_timesheet.calculated_hours:.2f}, Amount: ${weekday_timesheet.calculated_amount:.2f}")
        
        print("\nTest completed successfully")

if __name__ == "__main__":
    create_test_timesheets()
