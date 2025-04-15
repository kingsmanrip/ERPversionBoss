def generate_customer_invoice_pdf(invoice_id):
    """
    Generate a professional PDF invoice for customers with a modern design.
    
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
    
    # Set default margins
    pdf.set_margins(15, 15, 15)
    
    # Define colors
    primary_color = (0, 51, 153)  # Dark blue
    accent_color = (255, 0, 0)    # Red
    highlight_color = (0, 102, 204)  # Medium blue
    
    # Header with company info - modern centered design with color
    pdf.set_font('DejaVu', 'B', 22)
    pdf.set_text_color(primary_color[0], primary_color[1], primary_color[2])
    pdf.cell(0, 15, 'Mauricio PDQ Paint & Drywall LLC', 0, 1, 'C')
    
    # Company address in smaller font
    pdf.set_font('DejaVu', '', 11)
    pdf.set_text_color(80, 80, 80)  # Dark gray
    pdf.cell(0, 6, '968 WPA RD', 0, 1, 'C')
    pdf.cell(0, 6, 'Sumrall Ms, 39482', 0, 1, 'C')
    
    # Contact information in red with a horizontal line above and below
    pdf.ln(2)
    pdf.line(40, pdf.get_y(), pdf.w - 40, pdf.get_y())
    pdf.ln(3)
    pdf.set_text_color(accent_color[0], accent_color[1], accent_color[2])
    pdf.set_font('DejaVu', 'B', 11)
    pdf.cell(0, 6, 'MAURICIO: 601-596-3130        FAX: 601-752-3519', 0, 1, 'C')
    pdf.ln(3)
    pdf.set_text_color(80, 80, 80)
    pdf.line(40, pdf.get_y(), pdf.w - 40, pdf.get_y())
    pdf.ln(8)
    
    # Client details in a modern table format with colored headers
    pdf.set_fill_color(240, 240, 240)  # Light gray background for headers
    pdf.set_text_color(primary_color[0], primary_color[1], primary_color[2])
    pdf.set_font('DejaVu', 'B', 10)
    
    # Table header row - first column
    col_width1 = 45
    col_width2 = 85
    col_width3 = 25
    col_width4 = 30
    
    # First row
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(col_width1, 9, 'NAME', 1, 0, 'L', True)
    pdf.set_text_color(highlight_color[0], highlight_color[1], highlight_color[2])
    pdf.set_font('DejaVu', '', 10)
    pdf.cell(col_width2, 9, project.client_name, 1, 0, 'L')
    pdf.set_text_color(primary_color[0], primary_color[1], primary_color[2])
    pdf.set_font('DejaVu', 'B', 10)
    pdf.cell(col_width3, 9, 'PHONE', 1, 0, 'L', True)
    pdf.set_font('DejaVu', '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(col_width4, 9, '', 1, 1)
    
    # Second row
    pdf.set_text_color(primary_color[0], primary_color[1], primary_color[2])
    pdf.set_font('DejaVu', 'B', 10)
    pdf.cell(col_width1, 9, 'STREET', 1, 0, 'L', True)
    pdf.set_font('DejaVu', '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(col_width2, 9, project.location, 1, 0, 'L')
    pdf.set_text_color(primary_color[0], primary_color[1], primary_color[2])
    pdf.set_font('DejaVu', 'B', 10)
    pdf.cell(col_width3, 9, 'DATE', 1, 0, 'L', True)
    pdf.set_text_color(highlight_color[0], highlight_color[1], highlight_color[2])
    pdf.set_font('DejaVu', '', 10)
    pdf.cell(col_width4, 9, invoice.invoice_date.strftime('%m/%d/%Y'), 1, 1, 'C')
    
    # Third row
    pdf.set_text_color(primary_color[0], primary_color[1], primary_color[2])
    pdf.set_font('DejaVu', 'B', 10)
    pdf.cell(col_width1, 9, 'CITY/STATE', 1, 0, 'L', True)
    pdf.set_font('DejaVu', '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(col_width2, 9, '', 1, 0, 'L')
    pdf.set_text_color(primary_color[0], primary_color[1], primary_color[2])
    pdf.set_font('DejaVu', 'B', 10)
    pdf.cell(col_width3, 9, 'CELL', 1, 0, 'L', True)
    pdf.set_font('DejaVu', '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(col_width4, 9, '', 1, 1)
    
    # Fourth row
    pdf.set_text_color(primary_color[0], primary_color[1], primary_color[2])
    pdf.set_font('DejaVu', 'B', 10)
    pdf.cell(col_width1, 9, 'SUBDIVISION', 1, 0, 'L', True)
    pdf.set_font('DejaVu', '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(col_width2, 9, '', 1, 0, 'L')
    pdf.set_text_color(primary_color[0], primary_color[1], primary_color[2])
    pdf.set_font('DejaVu', 'B', 10)
    pdf.cell(col_width3 + col_width4, 9, 'JOB LOCATION', 1, 1, 'L', True)
    
    # Proposal statement with a modern touch
    pdf.ln(8)
    pdf.set_draw_color(primary_color[0], primary_color[1], primary_color[2])
    pdf.set_text_color(primary_color[0], primary_color[1], primary_color[2])
    pdf.set_font('DejaVu', 'B', 11)
    pdf.cell(0, 10, 'PROPOSAL', 0, 1, 'L')
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('DejaVu', '', 10)
    pdf.cell(0, 8, 'I propose to furnish all materials and perform all necessary labor to complete the following:', 0, 1, 'L')
    
    # Description and directions table - modern design with rounded corners effect
    pdf.set_fill_color(252, 252, 252)  # Very light gray
    pdf.set_draw_color(200, 200, 200)  # Light gray border
    
    # Description box with light fill
    description_height = 65
    pdf.rect(15, pdf.get_y(), 130, description_height, 'DF')
    
    # Directions box with colored header
    pdf.set_fill_color(primary_color[0], primary_color[1], primary_color[2])
    pdf.set_text_color(255, 255, 255)  # White text
    pdf.set_xy(145, pdf.get_y())
    pdf.cell(50, 10, 'DIRECTIONS', 1, 1, 'C', True)
    
    # Reset colors and continue with directions box
    pdf.set_fill_color(252, 252, 252)
    pdf.set_draw_color(200, 200, 200)
    pdf.rect(145, pdf.get_y() - 10 + 10, 50, description_height - 10, 'D')
    
    # Position cursor for description text (inside the left cell)
    pdf.set_xy(20, pdf.get_y() - description_height + 5)
    pdf.set_font('DejaVu', '', 11)
    pdf.set_text_color(highlight_color[0], highlight_color[1], highlight_color[2])
    pdf.multi_cell(120, 8, project.description, 0, 'L')
    
    # Move to position after the description/directions boxes
    pdf.set_y(pdf.get_y() + description_height - 5)
    
    # Payment section with modern styling
    pdf.ln(10)
    pdf.set_text_color(80, 80, 80)
    pdf.set_font('DejaVu', '', 10)
    pdf.cell(0, 8, 'All of the work to be completed in a substantial and workmanlike manner for the sum of:', 0, 1, 'C')
    
    # Payment Details Section
    pdf.ln(5)
    pdf.set_font('DejaVu', 'B', 13)
    pdf.set_text_color(primary_color[0], primary_color[1], primary_color[2])
    pdf.cell(0, 10, 'PAYMENT DETAILS', 0, 1, 'L')
    pdf.set_font('DejaVu', '', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 7, invoice.description or '', 0, 'L')
    pdf.ln(2)
    pdf.set_font('DejaVu', '', 11)
    pdf.cell(60, 8, 'Base Amount:', 0, 0, 'L')
    pdf.cell(40, 8, f"${invoice.base_amount:,.2f}", 0, 0, 'L')
    pdf.cell(40, 8, 'Tax/Fees:', 0, 0, 'L')
    pdf.cell(40, 8, f"${invoice.tax_amount:,.2f}", 0, 1, 'L')
    pdf.set_font('DejaVu', 'B', 12)
    pdf.set_text_color(0, 102, 204)
    pdf.cell(60, 10, '', 0, 0)
    pdf.cell(40, 10, 'TOTAL:', 0, 0, 'L')
    pdf.set_font('DejaVu', 'B', 16)
    pdf.set_text_color(0, 102, 204)
    pdf.cell(40, 10, f"${invoice.amount:,.2f}", 0, 1, 'L')
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)
    
    # Price line with modern styling
    pdf.set_text_color(0, 0, 0)
    pdf.cell(15, 10, '$', 0, 0, 'R')
    base_amount_str = f"{invoice.base_amount:,.2f}"
    pdf.cell(25, 10, base_amount_str, 'B', 0, 'C')
    pdf.cell(5, 10, '+', 0, 0, 'C')
    pdf.cell(5, 10, '$', 0, 0, 'R')
    tax_amount_str = f"{invoice.tax_amount:,.2f}"
    pdf.cell(25, 10, tax_amount_str, 'B', 0, 'C')
    pdf.cell(40, 10, '(tax) TOTAL:', 0, 0, 'C')
    
    # Total amount with highlight
    pdf.set_font('DejaVu', 'B', 14)
    pdf.set_text_color(highlight_color[0], highlight_color[1], highlight_color[2])
    pdf.cell(0, 10, f'${invoice.amount:.2f}', 0, 1, 'L')
    
    # Terms in a cleaner, more readable format
    pdf.ln(5)
    pdf.set_text_color(80, 80, 80)
    pdf.set_font('DejaVu', '', 9)
    pdf.multi_cell(0, 5, 'The entire amount of the contract to be paid upon completion. Any alterations or deviation from the above specifications involving extra cost of material or labor will be executed upon written order for same and will become an extra charge over the sum mentioned in this contract. All agreements must be made in writing.', 0, 'C')
    
    # Acceptance section with modern styling
    pdf.ln(8)
    pdf.set_fill_color(primary_color[0], primary_color[1], primary_color[2])
    pdf.set_text_color(255, 255, 255)  # White text
    pdf.set_font('DejaVu', 'B', 11)
    pdf.cell(0, 8, 'ACCEPTANCE', 0, 1, 'C', True)
    
    pdf.ln(3)
    pdf.set_text_color(80, 80, 80)
    pdf.set_font('DejaVu', '', 9)
    pdf.multi_cell(0, 5, 'I hereby authorize Mauricio PDQ Paint and Drywall LLC to furnish all materials and labor required to complete the work mentioned in the above proposal, and I agree to pay the amount mentioned in said proposal and according to the terms thereof.', 0, 'L')
    
    # Payment details and signature section with modern layout
    pdf.ln(8)
    
    # Create a box for payment details on the left with light fill and border
    payment_box_y = pdf.get_y()
    pdf.set_fill_color(252, 252, 252)
    pdf.set_draw_color(200, 200, 200)
    pdf.rect(15, payment_box_y, 80, 40, 'DF')
    
    # Payment details with better spacing
    pdf.set_text_color(80, 80, 80)
    pdf.set_font('DejaVu', '', 9)
    pdf.set_xy(20, payment_box_y + 5)
    pdf.cell(70, 5, 'C/C #_________________________', 0, 1)
    pdf.set_xy(20, pdf.get_y() + 3)
    pdf.cell(70, 5, 'EXP______________ CVV__________', 0, 1)
    pdf.set_xy(20, pdf.get_y() + 3)
    pdf.cell(70, 5, 'Name_________________________', 0, 1)
    pdf.set_xy(20, pdf.get_y() + 3)
    pdf.cell(70, 5, 'Address_______________________', 0, 1)
    pdf.set_xy(20, pdf.get_y() + 3)
    pdf.cell(70, 5, 'Zip Code______________________', 0, 1)
    
    # Signature section on the right with modern styling
    pdf.set_text_color(80, 80, 80)
    pdf.set_font('DejaVu', 'B', 9)
    pdf.set_xy(110, payment_box_y + 5)
    pdf.cell(30, 5, 'Date:', 0, 0)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(145, pdf.get_y() + 3, 190, pdf.get_y() + 3)  # Date line
    
    pdf.set_xy(110, pdf.get_y() + 15)
    pdf.cell(30, 5, 'Customer Signature:', 0, 0)
    pdf.line(145, pdf.get_y() + 3, 190, pdf.get_y() + 3)  # Customer signature line
    
    pdf.set_xy(110, pdf.get_y() + 15)
    pdf.cell(30, 5, 'Contractor Signature:', 0, 0)
    
    # Add the contractor name in red and bold below the signature line
    pdf.set_xy(145, pdf.get_y() + 5)
    pdf.set_text_color(accent_color[0], accent_color[1], accent_color[2])
    pdf.set_font('DejaVu', 'B', 11)
    pdf.cell(45, 5, 'MAURICIO SANTOS', 0, 1)
    
    # Create a temporary file to store the PDF
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf_output = pdf.output(dest='S').encode('latin1')
    temp_file.write(pdf_output)
    temp_file.close()
    
    # Send the PDF file to the client
    return_value = send_file(
        temp_file.name,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'invoice_{invoice.id:03d}_{project.name.replace(" ", "_")}.pdf'
    )
    
    # Schedule the temp file for deletion
    @after_this_request
    def remove_file(response):
        try:
            os.unlink(temp_file.name)
        except:
            pass
        return response
    
    return return_value
