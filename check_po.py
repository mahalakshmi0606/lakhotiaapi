from app import create_app, db
from app.models.purchaseorder import PurchaseOrder
import json

app = create_app()
with app.app_context():
    po = PurchaseOrder.query.filter_by(po_number='PO-202603-002').first()
    if po:
        print(f"PO Number: {po.po_number}")
        print(f"Status: {po.status}")
        print(f"Items (JSON): {json.dumps(po.items, indent=2)}")
        print(f"Received Items (JSON): {json.dumps(po.received_items, indent=2)}")
    else:
        print("PO not found")
