from app import db
from datetime import datetime

class GRN(db.Model):
    __tablename__ = "grn"

    id = db.Column(db.Integer, primary_key=True)

    # Invoice details
    invoice_number = db.Column(db.String(100))
    invoice_date = db.Column(db.String(20))

    # Customer Details
    customer_name = db.Column(db.String(200))
    customer_part_no = db.Column(db.String(100))
    customer_description = db.Column(db.String(500))

    # Item Details
    item_name = db.Column(db.String(200))
    brand = db.Column(db.String(100))
    length = db.Column(db.String(50))
    width = db.Column(db.String(50))
    buy_price = db.Column(db.Float)

    # Auto generated batch code
    batch_code = db.Column(db.String(100))

    created_on = db.Column(db.DateTime, default=datetime.utcnow)
