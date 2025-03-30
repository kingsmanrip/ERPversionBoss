# Mauricio PDQ ERP System: Roadmap & Todo List

This document outlines the roadmap and task list to complete the Mauricio PDQ ERP System according to the detailed requirements.

## Priority 1: Payroll Management Enhancements

### Todo Items:
- [x] **Implement Precise Lunch Break Rules**
  - Calculate 30 minute deduction only if lunch duration >= 1 hour
  - No deduction for lunch breaks < 30 minutes
  - Allow manual adjustment of lunch times

- [x] **Enhance Payment Method Tracking**
  - Add more detailed selection of Cash/Check payment methods per employee
  - Track payment method history per payment period
  - Add payment date recording

- [x] **Improve Payroll Reporting**
  - Create detailed weekly report showing Cash vs Check payments separately
  - Implement report showing total paid in Cash and Check with breakdown by employee
  - Add report showing total hours worked by employee per period
  - Add payment summary report with totals by payment type

- [ ] **Add Payroll Deductions**
  - Implement ability to record and calculate various deductions
  - Display deductions on payroll reports

## Priority 2: Financial Management System

### Todo Items:
- [ ] **Accounts Payable Module**
  - Create form for recording accounts payable with all required fields:
    - Vendor/Service Provider
    - Expense description
    - Amount
    - Due date
    - Payment method (Cash, Check, Transfer, Card, Other)
    - Category (Rent, Taxes, Materials, etc.)
    - Status (Pending, Paid)
    - Notes

- [ ] **Paid Accounts Module**
  - Create form for recording paid accounts with:
    - Vendor/Service Provider
    - Amount paid
    - Payment date
    - Payment method
    - Check number (if check payment)
    - Bank (if check payment)
    - Option to attach payment proof
    - Notes

- [ ] **Monthly Expenses Tracking**
  - Implement expense entry form with:
    - Expense description
    - Amount
    - Date
    - Category
    - Payment method
    - Notes

- [ ] **Financial Reporting**
  - Create accounts payable report with due dates and payment methods
  - Add paid accounts report filtered by payment method
  - Implement monthly expense report with categories and payment methods
  - Create payment forecast report with due date alerts
  - Develop report showing payments by payment method

## Priority 3: Project Invoice Enhancement

### Todo Items:
- [ ] **Complete Invoice Structure**
  - Add all required invoice fields:
    - Invoice number
    - Issue date
    - Due date
    - Company details
    - Client details
    - Terms and conditions

- [ ] **Project Details Enhancement**
  - Expand project record to include:
    - More detailed project description
    - Start and end dates
    - Complete list of workers involved
    - Hours worked per employee on project

- [ ] **Cost Tracking Enhancement**
  - Improve material cost tracking with more details
  - Add labor cost detailed breakdown
  - Implement total project cost calculation

- [ ] **Billing and Payment Tracking**
  - Add fields for tracking the amount charged to client
  - Implement discounts/surcharges
  - Add tax calculation
  - Include payment receipt tracking

- [ ] **Project Financial Reporting**
  - Create detailed project billing report
  - Implement project cost breakdown report
  - Add profit margin analysis report

## Priority 4: Dashboard and System Improvements

### Todo Items:
- [ ] **Financial Dashboard**
  - Add widgets for key financial metrics
  - Display pending payments and upcoming due dates
  - Show weekly labor hours
  - Display project profit metrics

- [ ] **Data Export Enhancements**
  - Implement Excel export for all financial reports
  - Add PDF generation for invoices
  - Create printable payroll reports

- [ ] **User Interface Improvements**
  - Optimize forms for faster data entry
  - Add data validation for all critical fields
  - Implement batch operations for common tasks

## Implementation Timeline

### Phase 1 (Weeks 1-2)
- Complete Payroll Management Enhancements
- Begin Financial Management System

### Phase 2 (Weeks 3-4)
- Complete Financial Management System
- Begin Project Invoice Enhancement

### Phase 3 (Weeks 5-6)
- Complete Project Invoice Enhancement
- Begin Dashboard and System Improvements

### Phase 4 (Weeks 7-8)
- Complete Dashboard and System Improvements
- System Testing and User Training

## Technical Requirements

### Database Updates
- [ ] Add new fields to Employee model for enhanced payroll tracking
- [ ] Create new models for Accounts Payable and Paid Accounts
- [ ] Expand Project and Invoice models with additional fields

### User Interface Updates
- [ ] Redesign forms to accommodate new fields
- [ ] Create new report templates for financial reporting
- [ ] Develop improved dashboard with financial metrics

### Business Logic Updates
- [ ] Implement lunch break calculation rules
- [ ] Add financial calculations for reports
- [ ] Create export functionality for all reports

## Conclusion

This roadmap provides a structured approach to completing the Mauricio PDQ ERP System according to the specific requirements provided by the client. By following this plan, the development team can ensure all necessary features are implemented in a logical and efficient manner.
