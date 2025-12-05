from app import db

class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(100), nullable=False)
    mrp = db.Column(db.Float, nullable=False)

    def to_dict(self):
        """Convert model to dictionary for JSON responses."""
        return {
            "id": self.id,
            "brand": self.brand,
            "mrp": self.mrp,
        }

    def __repr__(self):
        """Debug display for logs."""
        return f"<Product {self.brand} | MRP: {self.mrp}>"
