from flask import Blueprint, request, jsonify
from datetime import datetime, date, timedelta
from app import db
from app.models.purchaseorder import PurchaseOrder

purchase_order_bp = Blueprint('purchase_orders', __name__)

VALID_STATUSES = ['pending', 'approved', 'rejected', 'completed']


# ---------------------------
# Helper: Generate PO Number
# ---------------------------
def generate_po_number():
    today = datetime.now()
    year_month = today.strftime("%Y%m")  # YYYYMM

    latest_po = (
        PurchaseOrder.query
        .filter(PurchaseOrder.po_number.like(f'PO-{year_month}-%'))
        .order_by(PurchaseOrder.created_on.desc())
        .first()
    )

    if latest_po and latest_po.po_number:
        try:
            last_seq = int(latest_po.po_number.split('-')[-1])
            sequence = last_seq + 1
        except ValueError:
            sequence = 1
    else:
        sequence = 1

    return f"PO-{year_month}-{str(sequence).zfill(3)}"


# ---------------------------
# Create Purchase Order
# ---------------------------
@purchase_order_bp.route('/create', methods=['POST'])
def create_purchase_order():
    try:
        data = request.get_json() or {}

        # Required fields
        if not data.get('company_name'):
            return jsonify({'success': False, 'error': 'Company Name is required'}), 400
            
        if not data.get('customer_name'):
            return jsonify({'success': False, 'error': 'Customer Name is required'}), 400

        items = data.get('items')
        if not isinstance(items, list) or not items:
            return jsonify({'success': False, 'error': 'At least one item is required'}), 400

        # Calculate total amount
        total_amount = 0.0
        for item in items:
            quantity = float(item.get('quantity', 0))
            buy_price = float(item.get('buy_price', 0))
            total_amount += quantity * buy_price

        po_number = generate_po_number()

        po_date = (
            datetime.strptime(data['po_date'], '%Y-%m-%d').date()
            if data.get('po_date') else date.today()
        )

        # Handle delivery date (optional)
        delivery_date = None
        if data.get('delivery_date'):
            delivery_date = datetime.strptime(data['delivery_date'], '%Y-%m-%d').date()

        status = data.get('status', 'pending')
        if status not in VALID_STATUSES:
            return jsonify({
                'success': False,
                'error': f'Status must be one of {", ".join(VALID_STATUSES)}'
            }), 400

        new_po = PurchaseOrder(
            po_number=po_number,
            po_date=po_date,
            company_id=data.get('company_id'),
            company_name=data['company_name'],
            company_address=data.get('company_address'),
            customer_name=data['customer_name'],
            customer_mobile=data.get('customer_mobile'),
            customer_email=data.get('customer_email'),
            department=data.get('department'),
            gst_number=data.get('gst_number'),
            supplier_part_no=data.get('supplier_part_no'),
            supplier_description=data.get('supplier_description'),
            delivery_date=delivery_date,
            status=status,
            items=items,
            total_amount=total_amount
        )

        db.session.add(new_po)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Purchase Order created successfully',
            'data': new_po.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Error creating purchase order: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ---------------------------
# Get All Purchase Orders
# ---------------------------
@purchase_order_bp.route('/all', methods=['GET'])
def get_all_purchase_orders():
    try:
        status = request.args.get('status')

        query = PurchaseOrder.query
        if status and status != 'all':
            query = query.filter(PurchaseOrder.status == status)

        purchase_orders = query.order_by(PurchaseOrder.created_on.desc()).all()

        return jsonify({
            'success': True,
            'count': len(purchase_orders),
            'data': [po.to_dict() for po in purchase_orders]
        }), 200

    except Exception as e:
        print(f"Error getting purchase orders: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ---------------------------
# Update PO Status (with remarks)
# ---------------------------
@purchase_order_bp.route('/update-status/<int:po_id>', methods=['PUT'])
def update_purchase_order_status(po_id):
    try:
        data = request.get_json() or {}
        new_status = data.get('status')
        approval_remarks = data.get('approval_remarks')
        rejection_remarks = data.get('rejection_remarks')

        if new_status not in VALID_STATUSES:
            return jsonify({
                'success': False,
                'error': f'Status must be one of {", ".join(VALID_STATUSES)}'
            }), 400

        purchase_order = PurchaseOrder.query.get(po_id)
        if not purchase_order:
            return jsonify({'success': False, 'error': 'Purchase Order not found'}), 404

        purchase_order.status = new_status
        
        # Handle approval
        if new_status == 'approved':
            purchase_order.approval_remarks = approval_remarks
            purchase_order.approved_date = datetime.utcnow()
            purchase_order.rejection_remarks = None
            purchase_order.rejected_date = None
        
        # Handle rejection
        elif new_status == 'rejected':
            purchase_order.rejection_remarks = rejection_remarks
            purchase_order.rejected_date = datetime.utcnow()
            purchase_order.approval_remarks = None
            purchase_order.approved_date = None
        
        # Handle completion or reset to pending
        else:
            if new_status == 'pending':
                purchase_order.approval_remarks = None
                purchase_order.approved_date = None
                purchase_order.rejection_remarks = None
                purchase_order.rejected_date = None
            elif new_status == 'completed':
                # Keep existing approval remarks for completed orders
                pass

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Status updated to {new_status}',
            'data': purchase_order.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error updating status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ---------------------------
# Update Purchase Order
# ---------------------------
@purchase_order_bp.route('/update/<int:po_id>', methods=['PUT'])
def update_purchase_order(po_id):
    try:
        data = request.get_json() or {}
        purchase_order = PurchaseOrder.query.get(po_id)

        if not purchase_order:
            return jsonify({'success': False, 'error': 'Purchase Order not found'}), 404

        # Only allow updates if status is pending
        if purchase_order.status != 'pending':
            return jsonify({
                'success': False,
                'error': f'Cannot update PO with status {purchase_order.status}'
            }), 400

        # Update company fields
        update_fields = [
            'company_name', 'company_address', 'customer_name', 
            'customer_mobile', 'customer_email', 'department',
            'gst_number', 'company_id', 'supplier_part_no', 
            'supplier_description', 'status'
        ]
        
        for field in update_fields:
            if field in data:
                setattr(purchase_order, field, data[field])

        if data.get('po_date'):
            purchase_order.po_date = datetime.strptime(data['po_date'], '%Y-%m-%d').date()

        if 'delivery_date' in data:
            purchase_order.delivery_date = (
                datetime.strptime(data['delivery_date'], '%Y-%m-%d').date()
                if data['delivery_date'] else None
            )

        if 'items' in data:
            if not isinstance(data['items'], list) or not data['items']:
                return jsonify({'success': False, 'error': 'Items must be a non-empty list'}), 400

            purchase_order.items = data['items']
            purchase_order.total_amount = sum(
                float(i.get('quantity', 0)) * float(i.get('buy_price', 0))
                for i in data['items']
            )

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Purchase Order updated successfully',
            'data': purchase_order.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error updating purchase order: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ---------------------------
# Delete Purchase Order
# ---------------------------
@purchase_order_bp.route('/delete/<int:po_id>', methods=['DELETE'])
def delete_purchase_order(po_id):
    try:
        purchase_order = PurchaseOrder.query.get(po_id)

        if not purchase_order:
            return jsonify({'success': False, 'error': 'Purchase Order not found'}), 404

        # Only allow deletion if status is pending
        if purchase_order.status != 'pending':
            return jsonify({
                'success': False,
                'error': f'Cannot delete PO with status {purchase_order.status}'
            }), 400

        db.session.delete(purchase_order)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Purchase Order deleted'}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error deleting purchase order: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ---------------------------
# Purchase Order Statistics
# ---------------------------
@purchase_order_bp.route('/stats', methods=['GET'])
def get_po_statistics():
    try:
        total = PurchaseOrder.query.count()

        by_status = {
            status: PurchaseOrder.query.filter_by(status=status).count()
            for status in VALID_STATUSES
        }

        amount_by_status = {
            status: float(
                db.session.query(db.func.sum(PurchaseOrder.total_amount))
                .filter_by(status=status)
                .scalar() or 0
            )
            for status in ['pending', 'approved', 'completed']
        }

        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_count = PurchaseOrder.query.filter(
            PurchaseOrder.created_on >= week_ago
        ).count()

        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'pending': by_status.get('pending', 0),
                'approved': by_status.get('approved', 0),
                'rejected': by_status.get('rejected', 0),
                'completed': by_status.get('completed', 0),
                'amount_by_status': amount_by_status,
                'recent_count': recent_count
            }
        }), 200

    except Exception as e:
        print(f"Error getting statistics: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500