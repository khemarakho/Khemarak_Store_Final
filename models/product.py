from extensions import db
from decimal import Decimal

class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    thumbnail = db.Column(db.String(255), nullable=True)
    cost = db.Column(db.Numeric(10, 2), default=Decimal("0.00"), nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, default=0, nullable=False)
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False
    )
    description = db.Column(db.Text, nullable=True)

    # Relationship to ProductImage
    images = db.relationship(
        "ProductImage",
        backref="product",
        lazy=True,
        cascade="all, delete-orphan"
    )

    # Convenience alias properties matching user specification
    @property
    def Cost(self):
        return self.cost

    @Cost.setter
    def Cost(self, value):
        self.cost = value

    @property
    def Price(self):
        return self.price

    @Price.setter
    def Price(self, value):
        self.price = value

    @property
    def Stock(self):
        return self.stock

    @Stock.setter
    def Stock(self, value):
        self.stock = value

    @property
    def CategoryId(self):
        return self.category_id

    @CategoryId.setter
    def CategoryId(self, value):
        self.category_id = value

    @property
    def image(self):
        from upload_service import get_image_url
        return get_image_url(self.thumbnail, "products")

    @property
    def brand(self):
        return self.category.name if self.category else ""

    @property
    def rating(self):
        return 4.9

    @property
    def reviews(self):
        return 128

    @property
    def original_price(self):
        return (self.price * Decimal("1.10")).quantize(Decimal("0.01"))

    @property
    def discount_savings(self):
        return (self.original_price - self.price).quantize(Decimal("0.01"))

    @property
    def discount(self):
        return 10

    @property
    def colors(self):
        return ["Black", "Titanium", "Silver", "Blue"]

    @property
    def storage(self):
        return ["128GB", "256GB", "512GB", "1TB"]

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "thumbnail": self.image,
            "image": self.image,
            "cost": float(self.cost) if self.cost is not None else 0.0,
            "price": float(self.price) if self.price is not None else 0.0,
            "stock": self.stock,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else "",
            "description": self.description or "",
            "images": [img.image_url for img in self.images] if self.images else []
        }

    def __repr__(self):
        return f"<Product {self.id}: {self.name}>"
