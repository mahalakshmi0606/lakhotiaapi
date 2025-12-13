# backend/models/quotation.py
from app import db
from datetime import datetime

# ---------------------------
# QUOTATION MODEL
# ---------------------------
class Quotation(db.Model):
    __tablename__ = 'quotations'

    id = db.Column(db.Integer, primary_key=True)
    quote_number = db.Column(db.String(50), unique=True, nullable=False)

    # Date & Time
    date = db.Column(db.String(10), nullable=False)
    time = db.Column(db.String(10), nullable=False)

    # Company Details
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    company_name = db.Column(db.String(200), nullable=False)
    company_address = db.Column(db.Text, nullable=True)
    company_gstin = db.Column(db.String(20), nullable=True)

    # Contact Details
    contact_person = db.Column(db.String(100))
    contact_mobile = db.Column(db.String(20))
    contact_email = db.Column(db.String(100))

    # Issuer
    issuer_details = db.Column(db.JSON, default={})

    # Totals
    subtotal = db.Column(db.Numeric(12, 2), default=0)
    total_discount = db.Column(db.Numeric(12, 2), default=0)
    total_tax = db.Column(db.Numeric(12, 2), default=0)
    grand_total = db.Column(db.Numeric(12, 2), default=0)

    # Status
    status = db.Column(db.String(20), default='draft')
    review_status = db.Column(db.String(20), default='pending')

    # User Tracking
    created_by = db.Column(db.String(100))
    updated_by = db.Column(db.String(100))

    # Notes
    notes = db.Column(db.Text)
    
    # New fields for requote
    requote_note = db.Column(db.Text)  # Note for re-quote reason
    original_quote_id = db.Column(db.Integer, nullable=True)  # Reference to original quote if this is a re-quote
    requote_date = db.Column(db.DateTime, nullable=True)  # When re-quote was created

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    items = db.relationship(
        'QuotationItem',
        backref='quotation',
        lazy=True,
        cascade='all, delete-orphan'
    )

    # Convert to dict
    def to_dict(self):
        return {
            'id': self.id,
            'quote_number': self.quote_number,
            'date': self.date,
            'time': self.time,
            'company_id': self.company_id,
            'company_name': self.company_name,
            'company_address': self.company_address,
            'company_gstin': self.company_gstin,
            'contact_person': self.contact_person,
            'contact_mobile': self.contact_mobile,
            'contact_email': self.contact_email,
            'issuer_details': self.issuer_details or {},
            'subtotal': float(self.subtotal),
            'total_discount': float(self.total_discount),
            'total_tax': float(self.total_tax),
            'grand_total': float(self.grand_total),
            'notes': self.notes,
            'requote_note': self.requote_note,
            'original_quote_id': self.original_quote_id,
            'requote_date': self.requote_date.isoformat() if self.requote_date else None,
            'status': self.status,
            'review_status': self.review_status,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'items': [item.to_dict() for item in self.items]
        }


# ---------------------------
# QUOTATION ITEM MODEL
# ---------------------------
class QuotationItem(db.Model):
    __tablename__ = 'quotation_items'

    id = db.Column(db.Integer, primary_key=True)
    quotation_id = db.Column(db.Integer, db.ForeignKey('quotations.id'), nullable=False)

    # Item Details
    item_name = db.Column(db.String(200), nullable=False)
    hsn_sac = db.Column(db.String(20))
    supplier_part_no = db.Column(db.String(100))
    description = db.Column(db.Text)

    # Dimensions
    cut_width = db.Column(db.Numeric(10, 2), default=0)
    length = db.Column(db.Numeric(10, 2), default=0)

    # Batch
    batch_no = db.Column(db.String(50))

    # Pricing
    mrp = db.Column(db.Numeric(12, 2), default=0)
    quantity = db.Column(db.Numeric(10, 2), default=1)
    unit = db.Column(db.String(20), default='pcs')

    # Discount
    discount = db.Column(db.Numeric(10, 2), default=0)
    discount_type = db.Column(db.String(20), default='amount')   # amount or percentage

    # Tax
    tax_rate = db.Column(db.Numeric(5, 2), default=18.0)

    # Status
    item_status = db.Column(db.String(20), default='pending')
    review_status = db.Column(db.String(20), default='pending')

    updated_by = db.Column(db.String(100))

    # Calculated Fields
    price_per_unit = db.Column(db.Numeric(12, 2), default=0)
    amount_before_discount = db.Column(db.Numeric(12, 2), default=0)
    discount_amount = db.Column(db.Numeric(12, 2), default=0)
    amount_after_discount = db.Column(db.Numeric(12, 2), default=0)
    tax_amount = db.Column(db.Numeric(12, 2), default=0)
    item_total = db.Column(db.Numeric(12, 2), default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'quotation_id': self.quotation_id,
            'item_name': self.item_name,
            'hsn_sac': self.hsn_sac,
            'supplier_part_no': self.supplier_part_no,
            'description': self.description,
            'cut_width': float(self.cut_width),
            'length': float(self.length),
            'batch_no': self.batch_no,
            'mrp': float(self.mrp),
            'quantity': float(self.quantity),
            'unit': self.unit,
            'discount': float(self.discount),
            'discount_type': self.discount_type,
            'tax_rate': float(self.tax_rate),
            'item_status': self.item_status,
            'review_status': self.review_status,
            'updated_by': self.updated_by,
            'price_per_unit': float(self.price_per_unit),
            'amount_before_discount': float(self.amount_before_discount),
            'discount_amount': float(self.discount_amount),
            'amount_after_discount': float(self.amount_after_discount),
            'tax_amount': float(self.tax_amount),
            'item_total': float(self.item_total)
        }