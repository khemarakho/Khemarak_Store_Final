from extensions import db
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100),nullable=False)
    email = db.Column(db.String(150),unique=True,nullable=False)
    password = db.Column(db.String(255),nullable=False)
    role = db.Column(db.String(50),default="user")
    image = db.Column(db.String(255),nullable=True)