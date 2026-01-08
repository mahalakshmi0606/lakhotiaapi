from flask import Blueprint, request, jsonify
from datetime import datetime
from app import db
from app.models.grn import GRN
from app.models.purchaseorder import PurchaseOrder

grn_bp = Blueprint("grn_bp", __name__, url_prefix="/api/grn")


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
        
        return jsonify({
            "success": True,
            "data": {
                "po_number": po.po_number,
                "po_date": po.po_date.isoformat() if po.po_date else None,
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
def generate_batch_code(brand, po_number):
    if not brand:
        brand = "UNK"
    
    brand_code = brand[:3].upper()
    today = datetime.now()
    date_str = today.strftime("%Y%m%d")
    
    # Count existing batch codes with same brand and date
    count = GRN.query.filter(
        GRN.batch_code.like(f'{brand_code}-{date_str}-%')
    ).count()
    
    count += 1
    
    return f"{brand_code}-{date_str}-{str(count).zfill(3)}-{po_number[:5]}"


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
        
        # Generate invoice number
        invoice_number = generate_invoice_number()
        
        # Save each item
        saved_items = []
        for item in items:
            # Generate batch code
            batch_code = generate_batch_code(
                item.get("brand", ""),
                po_number
            )
            
            new_grn = GRN(
                po_number=po_number,
                invoice_number=invoice_number,
                invoice_date=datetime.now().strftime("%Y-%m-%d"),
                
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
                quantity=item.get("quantity"),
                buy_price=item.get("buy_price"),
                batch_code=batch_code
            )
            
            db.session.add(new_grn)
            saved_items.append({
                "item_name": item.get("item_name"),
                "batch_code": batch_code,
                "brand": item.get("brand")
            })
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"GRN created successfully! Invoice: {invoice_number}",
            "invoice_number": invoice_number,
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
        grn_list = GRN.query.order_by(GRN.id.desc()).all()
        
        result = []
        for g in grn_list:
            result.append({
                "id": g.id,
                "po_number": g.po_number,
                "invoice_number": g.invoice_number,
                "invoice_date": g.invoice_date,
                
                # Company details
                "company_name": g.company_name,
                "customer_name": g.customer_name,
                "gst_number": g.gst_number,
                
                # Item details
                "item_name": g.item_name,
                "brand": g.brand,
                "brand_code": g.brand_code,
                "brand_description": g.brand_description,
                "length": g.length,
                "width": g.width,
                "unit": g.unit,
                "quantity": g.quantity,
                "buy_price": g.buy_price,
                "batch_code": g.batch_code,
                
                "created_on": g.created_on.strftime("%Y-%m-%d %H:%M:%S") if g.created_on else None
            })
        
        return jsonify({"success": True, "data": result})
        
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
        for g in grn_items:
            result.append({
                "id": g.id,
                "po_number": g.po_number,
                "invoice_number": g.invoice_number,
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
                "buy_price": g.buy_price,
                "batch_code": g.batch_code,
                
                "created_on": g.created_on.strftime("%Y-%m-%d %H:%M:%S") if g.created_on else None
            })
        
        return jsonify({"success": True, "data": result})
        
    except Exception as e:
        print(f"Error loading GRN by invoice: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500