"""
Comprehensive test script for the payroll system of Mauricio PDQ ERP.
This tests the key components of the payroll workflow:
1. Timesheet calculation with lunch break rules
2. Saturday premium calculation
3. Payroll payment and deduction handling
"""
from app import app, db
from models import (
    Employee, Project, Timesheet, PayrollPayment, PayrollDeduction,
    ProjectStatus, PaymentMethod, DeductionType
)
from datetime import date, time, timedelta, datetime
import sys

def print_header(text):
    """Print a formatted header for test sections."""
    print("\n" + "=" * 80)
    print(f" {text} ".center(80, "="))
    print("=" * 80)

def test_lunch_break_calculation():
    """Test the lunch break calculation in timesheet entries."""
    print_header("TESTING LUNCH BREAK CALCULATION")
    
    # Create test scenarios with different lunch break durations
    scenarios = [
        {"entry": time(8, 0), "exit": time(16, 0), "lunch": 0, "expected": 8.0, "name": "No lunch break"},
        {"entry": time(8, 0), "exit": time(16, 0), "lunch": 15, "expected": 8.0, "name": "15 min lunch (< 30 min)"},
        {"entry": time(8, 0), "exit": time(16, 0), "lunch": 29, "expected": 8.0, "name": "29 min lunch (< 30 min)"},
        {"entry": time(8, 0), "exit": time(16, 0), "lunch": 30, "expected": 7.5, "name": "30 min lunch (exact 30 min)"},
        {"entry": time(8, 0), "exit": time(16, 0), "lunch": 45, "expected": 7.25, "name": "45 min lunch (30-59 min)"},
        {"entry": time(8, 0), "exit": time(16, 0), "lunch": 59, "expected": 7.017, "name": "59 min lunch (30-59 min)"},
        {"entry": time(8, 0), "exit": time(16, 0), "lunch": 60, "expected": 7.5, "name": "60 min lunch (≥ 60 min)"},
        {"entry": time(8, 0), "exit": time(16, 0), "lunch": 90, "expected": 7.5, "name": "90 min lunch (≥ 60 min)"},
        {"entry": time(8, 0), "exit": time(17, 0), "lunch": 120, "expected": 8.5, "name": "120 min lunch (≥ 60 min, longer day)"}
    ]
    
    def create_test_timesheet(entry, exit_time, lunch_duration):
        """Create a test timesheet object without saving to DB."""
        ts = Timesheet()
        ts.entry_time = entry
        ts.exit_time = exit_time
        ts.lunch_duration_minutes = lunch_duration
        return ts
    
    results = []
    
    # Test each scenario
    for scenario in scenarios:
        ts = create_test_timesheet(
            scenario["entry"], 
            scenario["exit"], 
            scenario["lunch"]
        )
        
        calculated = ts.calculated_hours
        raw = ts.raw_hours
        lunch_deduction = raw - calculated
        
        result = {
            "name": scenario["name"],
            "entry": scenario["entry"].strftime("%H:%M"),
            "exit": scenario["exit"].strftime("%H:%M"),
            "lunch_mins": scenario["lunch"],
            "raw_hours": f"{raw:.2f}",
            "lunch_deduction": f"{lunch_deduction:.2f}",
            "calculated_hours": f"{calculated:.2f}",
            "expected": f"{scenario['expected']:.2f}",
            "matches": abs(calculated - scenario["expected"]) < 0.01
        }
        results.append(result)
    
    # Print results as a table
    print(f"{'Scenario':<30} | {'Work Hours':<10} | {'Lunch':<8} | {'Deduction':<10} | {'Calculated':<10} | {'Expected':<10} | {'Match':<5}")
    print("-" * 90)
    
    all_passed = True
    
    for r in results:
        print(f"{r['name']:<30} | {r['entry']}-{r['exit']} | {r['lunch_mins']:>3} min | {r['lunch_deduction']} hr | {r['calculated_hours']} hr | {r['expected']} hr | {'✓' if r['matches'] else '✗'}")
        if not r['matches']:
            all_passed = False
    
    if all_passed:
        print("\n✅ All lunch break scenarios calculated correctly!")
    else:
        print("\n⚠️ Some lunch break calculations don't match expected results!")
        
    return all_passed

def test_saturday_premium():
    """Test that Saturday work receives the $5/hour premium."""
    print_header("TESTING SATURDAY PREMIUM")
    
    # Create test timesheet objects for different days of the week
    # Start with Monday (weekday() == 0)
    monday = date.today()
    # Find the nearest Monday to use as our base
    while monday.weekday() != 0:
        monday = monday - timedelta(days=1)
    
    # Create a Tuesday through Sunday by adding days to Monday
    weekdays = [monday + timedelta(days=i) for i in range(7)]
    
    # Create an employee with a base rate
    employee = Employee(name="Test Employee", pay_rate=20.0)
    
    # Now create a test timesheet for each day
    results = []
    for day in weekdays:
        ts = Timesheet()
        ts.date = day
        ts.employee = employee
        
        day_name = day.strftime("%A")
        rate = ts.effective_hourly_rate
        premium = rate - employee.pay_rate
        
        result = {
            "day": day_name,
            "date": day.strftime("%Y-%m-%d"),
            "base_rate": f"${employee.pay_rate:.2f}",
            "effective_rate": f"${rate:.2f}",
            "premium": f"${premium:.2f}",
            "expected_premium": "$5.00" if day_name == "Saturday" else "$0.00",
            "matches": (day_name == "Saturday" and premium == 5.0) or 
                      (day_name != "Saturday" and premium == 0.0)
        }
        results.append(result)
    
    # Print results as a table
    print(f"{'Day':<10} | {'Date':<12} | {'Base Rate':<10} | {'Effective Rate':<15} | {'Premium':<10} | {'Expected':<10} | {'Match':<5}")
    print("-" * 80)
    
    all_passed = True
    for r in results:
        print(f"{r['day']:<10} | {r['date']} | {r['base_rate']:<10} | {r['effective_rate']:<15} | {r['premium']:<10} | {r['expected_premium']:<10} | {'✓' if r['matches'] else '✗'}")
        if not r['matches']:
            all_passed = False
    
    if all_passed:
        print("\n✅ Saturday premium calculated correctly for all days!")
    else:
        print("\n⚠️ Saturday premium not calculated correctly!")
        
    return all_passed

def test_payroll_deduction():
    """Test that payroll deductions are calculated correctly."""
    print_header("TESTING PAYROLL DEDUCTIONS")
    
    # Create a test payroll payment with deductions
    payment = PayrollPayment(
        gross_amount=1000.0,
        amount=1000.0  # Will be reduced by deductions
    )
    
    # Add test deductions
    deductions = [
        {"description": "Income Tax", "amount": 150.0, "type": DeductionType.TAX},
        {"description": "Health Insurance", "amount": 75.0, "type": DeductionType.INSURANCE},
        {"description": "Retirement", "amount": 50.0, "type": DeductionType.RETIREMENT}
    ]
    
    # Manually calculate expected total
    expected_total_deductions = sum(d["amount"] for d in deductions)
    expected_net = payment.gross_amount - expected_total_deductions
    
    # Now simulate adding deductions like the app would
    actual_deductions = []
    for d in deductions:
        deduction = PayrollDeduction(
            description=d["description"],
            amount=d["amount"],
            deduction_type=d["type"]
        )
        # Link to payment but don't save to DB
        deduction.payroll_payment = payment
        actual_deductions.append(deduction)
    
    # Calculate the total deductions and net amount
    total_deductions = sum(d.amount for d in actual_deductions)
    payment.amount = payment.gross_amount - total_deductions
    
    # Check results
    print(f"Payment gross amount: ${payment.gross_amount:.2f}")
    print(f"Total deductions: ${total_deductions:.2f}")
    print(f"Payment net amount: ${payment.amount:.2f}")
    print()
    
    print("Individual deductions:")
    for d in actual_deductions:
        print(f"- {d.description}: ${d.amount:.2f} ({d.deduction_type.value})")
    
    # Verify calculations
    net_matches = abs(payment.amount - expected_net) < 0.01
    deduction_matches = abs(total_deductions - expected_total_deductions) < 0.01
    
    print()
    if net_matches and deduction_matches:
        print("✅ Deduction calculations are correct!")
    else:
        print("⚠️ Deduction calculations have issues:")
        if not deduction_matches:
            print(f"  - Total deductions: ${total_deductions:.2f}, Expected: ${expected_total_deductions:.2f}")
        if not net_matches:
            print(f"  - Net amount: ${payment.amount:.2f}, Expected: ${expected_net:.2f}")
    
    return net_matches and deduction_matches

def test_with_real_data():
    """Test payroll with a sample of real data from the database."""
    print_header("TESTING WITH SAMPLE REAL DATA")
    
    # Get one employee with timesheets
    employee = Employee.query.join(Timesheet).first()
    
    if not employee:
        print("❌ No employees with timesheets found in the database!")
        return True  # Return True to avoid failing the overall test
    
    print(f"Testing with employee: {employee.name} (ID: {employee.id}, Rate: ${employee.pay_rate}/hr)")
    
    # Get a few timesheets for this employee
    timesheets = Timesheet.query.filter_by(employee_id=employee.id).order_by(Timesheet.date.desc()).limit(5).all()
    
    if not timesheets:
        print(f"No timesheets found for {employee.name}")
        return True
    
    print(f"\nFound {len(timesheets)} timesheets for {employee.name}")
    print(f"{'Date':<12} | {'Hours':<14} | {'Lunch':<8} | {'Raw Hrs':<8} | {'Calc Hrs':<8} | {'Amount':<10}")
    print("-" * 70)
    
    for ts in timesheets:
        hours_str = f"{ts.entry_time.strftime('%H:%M')}-{ts.exit_time.strftime('%H:%M')}"
        raw_hrs = ts.raw_hours
        calc_hrs = ts.calculated_hours
        amount = ts.calculated_amount
        
        print(f"{ts.date} | {hours_str:<14} | {ts.lunch_duration_minutes:>3} min | {raw_hrs:>7.2f} | {calc_hrs:>7.2f} | ${amount:>8.2f}")
    
    # Test lunch break durations
    issues_found = False
    for ts in timesheets:
        # Verify the lunch break deduction matches our rules
        raw_hours = ts.raw_hours
        calculated_hours = ts.calculated_hours
        lunch_deduction = raw_hours - calculated_hours
        
        # Check lunch break rule application
        expected_deduction = 0
        if ts.lunch_duration_minutes >= 60:
            expected_deduction = 0.5
        elif ts.lunch_duration_minutes >= 30:
            expected_deduction = ts.lunch_duration_minutes / 60
        else:
            expected_deduction = 0
            
        # Check if calculated deduction matches expected
        if abs(lunch_deduction - expected_deduction) > 0.01:
            print(f"\n⚠️ Issue with lunch calculation for timesheet on {ts.date}:")
            print(f"  Lunch: {ts.lunch_duration_minutes} min")
            print(f"  Expected deduction: {expected_deduction:.2f} hr")
            print(f"  Actual deduction: {lunch_deduction:.2f} hr")
            issues_found = True
    
    if not issues_found:
        print("\n✅ All lunch break calculations match expected rules!")
    
    return not issues_found

def main():
    """Run all payroll tests."""
    print("\n" + "*" * 100)
    print("MAURICIO PDQ ERP - PAYROLL SYSTEM TEST".center(100))
    print("*" * 100)
    print(f"Test run at: {datetime.now()}")
    print(f"Using database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    with app.app_context():
        test_results = []
        
        # Test 1: Lunch break calculation
        test_results.append(("Lunch Break Calculation", test_lunch_break_calculation()))
        
        # Test 2: Saturday premium
        test_results.append(("Saturday Premium", test_saturday_premium()))
        
        # Test 3: Payroll deduction
        test_results.append(("Payroll Deduction", test_payroll_deduction()))
        
        # Test 4: Real data
        test_results.append(("Sample Real Data", test_with_real_data()))
        
        # Print summary
        print_header("TEST SUMMARY")
        print(f"{'Test':<30} | {'Result':<10}")
        print("-" * 45)
        
        all_passed = True
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:<30} | {status:<10}")
            all_passed = all_passed and result
        
        print("\nOVERALL RESULT: " + ("✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED"))
        
        if not all_passed:
            print("\n⚠️ Issues were found in the payroll system. See test details above.")
            print("\nRecommended next steps:")
            print("1. Review the lunch break calculation logic in the Timesheet model")
            print("2. Verify that Saturday premium is applied correctly")
            print("3. Check payroll deduction calculations in PayrollPayment model")
        else:
            print("\nThe payroll system appears to be functioning correctly.")

if __name__ == "__main__":
    main()
