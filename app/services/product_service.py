from typing import List, Dict, Any, Optional
from sqlalchemy import or_, and_
from app.extensions import db
from app.models.product import Product

class ProductService:
    
    @staticmethod
    def get_products(
        sku: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        query = db.session.query(Product)
        
        filters = []
        if sku:
            filters.append(db.func.lower(Product.sku) == sku.lower())
        if name:
            filters.append(Product.name.ilike(f'%{name}%'))
        if description:
            filters.append(Product.description.ilike(f'%{description}%'))
        if active is not None:
            filters.append(Product.active == active)
        
        if filters:
            query = query.filter(and_(*filters))
        
        total = query.count()
        products = query.order_by(Product.created_at.desc()).limit(limit).offset(offset).all()
        
        return {
            'products': [p.to_dict() for p in products],
            'total': total,
            'limit': limit,
            'offset': offset
        }
    
    @staticmethod
    def get_product_by_id(product_id: int) -> Optional[Product]:
        return db.session.query(Product).filter_by(id=product_id).first()
    
    @staticmethod
    def create_product(data: Dict[str, Any]) -> Product:
        product = Product.from_dict(data)
        db.session.add(product)
        db.session.commit()
        return product
    
    @staticmethod
    def update_product(product_id: int, data: Dict[str, Any]) -> Optional[Product]:
        product = ProductService.get_product_by_id(product_id)
        if not product:
            return None
        
        product.update_from_dict(data)
        db.session.commit()
        return product
    
    @staticmethod
    def delete_product(product_id: int) -> bool:
        product = ProductService.get_product_by_id(product_id)
        if not product:
            return False
        
        db.session.delete(product)
        db.session.commit()
        return True
    
    @staticmethod
    def delete_all_products() -> int:
        count = db.session.query(Product).count()
        db.session.query(Product).delete()
        db.session.commit()
        return count
