from app import app, db
from models import Project, Invoice, ProjectStatus, PaymentStatus
from datetime import date, timedelta
import random

def add_unpaid_invoices():
    """Add 3 low-cost unpaid invoices to the system"""
    with app.app_context():
        print("Adding low-cost unpaid invoices...")
        
        # Find projects that don't have invoices yet
        all_projects = Project.query.all()
        projects_without_invoices = []
        
        for project in all_projects:
            if not Invoice.query.filter_by(project_id=project.id).first():
                projects_without_invoices.append(project)
        
        # If we don't have enough projects without invoices, we can create duplicates 
        # for existing projects that don't already have unpaid invoices
        if len(projects_without_invoices) < 3:
            for project in all_projects:
                has_unpaid = False
                for invoice in Invoice.query.filter_by(project_id=project.id).all():
                    if invoice.status != PaymentStatus.PAID:
                        has_unpaid = True
                        break
                
                if not has_unpaid:
                    projects_without_invoices.append(project)
        
        # Limit to 3 projects
        projects_to_use = projects_without_invoices[:3]
        
        invoice_count = 0
        for project in projects_to_use:
            # Set a low cost for these invoices
            amount = random.uniform(500, 1200)
            
            # Set dates
            invoice_date = date.today() - timedelta(days=random.randint(15, 30))
            due_date = invoice_date + timedelta(days=30)
            
            # Status - mix of pending and overdue
            if random.random() < 0.5:
                status = PaymentStatus.PENDING
            else:
                status = PaymentStatus.OVERDUE
            
            # Create the invoice
            invoice = Invoice(
                project_id=project.id,
                invoice_number=f"INV-{project.project_id_str}-UNPD-{invoice_count+1}",
                invoice_date=invoice_date,
                due_date=due_date,
                amount=amount,
                status=status,
                payment_received_date=None
            )
            
            db.session.add(invoice)
            
            print(f"Created unpaid invoice for {project.name}: ${amount:.2f} ({status.value})")
            invoice_count += 1
        
        # Commit all changes
        db.session.commit()
        
        print(f"Added {invoice_count} unpaid invoices")
        print("Done!")

if __name__ == "__main__":
    add_unpaid_invoices()
