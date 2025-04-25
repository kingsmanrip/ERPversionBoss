# Mauricio PDQ ERP System - Deployment Guide

This guide will help you deploy the Mauricio PDQ ERP System on a new server or PC. The application has been updated with enhanced invoice functionality, including separate base and tax amount fields and per-invoice descriptions.

## System Requirements

- Ubuntu Linux (or compatible Linux distribution)
- Python 3.7 or higher
- Git (for cloning the repository)
- Nginx (for production deployment)

## Step 1: Clone the Repository

```bash
git clone https://github.com/kingsmanrip/finalERP.git
cd finalERP
```

Alternatively, if you're transferring from the backup:

```bash
# On the source server (where the backup was created)
tar -czvf finalERP_backup.tar.gz finalERP

# Transfer the file to the new server (using scp, rsync, or any transfer method)
scp finalERP_backup.tar.gz user@newserver:/path/to/destination

# On the new server
tar -xzvf finalERP_backup.tar.gz
cd finalERP
```

## Step 2: Set Up a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
pip install bootstrap-flask==2.3.0 flask-excel gunicorn
```

## Step 4: Initialize the Database

```bash
python init_db.py
```

## Step 5: Create an Admin User

```bash
python create_admin.py
# This creates a user with:
# - Username: admin
# - Password: mauriciopdq
```

## Step 6: Generate Sample Data (Optional)

```bash
python generate_mock_data.py
```

## Step 7: Run the Application

### For Development/Testing

```bash
python app.py
```

### For Production with Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## Step 8: Configure Nginx for Production (Optional)

Create an Nginx configuration file:

```bash
sudo nano /etc/nginx/sites-available/mauriciopdq.site
```

Add the following content:

```nginx
server {
    listen 80;
    server_name mauriciopdq.site www.mauriciopdq.site;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/mauriciopdq.site /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Step 9: Set Up a Systemd Service for Automatic Startup (Optional)

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/finalerp.service
```

Add the following content (adjust paths as needed):

```ini
[Unit]
Description=Mauricio PDQ ERP Gunicorn Service
After=network.target

[Service]
User=root  # Change to appropriate user
Group=root  # Change to appropriate group
WorkingDirectory=/root/finalERP
Environment="PATH=/root/finalERP/venv/bin"
ExecStart=/root/finalERP/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable finalerp
sudo systemctl start finalerp
```

## Recent Updates (April 21, 2025)

### Employee Management Improvements
- Fixed employee deletion functionality to properly handle related records
- Added cascade deletion for timesheet and payroll payment records 
- Added script for importing actual employee data (`add_real_employees.py`)
- Fixed database relationships for better data integrity

### Database Changes
If you're updating from an older version, make sure to run these scripts:

```bash
python fix_employee_delete.py  # Fixes employee deletion issue
python add_real_employees.py   # Imports actual employee data (optional)
python migrate_invoice_amounts.py
python update_invoice_status.py
```

### Invoice System Enhancements
- Added support for creating invoices for IN_PROGRESS projects
- Added invoice editing functionality via Edit button
- Implemented automatic status updates for invoices with payment dates
- Added validation to ensure payment dates and statuses are synchronized
- Fixed issue where invoices with payment dates remained in PENDING status

### Previous Updates (April 15, 2025)

### Invoice System Enhancements
- Added separate Base Amount and Tax Amount fields
- Added automatic calculation of the total amount
- Added per-invoice description field
- Updated PDF generation to match the required format

### Database Changes
If you're updating from an older version, make sure to run these migration scripts:

```bash
python migrate_invoice_description.py
python migrate_invoice_amounts.py
```

## Troubleshooting

### Common Issues

1. **Database Errors**:
   - Check that the database file exists in the instance directory
   - Run `python init_db.py` to initialize the database

2. **Missing Dependencies**:
   - Ensure you've installed all dependencies with `pip install -r requirements.txt`
   - Make sure to install bootstrap-flask version 2.3.0 specifically

3. **Port Already in Use**:
   - If port 8000 is already in use, change the port in the gunicorn command
   - Update the Nginx configuration to match the new port

4. **Permission Issues**:
   - Ensure proper directory permissions for the application files
   - Check that the user running the application has write access to the instance folder

## Support

For questions or issues, please contact the development team or submit an issue through GitHub.

## System Testing and Production Readiness

As of April 25, 2025, the Mauricio PDQ ERP system has undergone comprehensive testing and is considered production-ready:

### Components Tested

1. **Payroll System**
   - Confirmed lunch break calculations function correctly:
     - Lunch < 30 min: No deduction
     - Lunch 30-59 min: Full break time deducted
     - Lunch ≥ 60 min: Only 30 minutes deducted
   - Verified Saturday premium ($5/hour) is applied correctly
   - Validated payroll deduction calculations

2. **Project Management**
   - Confirmed date validation works correctly
   - Verified project financial calculations (labor cost, material cost, profit)
   - Tested all status transitions
   - Validated relationships with timesheets, materials, expenses, and invoices

3. **Invoice System**
   - Confirmed proper PDF generation
   - Tested invoice creation, editing, and deletion
   - Verified proper relationship with projects

### System Reliability

The system has been thoroughly tested and is stable for daily business operations. The current production deployment at https://mauriciopdq.site/ reflects all tested functionality and is recommended for regular use by the business.

### Future Enhancements

While the system is production-ready, consider these future improvements:
- Migrating from SQLite to a more robust database for larger dataset handling
- Upgrading from Flask's development server to Gunicorn/uWSGI for better performance
- Implementing automated backup procedures
- Adding more comprehensive reporting features

---

Maintained by Mauricio PDQ Paint & Drywall (2025)
