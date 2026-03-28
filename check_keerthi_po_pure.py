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
    for po in pos:
        for idx, item in enumerate(po.items):
            if 'keerthi' in item.get('item_name', '').lower():
                print(f"PO Number: {po.po_number}")
                print(f"PO Status: {po.status}")
                print(f"Ordered Qty (type {type(item.get('quantity'))}): {item.get('quantity')}")
                # print item without unicode issues
                item_str = json.dumps(item)
                print(f"Item: {item_str.encode('ascii', 'ignore').decode('ascii')}")
                
                # print received items for this PO
                print("Received items:")
                for r in po.received_items or []:
                    if r.get('item_index') == idx:
                        r_str = json.dumps(r)
                        print(f" - {r_str.encode('ascii', 'ignore').decode('ascii')}")
                        
                # Let's see what calculate_remaining_items_with_received does
                from app.routes.purchaseorder_routes import calculate_remaining_items_with_received
                items_with_delivery, _, _ = calculate_remaining_items_with_received(po)
                print(f"Calculated for idx {idx}:")
                calc_str = str(items_with_delivery[idx])
                print(f" -> {calc_str.encode('ascii', 'ignore').decode('ascii')}")
                print("="*40)
