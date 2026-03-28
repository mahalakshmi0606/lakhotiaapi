import os
import sys

# Add app directories to path
sys.path.append(r'e:\lakotia\lakhotiaapi')

from app import create_app, db
from app.models.purchaseorder import PurchaseOrder
import json

app = create_app()
with app.app_context():
    # Find the PO containing 'keerthi'
    pos = PurchaseOrder.query.all()
    results = []
    for po in pos:
        for idx, item in enumerate(po.items):
            if 'keerthi' in item.get('item_name', '').lower():
                from app.routes.purchaseorder_routes import calculate_remaining_items_with_received
                items_with_delivery, remaining_items, formatted_received = calculate_remaining_items_with_received(po)
                
                results.append({
                    "po_number": po.po_number,
                    "po_status": po.status,
                    "item": item,
                    "received_items": po.received_items,
                    "calculated_item": items_with_delivery[idx] if idx < len(items_with_delivery) else None,
                })
    
    with open('keerthi.json', 'w') as f:
        json.dump(results, f, indent=4)
