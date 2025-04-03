from app import app
from models import db

with app.app_context():
    # Create all tables but don't add any data
    db.create_all()
    print('Created empty database with schema only')
