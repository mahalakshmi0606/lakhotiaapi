import sys
import os

# Add the current directory to sys.path so we can import 'app'
sys.path.append(os.getcwd())

try:
    from app import create_app, db
    from sqlalchemy import inspect
    
    app = create_app()
    with app.app_context():
        print("Checking database...")
        db.create_all()
        print("Tables created (if they didn't exist).")
        
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"Current tables in database: {tables}")
        
except Exception as e:
    import traceback
    print("Error occurred:")
    traceback.print_exc()
