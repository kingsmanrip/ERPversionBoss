import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, send_file, jsonify, after_this_request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from datetime import date, timedelta, datetime
from dotenv import load_dotenv
from flask_bootstrap import Bootstrap5
from functools import wraps
import flask_excel as excel
from fpdf import FPDF
import tempfile
import io
import pandas as pd
import json
import uuid
import shutil

from models import db, Employee, Project, Timesheet, Material, Expense, PayrollPayment, PayrollDeduction, Invoice, ProjectStatus, PaymentMethod, PaymentStatus, User, DeductionType, AccountsPayable, PaidAccount, MonthlyExpense, ExpenseCategory
from forms import EmployeeForm, ProjectForm, TimesheetForm, MaterialForm, ExpenseForm, PayrollPaymentForm, PayrollDeductionForm, InvoiceForm, LoginForm, AccountsPayableForm, PaidAccountForm, MonthlyExpenseForm

load_dotenv()  # Load environment variables if needed

app = Flask(__name__)

# --- Configuration ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-default-hardcoded-secret-key')  # CHANGE THIS in production
# Use instance folder for the database
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(instance_path, "erp.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Initialize Extensions ---
db.init_app(app)
csrf = CSRFProtect(app)
bootstrap = Bootstrap5(app)  # Initialize Bootstrap5
excel.init_excel(app)  # Initialize Excel export

# --- Authentication utilities ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Helper Functions ---
def get_week_start_end(dt=None):
    """Gets the start (Friday) and end (Thursday) dates of the work week for a given date.
    Work weeks are defined as running from Friday through Thursday.
    """
    dt = dt or date.today()
    # Calculate days to go back to reach Friday
    # weekday() returns: Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5, Sun=6
    # So to get to Friday: if today is Mon (0), go back 3 days; if today is Fri (4), go back 0 days, etc.
    days_to_friday = (dt.weekday() - 4) % 7
    start = dt - timedelta(days=days_to_friday)
    end = start + timedelta(days=6)  # 6 days after Friday is Thursday
    return start, end

# --- Export Helpers ---
def export_to_excel(data, prefix):
    """Helper function to export data to Excel"""
    df = pd.DataFrame(data)
    excel_file = io.BytesIO()
    df.to_excel(excel_file, index=False, engine='openpyxl')
    excel_file.seek(0)
    
    return send_file(
        excel_file,
        as_attachment=True,
        download_name=f'{prefix}_report.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

def export_to_pdf(data, title, filename):
    """Helper function to export data to PDF with totals for numerical fields"""
    # Initialize PDF with Unicode support
    pdf = FPDF()
    pdf.add_page('L')  # Landscape orientation for more columns
    
    # Add Unicode font support
    pdf.add_font('DejaVu', '', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', uni=True)
    pdf.add_font('DejaVu', 'B', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', uni=True)
    pdf.add_font('DejaVu', 'I', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Oblique.ttf', uni=True)
    
    # Add title
    pdf.set_font('DejaVu', 'B', 16)
    pdf.cell(0, 10, f'{title} Report', 0, 1, 'C')
    pdf.ln(5)
    
    # Add header
    if data:
        # Initialize totals dictionary for numerical columns
        totals = {}
        column_keys = list(data[0].keys())
        
        # Calculate appropriate column widths based on number of columns
        page_width = 270
        max_col_width = 40  # Maximum column width in mm
        min_col_width = 15  # Minimum column width in mm
        
        # Calculate base width for all columns
        base_col_width = page_width / len(column_keys)
        
        # If base width exceeds max, cap it
        col_width = min(base_col_width, max_col_width)
        # If base width is too small, use minimum
        col_width = max(col_width, min_col_width)
        
        # Add header row
        pdf.set_font('DejaVu', 'B', 8)
        for key in column_keys:
            # Truncate header text if too long
            header_text = str(key)
            if len(header_text) > 15:
                header_text = header_text[:12] + '...'
            pdf.cell(col_width, 10, header_text, 1)
            # Initialize totals for columns that might contain numbers
            totals[key] = 0
        pdf.ln()
        
        # Add data rows and calculate totals for numerical fields
        pdf.set_font('DejaVu', '', 8)
        for item in data:
            for key, value in item.items():
                # Ensure all values are properly encoded as strings and truncate if too long
                cell_value = str(value)
                if len(cell_value) > 15:
                    cell_value = cell_value[:12] + '...'
                
                pdf.cell(col_width, 10, cell_value, 1)
                
                # Update total if the value is numerical (uses string checking since data might be pre-formatted)
                string_value = str(value)
                if string_value.replace('.', '', 1).replace(',', '', 1).replace('$', '', 1).replace('-', '', 1).isdigit():
                    # Extract and clean the numerical value
                    clean_value = string_value.replace('$', '').replace(',', '')
                    try:
                        # Try to convert to float and add to total
                        totals[key] += float(clean_value)
                    except ValueError:
                        pass
                elif string_value.startswith('$') and string_value[1:].replace('.', '', 1).replace(',', '', 1).isdigit():
                    # Handle currency values starting with $
                    clean_value = string_value.replace('$', '').replace(',', '')
                    try:
                        totals[key] += float(clean_value)
                    except ValueError:
                        pass
            pdf.ln()
        
        # Add a separating line
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 285, pdf.get_y())
        pdf.ln(2)
        
        # Add totals row with bold formatting
        pdf.set_font('DejaVu', 'B', 8)
        pdf.set_fill_color(240, 240, 240)  # Light gray background
        
        # First cell is the 'TOTALS' label
        pdf.cell(col_width, 10, 'TOTALS', 1, 0, 'L', True)
        
        # Add total values for each column
        for key in column_keys[1:]:  # Skip the first column which usually has labels
            # Check if this column had numerical values
            if totals[key] > 0:
                # Format the total based on the column content (currency, decimals, etc.)
                if any('$' in str(item[key]) for item in data):
                    # Currency format
                    formatted_total = f'${totals[key]:,.2f}'
                elif any('hours' in str(key).lower() for item in data) or \
                     any('hrs' in str(key).lower() for item in data):
                    # Hours format - 2 decimal places
                    formatted_total = f'{totals[key]:.2f}'
                elif isinstance(totals[key], float):
                    # Regular float format
                    formatted_total = f'{totals[key]:,.2f}'
                else:
                    # Integer format
                    formatted_total = f'{int(totals[key]):,}'
                
                # Truncate total value if too long
                if len(formatted_total) > 15:
                    formatted_total = formatted_total[:12] + '...'
                
                pdf.cell(col_width, 10, formatted_total, 1, 0, 'R', True)
            else:
                # Non-numerical column
                pdf.cell(col_width, 10, '', 1, 0, 'C', True)
        pdf.ln()
        
        # Add note about totals
        pdf.ln(5)
        pdf.set_font('DejaVu', 'I', 8)
        pdf.cell(0, 10, 'Note: Totals are calculated for numerical fields only.', 0, 1, 'L')
    
    # Create temp file and write PDF to it
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        pdf_path = tmp.name
        pdf.output(pdf_path)
        
    # Return the created PDF file
    return send_file(
        pdf_path,
        as_attachment=True, 
        download_name=filename,
        mimetype='application/pdf'
    )

def export_to_csv(data, prefix):
    """Helper function to export data to CSV"""
    df = pd.DataFrame(data)
    csv_file = io.StringIO()
    df.to_csv(csv_file, index=False)
    csv_file.seek(0)
    
    return send_file(
        csv_file,
        as_attachment=True,
        download_name=f'{prefix}_report.csv',
        mimetype='text/csv'
    )

# --- PDF Generation Functions ---
def generate_customer_invoice_pdf(invoice_id):
    """
    Generate a professional PDF invoice for customers with a compact, information-focused design.
    
    Args:
        invoice_id: The ID of the invoice to generate a PDF for
        
    Returns:
        A Flask send_file response with the PDF
    """
    from models import Invoice, Project
    from flask import send_file, after_this_request
    from fpdf import FPDF
    import tempfile
    import os
    
    invoice = Invoice.query.get_or_404(invoice_id)
    project = Project.query.get_or_404(invoice.project_id)
    
    # Create PDF object (A4 size)
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # Add Unicode font support
    pdf.add_font('DejaVu', '', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', uni=True)
    pdf.add_font('DejaVu', 'B', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', uni=True)
    
    # Set tighter margins for more space
    pdf.set_margins(10, 10, 10)
    
    # Define colors - more muted professional palette
    primary_color = (30, 55, 90)     # Darker blue
    accent_color = (180, 30, 30)     # Darker red
    highlight_color = (60, 100, 160) # Lighter blue
    text_color = (70, 70, 70)        # Dark gray for text
    light_fill = (248, 248, 248)     # Very light gray for fills
    
    # Header with company info - compact design with horizontal layout
    # Create a header box
    pdf.set_fill_color(primary_color[0], primary_color[1], primary_color[2])
    pdf.rect(10, 10, 190, 14, 'F')
    
    # Company name in white on blue background
    pdf.set_font('DejaVu', 'B', 16)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(12, 12)
    pdf.cell(120, 10, 'Mauricio PDQ Paint & Drywall LLC', 0, 0, 'L')
    
    # Contact info on right side of header
    pdf.set_font('DejaVu', '', 8)
    pdf.set_xy(132, 12)
    pdf.cell(68, 5, 'MAURICIO: 601-596-3130', 0, 1, 'R')
    pdf.set_xy(132, 17)
    pdf.cell(68, 5, 'FAX: 601-752-3519', 0, 0, 'R')
    
    # Company address below header
    pdf.set_xy(10, 26)
    pdf.set_font('DejaVu', '', 9)
    pdf.set_text_color(text_color[0], text_color[1], text_color[2])
    pdf.cell(95, 4, '968 WPA RD, Sumrall Ms, 39482', 0, 0, 'L')
    
    # Invoice number and date on right
    pdf.set_font('DejaVu', 'B', 9)
    pdf.set_xy(105, 26)
    pdf.cell(40, 4, 'INVOICE #:', 0, 0, 'R')
    pdf.set_font('DejaVu', '', 9)
    pdf.set_text_color(highlight_color[0], highlight_color[1], highlight_color[2])
    pdf.cell(55, 4, f'{invoice.id:03d}', 0, 1, 'L')
    
    pdf.set_xy(105, 30)
    pdf.set_font('DejaVu', 'B', 9)
    pdf.set_text_color(text_color[0], text_color[1], text_color[2])
    pdf.cell(40, 4, 'DATE:', 0, 0, 'R')
    pdf.set_font('DejaVu', '', 9)
    pdf.set_text_color(highlight_color[0], highlight_color[1], highlight_color[2])
    pdf.cell(55, 4, invoice.invoice_date.strftime('%m/%d/%Y'), 0, 1, 'L')
    
    # Client information section - two column layout
    pdf.ln(5)
    pdf.set_text_color(primary_color[0], primary_color[1], primary_color[2])
    pdf.set_font('DejaVu', 'B', 10)
    pdf.cell(0, 6, 'CLIENT INFORMATION', 0, 1, 'L')
    
    # Horizontal line under section title
    pdf.set_draw_color(primary_color[0], primary_color[1], primary_color[2])
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(1)
    
    # Client details in a compact two-column layout
    col_width = 95
    line_height = 5
    
    # Set up client info box with light background
    client_box_y = pdf.get_y()
    pdf.set_fill_color(light_fill[0], light_fill[1], light_fill[2])
    pdf.rect(10, client_box_y, 190, 28, 'F')
    
    # First column
    pdf.set_xy(12, client_box_y + 2)
    pdf.set_font('DejaVu', 'B', 8)
    pdf.set_text_color(text_color[0], text_color[1], text_color[2])
    pdf.cell(20, line_height, 'NAME:', 0, 0)
    pdf.set_font('DejaVu', '', 9)
    pdf.set_text_color(highlight_color[0], highlight_color[1], highlight_color[2])
    pdf.cell(75, line_height, project.client_name, 0, 0)
    
    # Second column
    pdf.set_xy(107, client_box_y + 2)
    pdf.set_font('DejaVu', 'B', 8)
    pdf.set_text_color(text_color[0], text_color[1], text_color[2])
    pdf.cell(20, line_height, 'PHONE:', 0, 0)
    pdf.set_font('DejaVu', '', 9)
    pdf.set_text_color(highlight_color[0], highlight_color[1], highlight_color[2])
    pdf.cell(70, line_height, '', 0, 1)
    
    # First column - second row
    pdf.set_xy(12, client_box_y + 2 + line_height + 2)
    pdf.set_font('DejaVu', 'B', 8)
    pdf.cell(20, line_height, 'STREET:', 0, 0)
    pdf.set_font('DejaVu', '', 9)
    pdf.cell(75, line_height, project.location, 0, 0)
    
    # Second column - second row
    pdf.set_xy(107, client_box_y + 2 + line_height + 2)
    pdf.set_font('DejaVu', 'B', 8)
    pdf.cell(20, line_height, 'CELL:', 0, 0)
    pdf.set_font('DejaVu', '', 9)
    pdf.set_text_color(highlight_color[0], highlight_color[1], highlight_color[2])
    pdf.cell(70, line_height, '', 0, 1)
    
    # First column - third row
    pdf.set_xy(12, client_box_y + 2 + (line_height + 2) * 2)
    pdf.set_font('DejaVu', 'B', 8)
    pdf.cell(20, line_height, 'CITY/STATE:', 0, 0)
    pdf.set_font('DejaVu', '', 9)
    pdf.set_text_color(highlight_color[0], highlight_color[1], highlight_color[2])
    pdf.cell(75, line_height, '', 0, 0)
    
    # Second column - third row
    pdf.set_xy(107, client_box_y + 2 + (line_height + 2) * 2)
    pdf.set_font('DejaVu', 'B', 8)
    pdf.cell(20, line_height, 'JOB LOCATION:', 0, 0)
    pdf.set_font('DejaVu', '', 9)
    pdf.set_text_color(highlight_color[0], highlight_color[1], highlight_color[2])
    pdf.cell(70, line_height, '', 0, 1)
    
    # First column - fourth row
    pdf.set_xy(12, client_box_y + 2 + (line_height + 2) * 3)
    pdf.set_font('DejaVu', 'B', 8)
    pdf.cell(20, line_height, 'SUBDIVISION:', 0, 0)
    pdf.set_font('DejaVu', '', 9)
    pdf.set_text_color(highlight_color[0], highlight_color[1], highlight_color[2])
    pdf.cell(75, line_height, '', 0, 1)
    
    # Move cursor after client info box
    pdf.set_y(client_box_y + 30)
    
    # Proposal section
    pdf.set_text_color(primary_color[0], primary_color[1], primary_color[2])
    pdf.set_font('DejaVu', 'B', 10)
    pdf.cell(0, 6, 'PROPOSAL', 0, 1, 'L')
    
    # Horizontal line under section title
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(1)
    
    # Proposal text
    pdf.set_font('DejaVu', '', 8)
    pdf.set_text_color(text_color[0], text_color[1], text_color[2])
    pdf.cell(0, 5, 'I propose to furnish all materials and perform all necessary labor to complete the following:', 0, 1, 'L')
    
    # Description box with light fill
    description_y = pdf.get_y() + 1
    description_height = 50  # Shorter height for more compact design
    
    # Create description box with light background
    pdf.set_fill_color(light_fill[0], light_fill[1], light_fill[2])
    pdf.rect(10, description_y, 190, description_height, 'F')
    
    # Description header
    pdf.set_xy(12, description_y + 2)
    pdf.set_font('DejaVu', 'B', 9)
    pdf.set_text_color(primary_color[0], primary_color[1], primary_color[2])
    pdf.cell(186, 5, 'DESCRIPTION & DIRECTIONS', 0, 1, 'L')
    
    # Description content
    pdf.set_xy(12, description_y + 8)
    pdf.set_font('DejaVu', '', 9)
    pdf.set_text_color(text_color[0], text_color[1], text_color[2])
    # Only show invoice description
    if invoice.description and invoice.description.strip():
        pdf.multi_cell(186, 5, invoice.description, 0, 'L')
    else:
        # If no invoice description is available, show empty space
        pdf.ln(10)
    
    # Move cursor after description box
    pdf.set_y(description_y + description_height + 2)
    
    # Payment section
    pdf.set_text_color(primary_color[0], primary_color[1], primary_color[2])
    pdf.set_font('DejaVu', 'B', 10)
    pdf.cell(0, 6, 'PAYMENT DETAILS', 0, 1, 'L')
    
    # Horizontal line under section title
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(1)
    
    # Payment box with light background
    payment_y = pdf.get_y()
    pdf.set_fill_color(light_fill[0], light_fill[1], light_fill[2])
    pdf.rect(10, payment_y, 190, 25, 'F')
    
    # Payment text
    pdf.set_xy(12, payment_y + 2)
    pdf.set_font('DejaVu', '', 8)
    pdf.set_text_color(text_color[0], text_color[1], text_color[2])
    pdf.cell(0, 5, 'All of the work to be completed in a substantial and workmanlike manner for the sum of:', 0, 1, 'L')
    
    # Price line with modern styling - more compact
    pdf.set_xy(12, payment_y + 8)
    pdf.cell(10, 6, '$', 0, 0)
    
    # Calculate a default base amount (95% of total) and tax amount (5% of total)
    # This is just for display purposes since we now store only the total amount
    base_amount = invoice.base_amount or 0
    tax_amount = invoice.tax_amount or 0
    
    # Display base amount
    base_amount_str = f"{base_amount:,.2f}"
    pdf.cell(25, 6, base_amount_str, 'B', 0)
    pdf.cell(5, 6, '+', 0, 0, 'C')
    pdf.cell(10, 6, '$', 0, 0)
    
    # Display tax amount
    tax_amount_str = f"{tax_amount:,.2f}" 
    pdf.cell(25, 6, tax_amount_str, 'B', 0)
    pdf.cell(30, 6, '(tax) TOTAL:', 0, 0)
    
    # Total amount with highlight
    pdf.set_font('DejaVu', 'B', 12)
    pdf.set_text_color(highlight_color[0], highlight_color[1], highlight_color[2])
    pdf.cell(0, 6, f'${invoice.amount:.2f}', 0, 1)
    
    # Terms in a more compact format
    pdf.set_xy(12, payment_y + 16)
    pdf.set_font('DejaVu', '', 7)
    pdf.set_text_color(text_color[0], text_color[1], text_color[2])
    pdf.multi_cell(186, 3, 'The entire amount of the contract to be paid upon completion. Any alterations or deviation from the above specifications involving extra cost of material or labor will be executed upon written order for same and will become an extra charge over the sum mentioned in this contract. All agreements must be made in writing.', 0, 'L')
    
    # Move cursor after payment box
    pdf.set_y(payment_y + 27)
    
    # Acceptance and signature section
    pdf.set_text_color(primary_color[0], primary_color[1], primary_color[2])
    pdf.set_font('DejaVu', 'B', 10)
    pdf.cell(0, 6, 'ACCEPTANCE & PAYMENT INFORMATION', 0, 1, 'L')
    
    # Horizontal line under section title
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(1)
    
    # Acceptance text
    pdf.set_font('DejaVu', '', 7)
    pdf.set_text_color(text_color[0], text_color[1], text_color[2])
    pdf.multi_cell(0, 3, 'I hereby authorize Mauricio PDQ Paint and Drywall LLC to furnish all materials and labor required to complete the work mentioned in the above proposal, and I agree to pay the amount mentioned in said proposal and according to the terms thereof.', 0, 'L')
    pdf.ln(1)
    
    # Create a two-column layout for payment details and signatures
    signature_y = pdf.get_y()
    
    # Payment details on the left with light fill
    pdf.set_fill_color(light_fill[0], light_fill[1], light_fill[2])
    pdf.rect(10, signature_y, 90, 35, 'F')
    
    # Payment details header
    pdf.set_xy(12, signature_y + 2)
    pdf.set_font('DejaVu', 'B', 8)
    pdf.set_text_color(primary_color[0], primary_color[1], primary_color[2])
    pdf.cell(86, 4, 'PAYMENT INFORMATION', 0, 1, 'L')
    
    # Payment form fields
    pdf.set_font('DejaVu', '', 8)
    pdf.set_text_color(text_color[0], text_color[1], text_color[2])
    
    form_y = signature_y + 7
    pdf.set_xy(12, form_y)
    pdf.cell(25, 4, 'C/C #:', 0, 0)
    pdf.cell(63, 4, '_______________________', 0, 1)
    
    pdf.set_xy(12, form_y + 6)
    pdf.cell(25, 4, 'EXP:', 0, 0)
    pdf.cell(20, 4, '__________', 0, 0)
    pdf.cell(15, 4, 'CVV:', 0, 0)
    pdf.cell(28, 4, '________', 0, 1)
    
    pdf.set_xy(12, form_y + 12)
    pdf.cell(25, 4, 'Name:', 0, 0)
    pdf.cell(63, 4, '_______________________', 0, 1)
    
    pdf.set_xy(12, form_y + 18)
    pdf.cell(25, 4, 'Address:', 0, 0)
    pdf.cell(63, 4, '_______________________', 0, 1)
    
    pdf.set_xy(12, form_y + 24)
    pdf.cell(25, 4, 'Zip Code:', 0, 0)
    pdf.cell(63, 4, '_______________________', 0, 1)
    
    # Signature section on the right with light fill
    pdf.set_fill_color(light_fill[0], light_fill[1], light_fill[2])
    pdf.rect(110, signature_y, 90, 35, 'F')
    
    # Signature header
    pdf.set_xy(112, signature_y + 2)
    pdf.set_font('DejaVu', 'B', 8)
    pdf.set_text_color(primary_color[0], primary_color[1], primary_color[2])
    pdf.cell(86, 4, 'SIGNATURES', 0, 1, 'L')
    
    # Date line
    pdf.set_xy(112, form_y)
    pdf.set_font('DejaVu', '', 8)
    pdf.set_text_color(text_color[0], text_color[1], text_color[2])
    pdf.cell(20, 4, 'Date:', 0, 0)
    pdf.cell(68, 4, '_______________________', 0, 1)
    
    # Customer signature
    pdf.set_xy(112, form_y + 10)
    pdf.cell(30, 4, 'Customer Signature:', 0, 0)
    pdf.cell(58, 4, '_______________________', 0, 1)
    
    # Contractor signature
    pdf.set_xy(112, form_y + 20)
    pdf.cell(30, 4, 'Contractor Signature:', 0, 0)
    
    # Add the contractor name in red below the signature line
    pdf.set_xy(142, form_y + 20)
    pdf.set_text_color(accent_color[0], accent_color[1], accent_color[2])
    pdf.set_font('DejaVu', 'B', 9)
    pdf.cell(56, 4, 'MAURICIO SANTOS', 0, 1)
    
    # Create a temporary file to store the PDF
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf_output = pdf.output(dest='S').encode('latin1')
    temp_file.write(pdf_output)
    temp_file.close()
    
    # Send the PDF file to the client
    return send_file(
        temp_file.name,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'invoice_{invoice.id:03d}_{project.name.replace(" ", "_")}.pdf'
    )

@app.route('/invoice/print/<int:id>')
@login_required
def print_customer_invoice(id):
    """Generate and download a customer-facing invoice PDF"""
    try:
        return generate_customer_invoice_pdf(id)
    except Exception as e:
        flash(f'Error generating invoice PDF: {str(e)}', 'danger')
        return redirect(url_for('invoices'))

# --- Auth Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    # If already logged in, redirect to dashboard
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    """Handle user logout"""
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# --- Routes ---

@app.route('/')
@login_required
def index():
    """Dashboard"""
    # Total projects counter (instead of just active projects)
    total_projects = Project.query.count()
    active_projects = Project.query.filter(Project.status == ProjectStatus.IN_PROGRESS).count()
    
    # Project financial metrics - include all projects
    all_projects = Project.query.all()
    
    # Sort by profit margin (descending)
    sorted_projects = sorted(
        all_projects, 
        key=lambda p: p.profit_margin if p.profit_margin is not None else -999, 
        reverse=True
    )
    
    # Calculate progress bar widths for the top projects
    top_projects = sorted_projects[:5]
    for project in top_projects:
        # Calculate a width between 0-100% for the progress bar
        # Add 40% to profit margin to make small profit margins visible
        # but cap at 100%
        profit_margin = project.profit_margin or 0
        project.progress_width = max(0, min(100, profit_margin + 40))
    
    # Financial summary
    total_invoiced = db.session.query(db.func.sum(Invoice.amount)).scalar() or 0
    unpaid_invoices = db.session.query(db.func.sum(Invoice.amount)).filter(
        Invoice.status != PaymentStatus.PAID
    ).scalar() or 0
    
    # Calculate total net profit across all projects
    total_net_profit = sum(project.actual_net_profit for project in all_projects)
    
    # Timesheet summary for current week
    start_of_week, end_of_week = get_week_start_end()
    # Get timesheets directly instead of using the property in SQL
    weekly_timesheets = Timesheet.query.filter(
        Timesheet.date >= start_of_week,
        Timesheet.date <= end_of_week
    ).all()
    
    # Calculate hours in Python logic instead of SQL
    weekly_hours = sum(ts.calculated_hours for ts in weekly_timesheets)
    
    # Project status distribution
    project_status_counts = {}
    for status in ProjectStatus:
        project_status_counts[status.name] = Project.query.filter(Project.status == status).count()
    
    # Recent expenses
    recent_expenses = Expense.query.order_by(Expense.date.desc()).limit(5).all()
    expenses_total = db.session.query(db.func.sum(Expense.amount)).scalar() or 0
    
    # Monthly expense trend (last 5 months)
    today = date.today()
    monthly_expenses = []
    monthly_labels = []
    for i in range(4, -1, -1):
        month_date = today.replace(day=1) - timedelta(days=i*30)  # Approximate
        month_name = month_date.strftime('%b')
        monthly_labels.append(month_name)
        
        next_month = month_date.replace(day=28) + timedelta(days=4)  # Move to next month
        next_month = next_month.replace(day=1)  # First day of next month
        
        month_expenses = db.session.query(db.func.sum(Expense.amount)).filter(
            Expense.date >= month_date,
            Expense.date < next_month
        ).scalar() or 0
        
        monthly_expenses.append(round(month_expenses, 2))
    
    return render_template('index.html',
                          active_projects=active_projects,
                          total_projects=total_projects,
                          top_projects=top_projects,
                          recent_expenses=recent_expenses,
                          total_invoiced=total_invoiced,
                          unpaid_invoices=unpaid_invoices,
                          weekly_hours=weekly_hours,
                          project_status_counts=project_status_counts,
                          expenses_total=expenses_total,
                          monthly_expenses=monthly_expenses,
                          monthly_labels=monthly_labels,
                          total_net_profit=total_net_profit)

# --- Employee Routes ---
@app.route('/employees')
@login_required
def employees():
    all_employees = Employee.query.order_by(Employee.name).all()
    return render_template('employees.html', employees=all_employees)

@app.route('/employee/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    form = EmployeeForm()
    if form.validate_on_submit():
        # Handle empty employee_id_str by setting it to None instead of empty string
        employee_id_str = form.employee_id_str.data if form.employee_id_str.data else None
        
        new_employee = Employee(
            name=form.name.data,
            employee_id_str=employee_id_str,
            contact_details=form.contact_details.data,
            pay_rate=form.pay_rate.data,
            payment_method_preference=PaymentMethod[form.payment_method_preference.data] if form.payment_method_preference.data else None,
            is_active=form.is_active.data,
            hire_date=form.hire_date.data
        )
        db.session.add(new_employee)
        db.session.commit()
        flash(f'Employee {new_employee.name} added successfully!', 'success')
        return redirect(url_for('employees'))
    return render_template('employee_form.html', form=form, title="Add Employee")

@app.route('/employee/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    employee = db.session.get(Employee, id)
    if not employee:
        flash('Employee not found.', 'danger')
        return redirect(url_for('employees')), 404
        
    form = EmployeeForm(obj=employee)
    # Ensure correct enum loading for SelectField
    if request.method == 'GET' and employee.payment_method_preference:
        form.payment_method_preference.data = employee.payment_method_preference.name

    if form.validate_on_submit():
        employee.name = form.name.data
        # Handle empty employee_id_str by setting it to None instead of empty string
        employee.employee_id_str = form.employee_id_str.data if form.employee_id_str.data else None
        employee.contact_details = form.contact_details.data
        employee.pay_rate = form.pay_rate.data
        employee.payment_method_preference = PaymentMethod[form.payment_method_preference.data] if form.payment_method_preference.data else None
        employee.is_active = form.is_active.data
        employee.hire_date = form.hire_date.data
        db.session.commit()
        flash(f'Employee {employee.name} updated successfully!', 'success')
        return redirect(url_for('employees'))
    return render_template('employee_form.html', form=form, title="Edit Employee", employee=employee)

@app.route('/employee/delete/<int:id>', methods=['POST'])
@login_required
def delete_employee(id):
    employee = db.session.get(Employee, id)
    if not employee:
        flash('Employee not found.', 'danger')
        return redirect(url_for('employees')), 404
        
    try:
        db.session.delete(employee)
        db.session.commit()
        flash(f'Employee {employee.name} deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting employee: {e}. They might have associated records.', 'danger')
    return redirect(url_for('employees'))

# --- Project Routes ---
@app.route('/projects')
@login_required
def projects():
    all_projects = Project.query.order_by(Project.start_date.desc()).all()
    return render_template('projects.html', projects=all_projects)

@app.route('/project/add', methods=['GET', 'POST'])
@login_required
def add_project():
    form = ProjectForm()
    if form.validate_on_submit():
        # Handle empty project_id_str by setting it to None instead of empty string
        project_id_str = form.project_id_str.data if form.project_id_str.data else None
        
        new_project = Project(
            name=form.name.data,
            project_id_str=project_id_str,
            client_name=form.client_name.data,
            location=form.location.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            contract_value=form.contract_value.data,
            description=form.description.data,
            status=ProjectStatus[form.status.data]
        )
        
        # Validate that end date is after start date if both are provided
        if not new_project.validate_dates() and form.start_date.data and form.end_date.data:
            flash('Error: End date must be on or after start date.', 'danger')
            return render_template('project_form.html', form=form, title="Add Project")
            
        db.session.add(new_project)
        db.session.commit()
        flash(f'Project {new_project.name} added successfully!', 'success')
        return redirect(url_for('projects'))
    return render_template('project_form.html', form=form, title="Add Project")

@app.route('/project/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_project(id):
    project = db.session.get(Project, id)
    if not project:
        flash('Project not found.', 'danger')
        return redirect(url_for('projects')), 404
    
    form = ProjectForm(obj=project)
    # Handle enum loading for SelectField
    if request.method == 'GET':
        form.status.data = project.status.name

    if form.validate_on_submit():
        project.name = form.name.data
        # Handle empty project_id_str by setting it to None instead of empty string
        project.project_id_str = form.project_id_str.data if form.project_id_str.data else None
        project.client_name = form.client_name.data
        project.location = form.location.data
        project.start_date = form.start_date.data
        project.end_date = form.end_date.data
        project.contract_value = form.contract_value.data
        project.description = form.description.data
        project.status = ProjectStatus[form.status.data]  # Update status from form
        
        # Validate that end date is after start date if both are provided
        if not project.validate_dates() and form.start_date.data and form.end_date.data:
            flash('Error: End date must be on or after start date.', 'danger')
            return render_template('project_form.html', form=form, title="Edit Project", project=project)
            
        db.session.commit()
        flash(f'Project {project.name} updated successfully!', 'success')
        return redirect(url_for('projects'))
    return render_template('project_form.html', form=form, title="Edit Project", project=project)

@app.route('/project/view/<int:id>')
@login_required
def project_detail(id):
    project = db.session.get(Project, id)
    if not project:
        flash('Project not found.', 'danger')
        return redirect(url_for('projects')), 404
        
    # Calculate costs (using properties defined in model)
    labor_cost = project.total_labor_cost
    material_cost = project.total_material_cost
    other_expenses = project.total_other_expenses
    total_cost = project.total_cost
    profit = project.profit

    # Fetch related items
    timesheets = Timesheet.query.filter_by(project_id=id).order_by(Timesheet.date.desc()).all()
    materials = Material.query.filter_by(project_id=id).order_by(Material.purchase_date.desc()).all()
    expenses = Expense.query.filter_by(project_id=id).order_by(Expense.date.desc()).all()
    invoices = Invoice.query.filter_by(project_id=id).order_by(Invoice.invoice_date.desc()).all()

    return render_template('project_detail.html',
                           project=project,
                           labor_cost=labor_cost,
                           material_cost=material_cost,
                           other_expenses=other_expenses,
                           total_cost=total_cost,
                           profit=profit,
                           timesheets=timesheets,
                           materials=materials,
                           expenses=expenses,
                           invoices=invoices)

@app.route('/project/<int:id>/delete', methods=['POST'])
@login_required
def delete_project(id):
    project = db.session.get(Project, id)
    if not project:
        flash('Project not found.', 'danger')
        return redirect(url_for('projects')), 404
        
    try:
        db.session.delete(project)
        db.session.commit()
        flash(f'Project {project.name} deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting project: {e}. It might have associated records.', 'danger')
    return redirect(url_for('projects'))

# --- Timesheet Routes ---
@app.route('/timesheets')
@login_required
def timesheets():
    # Basic view - show all timesheets, maybe filter by week later
    page = request.args.get('page', 1, type=int)
    timesheet_list = Timesheet.query.join(Employee).outerjoin(Project)\
                        .order_by(Timesheet.date.desc(), Employee.name)\
                        .paginate(page=page, per_page=20)  # Add pagination
    return render_template('timesheets.html', timesheets=timesheet_list)

@app.route('/timesheet/add', methods=['GET', 'POST'])
@login_required
def add_timesheet():
    form = TimesheetForm()
    
    # Populate the employee and project choices
    form.employee_id.choices = [(emp.id, f"{emp.name} ({emp.employee_id_str or 'No ID'})") 
                               for emp in Employee.query.filter_by(is_active=True).order_by(Employee.name).all()]
    
    # Add a "None" option for projects
    active_projects = [(proj.id, f"{proj.name} ({proj.project_id_str or 'No ID'})") 
                      for proj in Project.query.order_by(Project.name).all()]
    form.project_id.choices = [(None, "None - No Project")] + active_projects
    
    if form.validate_on_submit():
        # Check if "None - No Project" was selected and set a default project ID
        # Use 0 as a placeholder for "No Project" if None is not allowed by the database
        project_id = form.project_id.data if form.project_id.data else 0
        
        # Create new timesheet
        timesheet = Timesheet(
            employee_id=form.employee_id.data,
            project_id=project_id,
            date=form.date.data,
            entry_time=form.entry_time.data,
            exit_time=form.exit_time.data,
            lunch_duration_minutes=form.lunch_duration_minutes.data
        )
        
        # Validate the timesheet
        is_valid, message = timesheet.is_valid()
        if is_valid:
            try:
                db.session.add(timesheet)
                db.session.commit()
                
                # Get the employee name for the flash message
                employee = db.session.get(Employee, form.employee_id.data)
                
                # Customize message based on if project is selected or not
                if form.project_id.data:
                    project = db.session.get(Project, form.project_id.data)
                    flash(f'Timesheet for {employee.name} on project {project.name} added successfully!', 'success')
                else:
                    flash(f'Timesheet for {employee.name} (no project) added successfully!', 'success')
                    
                return redirect(url_for('timesheets'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error adding timesheet: {str(e)}', 'danger')
        else:
            flash(f'Error adding timesheet: {message}', 'danger')
    
    return render_template('timesheet_form.html', form=form, title="Add Timesheet Entry")

@app.route('/timesheet/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_timesheet(id):
    # Find the timesheet record
    timesheet = db.session.get(Timesheet, id)
    if not timesheet:
        flash('Timesheet not found.', 'danger')
        return redirect(url_for('timesheets'))
    
    form = TimesheetForm(obj=timesheet)
    
    # Populate the employee and project choices
    form.employee_id.choices = [(emp.id, f"{emp.name} ({emp.employee_id_str or 'No ID'})") 
                               for emp in Employee.query.filter_by(is_active=True).order_by(Employee.name).all()]
    
    # Get active projects (pending and in-progress)
    active_projects = [(proj.id, f"{proj.name} ({proj.project_id_str or 'No ID'})") 
                      for proj in Project.query.order_by(Project.name).all()]
    
    # Make sure the current project is in the list, even if it's completed or cancelled
    current_project_in_list = False
    if timesheet.project_id:
        for proj_id, _ in active_projects:
            if proj_id == timesheet.project_id:
                current_project_in_list = True
                break
        
        # If current project is not in the list, add it
        if not current_project_in_list and timesheet.project:
            active_projects.append((timesheet.project.id, 
                                  f"{timesheet.project.name} ({timesheet.project.project_id_str or 'No ID'}) - {timesheet.project.status.value}"))
    
    # Add the None option at the beginning
    form.project_id.choices = [(None, "None - No Project")] + active_projects
    
    if form.validate_on_submit():
        # Update the timesheet record
        timesheet.employee_id = form.employee_id.data
        timesheet.project_id = form.project_id.data if form.project_id.data else 0
        timesheet.date = form.date.data
        timesheet.entry_time = form.entry_time.data
        timesheet.exit_time = form.exit_time.data
        timesheet.lunch_duration_minutes = form.lunch_duration_minutes.data
        
        # Validate the timesheet
        is_valid, message = timesheet.is_valid()
        if is_valid:
            db.session.commit()
            
            # Get the employee name for the flash message
            employee = db.session.get(Employee, form.employee_id.data)
            
            # Customize message based on if project is selected or not
            if form.project_id.data:
                project = db.session.get(Project, form.project_id.data)
                flash(f'Timesheet for {employee.name} on project {project.name} updated successfully!', 'success')
            else:
                flash(f'Timesheet for {employee.name} (no project) updated successfully!', 'success')
                
            return redirect(url_for('timesheets'))
        else:
            flash(f'Error updating timesheet: {message}', 'danger')
    
    return render_template('timesheet_form.html', form=form, title="Edit Timesheet Entry")

@app.route('/timesheet/<int:id>/delete', methods=['POST'])
@login_required
def delete_timesheet(id):
    timesheet = db.session.get(Timesheet, id)
    if not timesheet:
        flash('Timesheet entry not found.', 'danger')
        return redirect(url_for('timesheets')), 404
        
    try:
        # Get the employee name before deletion for the flash message
        employee_name = timesheet.employee.name if timesheet.employee else "Unknown"
        
        # Explicitly delete the timesheet using SQL DELETE to avoid ORM constraints
        db.session.execute(db.delete(Timesheet).where(Timesheet.id == id))
        db.session.commit()
        
        flash(f'Timesheet entry for {employee_name} deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting timesheet entry: {e}', 'danger')
    return redirect(url_for('timesheets'))

# --- Material Routes ---
@app.route('/materials')
@login_required
def materials():
    all_materials = Material.query.join(Project).order_by(Material.purchase_date.desc()).all()
    return render_template('materials.html', materials=all_materials)

@app.route('/material/add', methods=['GET', 'POST'])
@login_required
def add_material():
    form = MaterialForm()
    form.project_id.choices = [(p.id, p.name) for p in Project.query.order_by('name')]

    if form.validate_on_submit():
        new_material = Material(
            project_id=form.project_id.data,
            description=form.description.data,
            supplier=form.supplier.data,
            cost=form.cost.data,
            purchase_date=form.purchase_date.data,
            category=form.category.data
        )
        db.session.add(new_material)
        db.session.commit()
        flash('Material added successfully!', 'success')
        return redirect(url_for('materials'))

    if not form.is_submitted():
        form.purchase_date.data = date.today()

    return render_template('material_form.html', form=form, title="Add Material")

# --- Expense Routes ---
@app.route('/expenses')
@login_required
def expenses():
    all_expenses = Expense.query.order_by(Expense.date.desc()).all()
    return render_template('expenses.html', expenses=all_expenses)

@app.route('/expense/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    form = ExpenseForm()
    # Add empty choice + projects
    form.project_id.choices = [('', '-- None --')] + [(p.id, p.name) for p in Project.query.order_by('name')]

    if form.validate_on_submit():
        new_expense = Expense(
            description=form.description.data,
            category=form.category.data,
            amount=form.amount.data,
            date=form.date.data,
            supplier_vendor=form.supplier_vendor.data,
            payment_method=PaymentMethod[form.payment_method.data] if form.payment_method.data else None,
            payment_status=PaymentStatus[form.payment_status.data],
            due_date=form.due_date.data,
            # Handle optional project link
            project_id=form.project_id.data if form.project_id.data else None
        )
        db.session.add(new_expense)
        db.session.commit()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('expenses'))

    if not form.is_submitted():
        form.date.data = date.today()
        form.payment_status.data = PaymentStatus.PENDING.name  # Default status

    return render_template('expense_form.html', form=form, title="Add Expense")

# --- Payroll Routes ---
@app.route('/payroll/record-payment', methods=['GET', 'POST'])
@login_required
def record_payroll_payment():
    form = PayrollPaymentForm()
    # Populate employee choices
    form.employee_id.choices = [(e.id, e.name) for e in Employee.query.order_by(Employee.name).all()]
    
    # Get deduction types for the template
    deduction_types = list(DeductionType)
    
    if form.validate_on_submit():
        # Create the payment with gross amount and initially set amount equal to gross_amount
        new_payment = PayrollPayment(
            employee_id=form.employee_id.data,
            pay_period_start=form.pay_period_start.data,
            pay_period_end=form.pay_period_end.data,
            gross_amount=form.gross_amount.data,
            amount=form.gross_amount.data,  # Initially set to gross amount, will be updated after deductions
            payment_date=form.payment_date.data,
            payment_method=PaymentMethod[form.payment_method.data],
            notes=form.notes.data,
            # Add check details
            check_number=form.check_number.data if form.payment_method.data == 'CHECK' else None,
            bank_name=form.bank_name.data if form.payment_method.data == 'CHECK' else None
        )
        
        # Validate that end date is after start date
        if not new_payment.validate_dates():
            flash('Error: Pay period end date must be on or after start date.', 'danger')
            return render_template('payroll_payment_form.html', form=form, deduction_types=deduction_types, title="Record Payroll Payment")
            
        # Validate check details if payment method is Check
        if form.payment_method.data == 'CHECK' and not new_payment.validate_check_details():
            flash('Error: Check number is required for check payments.', 'danger')
            return render_template('payroll_payment_form.html', form=form, deduction_types=deduction_types, title="Record Payroll Payment")
        
        # Add the payment first to get an ID
        db.session.add(new_payment)
        db.session.flush()
        
        # Process deductions if any
        if 'deduction_description[]' in request.form:
            descriptions = request.form.getlist('deduction_description[]')
            amounts = request.form.getlist('deduction_amount[]')
            types = request.form.getlist('deduction_type[]')
            notes = request.form.getlist('deduction_notes[]')
            
            for i in range(len(descriptions)):
                if descriptions[i] and amounts[i] and float(amounts[i]) > 0:
                    deduction = PayrollDeduction(
                        payroll_payment_id=new_payment.id,
                        description=descriptions[i],
                        amount=float(amounts[i]),
                        deduction_type=DeductionType[types[i]],
                        notes=notes[i] if i < len(notes) else None
                    )
                    db.session.add(deduction)
            
            # Update the net amount after all deductions are processed
            total_deductions = sum(float(amount) for amount in amounts if amount and float(amount) > 0)
            new_payment.amount = new_payment.gross_amount - total_deductions
        
        db.session.commit()
        flash('Payment recorded successfully!', 'success')
        return redirect(url_for('payroll_report'))
    
    return render_template('payroll_payment_form.html', form=form, deduction_types=deduction_types, title="Record Payment")

@app.route('/payroll/report')
@login_required
def payroll_report():
    """Comprehensive report showing weekly hours and recorded payments with payment method breakdown"""
    target_date_str = request.args.get('date')
    employee_id = request.args.get('employee_id', '')
    target_date = date.today()
    if target_date_str:
        try:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash("Invalid date format. Using today's date.", 'warning')

    start_of_week, end_of_week = get_week_start_end(target_date)
    
    # Get all employees for the dropdown
    all_employees = Employee.query.order_by(Employee.name).all()

    # 1. Calculate hours worked per employee for the selected week
    # Filter employees by selected employee_id if provided
    employee_query = Employee.query.filter_by(is_active=True)
    if employee_id and employee_id.isdigit():
        employee_query = employee_query.filter(Employee.id == int(employee_id))
    employees = employee_query.all()
    weekly_hours_data = {}
    for emp in employees:
        timesheets_this_week = Timesheet.query.filter(
            Timesheet.employee_id == emp.id,
            Timesheet.date >= start_of_week,
            Timesheet.date <= end_of_week
        ).all()
        total_hours = sum(ts.calculated_hours for ts in timesheets_this_week)
        potential_pay = total_hours * emp.pay_rate
        weekly_hours_data[emp.id] = {
            'employee': emp,
            'total_hours': total_hours,
            'potential_pay': potential_pay,
            'timesheets': timesheets_this_week
        }

    # 2. Get recorded payments for that period (or overlapping)
    recorded_payments = PayrollPayment.query.filter(
        # Simple overlap check, might need refinement
        PayrollPayment.pay_period_end >= start_of_week,
        PayrollPayment.pay_period_start <= end_of_week
    ).order_by(PayrollPayment.payment_date.desc()).all()
    
    # Fetch deductions for each payment
    for payment in recorded_payments:
        # Load deductions for the payment
        payment.deductions = PayrollDeduction.query.filter_by(payroll_payment_id=payment.id).all()
        
        # We don't need to calculate total_deductions here as it's a property in the model
        # that will be calculated automatically when accessed

    # Add payment info to the weekly data
    for payment in recorded_payments:
        if payment.employee_id in weekly_hours_data:
             if 'payments' not in weekly_hours_data[payment.employee_id]:
                 weekly_hours_data[payment.employee_id]['payments'] = []
             weekly_hours_data[payment.employee_id]['payments'].append(payment)
    
    # 3. Calculate payment method totals for the report
    payment_method_totals = {
        'CASH': {
            'count': 0,
            'total': 0.0,
            'payments': []
        },
        'CHECK': {
            'count': 0,
            'total': 0.0,
            'payments': []
        }
    }
    
    # Add other payment methods as needed
    for payment in recorded_payments:
        if payment.payment_method == PaymentMethod.CASH:
            method = 'CASH'
        elif payment.payment_method == PaymentMethod.CHECK:
            method = 'CHECK'
        else:
            # Skip other payment methods for this specific report
            continue
            
        payment_method_totals[method]['count'] += 1
        payment_method_totals[method]['total'] += payment.gross_amount
        # Use the net_amount property from the model
        # Add net amount to the totals if not already there
        if 'total_after_deductions' not in payment_method_totals[method]:
            payment_method_totals[method]['total_after_deductions'] = 0
        payment_method_totals[method]['total_after_deductions'] += payment.net_amount
        payment_method_totals[method]['payments'].append(payment)
    
    # 4. Calculate total hours across all employees
    total_weekly_hours = sum(data['total_hours'] for data in weekly_hours_data.values())
    
    # Find previous and next week for navigation
    prev_week = target_date - timedelta(days=7)
    next_week = target_date + timedelta(days=7)
    
    # For employee search history feature
    search_history = []
    if employee_id and employee_id.isdigit():
        # Get previous payments and hours for this employee across time periods
        search_results = {}
        for employee in employees:
            emp_payments = PayrollPayment.query.filter_by(employee_id=employee.id).order_by(PayrollPayment.payment_date.desc()).limit(10).all()
            emp_timesheets = Timesheet.query.filter_by(employee_id=employee.id).order_by(Timesheet.date.desc()).limit(20).all()
            
            # Calculate total hours and payments
            total_paid = sum(payment.amount for payment in emp_payments)
            total_hours_worked = sum(ts.calculated_hours for ts in emp_timesheets)
            
            search_results[employee.id] = {
                'employee': employee,
                'recent_payments': emp_payments,
                'recent_timesheets': emp_timesheets,
                'total_paid': total_paid,
                'total_hours_worked': total_hours_worked
            }
        search_history = search_results
    
    return render_template('payroll_report.html', 
                          weekly_data=weekly_hours_data,
                          recorded_payments=recorded_payments,
                          payment_method_totals=payment_method_totals,
                          current_week_start=start_of_week,
                          current_week_end=end_of_week,
                          prev_week=prev_week,
                          next_week=next_week,
                          total_weekly_hours=total_weekly_hours,
                          employee_id=employee_id,
                          search_history=search_history,
                          all_employees=all_employees)

# --- User Guide Route ---
@app.route('/user-guide')
@login_required
def user_guide():
    return render_template('user_guide_pt.html')

# --- Invoice Routes (Basic CRUD) ---
@app.route('/invoices')
@login_required
def invoices():
    try:
        # Use outerjoin instead of join to include invoices even if project relationship is broken
        all_invoices = Invoice.query.outerjoin(Project).order_by(Invoice.invoice_date.desc()).all()
        
        # Debug info to help diagnose issues
        invoice_count = len(all_invoices) if all_invoices else 0
        flash(f'Found {invoice_count} invoices in the system.', 'info')
        
        return render_template('invoices.html', invoices=all_invoices)
    except Exception as e:
        # Log the error and show a user-friendly message
        print(f"Error in invoices route: {str(e)}")
        flash(f'Error loading invoices: {str(e)}', 'danger')
        return render_template('invoices.html', invoices=[])

@app.route('/invoice/add', methods=['GET', 'POST'])
@login_required
def add_invoice():
    form = InvoiceForm()
    # Populate project choices
    form.project_id.choices = [(p.id, p.name) for p in Project.query.filter(
        Project.status.in_([ProjectStatus.PENDING, ProjectStatus.COMPLETED, ProjectStatus.INVOICED])
    ).order_by(Project.name).all()]

    if form.validate_on_submit():
        # Calculate total amount from base_amount and tax_amount
        base_amount = form.base_amount.data or 0
        tax_amount = form.tax_amount.data or 0
        total_amount = base_amount + tax_amount
        
        # Generate a unique invoice number if not provided
        invoice_number = form.invoice_number.data
        if not invoice_number or invoice_number.strip() == '':
            # Generate a unique invoice number based on timestamp and random suffix
            from datetime import datetime
            import random
            import string
            timestamp = datetime.now().strftime('%Y%m%d')
            random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            invoice_number = f"INV-{timestamp}-{random_suffix}"
            
        new_invoice = Invoice(
            project_id=form.project_id.data,
            invoice_number=invoice_number,
            invoice_date=form.invoice_date.data,
            due_date=form.due_date.data,
            base_amount=base_amount,
            tax_amount=tax_amount,
            amount=total_amount,
            description=form.description.data,
            status=PaymentStatus[form.status.data],
            payment_received_date=form.payment_received_date.data
        )
        db.session.add(new_invoice)
        # Update project status if invoice is being created
        project = Project.query.get(form.project_id.data)
        if project.status == ProjectStatus.COMPLETED:
            project.status = ProjectStatus.INVOICED
        # Update project status if invoice is marked as paid
        if form.status.data == PaymentStatus.PAID.name:
            project.status = ProjectStatus.PAID
        db.session.commit()
        flash('Invoice added successfully!', 'success')
        return redirect(url_for('invoices'))

    return render_template('invoice_form.html', form=form, title="Add Invoice")

@app.route('/invoice/delete/<int:id>', methods=['POST'])
@login_required
def delete_invoice(id):
    invoice = db.session.get(Invoice, id)
    if not invoice:
        flash('Invoice not found.', 'danger')
        return redirect(url_for('invoices')), 404
    
    try:
        # Get the project and status before deleting the invoice
        project = invoice.project
        project_has_other_invoices = Invoice.query.filter(Invoice.project_id == project.id, Invoice.id != invoice.id).count() > 0
        was_paid = invoice.status == PaymentStatus.PAID

        # Delete the invoice
        db.session.delete(invoice)
        
        # Update project status if needed
        if was_paid and not project_has_other_invoices:
            # If this was the only paid invoice, revert project to completed
            project.status = ProjectStatus.COMPLETED
        elif not project_has_other_invoices and project.status == ProjectStatus.INVOICED:
            # If this was the only invoice and not paid, revert to completed
            project.status = ProjectStatus.COMPLETED
            
        db.session.commit()
        flash(f'Invoice {invoice.invoice_number} deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting invoice: {e}', 'danger')
    return redirect(url_for('invoices'))

# --- Export Routes ---
@app.route('/export/projects/<format>')
@login_required
def export_projects(format):
    """Export projects to Excel, PDF, or CSV"""
    projects = Project.query.order_by(Project.start_date.desc()).all()
    
    projects_data = []
    for project in projects:
        projects_data.append({
            'Project ID': project.project_id_str or '',
            'Name': project.name,
            'Client': project.client_name or '',
            'Location': project.location or '',
            'Start Date': project.start_date.strftime('%Y-%m-%d') if project.start_date else '',
            'End Date': project.end_date.strftime('%Y-%m-%d') if project.end_date else '',
            'Status': project.status.value if project.status else '',
            'Contract Value': f"${project.contract_value:.2f}" if project.contract_value else '$0.00',
            'Labor Cost': f"${project.total_labor_cost:.2f}",
            'Material Cost': f"${project.total_material_cost:.2f}",
            'Other Expenses': f"${project.total_other_expenses:.2f}",
            'Total Cost': f"${project.total_cost:.2f}",
            'Profit': f"${project.profit:.2f}",
            'Profit Margin': f"{project.profit_margin:.2f}%"
        })
    
    if format == 'excel':
        return export_to_excel(projects_data, 'projects')
    elif format == 'pdf':
        return export_to_pdf(projects_data, 'Projects', 'projects.pdf')
    elif format == 'csv':
        return export_to_csv(projects_data, 'projects')
    else:
        flash('Invalid export format', 'error')
        return redirect(url_for('projects'))

@app.route('/export/timesheets/<format>')
@login_required
def export_timesheets(format):
    """Export timesheets to Excel, PDF, or CSV"""
    timesheets = Timesheet.query.order_by(Timesheet.date.desc()).all()
    
    timesheets_data = []
    for timesheet in timesheets:
        employee = db.session.get(Employee, timesheet.employee_id)
        project = db.session.get(Project, timesheet.project_id)
        
        timesheets_data.append({
            'Date': timesheet.date.strftime('%Y-%m-%d'),
            'Employee': employee.name if employee else 'Unknown',
            'Project': project.name if project else 'Unknown',
            'Entry Time': timesheet.entry_time.strftime('%H:%M'),
            'Exit Time': timesheet.exit_time.strftime('%H:%M'),
            'Lunch (mins)': timesheet.lunch_duration_minutes or 0,
            'Raw Hours': f"{timesheet.raw_hours:.2f}",
            'Calculated Hours': f"{timesheet.calculated_hours:.2f}",
            'Labor Cost': f"${timesheet.calculated_hours * (employee.pay_rate if employee else 0):.2f}"
        })
    
    if format == 'excel':
        return export_to_excel(timesheets_data, 'timesheets')
    elif format == 'pdf':
        return export_to_pdf(timesheets_data, 'Timesheets', 'timesheets.pdf')
    elif format == 'csv':
        return export_to_csv(timesheets_data, 'timesheets')
    else:
        flash('Invalid export format', 'error')
        return redirect(url_for('timesheets'))

@app.route('/export/expenses/<format>')
@login_required
def export_expenses(format):
    """Export expenses to Excel, PDF, or CSV"""
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    
    expenses_data = []
    for expense in expenses:
        project = db.session.get(Project, expense.project_id) if expense.project_id else None
        
        expenses_data.append({
            'Date': expense.date.strftime('%Y-%m-%d'),
            'Description': expense.description,
            'Category': expense.category or '',
            'Amount': f"${expense.amount:.2f}",
            'Supplier/Vendor': expense.supplier_vendor or '',
            'Project': project.name if project else 'N/A',
            'Payment Method': expense.payment_method.value if expense.payment_method else '',
            'Payment Status': expense.payment_status.value if expense.payment_status else ''
        })
    
    if format == 'excel':
        return export_to_excel(expenses_data, 'expenses')
    elif format == 'pdf':
        return export_to_pdf(expenses_data, 'Expenses', 'expenses.pdf')
    elif format == 'csv':
        return export_to_csv(expenses_data, 'expenses')
    else:
        flash('Invalid export format', 'error')
        return redirect(url_for('expenses'))

@app.route('/export/payroll/<format>')
@login_required
def export_payroll(format):
    """Export payroll data to Excel, PDF, or CSV"""
    payroll_payments = PayrollPayment.query.order_by(PayrollPayment.payment_date.desc()).all()
    
    payroll_data = []
    for payment in payroll_payments:
        employee = db.session.get(Employee, payment.employee_id)
        
        check_info = ""
        if payment.payment_method == PaymentMethod.CHECK:
            check_info = f"Check #{payment.check_number}" if payment.check_number else "No check number"
            if payment.bank_name:
                check_info += f", {payment.bank_name}"
        
        payroll_data.append({
            'Employee': employee.name if employee else 'Unknown',
            'Pay Period Start': payment.pay_period_start.strftime('%Y-%m-%d'),
            'Pay Period End': payment.pay_period_end.strftime('%Y-%m-%d'),
            'Payment Date': payment.payment_date.strftime('%Y-%m-%d'),
            'Amount': f"${payment.amount:.2f}",
            'Payment Method': payment.payment_method.value,
            'Check Details': check_info,
            'Notes': payment.notes or ''
        })
    
    if format == 'excel':
        return export_to_excel(payroll_data, 'payroll')
    elif format == 'pdf':
        return export_to_pdf(payroll_data, 'Payroll', 'payroll.pdf')
    elif format == 'csv':
        return export_to_csv(payroll_data, 'payroll')
    else:
        flash('Invalid export format', 'error')
        return redirect(url_for('payroll_report'))

# --- Future Enhancements Routes ---
@app.route('/future-enhancements')
@login_required
def future_enhancements():
    """Display future enhancement plans and suggestion form"""
    # Predefined enhancements based on documentation
    enhancements = [
        {
            'title': 'Role-Based Authentication',
            'description': 'Expand the existing authentication system to include role-based permissions for administrators, managers, and staff, allowing different access levels to various features.',
            'priority': 'High'
        },
        {
            'title': 'Multi-Factor Authentication',
            'description': 'Enhance security by implementing multi-factor authentication options such as email verification codes or authenticator apps.',
            'priority': 'Medium'
        },
        {
            'title': 'Enhanced Analytics Dashboard',
            'description': 'Expand the current dashboard with more interactive drill-down capabilities, data filtering options, and custom date range selections.',
            'priority': 'Medium'
        },
        {
            'title': 'Document Management',
            'description': 'Upload and store project-related documents such as contracts, designs, and client communications directly in the system.',
            'priority': 'Medium'
        },
        {
            'title': 'Client Portal',
            'description': 'Allow clients to view project status, approve work, and access invoices through a secure client portal.',
            'priority': 'Medium'
        },
        {
            'title': 'PDF Export',
            'description': 'Generate downloadable PDF reports, invoices, and timesheets for offline sharing and record-keeping.',
            'priority': 'Medium'
        },
        {
            'title': 'Email Notifications',
            'description': 'Send automatic updates for key events such as invoice due dates, project milestones, and payment confirmations.',
            'priority': 'Low'
        },
        {
            'title': 'Mobile Application',
            'description': 'Develop a companion app for field use, allowing employees to log time and materials directly from job sites.',
            'priority': 'High'
        },
        {
            'title': 'Inventory Management',
            'description': 'Track inventory levels and automate reordering to ensure materials are always available when needed.',
            'priority': 'Medium'
        },
        {
            'title': 'Integration with Accounting Software',
            'description': 'Connect with accounting and tax software to streamline financial reporting and tax preparation.',
            'priority': 'Medium'
        },
        {
            'title': 'Electronic Signatures',
            'description': 'Enable digital signing of documents for contracts, approvals, and other paperwork.',
            'priority': 'Low'
        },
        {
            'title': 'Password Reset Functionality',
            'description': 'Implement a self-service password reset feature that allows users to reset their passwords via email verification.',
            'priority': 'Medium'
        },
        {
            'title': 'User Profile Management',
            'description': 'Allow users to update their profile information and preferences, including password changes and notification settings.',
            'priority': 'Low'
        }
    ]
    
    # Form for suggesting new enhancements
    from forms import EnhancementSuggestionForm
    form = EnhancementSuggestionForm()
    
    return render_template('future_enhancements.html', enhancements=enhancements, form=form)

@app.route('/suggest-enhancement', methods=['POST'])
@login_required
def suggest_enhancement():
    """Handle enhancement suggestions"""
    from forms import EnhancementSuggestionForm
    form = EnhancementSuggestionForm()
    
    if form.validate_on_submit():
        # In a real implementation, you would save this to a database
        # For now, just show a success message
        flash(f'Thank you for your enhancement suggestion: "{form.title.data}". Our team will review it!', 'success')
        return redirect(url_for('future_enhancements'))
    
    # If form validation fails, return to the page with errors
    enhancements = []  # You would need to repopulate this
    flash('Please correct the errors in your submission.', 'danger')
    return render_template('future_enhancements.html', enhancements=enhancements, form=form)

# --- User Needs Feedback System ---
@app.route('/submit_user_needs', methods=['POST'])
def submit_user_needs():
    if not session.get('user_id'):
        flash('Please log in to submit feedback.', 'danger')
        return redirect(url_for('login'))
        
    # Get feedback content from form
    content = request.form.get('content', '')
    section = request.form.get('section', '/')
    
    # Create feedback entry
    feedback_entry = {
        'id': str(uuid.uuid4()),
        'user_id': session.get('user_id'),
        'username': session.get('username', 'Anonymous'),
        'content': content,
        'section': section,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Load existing feedback from JSON file
    try:
        with open('userneeds.json', 'r') as f:
            feedback_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        feedback_data = []
        
    # Add new feedback and save back to JSON file
    feedback_data.append(feedback_entry)
    with open('userneeds.json', 'w') as f:
        json.dump(feedback_data, f, indent=4)
        
    flash('Thank you for your feedback! We value your input.', 'success')
    return redirect(request.referrer or url_for('index'))

# --- Financial Management System Routes ---

# Accounts Payable Routes
@app.route('/accounts_payable')
@login_required
def accounts_payable():
    """Display list of accounts payable."""
    payables = AccountsPayable.query.order_by(AccountsPayable.due_date).all()
    return render_template('accounts_payable/index.html', payables=payables)

@app.route('/add_accounts_payable', methods=['GET', 'POST'])
@login_required
def add_accounts_payable():
    """Add a new accounts payable entry."""
    form = AccountsPayableForm()
    
    # Populate project choices
    projects = Project.query.order_by(Project.name).all()
    form.project_id.choices = [(0, '-- No Project --')] + [(p.id, p.name) for p in projects]
    
    if form.validate_on_submit():
        payable = AccountsPayable(
            vendor=form.vendor.data,
            description=form.description.data,
            amount=form.amount.data,
            issue_date=form.issue_date.data,
            due_date=form.due_date.data,
            payment_method=form.payment_method.data if form.payment_method.data else None,
            category=form.category.data,
            notes=form.notes.data,
            project_id=form.project_id.data if form.project_id.data else None
        )
        db.session.add(payable)
        db.session.commit()
        flash('Accounts payable added successfully!', 'success')
        return redirect(url_for('accounts_payable'))
    
    return render_template('accounts_payable/add.html', form=form)

@app.route('/edit_accounts_payable/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_accounts_payable(id):
    """Edit an existing accounts payable entry."""
    payable = AccountsPayable.query.get_or_404(id)
    form = AccountsPayableForm(obj=payable)
    
    # Populate project choices
    projects = Project.query.order_by(Project.name).all()
    form.project_id.choices = [(0, '-- No Project --')] + [(p.id, p.name) for p in projects]
    
    if form.validate_on_submit():
        payable.vendor = form.vendor.data
        payable.description = form.description.data
        payable.amount = form.amount.data
        payable.issue_date = form.issue_date.data
        payable.due_date = form.due_date.data
        payable.payment_method = form.payment_method.data if form.payment_method.data else None
        payable.category = form.category.data
        payable.notes = form.notes.data
        payable.project_id = form.project_id.data if form.project_id.data else None
        
        db.session.commit()
        flash('Accounts payable updated successfully!', 'success')
        return redirect(url_for('accounts_payable'))
    
    return render_template('accounts_payable/edit.html', form=form, payable=payable)

@app.route('/delete_accounts_payable/<int:id>', methods=['POST'])
@login_required
def delete_accounts_payable(id):
    """Delete an accounts payable entry."""
    payable = AccountsPayable.query.get_or_404(id)
    
    # Don't allow deletion if this has a paid account associated
    if hasattr(payable, 'paid_account') and payable.paid_account:
        flash('Cannot delete an accounts payable that has been paid. Mark it as paid instead.', 'danger')
        return redirect(url_for('accounts_payable'))
    
    db.session.delete(payable)
    db.session.commit()
    flash('Accounts payable deleted successfully!', 'success')
    return redirect(url_for('accounts_payable'))

# Paid Accounts Routes
@app.route('/paid_accounts')
@login_required
def paid_accounts():
    """Display list of paid accounts."""
    accounts = PaidAccount.query.order_by(PaidAccount.payment_date.desc()).all()
    return render_template('paid_accounts/index.html', accounts=accounts)

@app.route('/add_paid_account', methods=['GET', 'POST'])
@login_required
def add_paid_account():
    """Add a new paid account entry."""
    form = PaidAccountForm()
    
    # Populate project and accounts payable choices
    projects = Project.query.order_by(Project.name).all()
    form.project_id.choices = [(0, '-- No Project --')] + [(p.id, p.name) for p in projects]
    
    # Only show unpaid accounts payable
    payables = AccountsPayable.query.filter_by(status=PaymentStatus.PENDING).order_by(AccountsPayable.vendor).all()
    form.accounts_payable_id.choices = [(0, '-- Not Linked to Payable --')] + [(p.id, f'{p.vendor}: ${p.amount:.2f} due {p.due_date}') for p in payables]
    
    if form.validate_on_submit():
        # First, validate check details if payment method is check
        if form.payment_method.data == PaymentMethod.CHECK.name:
            if not form.check_number.data or not form.bank_name.data:
                flash('Check number and bank name are required for check payments.', 'danger')
                return render_template('paid_accounts/add.html', form=form)
        
        # Create the paid account entry
        paid_account = PaidAccount(
            vendor=form.vendor.data,
            amount=form.amount.data,
            payment_date=form.payment_date.data,
            payment_method=form.payment_method.data,
            check_number=form.check_number.data,
            bank_name=form.bank_name.data,
            receipt_attachment=form.receipt_attachment.data,
            notes=form.notes.data,
            category=form.category.data,
            project_id=form.project_id.data if form.project_id.data else None,
            accounts_payable_id=form.accounts_payable_id.data if form.accounts_payable_id.data else None
        )
        db.session.add(paid_account)
        
        # If this is linked to an accounts payable, update its status
        if form.accounts_payable_id.data:
            payable = AccountsPayable.query.get(form.accounts_payable_id.data)
            if payable:
                payable.status = PaymentStatus.PAID
        
        db.session.commit()
        flash('Paid account added successfully!', 'success')
        return redirect(url_for('paid_accounts'))
    
    return render_template('paid_accounts/add.html', form=form)

@app.route('/edit_paid_account/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_paid_account(id):
    """Edit an existing paid account entry."""
    account = PaidAccount.query.get_or_404(id)
    form = PaidAccountForm(obj=account)
    
    # Populate project and accounts payable choices
    projects = Project.query.order_by(Project.name).all()
    form.project_id.choices = [(0, '-- No Project --')] + [(p.id, p.name) for p in projects]
    
    # For editing, include the current accounts payable even if it's already paid
    payables = AccountsPayable.query.filter(
        (AccountsPayable.status == PaymentStatus.PENDING) | 
        (AccountsPayable.id == account.accounts_payable_id)
    ).order_by(AccountsPayable.vendor).all()
    form.accounts_payable_id.choices = [(0, '-- Not Linked to Payable --')] + [(p.id, f'{p.vendor}: ${p.amount:.2f} due {p.due_date}') for p in payables]
    
    if form.validate_on_submit():
        # First, validate check details if payment method is check
        if form.payment_method.data == PaymentMethod.CHECK.name:
            if not form.check_number.data or not form.bank_name.data:
                flash('Check number and bank name are required for check payments.', 'danger')
                return render_template('paid_accounts/edit.html', form=form, account=account)
        
        # Check if accounts_payable_id has changed
        old_payable_id = account.accounts_payable_id
        new_payable_id = form.accounts_payable_id.data if form.accounts_payable_id.data else None
        
        # Update the paid account
        account.vendor = form.vendor.data
        account.amount = form.amount.data
        account.payment_date = form.payment_date.data
        account.payment_method = form.payment_method.data
        account.check_number = form.check_number.data
        account.bank_name = form.bank_name.data
        account.receipt_attachment = form.receipt_attachment.data
        account.notes = form.notes.data
        account.category = form.category.data
        account.project_id = form.project_id.data if form.project_id.data else None
        account.accounts_payable_id = new_payable_id
        
        # Handle changes to accounts payable associations
        if old_payable_id != new_payable_id:
            # Reset old payable to PENDING if it exists
            if old_payable_id:
                old_payable = AccountsPayable.query.get(old_payable_id)
                if old_payable:
                    old_payable.status = PaymentStatus.PENDING
            
            # Set new payable to PAID if it exists
            if new_payable_id:
                new_payable = AccountsPayable.query.get(new_payable_id)
                if new_payable:
                    new_payable.status = PaymentStatus.PAID
        
        db.session.commit()
        flash('Paid account updated successfully!', 'success')
        return redirect(url_for('paid_accounts'))
    
    return render_template('paid_accounts/edit.html', form=form, account=account)

@app.route('/delete_paid_account/<int:id>', methods=['POST'])
@login_required
def delete_paid_account(id):
    """Delete a paid account entry."""
    account = PaidAccount.query.get_or_404(id)
    
    # If this is linked to an accounts payable, reset its status
    if account.accounts_payable_id:
        payable = AccountsPayable.query.get(account.accounts_payable_id)
        if payable:
            payable.status = PaymentStatus.PENDING
    
    db.session.delete(account)
    db.session.commit()
    flash('Paid account deleted successfully!', 'success')
    return redirect(url_for('paid_accounts'))

# Monthly Expenses Routes
@app.route('/monthly_expenses')
@login_required
def monthly_expenses():
    """Display list of monthly expenses."""
    expenses = MonthlyExpense.query.order_by(MonthlyExpense.expense_date.desc()).all()
    return render_template('monthly_expenses/index.html', expenses=expenses)

@app.route('/add_monthly_expense', methods=['GET', 'POST'])
@login_required
def add_monthly_expense():
    """Add a new monthly expense entry."""
    form = MonthlyExpenseForm()
    
    # Populate project choices
    projects = Project.query.order_by(Project.name).all()
    form.project_id.choices = [(0, '-- No Project --')] + [(p.id, p.name) for p in projects]
    
    if form.validate_on_submit():
        expense = MonthlyExpense(
            description=form.description.data,
            amount=form.amount.data,
            expense_date=form.expense_date.data,
            category=form.category.data,
            payment_method=form.payment_method.data,
            notes=form.notes.data,
            project_id=form.project_id.data if form.project_id.data else None
        )
        db.session.add(expense)
        db.session.commit()
        flash('Monthly expense added successfully!', 'success')
        return redirect(url_for('monthly_expenses'))
    
    return render_template('monthly_expenses/add.html', form=form)

@app.route('/edit_monthly_expense/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_monthly_expense(id):
    """Edit an existing monthly expense entry."""
    expense = MonthlyExpense.query.get_or_404(id)
    form = MonthlyExpenseForm(obj=expense)
    
    # Populate project choices
    projects = Project.query.order_by(Project.name).all()
    form.project_id.choices = [(0, '-- No Project --')] + [(p.id, p.name) for p in projects]
    
    if form.validate_on_submit():
        expense.description = form.description.data
        expense.amount = form.amount.data
        expense.expense_date = form.expense_date.data
        expense.category = form.category.data
        expense.payment_method = form.payment_method.data
        expense.notes = form.notes.data
        expense.project_id = form.project_id.data if form.project_id.data else None
        
        db.session.commit()
        flash('Monthly expense updated successfully!', 'success')
        return redirect(url_for('monthly_expenses'))
    
    return render_template('monthly_expenses/edit.html', form=form, expense=expense)

@app.route('/delete_monthly_expense/<int:id>', methods=['POST'])
@login_required
def delete_monthly_expense(id):
    """Delete a monthly expense entry."""
    expense = MonthlyExpense.query.get_or_404(id)
    db.session.delete(expense)
    db.session.commit()
    flash('Monthly expense deleted successfully!', 'success')
    return redirect(url_for('monthly_expenses'))

# Financial Reports
@app.route('/financial_reports')
@login_required
def financial_reports():
    """Display financial reports."""
    # Get current date for calculations
    today = date.today()
    current_year = today.year
    current_month = today.month
    
    # Get accounts payable statistics
    accounts_payable_total = db.session.query(db.func.sum(AccountsPayable.amount)).filter(
        AccountsPayable.status != PaymentStatus.PAID
    ).scalar() or 0
    
    accounts_payable_count = AccountsPayable.query.filter(
        AccountsPayable.status != PaymentStatus.PAID
    ).count()
    
    # Get paid accounts statistics for the current month
    month_start = date(current_year, current_month, 1)
    if current_month == 12:
        month_end = date(current_year, 12, 31)
    else:
        month_end = date(current_year, current_month + 1, 1) - timedelta(days=1)
    
    paid_accounts_total = db.session.query(db.func.sum(PaidAccount.amount)).filter(
        PaidAccount.payment_date >= month_start,
        PaidAccount.payment_date <= month_end
    ).scalar() or 0
    
    paid_accounts_count = PaidAccount.query.filter(
        PaidAccount.payment_date >= month_start,
        PaidAccount.payment_date <= month_end
    ).count()
    
    # Get monthly expenses statistics for the current month
    monthly_expenses_total = db.session.query(db.func.sum(MonthlyExpense.amount)).filter(
        MonthlyExpense.expense_date >= month_start,
        MonthlyExpense.expense_date <= month_end
    ).scalar() or 0
    
    monthly_expenses_count = MonthlyExpense.query.filter(
        MonthlyExpense.expense_date >= month_start,
        MonthlyExpense.expense_date <= month_end
    ).count()
    
    # Get payment status data for the chart
    payment_status_labels = ['Paid', 'Pending', 'Overdue']
    
    paid_amount = db.session.query(db.func.sum(PaidAccount.amount)).scalar() or 0
    pending_amount = db.session.query(db.func.sum(AccountsPayable.amount)).filter(
        AccountsPayable.status == PaymentStatus.PENDING
    ).scalar() or 0
    overdue_amount = db.session.query(db.func.sum(AccountsPayable.amount)).filter(
        AccountsPayable.status == PaymentStatus.OVERDUE
    ).scalar() or 0
    
    payment_status_data = [paid_amount, pending_amount, overdue_amount]
    
    # Get upcoming payments (due in next 30 days)
    upcoming_payments = []
    unpaid_accounts = AccountsPayable.query.filter(
        AccountsPayable.status != PaymentStatus.PAID,
        AccountsPayable.due_date <= today + timedelta(days=30)
    ).order_by(AccountsPayable.due_date).all()
    
    for account in unpaid_accounts:
        days_left = (account.due_date - today).days
        upcoming_payments.append({
            'vendor': account.vendor,
            'amount': account.amount,
            'due_date': account.due_date,
            'days_left': max(0, days_left)  # Ensure non-negative days
        })
    
    # Get expense categories data for the chart
    expense_categories = {}
    for expense in MonthlyExpense.query.all():
        category = expense.category.value
        if category in expense_categories:
            expense_categories[category] += expense.amount
        else:
            expense_categories[category] = expense.amount
    
    expense_categories_labels = list(expense_categories.keys())
    expense_categories_data = list(expense_categories.values())
    
    # Calculate cash flow data (income vs expenses) for the past 6 months
    cash_flow_labels = []
    income_data = []
    expense_data = []
    
    for i in range(6):
        # Calculate month offset from current month
        # Adjust for previous year if needed
        if current_month - i <= 0:
            target_month = 12 + current_month - i
            target_year = current_year - 1
        else:
            target_month = current_month - i
            target_year = current_year
        
        # Calculate start and end of month
        start_date = date(target_year, target_month, 1)
        if target_month == 12:
            end_date = date(target_year, 12, 31)
        else:
            end_date = date(target_year, target_month + 1, 1) - timedelta(days=1)
            
        # Add month label (format: 'Jan', 'Feb', etc.)
        cash_flow_labels.insert(0, start_date.strftime('%b'))
        
        # Calculate monthly income (from paid accounts)
        monthly_income = db.session.query(db.func.sum(PaidAccount.amount)).filter(
            PaidAccount.payment_date >= start_date,
            PaidAccount.payment_date <= end_date
        ).scalar() or 0
        income_data.insert(0, round(monthly_income, 2))
        
        # Calculate monthly expenses
        monthly_expense = db.session.query(db.func.sum(MonthlyExpense.amount)).filter(
            MonthlyExpense.expense_date >= start_date,
            MonthlyExpense.expense_date <= end_date
        ).scalar() or 0
        expense_data.insert(0, round(monthly_expense, 2))
    
    # Prepare data for the template
    selected_year = current_year
    selected_month = 'all'  # Default to show all months
    
    return render_template('financial_reports/index.html',
                          # Summary cards data
                          accounts_payable_total=accounts_payable_total,
                          accounts_payable_count=accounts_payable_count,
                          paid_accounts_total=paid_accounts_total,
                          paid_accounts_count=paid_accounts_count,
                          monthly_expenses_total=monthly_expenses_total,
                          monthly_expenses_count=monthly_expenses_count,
                          
                          # Chart data
                          payment_status_labels=payment_status_labels,
                          payment_status_data=payment_status_data,
                          expense_categories_labels=expense_categories_labels,
                          expense_categories_data=expense_categories_data,
                          cash_flow_labels=cash_flow_labels,
                          income_data=income_data,
                          expense_data=expense_data,
                          
                          # Other data
                          upcoming_payments=upcoming_payments,
                          current_year=current_year,
                          selected_year=selected_year,
                          selected_month=selected_month)

# --- Database Backup and Restore Routes ---
@app.route('/backup_database')
@login_required
def backup_database():
    """Create a backup of the current database and send it as a download."""
    try:
        # Close database connection
        db.session.close()
        
        # Get the path to the current database file
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        # Create a timestamp for the backup filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"erp_backup_{timestamp}.db"
        
        # Send the file as a download
        return send_file(
            db_path,
            as_attachment=True,
            download_name=backup_filename,
            mimetype='application/octet-stream'
        )
    except Exception as e:
        flash(f'Error creating database backup: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/restore_database', methods=['POST'])
@login_required
def restore_database():
    """Restore the database from an uploaded backup file."""
    try:
        # Check if a file was uploaded
        if 'backup_file' not in request.files:
            flash('No backup file selected', 'danger')
            return redirect(url_for('index'))
        
        backup_file = request.files['backup_file']
        
        # Check if the file has a name
        if backup_file.filename == '':
            flash('No backup file selected', 'danger')
            return redirect(url_for('index'))
        
        # Get the path to the current database file
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        # Close database connection
        db.session.close()
        
        # Create a backup of the current database before restoring
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pre_restore_backup = f"{db_path}_pre_restore_{timestamp}"
        import shutil
        shutil.copy2(db_path, pre_restore_backup)
        
        # Save the uploaded file to the database path
        backup_file.save(db_path)
        
        # Reinitialize the database connection - Fixed to avoid KeyError
        db.engine.dispose()
        
        flash('Database successfully restored from backup', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        import traceback
        flash(f'Error restoring database: {traceback.format_exc()}', 'danger')
        return redirect(url_for('index'))

# --- Create DB tables ---
@app.cli.command('init-db')
def init_db_command():
    """Creates the database tables."""
    with app.app_context():
        db.create_all()
    print('Initialized the database.')

# --- Main execution ---
if __name__ == '__main__':
    with app.app_context():
        # Create database tables if they don't exist
        db.create_all()
        
        # Create default user if it doesn't exist
        if not User.query.filter_by(username='patricia').first():
            default_user = User(username='patricia')
            default_user.set_password('Patri2025')
            db.session.add(default_user)
            db.session.commit()
            print('Created default user: patricia')
            
    app.run(debug=False, host='0.0.0.0', port=3002)  # Run on port 3002 for Nginx proxy