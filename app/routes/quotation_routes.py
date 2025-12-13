# backend/routes/quotation.py
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

# Helper function to generate requote number
def generate_requote_number(original_quote_number):
    """Generate requote number by adding -R1, -R2, etc."""
    import re
    # Check if already has -R{n} suffix
    pattern = r'^(.*?)(?:-R(\d+))?$'
    match = re.match(pattern, original_quote_number)
    if match:
        base = match.group(1)
        current_count = int(match.group(2)) if match.group(2) else 0
        new_count = current_count + 1
        return f"{base}-R{new_count}"
    return f"{original_quote_number}-R1"

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
        
        # Check if this is a re-quote
        original_quote_id = data.get('original_quote_id')
        if original_quote_id:
            # If it's a re-quote, generate re-quote number
            original_quote = Quotation.query.get(original_quote_id)
            if original_quote:
                quote_number = generate_requote_number(original_quote.quote_number)
        
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
            requote_note=data.get('requote_note', ''),
            original_quote_id=original_quote_id,
            requote_date=datetime.now() if original_quote_id else None,
            status=data.get('status', 'draft'),
            review_status=data.get('review_status', 'pending'),
            created_by=data.get('created_by'),
            updated_by=data.get('updated_by'),
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
                item_status=item_data.get('item_status', 'pending'),
                review_status=item_data.get('review_status', 'pending'),
                updated_by=data.get('updated_by'),
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
        
        # Check if quotation is completed (read-only)
        if quotation.status.lower() == 'completed':
            return jsonify({
                'success': False, 
                'message': 'Cannot update a completed quotation'
            }), 400
        
        # Update quotation fields
        update_fields = [
            'company_name', 'company_address', 'company_gstin', 
            'contact_person', 'contact_mobile', 'contact_email',
            'subtotal', 'total_discount', 'total_tax', 'grand_total',
            'notes', 'status', 'review_status', 'updated_by'
        ]
        
        for field in update_fields:
            if field in data:
                setattr(quotation, field, data[field])
        
        # Handle re-quote specific fields
        if 'requote_note' in data:
            quotation.requote_note = data['requote_note']
        
        # If marking as re-quote, update quote number
        if data.get('status') == 'requote' and 'quote_number' in data:
            quotation.quote_number = data['quote_number']
            if 'original_quote_id' in data:
                quotation.original_quote_id = data['original_quote_id']
            if 'requote_date' in data:
                quotation.requote_date = datetime.fromisoformat(data['requote_date'])
            elif data.get('status') == 'requote':
                # If status changed to requote but no date provided, set it
                quotation.requote_date = datetime.now()
        
        quotation.updated_at = datetime.now()
        
        # Update items if provided
        if 'items' in data:
            # Update existing items instead of deleting and recreating
            for item_data in data['items']:
                item_id = item_data.get('id')
                if item_id:
                    # Update existing item
                    item = QuotationItem.query.get(item_id)
                    if item and item.quotation_id == quote_id:
                        update_item_fields = [
                            'item_name', 'hsn_sac', 'supplier_part_no', 'description',
                            'cut_width', 'length', 'batch_no', 'mrp', 'quantity', 'unit',
                            'discount', 'discount_type', 'tax_rate', 'item_status',
                            'review_status', 'updated_by', 'price_per_unit',
                            'amount_before_discount', 'discount_amount',
                            'amount_after_discount', 'tax_amount', 'item_total'
                        ]
                        for field in update_item_fields:
                            if field in item_data:
                                setattr(item, field, item_data[field])
                else:
                    # Add new item
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
                        item_status=item_data.get('item_status', 'pending'),
                        review_status=item_data.get('review_status', 'pending'),
                        updated_by=data.get('updated_by', quotation.updated_by),
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
        
        # Check if quotation is completed
        if quotation.status.lower() == 'completed':
            return jsonify({
                'success': False, 
                'message': 'Cannot delete a completed quotation'
            }), 400
        
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
        valid_statuses = ['draft', 'sent', 'accepted', 'rejected', 'paid', 'cancelled', 'completed', 'requote']
        
        if new_status not in valid_statuses:
            return jsonify({'success': False, 'message': 'Invalid status'}), 400
        
        # Check if trying to update a completed quotation
        if quotation.status.lower() == 'completed' and new_status != 'completed':
            return jsonify({
                'success': False, 
                'message': 'Cannot change status of a completed quotation'
            }), 400
        
        quotation.status = new_status
        
        # Handle special cases
        if new_status == 'requote':
            # Generate new quote number for re-quote
            quotation.quote_number = generate_requote_number(quotation.quote_number)
            quotation.requote_note = data.get('requote_note', '')
            quotation.requote_date = datetime.now()
        
        quotation.updated_at = datetime.now()
        quotation.updated_by = data.get('updated_by', quotation.updated_by)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Status updated to {new_status}',
            'data': quotation.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# Update item status in quotation
@quotation_bp.route('/api/quotations/<int:quote_id>/items/<int:item_id>/status', methods=['PATCH'])
def update_item_status(quote_id, item_id):
    try:
        quotation = Quotation.query.get_or_404(quote_id)
        
        # Check if quotation is completed
        if quotation.status.lower() == 'completed':
            return jsonify({
                'success': False, 
                'message': 'Cannot update items in a completed quotation'
            }), 400
        
        data = request.get_json()
        
        new_status = data.get('status')
        valid_statuses = ['pending', 'approved', 'rejected', 'dispatched', 'delivered']
        
        if new_status not in valid_statuses:
            return jsonify({'success': False, 'message': 'Invalid item status'}), 400
        
        # Find and update the specific item
        item = QuotationItem.query.filter_by(id=item_id, quotation_id=quote_id).first()
        if not item:
            return jsonify({'success': False, 'message': 'Item not found'}), 404
        
        item.item_status = new_status
        item.updated_by = data.get('updated_by', item.updated_by)
        quotation.updated_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Item status updated to {new_status}',
            'data': item.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# Get item status statistics for a quotation
@quotation_bp.route('/api/quotations/<int:quote_id>/item-statistics', methods=['GET'])
def get_item_statistics(quote_id):
    try:
        quotation = Quotation.query.get_or_404(quote_id)
        
        # Count items by status
        status_counts = {}
        for status in ['pending', 'approved', 'rejected', 'dispatched', 'delivered']:
            count = QuotationItem.query.filter_by(quotation_id=quote_id, item_status=status).count()
            status_counts[status] = count
        
        return jsonify({
            'success': True,
            'data': {
                'quotation_id': quote_id,
                'quote_number': quotation.quote_number,
                'total_items': len(quotation.items),
                'status_counts': status_counts
            }
        }), 200
        
    except Exception as e:
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
        
        # Count by status (including new statuses)
        status_counts = {}
        valid_statuses = ['draft', 'sent', 'accepted', 'rejected', 'paid', 'cancelled', 'completed', 'requote']
        for status in valid_statuses:
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
        
        # Get all item status counts
        item_status_counts = {}
        for status in ['pending', 'approved', 'rejected', 'dispatched', 'delivered']:
            count = QuotationItem.query.filter_by(item_status=status).count()
            item_status_counts[status] = count
        
        # Calculate average items per quotation
        total_items = QuotationItem.query.count()
        avg_items_per_quotation = round(total_items / total, 2) if total > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'status_counts': status_counts,
                'monthly_totals': monthly_data,
                'current_month_revenue': current_month_revenue,
                'year': current_year,
                'item_statistics': {
                    'total_items': total_items,
                    'avg_items_per_quotation': avg_items_per_quotation,
                    'status_counts': item_status_counts
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Bulk update item statuses
@quotation_bp.route('/api/quotations/<int:quote_id>/items/bulk-status', methods=['PATCH'])
def bulk_update_item_status(quote_id):
    try:
        quotation = Quotation.query.get_or_404(quote_id)
        
        # Check if quotation is completed
        if quotation.status.lower() == 'completed':
            return jsonify({
                'success': False, 
                'message': 'Cannot update items in a completed quotation'
            }), 400
        
        data = request.get_json()
        
        item_ids = data.get('item_ids', [])
        new_status = data.get('status')
        
        if not item_ids:
            return jsonify({'success': False, 'message': 'No items provided'}), 400
        
        valid_statuses = ['pending', 'approved', 'rejected', 'dispatched', 'delivered']
        if new_status not in valid_statuses:
            return jsonify({'success': False, 'message': 'Invalid item status'}), 400
        
        # Update all specified items
        updated_count = QuotationItem.query.filter(
            QuotationItem.id.in_(item_ids),
            QuotationItem.quotation_id == quote_id
        ).update({
            'item_status': new_status, 
            'updated_by': data.get('updated_by'),
            'updated_at': datetime.now()
        })
        
        quotation.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Updated {updated_count} item(s) to {new_status}',
            'data': {
                'updated_count': updated_count,
                'status': new_status
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# Search quotations by company, item name, or quote number
@quotation_bp.route('/api/quotations/search', methods=['GET'])
def search_quotations():
    try:
        search_term = request.args.get('q', '').strip()
        if not search_term:
            return jsonify({'success': False, 'message': 'Search term required'}), 400
        
        # Search in company name, quote number, contact person, and notes
        quotations = Quotation.query.filter(
            (Quotation.company_name.ilike(f'%{search_term}%')) |
            (Quotation.quote_number.ilike(f'%{search_term}%')) |
            (Quotation.contact_person.ilike(f'%{search_term}%')) |
            (Quotation.notes.ilike(f'%{search_term}%')) |
            (Quotation.requote_note.ilike(f'%{search_term}%'))
        ).order_by(Quotation.created_at.desc()).limit(50).all()
        
        # Also search in items
        item_quotations = Quotation.query.join(QuotationItem).filter(
            QuotationItem.item_name.ilike(f'%{search_term}%') |
            QuotationItem.description.ilike(f'%{search_term}%') |
            QuotationItem.supplier_part_no.ilike(f'%{search_term}%')
        ).order_by(Quotation.created_at.desc()).limit(50).all()
        
        # Combine results and remove duplicates
        all_quotations = quotations + item_quotations
        unique_quotations = list({quote.id: quote for quote in all_quotations}.values())
        
        return jsonify({
            'success': True,
            'data': [quote.to_dict() for quote in unique_quotations],
            'count': len(unique_quotations)
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Get recent quotations
@quotation_bp.route('/api/quotations/recent', methods=['GET'])
def get_recent_quotations():
    try:
        limit = int(request.args.get('limit', 10))
        
        recent_quotations = Quotation.query\
            .order_by(Quotation.created_at.desc())\
            .limit(limit)\
            .all()
        
        return jsonify({
            'success': True,
            'data': [quote.to_dict() for quote in recent_quotations],
            'count': len(recent_quotations)
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Create re-quote from existing quotation
@quotation_bp.route('/api/quotations/<int:quote_id>/requote', methods=['POST'])
def create_requote(quote_id):
    try:
        original_quotation = Quotation.query.get_or_404(quote_id)
        data = request.get_json()
        
        # Generate new quote number for re-quote
        new_quote_number = generate_requote_number(original_quotation.quote_number)
        
        # Create re-quote
        requote = Quotation(
            quote_number=new_quote_number,
            date=datetime.now().date().isoformat(),
            time=datetime.now().time().strftime('%H:%M:%S'),
            issuer_details=original_quotation.issuer_details,
            company_id=original_quotation.company_id,
            company_name=original_quotation.company_name,
            company_address=original_quotation.company_address,
            company_gstin=original_quotation.company_gstin,
            contact_person=original_quotation.contact_person,
            contact_mobile=original_quotation.contact_mobile,
            contact_email=original_quotation.contact_email,
            subtotal=original_quotation.subtotal,
            total_discount=original_quotation.total_discount,
            total_tax=original_quotation.total_tax,
            grand_total=original_quotation.grand_total,
            notes=data.get('notes', original_quotation.notes),
            requote_note=data.get('requote_note', ''),
            original_quote_id=quote_id,
            requote_date=datetime.now(),
            status='draft',  # New re-quote starts as draft
            review_status='pending',
            created_by=data.get('created_by', original_quotation.created_by),
            updated_by=data.get('updated_by'),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.session.add(requote)
        db.session.flush()
        
        # Copy items from original quotation
        for original_item in original_quotation.items:
            item = QuotationItem(
                quotation_id=requote.id,
                item_name=original_item.item_name,
                hsn_sac=original_item.hsn_sac,
                supplier_part_no=original_item.supplier_part_no,
                description=original_item.description,
                cut_width=original_item.cut_width,
                length=original_item.length,
                batch_no=original_item.batch_no,
                mrp=original_item.mrp,
                quantity=original_item.quantity,
                unit=original_item.unit,
                discount=original_item.discount,
                discount_type=original_item.discount_type,
                tax_rate=original_item.tax_rate,
                item_status='pending',  # Reset status for re-quote
                review_status='pending',
                updated_by=data.get('updated_by'),
                price_per_unit=original_item.price_per_unit,
                amount_before_discount=original_item.amount_before_discount,
                discount_amount=original_item.discount_amount,
                amount_after_discount=original_item.amount_after_discount,
                tax_amount=original_item.tax_amount,
                item_total=original_item.item_total
            )
            db.session.add(item)
        
        # Update original quotation status to 'requote' if requested
        if data.get('update_original_status', False):
            original_quotation.status = 'requote'
            original_quotation.updated_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Re-quote created successfully',
            'data': requote.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# Get all re-quotes for a quotation
@quotation_bp.route('/api/quotations/<int:quote_id>/requotes', methods=['GET'])
def get_requotes(quote_id):
    try:
        requotes = Quotation.query.filter_by(original_quote_id=quote_id)\
            .order_by(Quotation.created_at.desc())\
            .all()
        
        return jsonify({
            'success': True,
            'data': [quote.to_dict() for quote in requotes],
            'count': len(requotes)
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500