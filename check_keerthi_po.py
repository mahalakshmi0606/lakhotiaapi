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
            if item.get('item_name', '').lower() == 'keerthi':
                print(f"PO Number: {po.po_number}".encode('utf-8').decode('cp1252', 'ignore'))
                print(f"PO Status: {po.status}".encode('utf-8').decode('cp1252', 'ignore'))
                print(f"Ordered Qty (type {type(item.get('quantity'))}): {item.get('quantity')}")
                print(f"Item: {json.dumps(item)}".encode('utf-8').decode('cp1252', 'ignore'))
                
                # print received items for this PO
                print("Received items:")
                for r in po.received_items or []:
                    if r.get('item_index') == idx:
                        print(f" - {json.dumps(r)}".encode('utf-8').decode('cp1252', 'ignore'))
                        
                # Let's see what calculate_remaining_items_with_received does
                from app.routes.purchaseorder_routes import calculate_remaining_items_with_received
                items_with_delivery, _, _ = calculate_remaining_items_with_received(po)
                print(f"Calculated for idx {idx}:")
                print(f" -> {items_with_delivery[idx]}".encode('utf-8').decode('cp1252', 'ignore'))
                print("="*40)
