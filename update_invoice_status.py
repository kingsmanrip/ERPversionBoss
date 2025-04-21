from app import app, db
from models import Invoice, PaymentStatus

def update_invoice_statuses():
    """Update invoice statuses based on payment dates.
    
    If an invoice has a payment_received_date but is not marked as PAID,
    update its status to PAID.
    """
    with app.app_context():
        # Get all invoices with payment dates but not marked as PAID
        invoices_to_update = Invoice.query.filter(
            Invoice.payment_received_date.isnot(None),
            Invoice.status != PaymentStatus.PAID
        ).all()
        
        count = 0
        for invoice in invoices_to_update:
            invoice.status = PaymentStatus.PAID
            count += 1
            print(f"Updated invoice #{invoice.invoice_number} to PAID status")
        
        if count > 0:
            db.session.commit()
            print(f"Successfully updated {count} invoices to PAID status.")
        else:
            print("No invoices needed status updates.")

if __name__ == "__main__":
    update_invoice_statuses()
