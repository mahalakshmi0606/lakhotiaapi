from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid
from app.models.quotation import Quotation, QuotationItem
from app import db
from sqlalchemy import func, extract

quotation_bp = Blueprint('quotations', __name__)

# Generate unique quote number
def generate_quote_number():
    date_str = datetime.now().strftime("%Y%m%d")
    random_num = str(uuid.uuid4().int)[:6]
    return f"Q-{date_str}-{random_num}"

# Get all quotations
@quotation_bp.route('/api/quotations', methods=['GET'])
def get_quotations():
    try:
        status = request.args.get('status')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        query = Quotation.query
        
        if status:
            query = query.filter_by(status=status)
        
        quotations = query.order_by(Quotation.created_at.desc())\
                         .paginate(page=page, per_page=per_page, error_out=False)
        
        result = {
            'success': True,
            'data': [quote.to_dict() for quote in quotations.items],
            'pagination': {
                'page': quotations.page,
                'per_page': quotations.per_page,
                'total': quotations.total,
                'pages': quotations.pages
            }
        }
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Get single quotation
@quotation_bp.route('/api/quotations/<int:quote_id>', methods=['GET'])
def get_quotation(quote_id):
    try:
        quotation = Quotation.query.get_or_404(quote_id)
        return jsonify({'success': True, 'data': quotation.to_dict()}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Create new quotation
@quotation_bp.route('/api/quotations', methods=['POST'])
def create_quotation():
    try:
        data = request.get_json()
        
        # Generate quote number if not provided
        quote_number = data.get('quote_number') or generate_quote_number()
        
        # Create quotation
        quotation = Quotation(
            quote_number=quote_number,
            date=data.get('date', datetime.now().date().isoformat()),
            time=data.get('time', datetime.now().time().strftime('%H:%M:%S')),
            issuer_details=data.get('issuer_details', {}),
            company_id=data.get('company_id'),
            company_name=data.get('company_name'),
            company_address=data.get('company_address'),
            company_gstin=data.get('company_gstin'),
            contact_person=data.get('contact_person'),
            contact_mobile=data.get('contact_mobile'),
            contact_email=data.get('contact_email'),
            subtotal=data.get('subtotal', 0),
            total_discount=data.get('total_discount', 0),
            total_tax=data.get('total_tax', 0),
            grand_total=data.get('grand_total', 0),
            notes=data.get('notes', ''),
            status=data.get('status', 'draft'),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.session.add(quotation)
        db.session.flush()  # Get the quotation ID
        
        # Add items
        items = data.get('items', [])
        for item_data in items:
            item = QuotationItem(
                quotation_id=quotation.id,
                item_name=item_data.get('item_name'),
                hsn_sac=item_data.get('hsn_sac'),
                supplier_part_no=item_data.get('supplier_part_no'),
                description=item_data.get('description'),
                cut_width=item_data.get('cut_width', 0),
                length=item_data.get('length', 0),
                batch_no=item_data.get('batch_no'),
                mrp=item_data.get('mrp', 0),
                quantity=item_data.get('quantity', 1),
                unit=item_data.get('unit', 'pcs'),
                discount=item_data.get('discount', 0),
                discount_type=item_data.get('discount_type', 'amount'),
                tax_rate=item_data.get('tax_rate', 18),
                price_per_unit=item_data.get('price_per_unit', 0),
                amount_before_discount=item_data.get('amount_before_discount', 0),
                discount_amount=item_data.get('discount_amount', 0),
                amount_after_discount=item_data.get('amount_after_discount', 0),
                tax_amount=item_data.get('tax_amount', 0),
                item_total=item_data.get('item_total', 0)
            )
            db.session.add(item)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Quotation created successfully',
            'data': quotation.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# Update quotation
@quotation_bp.route('/api/quotations/<int:quote_id>', methods=['PUT'])
def update_quotation(quote_id):
    try:
        quotation = Quotation.query.get_or_404(quote_id)
        data = request.get_json()
        
        # Update quotation fields
        for field in ['company_name', 'company_address', 'company_gstin', 
                     'contact_person', 'contact_mobile', 'contact_email',
                     'subtotal', 'total_discount', 'total_tax', 'grand_total',
                     'notes', 'status']:
            if field in data:
                setattr(quotation, field, data[field])
        
        quotation.updated_at = datetime.now()
        
        # Update items if provided
        if 'items' in data:
            # Delete existing items
            QuotationItem.query.filter_by(quotation_id=quote_id).delete()
            
            # Add new items
            for item_data in data['items']:
                item = QuotationItem(
                    quotation_id=quote_id,
                    item_name=item_data.get('item_name'),
                    hsn_sac=item_data.get('hsn_sac'),
                    supplier_part_no=item_data.get('supplier_part_no'),
                    description=item_data.get('description'),
                    cut_width=item_data.get('cut_width', 0),
                    length=item_data.get('length', 0),
                    batch_no=item_data.get('batch_no'),
                    mrp=item_data.get('mrp', 0),
                    quantity=item_data.get('quantity', 1),
                    unit=item_data.get('unit', 'pcs'),
                    discount=item_data.get('discount', 0),
                    discount_type=item_data.get('discount_type', 'amount'),
                    tax_rate=item_data.get('tax_rate', 18),
                    price_per_unit=item_data.get('price_per_unit', 0),
                    amount_before_discount=item_data.get('amount_before_discount', 0),
                    discount_amount=item_data.get('discount_amount', 0),
                    amount_after_discount=item_data.get('amount_after_discount', 0),
                    tax_amount=item_data.get('tax_amount', 0),
                    item_total=item_data.get('item_total', 0)
                )
                db.session.add(item)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Quotation updated successfully',
            'data': quotation.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# Delete quotation
@quotation_bp.route('/api/quotations/<int:quote_id>', methods=['DELETE'])
def delete_quotation(quote_id):
    try:
        quotation = Quotation.query.get_or_404(quote_id)
        
        # Delete associated items first
        QuotationItem.query.filter_by(quotation_id=quote_id).delete()
        
        # Delete quotation
        db.session.delete(quotation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Quotation deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# Update quotation status
@quotation_bp.route('/api/quotations/<int:quote_id>/status', methods=['PATCH'])
def update_quotation_status(quote_id):
    try:
        quotation = Quotation.query.get_or_404(quote_id)
        data = request.get_json()
        
        new_status = data.get('status')
        if new_status not in ['draft', 'sent', 'accepted', 'rejected', 'paid', 'cancelled']:
            return jsonify({'success': False, 'message': 'Invalid status'}), 400
        
        quotation.status = new_status
        quotation.updated_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Status updated to {new_status}',
            'data': quotation.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# Export quotation as PDF
@quotation_bp.route('/api/quotations/<int:quote_id>/export', methods=['GET'])
def export_quotation(quote_id):
    try:
        quotation = Quotation.query.get_or_404(quote_id)
        
        # This would generate PDF using a library like ReportLab or WeasyPrint
        # For now, return the quotation data
        return jsonify({
            'success': True,
            'message': 'PDF export functionality to be implemented',
            'data': quotation.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Get quotation statistics
@quotation_bp.route('/api/quotations/statistics', methods=['GET'])
def get_statistics():
    try:
        # Get current year
        current_year = datetime.now().year
        
        # Total count
        total = Quotation.query.count()
        
        # Count by status
        status_counts = {}
        for status in ['draft', 'sent', 'accepted', 'rejected', 'paid', 'cancelled']:
            count = Quotation.query.filter_by(status=status).count()
            status_counts[status] = count
        
        # Monthly totals for current year
        monthly_totals = db.session.query(
            extract('month', Quotation.created_at).label('month'),
            func.sum(Quotation.grand_total).label('total')
        ).filter(extract('year', Quotation.created_at) == current_year)\
         .group_by('month')\
         .order_by('month')\
         .all()
        
        # Format monthly totals
        monthly_data = {str(month): float(total or 0) for month, total in monthly_totals}
        
        # Current month revenue
        current_month = datetime.now().month
        current_month_revenue = 0
        for month, total in monthly_totals:
            if month == current_month:
                current_month_revenue = float(total or 0)
                break
        
        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'status_counts': status_counts,
                'monthly_totals': monthly_data,
                'current_month_revenue': current_month_revenue,
                'year': current_year
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500