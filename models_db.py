from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Product(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(200))
    brand       = db.Column(db.String(100))
    description = db.Column(db.Text)
    image_url   = db.Column(db.String(300))
    category    = db.Column(db.String(100))
    reviews     = db.relationship('Review', backref='product')

class Review(db.Model):
    id              = db.Column(db.Integer, primary_key=True)
    product_id      = db.Column(db.Integer, db.ForeignKey('product.id'))
    title           = db.Column(db.String(200))
    text            = db.Column(db.Text)
    rating          = db.Column(db.Integer)
    recommend_label = db.Column(db.Integer)   # 0 or 1
    user_overridden = db.Column(db.Boolean, default=False)