from flask import Blueprint, request, jsonify
from datetime import datetime
from app import db
from app.models.grn import GRN
from app.models.purchaseorder import PurchaseOrder

grn_bp = Blueprint("grn_bp", __name__, url_prefix="/api/grn")


# -------------------------------------------------------------------
# GET COMPLETED PURCHASE ORDERS
# -------------------------------------------------------------------
@grn_bp.route("/completed-po", methods=["GET"])
def get_completed_po():
    try:
        # Get only completed purchase orders
        completed_orders = PurchaseOrder.query.filter(
            PurchaseOrder.status == 'completed'
        ).order_by(PurchaseOrder.created_on.desc()).all()
        
        # Format the data
        orders_data = []
        for po in completed_orders:
            po_dict = po.to_dict()
            # Check if GRN already exists for this PO
            existing_grn = GRN.query.filter_by(po_number=po.po_number).first()
            po_dict['has_grn'] = existing_grn is not None
            po_dict['grn_invoice'] = existing_grn.invoice_number if existing_grn else None
            orders_data.append(po_dict)
        
        return jsonify({
            'success': True,
            'count': len(orders_data),
            'data': orders_data
        }), 200
        
    except Exception as e:
        print(f"Error fetching completed POs: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# -------------------------------------------------------------------
# GET PURCHASE ORDER DETAILS BY PO NUMBER
# -------------------------------------------------------------------
@grn_bp.route("/get-po/<string:po_number>", methods=["GET"])
def get_purchase_order_details(po_number):
    try:
        # Find purchase order by PO number
        po = PurchaseOrder.query.filter_by(po_number=po_number).first()
        
        if not po:
            return jsonify({"success": False, "message": "Purchase Order not found"}), 404
        
        # Check if PO is completed
        if po.status != 'completed':
            return jsonify({
                "success": False, 
                "message": f"Purchase Order status is '{po.status}', only completed POs can be converted to GRN"
            }), 400
        
        # Check if GRN already exists
        existing_grn = GRN.query.filter_by(po_number=po_number).first()
        if existing_grn:
            return jsonify({
                "success": False, 
                "message": f"GRN already exists for this PO (Invoice: {existing_grn.invoice_number})"
            }), 400
        
        return jsonify({
            "success": True,
            "data": {
                "po_number": po.po_number,
                "po_date": po.po_date.isoformat() if po.po_date and isinstance(po.po_date, datetime) else po.po_date,
                "company_name": po.company_name,
                "company_address": po.company_address,
                "customer_name": po.customer_name,
                "customer_mobile": po.customer_mobile,
                "customer_email": po.customer_email,
                "department": po.department,
                "gst_number": po.gst_number,
                "supplier_part_no": po.supplier_part_no,
                "supplier_description": po.supplier_description,
                "items": po.items if po.items else [],
                "total_amount": float(po.total_amount) if po.total_amount else 0.0,
                "status": po.status
            }
        })
        
    except Exception as e:
        print(f"Error fetching PO details: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------------------------------------------
# GENERATE INVOICE NUMBER
# -------------------------------------------------------------------
def generate_invoice_number():
    today = datetime.now()
    year_month = today.strftime("%Y%m")  # YYYYMM
    
    # Find latest invoice for this month
    latest_invoice = (
        GRN.query
        .filter(GRN.invoice_number.like(f'INV-{year_month}-%'))
        .order_by(GRN.created_on.desc())
        .first()
    )
    
    if latest_invoice and latest_invoice.invoice_number:
        try:
            last_seq = int(latest_invoice.invoice_number.split('-')[-1])
            sequence = last_seq + 1
        except ValueError:
            sequence = 1
    else:
        sequence = 1
    
    return f"INV-{year_month}-{str(sequence).zfill(3)}"


# -------------------------------------------------------------------
# GENERATE BATCH CODE
# -------------------------------------------------------------------
def generate_batch_code(brand, po_number, date_str=None):
    if not brand:
        brand = "UNK"
    
    brand_code = brand[:3].upper()
    today = datetime.now()
    if not date_str:
        date_str = today.strftime("%Y%m%d")
    
    # Count existing batch codes with same brand and date
    count = GRN.query.filter(
        GRN.batch_code.like(f'{brand_code}-{date_str}-%')
    ).count()
    
    count += 1
    
    return f"{brand_code}-{date_str}-{str(count).zfill(3)}"


# -------------------------------------------------------------------
# SAVE **MULTIPLE** GRN ITEMS FROM PURCHASE ORDER
# -------------------------------------------------------------------
@grn_bp.route("/save-from-po", methods=["POST"])
def save_grn_from_po():
    try:
        data = request.get_json()
        
        # Required fields
        po_number = data.get("po_number")
        items = data.get("items", [])
        
        if not po_number:
            return jsonify({"success": False, "message": "PO Number is required"}), 400
            
        if not items or not isinstance(items, list):
            return jsonify({"success": False, "message": "No items provided"}), 400
        
        # Get PO details
        po = PurchaseOrder.query.filter_by(po_number=po_number).first()
        if not po:
            return jsonify({"success": False, "message": "Purchase Order not found"}), 404
        
        # Check if PO is completed
        if po.status != 'completed':
            return jsonify({
                "success": False, 
                "message": f"Cannot create GRN for PO with status '{po.status}', only completed POs allowed"
            }), 400
        
        # Check if GRN already exists for this PO
        existing_grn = GRN.query.filter_by(po_number=po_number).first()
        if existing_grn:
            return jsonify({
                "success": False, 
                "message": f"GRN already exists for this PO (Invoice: {existing_grn.invoice_number})"
            }), 400
        
        # Validate batch codes are unique
        batch_codes = [item.get('batch_code') for item in items if item.get('batch_code')]
        if len(batch_codes) != len(set(batch_codes)):
            return jsonify({
                "success": False, 
                "message": "Duplicate batch codes detected! Please ensure all batch codes are unique."
            }), 400
        
        # Generate invoice number
        invoice_number = generate_invoice_number()
        today_date = datetime.now().date()
        invoice_date_str = today_date.strftime("%Y-%m-%d")  # Store as string
        
        # Save each item
        saved_items = []
        for item in items:
            # Use provided batch code or generate new one
            batch_code = item.get('batch_code')
            if not batch_code or batch_code.strip() == '':
                batch_code = generate_batch_code(
                    item.get("brand", ""),
                    po_number,
                    today_date.strftime("%Y%m%d")
                )
            
            # Validate batch code doesn't already exist
            existing_batch = GRN.query.filter_by(batch_code=batch_code).first()
            if existing_batch:
                return jsonify({
                    "success": False, 
                    "message": f"Batch code '{batch_code}' already exists! Please use a unique batch code."
                }), 400
            
            new_grn = GRN(
                po_number=po_number,
                invoice_number=invoice_number,
                invoice_date=invoice_date_str,  # Store as string
                
                # Company details from PO
                company_name=po.company_name,
                company_address=po.company_address,
                customer_name=po.customer_name,
                customer_mobile=po.customer_mobile,
                customer_email=po.customer_email,
                department=po.department,
                gst_number=po.gst_number,
                supplier_part_no=po.supplier_part_no,
                supplier_description=po.supplier_description,
                
                # Item details
                item_name=item.get("item_name"),
                brand=item.get("brand"),
                brand_code=item.get("brand_code"),
                brand_description=item.get("brand_description"),
                length=item.get("length"),
                width=item.get("width"),
                unit=item.get("unit", "PCS"),
                quantity=float(item.get("quantity", 0)),
                buy_price=float(item.get("buy_price", 0)),
                batch_code=batch_code
            )
            
            db.session.add(new_grn)
            saved_items.append({
                "item_name": item.get("item_name"),
                "batch_code": batch_code,
                "brand": item.get("brand"),
                "quantity": item.get("quantity"),
                "buy_price": item.get("buy_price")
            })
        
        # Update PO status to indicate GRN created
        po.status = 'converted_to_grn'
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"GRN created successfully! Invoice: {invoice_number}",
            "invoice_number": invoice_number,
            "invoice_date": invoice_date_str,
            "items_count": len(saved_items),
            "items": saved_items
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error saving GRN from PO: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------------------------------------------
# GET ALL GRN RECORDS
# -------------------------------------------------------------------
@grn_bp.route("/all", methods=["GET"])
def get_all_grn():
    try:
        grn_list = GRN.query.order_by(GRN.created_on.desc()).all()
        
        result = []
        for g in grn_list:
            result.append({
                "id": g.id,
                "po_number": g.po_number,
                "invoice_number": g.invoice_number,
                # FIX: invoice_date is a string, not a datetime
                "invoice_date": g.invoice_date,
                
                # Company details
                "company_name": g.company_name,
                "company_address": g.company_address,
                "customer_name": g.customer_name,
                "customer_mobile": g.customer_mobile,
                "customer_email": g.customer_email,
                "department": g.department,
                "gst_number": g.gst_number,
                "supplier_part_no": g.supplier_part_no,
                "supplier_description": g.supplier_description,
                
                # Item details
                "item_name": g.item_name,
                "brand": g.brand,
                "brand_code": g.brand_code,
                "brand_description": g.brand_description,
                "length": g.length,
                "width": g.width,
                "unit": g.unit,
                "quantity": g.quantity,
                "buy_price": float(g.buy_price) if g.buy_price else 0.0,
                "batch_code": g.batch_code,
                
                "created_on": g.created_on.strftime("%Y-%m-%d %H:%M:%S") if g.created_on else None
            })
        
        return jsonify({"success": True, "count": len(result), "data": result})
        
    except Exception as e:
        print(f"Error loading GRN list: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------------------------------------------
# GET GRN BY INVOICE NUMBER
# -------------------------------------------------------------------
@grn_bp.route("/invoice/<string:invoice_number>", methods=["GET"])
def get_grn_by_invoice(invoice_number):
    try:
        grn_items = GRN.query.filter_by(invoice_number=invoice_number).all()
        
        if not grn_items:
            return jsonify({"success": False, "message": "Invoice not found"}), 404
        
        result = []
        total_amount = 0.0
        for g in grn_items:
            item_total = g.quantity * (float(g.buy_price) if g.buy_price else 0)
            total_amount += item_total
            
            result.append({
                "id": g.id,
                "po_number": g.po_number,
                "invoice_number": g.invoice_number,
                # FIX: invoice_date is a string
                "invoice_date": g.invoice_date,
                
                # Company details
                "company_name": g.company_name,
                "company_address": g.company_address,
                "customer_name": g.customer_name,
                "customer_mobile": g.customer_mobile,
                "customer_email": g.customer_email,
                "department": g.department,
                "gst_number": g.gst_number,
                "supplier_part_no": g.supplier_part_no,
                "supplier_description": g.supplier_description,
                
                # Item details
                "item_name": g.item_name,
                "brand": g.brand,
                "brand_code": g.brand_code,
                "brand_description": g.brand_description,
                "length": g.length,
                "width": g.width,
                "unit": g.unit,
                "quantity": g.quantity,
                "buy_price": float(g.buy_price) if g.buy_price else 0.0,
                "item_total": item_total,
                "batch_code": g.batch_code,
                
                "created_on": g.created_on.strftime("%Y-%m-%d %H:%M:%S") if g.created_on else None
            })
        
        return jsonify({
            "success": True, 
            "count": len(result),
            "total_amount": total_amount,
            "data": result
        })
        
    except Exception as e:
        print(f"Error loading GRN by invoice: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------------------------------------------
# GET DISTINCT INVOICE NUMBERS
# -------------------------------------------------------------------
@grn_bp.route("/invoices", methods=["GET"])
def get_invoice_numbers():
    try:
        # Get distinct invoice numbers
        invoices = db.session.query(
            GRN.invoice_number,
            GRN.invoice_date,
            GRN.po_number,
            db.func.count(GRN.id).label('item_count'),
            db.func.sum(GRN.quantity * GRN.buy_price).label('total_amount')
        ).group_by(
            GRN.invoice_number, 
            GRN.invoice_date, 
            GRN.po_number
        ).order_by(GRN.created_on.desc()).all()
        
        result = []
        for inv in invoices:
            # Get company name from first item
            first_item = GRN.query.filter_by(
                invoice_number=inv.invoice_number
            ).first()
            
            result.append({
                "invoice_number": inv.invoice_number,
                # FIX: invoice_date is a string
                "invoice_date": inv.invoice_date,
                "po_number": inv.po_number,
                "company_name": first_item.company_name if first_item else "",
                "customer_name": first_item.customer_name if first_item else "",
                "item_count": inv.item_count,
                "total_amount": float(inv.total_amount) if inv.total_amount else 0.0
            })
        
        return jsonify({
            "success": True, 
            "count": len(result),
            "data": result
        })
        
    except Exception as e:
        print(f"Error loading invoice list: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------------------------------------------
# UPDATE GRN ITEM
# -------------------------------------------------------------------
@grn_bp.route("/update/<int:grn_id>", methods=["PUT"])
def update_grn_item(grn_id):
    try:
        data = request.get_json()
        
        grn_item = GRN.query.get(grn_id)
        if not grn_item:
            return jsonify({"success": False, "message": "GRN item not found"}), 404
        
        # Update fields
        update_fields = [
            'invoice_number', 'invoice_date', 'brand', 'brand_code', 
            'brand_description', 'length', 'width', 'buy_price', 
            'batch_code', 'quantity', 'unit'
        ]
        
        for field in update_fields:
            if field in data:
                setattr(grn_item, field, data[field])
        
        # Validate batch code uniqueness
        if 'batch_code' in data:
            existing_batch = GRN.query.filter(
                GRN.batch_code == data['batch_code'],
                GRN.id != grn_id
            ).first()
            if existing_batch:
                return jsonify({
                    "success": False, 
                    "message": f"Batch code '{data['batch_code']}' already exists"
                }), 400
        
        # Validate invoice date format if provided
        if 'invoice_date' in data:
            try:
                # Try to parse to ensure it's a valid date
                datetime.strptime(data['invoice_date'], '%Y-%m-%d')
            except ValueError:
                return jsonify({
                    "success": False, 
                    "message": "Invalid invoice date format. Use YYYY-MM-DD"
                }), 400
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "GRN item updated successfully",
            "data": grn_item.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating GRN item: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------------------------------------------
# DELETE GRN ITEM
# -------------------------------------------------------------------
@grn_bp.route("/delete/<int:grn_id>", methods=["DELETE"])
def delete_grn_item(grn_id):
    try:
        grn_item = GRN.query.get(grn_id)
        if not grn_item:
            return jsonify({"success": False, "message": "GRN item not found"}), 404
        
        # Check if this is the only item in the invoice
        invoice_items = GRN.query.filter_by(
            invoice_number=grn_item.invoice_number
        ).count()
        
        invoice_number = grn_item.invoice_number
        po_number = grn_item.po_number
        
        db.session.delete(grn_item)
        
        # If this was the last item, revert PO status
        if invoice_items == 1:
            po = PurchaseOrder.query.filter_by(
                po_number=po_number
            ).first()
            if po and po.status == 'converted_to_grn':
                po.status = 'completed'
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"GRN item deleted successfully. Invoice {invoice_number} updated."
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting GRN item: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------------------------------------------
# GET GRN STATISTICS
# -------------------------------------------------------------------
@grn_bp.route("/stats", methods=["GET"])
def get_grn_statistics():
    try:
        # Total GRN records
        total_count = GRN.query.count()
        
        # Total invoices
        invoice_count = db.session.query(
            db.func.count(db.func.distinct(GRN.invoice_number))
        ).scalar()
        
        # Total amount
        total_amount_result = db.session.query(
            db.func.sum(GRN.quantity * GRN.buy_price)
        ).scalar()
        total_amount = float(total_amount_result) if total_amount_result else 0.0
        
        # Today's GRN
        today = datetime.now().date()
        today_count = GRN.query.filter(
            db.func.date(GRN.created_on) == today
        ).count()
        
        # This month's GRN
        current_month = datetime.now().month
        current_year = datetime.now().year
        month_count = GRN.query.filter(
            db.extract('month', GRN.created_on) == current_month,
            db.extract('year', GRN.created_on) == current_year
        ).count()
        
        return jsonify({
            "success": True,
            "data": {
                "total_grn_items": total_count,
                "total_invoices": invoice_count,
                "total_amount": total_amount,
                "today_count": today_count,
                "month_count": month_count
            }
        })
        
    except Exception as e:
        print(f"Error loading GRN statistics: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------------------------------------------
# SEARCH GRN
# -------------------------------------------------------------------
@grn_bp.route("/search", methods=["GET"])
def search_grn():
    try:
        search_term = request.args.get('q', '')
        
        if not search_term:
            return jsonify({"success": False, "message": "Search term required"}), 400
        
        # Search in multiple fields
        results = GRN.query.filter(
            db.or_(
                GRN.invoice_number.ilike(f'%{search_term}%'),
                GRN.po_number.ilike(f'%{search_term}%'),
                GRN.company_name.ilike(f'%{search_term}%'),
                GRN.customer_name.ilike(f'%{search_term}%'),
                GRN.item_name.ilike(f'%{search_term}%'),
                GRN.batch_code.ilike(f'%{search_term}%'),
                GRN.brand.ilike(f'%{search_term}%')
            )
        ).order_by(GRN.created_on.desc()).limit(50).all()
        
        result_data = []
        for g in results:
            result_data.append({
                "id": g.id,
                "po_number": g.po_number,
                "invoice_number": g.invoice_number,
                "invoice_date": g.invoice_date,  # Already a string
                "company_name": g.company_name,
                "customer_name": g.customer_name,
                "item_name": g.item_name,
                "brand": g.brand,
                "batch_code": g.batch_code,
                "quantity": g.quantity,
                "buy_price": float(g.buy_price) if g.buy_price else 0.0,
                "created_on": g.created_on.strftime("%Y-%m-%d") if g.created_on else None
            })
        
        return jsonify({
            "success": True,
            "count": len(result_data),
            "data": result_data
        })
        
    except Exception as e:
        print(f"Error searching GRN: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500