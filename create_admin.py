import sys
import os

# Add the current directory to sys.path so we can import 'app'
sys.path.append(os.getcwd())

from app import create_app, db
from app.models.login import User

app = create_app()
with app.app_context():
    # Check if admin already exists
    admin = User.query.filter_by(email='admin@lakhotia.com').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@lakhotia.com',
            password='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created: admin@lakhotia.com / admin")
    else:
        print("Admin user already exists.")
