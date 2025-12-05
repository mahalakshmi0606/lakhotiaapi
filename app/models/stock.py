from app import db
from datetime import datetime

class Stock(db.Model):
    __tablename__ = "stock"

    id = db.Column(db.Integer, primary_key=True)

    item_name = db.Column(db.String(200))
    brand = db.Column(db.String(100))
    brand_code = db.Column(db.String(50))
    brand_description = db.Column(db.String(255))
    hsn = db.Column(db.String(50))
    batch_code = db.Column(db.String(100))
    mrp = db.Column(db.Float)
    buy_price = db.Column(db.Float)
    width = db.Column(db.String(50))
    length = db.Column(db.String(50))
    unit = db.Column(db.String(20))
    gst = db.Column(db.Float)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Stock {self.item_name}>"
