from extensions import db

class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    image = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)

    # Relationships
    products = db.relationship(
        "Product",
        backref="category",
        lazy=True,
        cascade="all, delete-orphan"
    )

    @property
    def image_url(self):
        from upload_service import get_image_url
        return get_image_url(self.image, "categories")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "image": self.image_url,
            "image_url": self.image_url,
            "description": self.description,
            "product_count": len(self.products) if self.products else 0
        }

    def __repr__(self):
        return f"<Category {self.id}: {self.name}>"
