from app import create_app, db
from app.models.purchaseorder import PurchaseOrder

app = create_app()
with app.app_context():
    pos = PurchaseOrder.query.all()
    for po in pos:
        print(f"PO: {po.po_number} | Status: {po.status} | Items: {len(po.items)} | Received Entries: {len(po.received_items)}")
