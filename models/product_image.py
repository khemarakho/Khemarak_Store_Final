from extensions import db

class ProductImage(db.Model):
    __tablename__ = "product_images"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False
    )
    name = db.Column(db.String(255), nullable=False)

    @property
    def ProductId(self):
        return self.product_id

    @ProductId.setter
    def ProductId(self, value):
        self.product_id = value

    @property
    def image_url(self):
        from upload_service import get_image_url
        return get_image_url(self.name, "products")

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "name": self.name,
            "image_url": self.image_url
        }

    def __repr__(self):
        return f"<ProductImage {self.id}: {self.name}>"
