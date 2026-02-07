from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from sqlalchemy import func, or_

from app import db
from app.models.enquiry import Enquiry, EnquiryItem

enquiry_bp = Blueprint('enquiries', __name__, url_prefix='/api/enquiries')

def build_item_description(item_data):
    """Build description string from item data (legacy support)"""
    description_parts = []
    
    if item_data.get("description"):
        description_parts.append(str(item_data["description"]))
    
    if item_data.get("customer_description"):
        description_parts.append(f"[CUSTOMER_DESC:{item_data['customer_description']}]")
    
    if item_data.get("brand_code"):
        description_parts.append(f"[BRAND_CODE:{item_data['brand_code']}]")
    
    if item_data.get("customer_requirements"):
        description_parts.append(f"[REQUIREMENTS:{item_data['customer_requirements']}]")
    
    return " ".join(description_parts) if description_parts else ""

def parse_description(description):
    """Parse description to extract embedded data (legacy support)"""
    if not description:
        return "", "", "", ""

    brand_code = ""
    customer_description = ""
    customer_requirements = ""
    clean_description = description

    try:
        if '[BRAND_CODE:' in description:
            brand_code = description.split('[BRAND_CODE:')[1].split(']')[0]

        if '[CUSTOMER_DESC:' in description:
            customer_description = description.split('[CUSTOMER_DESC:')[1].split(']')[0]

        if '[REQUIREMENTS:' in description:
            customer_requirements = description.split('[REQUIREMENTS:')[1].split(']')[0]

        for tag in ['[BRAND_CODE:', '[CUSTOMER_DESC:', '[REQUIREMENTS:']:
            while tag in clean_description:
                start = clean_description.find(tag)
                end = clean_description.find(']', start) + 1
                clean_description = clean_description[:start] + clean_description[end:]

        clean_description = clean_description.strip()

    except Exception:
        pass

    return clean_description, brand_code, customer_description, customer_requirements

@enquiry_bp.before_request
def log_request_info():
    """Log request info for debugging"""
    if request.method in ['POST', 'PUT', 'DELETE']:
        print(f"\n{'='*50}")
        print(f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{request.method} {request.path}")
        print(f"{'='*50}")


@enquiry_bp.route('/', methods=['GET'])
def get_enquiries():
    """Get all enquiries with pagination and filtering"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('q', '').strip()
    status = request.args.get('status', '').strip()

    query = Enquiry.query

    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                Enquiry.enquiry_number.ilike(like),
                Enquiry.company_name.ilike(like),
                Enquiry.contact_person.ilike(like),
                Enquiry.contact_email.ilike(like),
            )
        )

    if status and status != 'all':
        query = query.filter(Enquiry.status == status)

    total = query.count()
    enquiries = query.order_by(Enquiry.created_at.desc()) \
        .offset((page - 1) * per_page) \
        .limit(per_page) \
        .all()

    return jsonify({
        "success": True,
        "data": [e.to_dict() for e in enquiries],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": (total + per_page - 1) // per_page
        }
    })


@enquiry_bp.route('/', methods=['POST'])
def create_enquiry():
    """Create a new enquiry"""
    data = request.get_json()

    print(f"\n📝 CREATE ENQUIRY REQUEST:")
    print(f"Company: {data.get('company_name')}")
    print(f"Contact: {data.get('contact_person')}")
    print(f"Items: {len(data.get('items', []))}")

    if not data.get("company_name"):
        return jsonify({"success": False, "message": "Company name is required"}), 400

    try:
        # Convert company_id if provided
        company_id = None
        if 'company_id' in data and data['company_id']:
            try:
                company_id = int(data['company_id'])
            except (ValueError, TypeError):
                company_id = None
                print("⚠️ Warning: Invalid company_id, setting to None")

        # Create enquiry
        enquiry = Enquiry(
            enquiry_number=Enquiry.generate_enquiry_number(),
            company_name=data["company_name"],
            company_address=data.get("company_address", ""),
            company_pincode=data.get("company_pincode", ""),
            company_gstin=data.get("company_gstin", ""),
            contact_person=data.get("contact_person", ""),
            contact_mobile=data.get("contact_mobile", ""),
            contact_email=data.get("contact_email", ""),
            status=data.get("status", "draft"),
            created_by=data.get("created_by", "User"),
            updated_by=data.get("updated_by", "User"),
            company_id=company_id
        )

        db.session.add(enquiry)
        db.session.flush()  # Get the enquiry ID

        total_quantity = 0
        total_items = len(data.get("items", []))

        print(f"\n📦 Processing {total_items} items...")
        
        for idx, item in enumerate(data.get("items", []), 1):
            # Build description (legacy support)
            description = build_item_description(item)
            
            # Calculate count (width × length × quantity)
            cut_width = float(item.get("cut_width", 1.0))
            length = float(item.get("length", 1.0))
            quantity = float(item.get("quantity", 1.0))
            count = cut_width * length * quantity
            
            total_quantity += quantity
            
            # Create enquiry item
            enquiry_item = EnquiryItem(
                enquiry_id=enquiry.id,
                item_name=item.get("item_name", ""),
                hsn_sac=item.get("hsn_sac", ""),
                supplier_part_no=item.get("supplier_part_no", ""),
                description=description,
                cut_width=cut_width,
                length=length,
                count=count,
                batch_no=item.get("batch_no", ""),
                brand_code=item.get("brand_code", ""),
                quantity=quantity,
                unit=item.get("unit", "pcs"),
                # Store customer description and requirements in separate fields
                customer_description=item.get("customer_description", ""),
                customer_requirements=item.get("customer_requirements", ""),
                notes=item.get("notes", ""),
                source=item.get("source", "email")
            )
            
            db.session.add(enquiry_item)
            print(f"  {idx}. {item.get('item_name')[:30]}... (Qty: {quantity})")

        # Update totals
        enquiry.total_items = total_items
        enquiry.total_quantity = total_quantity

        db.session.commit()
        
        print(f"\n✅ ENQUIRY CREATED: {enquiry.enquiry_number}")
        print(f"   Items: {total_items}, Total Qty: {total_quantity}")
        print(f"{'='*50}\n")
        
        return jsonify({
            "success": True,
            "message": "Enquiry created successfully",
            "data": enquiry.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"\n❌ ERROR creating enquiry: {str(e)}")
        import traceback
        traceback.print_exc()
        print(f"{'='*50}\n")
        
        return jsonify({
            "success": False,
            "message": f"Failed to create enquiry: {str(e)}"
        }), 500


@enquiry_bp.route('/<int:enquiry_id>', methods=['GET'])
def get_enquiry(enquiry_id):
    """Get a single enquiry by ID"""
    enquiry = Enquiry.query.get_or_404(enquiry_id)
    return jsonify({"success": True, "data": enquiry.to_dict()})


@enquiry_bp.route('/<int:enquiry_id>', methods=['PUT'])
def update_enquiry(enquiry_id):
    """Update an existing enquiry"""
    enquiry = Enquiry.query.get_or_404(enquiry_id)
    data = request.get_json()
    
    print(f"\n🔄 UPDATE ENQUIRY {enquiry_id} ({enquiry.enquiry_number})")
    
    try:
        # Update enquiry status
        if 'status' in data:
            old_status = enquiry.status
            enquiry.status = data['status']
            print(f"Status: {old_status} → {data['status']}")
        
        # Update contact info if provided
        if 'contact_person' in data:
            enquiry.contact_person = data['contact_person']
        if 'contact_mobile' in data:
            enquiry.contact_mobile = data['contact_mobile']
        if 'contact_email' in data:
            enquiry.contact_email = data['contact_email']
        
        # Update updated_by
        if 'updated_by' in data:
            enquiry.updated_by = data['updated_by']
        
        db.session.commit()
        
        print(f"✅ Enquiry {enquiry_id} updated successfully")
        
        return jsonify({
            "success": True,
            "message": "Enquiry updated successfully",
            "data": enquiry.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR updating enquiry: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Failed to update enquiry: {str(e)}"
        }), 500


@enquiry_bp.route('/<int:enquiry_id>', methods=['DELETE'])
def delete_enquiry(enquiry_id):
    """Delete an enquiry"""
    enquiry = Enquiry.query.get_or_404(enquiry_id)
    
    print(f"\n🗑️ DELETE ENQUIRY {enquiry_id} ({enquiry.enquiry_number})")
    
    try:
        db.session.delete(enquiry)
        db.session.commit()
        
        print(f"✅ Enquiry {enquiry_id} deleted successfully")
        
        return jsonify({
            "success": True, 
            "message": "Enquiry deleted successfully"
        })
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR deleting enquiry: {str(e)}")
        return jsonify({
            "success": False, 
            "message": f"Failed to delete enquiry: {str(e)}"
        }), 500


# ==================== ITEMS ====================

@enquiry_bp.route('/<int:enquiry_id>/items', methods=['GET'])
def get_items(enquiry_id):
    """Get all items for an enquiry"""
    enquiry = Enquiry.query.get_or_404(enquiry_id)
    items = enquiry.items
    
    result = []
    for item in items:
        # Parse description for legacy support
        clean_desc, brand, cust_desc, req = parse_description(item.description)
        
        # Use separate fields if available, otherwise use parsed data
        d = {
            'id': item.id,
            'item_name': item.item_name,
            'hsn_sac': item.hsn_sac,
            'supplier_part_no': item.supplier_part_no,
            'description': clean_desc,
            'cut_width': item.cut_width,
            'length': item.length,
            'count': item.count,
            'batch_no': item.batch_no,
            'brand_code': item.brand_code or brand,
            'quantity': item.quantity,
            'unit': item.unit,
            'customer_description': item.customer_description or cust_desc,
            'customer_requirements': item.customer_requirements or req,
            'notes': item.notes,
            'source': item.source,
            'enquiry_id': item.enquiry_id,
            'created_at': item.created_at.isoformat() if item.created_at else None,
            'updated_at': item.updated_at.isoformat() if item.updated_at else None
        }
        result.append(d)

    return jsonify({"success": True, "data": result})


# ==================== STATUS MANAGEMENT ====================

@enquiry_bp.route('/<int:enquiry_id>/status', methods=['PUT'])
def update_enquiry_status(enquiry_id):
    """Update enquiry status only"""
    enquiry = Enquiry.query.get_or_404(enquiry_id)
    data = request.get_json()
    
    if not data.get('status'):
        return jsonify({
            "success": False,
            "message": "Status is required"
        }), 400
    
    valid_statuses = ['draft', 'in_progress', 'responded', 'converted', 'lost']
    new_status = data['status']
    
    if new_status not in valid_statuses:
        return jsonify({
            "success": False,
            "message": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        }), 400
    
    print(f"\n🔄 UPDATE STATUS: Enquiry {enquiry_id} ({enquiry.enquiry_number})")
    print(f"Current: {enquiry.status} → New: {new_status}")
    
    try:
        old_status = enquiry.status
        enquiry.status = new_status
        enquiry.updated_by = data.get('updated_by', 'System')
        
        db.session.commit()
        
        print(f"✅ Status updated successfully")
        
        return jsonify({
            "success": True,
            "message": f"Enquiry status updated from '{old_status}' to '{new_status}'",
            "data": {
                'id': enquiry.id,
                'enquiry_number': enquiry.enquiry_number,
                'old_status': old_status,
                'new_status': new_status,
                'updated_at': enquiry.updated_at.isoformat() if enquiry.updated_at else None
            }
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR updating status: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Failed to update status: {str(e)}"
        }), 500


@enquiry_bp.route('/status/bulk-update', methods=['POST'])
def bulk_update_status():
    """Bulk update enquiry statuses"""
    data = request.get_json()
    
    if not data.get('enquiry_ids') or not data.get('status'):
        return jsonify({
            "success": False,
            "message": "enquiry_ids and status are required"
        }), 400
    
    valid_statuses = ['draft', 'in_progress', 'responded', 'converted', 'lost']
    new_status = data['status']
    
    if new_status not in valid_statuses:
        return jsonify({
            "success": False,
            "message": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        }), 400
    
    print(f"\n🔄 BULK UPDATE STATUS:")
    print(f"Enquiries: {len(data['enquiry_ids'])}")
    print(f"New Status: {new_status}")
    
    try:
        enquiry_ids = data['enquiry_ids']
        updated_by = data.get('updated_by', 'System')
        
        # Update enquiries
        updated_count = Enquiry.query.filter(Enquiry.id.in_(enquiry_ids)).update(
            {
                'status': new_status,
                'updated_by': updated_by,
                'updated_at': datetime.utcnow()
            },
            synchronize_session=False
        )
        
        db.session.commit()
        
        print(f"✅ Updated {updated_count} enquiries")
        
        return jsonify({
            "success": True,
            "message": f"Updated status for {updated_count} enquiries to '{new_status}'",
            "data": {
                "updated_count": updated_count,
                "new_status": new_status
            }
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR in bulk update: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Failed to update statuses: {str(e)}"
        }), 500


# ==================== DASHBOARD & STATISTICS ====================

@enquiry_bp.route('/statistics', methods=['GET'])
def enquiry_statistics():
    """Get enquiry statistics"""
    try:
        stats = Enquiry.get_statistics()
        
        return jsonify({
            "success": True,
            "data": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error fetching statistics: {str(e)}"
        }), 500


@enquiry_bp.route('/dashboard/summary', methods=['GET'])
def dashboard_summary():
    """Dashboard summary endpoint"""
    return enquiry_statistics()


# ==================== DEBUG & TEST ENDPOINTS ====================

@enquiry_bp.route('/test', methods=['GET'])
def test_endpoint():
    """Test if API is working"""
    return jsonify({
        "success": True,
        "message": "Enquiries API is working",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0",
        "features": [
            "Enquiry creation with customer_description support",
            "Enquiry-level status management (no item-level status)",
            "Bulk status updates",
            "Enhanced debugging logs"
        ]
    })


@enquiry_bp.route('/fields', methods=['GET'])
def expected_fields():
    """Show expected fields for enquiry creation"""
    return jsonify({
        "success": True,
        "expected_fields": {
            "enquiry": {
                "required": ["company_name"],
                "optional": [
                    "company_address", "company_pincode", "company_gstin",
                    "contact_person", "contact_mobile", "contact_email",
                    "status", "created_by", "updated_by", "company_id"
                ]
            },
            "items": {
                "required": ["item_name"],
                "optional": [
                    "customer_description",  # Direct field
                    "brand_code",  # Direct field
                    "customer_requirements",  # Direct field
                    "hsn_sac", "supplier_part_no", "description",
                    "cut_width", "length", "quantity", "batch_no",
                    "unit", "notes", "source"
                ],
                "note": "customer_description, brand_code, and customer_requirements are now direct fields (no tags needed)"
            }
        }
    })