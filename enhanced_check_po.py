from app import create_app, db
from app.models.purchaseorder import PurchaseOrder
import json

app = create_app()
with app.app_context():
    po = PurchaseOrder.query.filter_by(po_number='PO-202603-002').first()
    if po:
        print(f"PO Number: {po.po_number}")
        print(f"Total Items in PO: {len(po.items)}")
        for i, item in enumerate(po.items):
            print(f"  Item {i}: {item.get('item_name')} - Qty: {item.get('quantity')}")
        
        print(f"Received Items Entries: {len(po.received_items)}")
        for i, ri in enumerate(po.received_items):
            print(f"  Received Entry {i}: Index {ri.get('item_index')} - Qty: {ri.get('received_quantity')}")
    else:
        print("PO not found")
