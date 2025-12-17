from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False, unique=True)
    title = db.Column(db.String(300), nullable=True)
    current_price = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship: One product has many price history records
    price_history = db.relationship('PriceHistory', backref='product', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Product {self.title}>'
    
    def get_price_trend(self):
        """Returns 'up', 'down', or 'same' based on last 2 prices"""
        if len(self.price_history) < 2:
            return 'same'
        
        sorted_history = sorted(self.price_history, key=lambda x: x.scraped_at, reverse=True)
        latest = sorted_history[0].price
        previous = sorted_history[1].price
        
        if latest < previous:
            return 'down'
        elif latest > previous:
            return 'up'
        else:
            return 'same'
    
    def get_price_change_percent(self):
        """Returns percentage change"""
        if len(self.price_history) < 2:
            return 0
        
        sorted_history = sorted(self.price_history, key=lambda x: x.scraped_at, reverse=True)
        latest = sorted_history[0].price
        previous = sorted_history[1].price
        
        if previous == 0:
            return 0
        
        return round(((latest - previous) / previous) * 100, 1)


class PriceHistory(db.Model):
    __tablename__ = 'price_history'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    scraped_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PriceHistory {self.price} at {self.scraped_at}>'