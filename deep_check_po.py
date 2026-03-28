from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    result = db.session.execute(text("SELECT * FROM purchase_orders WHERE po_number = 'PO-202603-002'"))
    row = result.fetchone()
    if row:
        columns = result.keys()
        for i, val in enumerate(row):
            print(f"{columns[i]}: {val}")
    else:
        print("PO not found")
