from app import create_app, db
from app.models.purchaseorder import PurchaseOrder

app = create_app()
with app.app_context():
    pos = PurchaseOrder.query.all()
    for po in pos:
        items = po.items or []
        received_items = po.received_items or []
        total_ordered = sum(float(item.get('quantity', 0)) for item in items)
        total_received = sum(float(ri.get('received_quantity', 0)) for ri in received_items)
        print(f"PO: {po.po_number} | Ordered Qty: {total_ordered} | Received Qty: {total_received} | Items: {len(items)}")
