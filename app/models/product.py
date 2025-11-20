from datetime import datetime
from app.extensions import db

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        db.Index('ix_products_sku_lower', db.text('LOWER(sku)'), unique=True),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'sku': self.sku,
            'name': self.name,
            'description': self.description,
            'price': float(self.price) if self.price else None,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            sku=data.get('sku'),
            name=data.get('name'),
            description=data.get('description'),
            price=data.get('price'),
            active=data.get('active', True)
        )
    
    def update_from_dict(self, data):
        if 'sku' in data:
            self.sku = data['sku']
        if 'name' in data:
            self.name = data['name']
        if 'description' in data:
            self.description = data['description']
        if 'price' in data:
            self.price = data['price']
        if 'active' in data:
            self.active = data['active']
        self.updated_at = datetime.utcnow()
