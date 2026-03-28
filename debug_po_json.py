from app import create_app, db
from app.models.purchaseorder import PurchaseOrder
import json

app = create_app()
with app.app_context():
    po = PurchaseOrder.query.filter_by(po_number='PO-202603-002').first()
    output = ""
    if po:
        output += "PO ITEMS:\n"
        output += json.dumps(po.items, indent=2)
        output += "\nRECEIVED ITEMS:\n"
        output += json.dumps(po.received_items, indent=2)
    else:
        output = "PO not found"
    
    with open("po_debug_output.txt", "w") as f:
        f.write(output)
