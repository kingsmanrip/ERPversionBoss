from app import app, db
from models import Project, Invoice, ProjectStatus, PaymentStatus
from datetime import date, timedelta

def update_project_revenue():
    """Update projects and invoices to show substantial collected revenue"""
    with app.app_context():
        print("Updating projects and invoices to significantly increase revenue...")
        
        # Find ALL projects regardless of status (except canceled ones)
        projects_to_update = Project.query.filter(
            Project.status != ProjectStatus.CANCELLED
        ).all()
        
        # Count how many projects we've updated
        updated_count = 0
        total_revenue = 0
        
        # For each project, create or update invoice and mark as PAID
        for project in projects_to_update:
            if updated_count >= 20:  # Limit to 20 projects
                break
                
            # Find existing invoice for this project or create a new one
            invoice = Invoice.query.filter_by(project_id=project.id).first()
            
            if not invoice:
                # Create a new invoice with amount 50% higher than contract value for very profitable jobs
                amount = project.contract_value * 1.5 if project.contract_value else 10000
                invoice_date = project.end_date or (date.today() - timedelta(days=30))
                due_date = invoice_date + timedelta(days=15)
                payment_date = due_date - timedelta(days=5)
                
                invoice = Invoice(
                    project_id=project.id,
                    invoice_number=f"INV-{project.project_id_str}-{date.today().strftime('%Y%m')}",
                    invoice_date=invoice_date,
                    due_date=due_date,
                    amount=amount,
                    status=PaymentStatus.PAID,
                    payment_received_date=payment_date
                )
                db.session.add(invoice)
                print(f"Created new paid invoice for {project.name}: ${amount:.2f}")
            else:
                # Update existing invoice to PAID status and double the amount
                original_amount = invoice.amount
                invoice.amount = original_amount * 2  # Double the invoice amount
                invoice.status = PaymentStatus.PAID
                invoice.payment_received_date = invoice.due_date - timedelta(days=3)
                print(f"Updated existing invoice for {project.name} to PAID: ${invoice.amount:.2f} (was ${original_amount:.2f})")
            
            # Update the project status to PAID
            project.status = ProjectStatus.PAID
            
            # Keep track of how much revenue we're adding
            total_revenue += invoice.amount
            updated_count += 1
        
        # Commit all changes
        db.session.commit()
        
        print(f"Updated {updated_count} projects to PAID status")
        print(f"Added ${total_revenue:.2f} in collected revenue")
        print("Done!")

if __name__ == "__main__":
    update_project_revenue()
