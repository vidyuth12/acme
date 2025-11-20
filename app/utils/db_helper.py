from datetime import datetime
from typing import List, Dict, Any, Iterable
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from app.extensions import db
from app.models.product import Product

class DatabaseHelper:
    
    @staticmethod
    def batch_upsert_products(products: Iterable[Dict[str, Any]], batch_size: int = 1000) -> Dict[str, int]:
        total_processed = 0
        total_inserted = 0
        total_updated = 0
        
        batch = []
        for product_data in products:
            batch.append(DatabaseHelper._prepare_product_data(product_data))
            
            if len(batch) >= batch_size:
                # Deduplicate batch to prevent CardinalityViolation
                deduped_batch = DatabaseHelper._deduplicate_batch(batch)
                inserted, updated = DatabaseHelper._execute_upsert_batch(deduped_batch)
                total_inserted += inserted
                total_updated += updated
                total_processed += len(batch)
                batch = []
        
        if batch:
            deduped_batch = DatabaseHelper._deduplicate_batch(batch)
            inserted, updated = DatabaseHelper._execute_upsert_batch(deduped_batch)
            total_inserted += inserted
            total_updated += updated
            total_processed += len(batch)
        
        return {
            'processed': total_processed,
            'inserted': total_inserted,
            'updated': total_updated
        }
    
    @staticmethod
    def _prepare_product_data(data: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.utcnow()
        return {
            'sku': data.get('sku', '').strip(),
            'name': data.get('name', '').strip(),
            'description': data.get('description', ''),
            'price': float(data.get('price', 0)),
            'active': bool(data.get('active', True)),
            'created_at': now,
            'updated_at': now
        }
    
    @staticmethod
    def _execute_upsert_batch(batch: List[Dict[str, Any]]) -> tuple[int, int]:
        if not batch:
            return 0, 0
        
        stmt = insert(Product.__table__).values(batch)
        
        update_dict = {
            'name': stmt.excluded.name,
            'description': stmt.excluded.description,
            'price': stmt.excluded.price,
            'active': stmt.excluded.active,
            'updated_at': stmt.excluded.updated_at
        }
        
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=[text('LOWER(sku)')],
            set_=update_dict
        )
        
        result = db.session.execute(upsert_stmt)
        db.session.commit()
        
        inserted = result.rowcount if hasattr(result, 'rowcount') else len(batch)
        updated = 0
        
        return inserted, updated
    
    @staticmethod
    def bulk_delete_products() -> int:
        count = db.session.query(Product).count()
        db.session.query(Product).delete()
        db.session.commit()
        return count
    
    @staticmethod
    def get_product_by_sku(sku: str) -> Product:
        return db.session.query(Product).filter(
            db.func.lower(Product.sku) == sku.lower()
        ).first()

    @staticmethod
    def _deduplicate_batch(batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicates a batch of products based on SKU (case-insensitive).
        Later records in the batch overwrite earlier ones.
        """
        sku_map = {}
        for item in batch:
            sku = item.get('sku', '').lower().strip()
            if sku:
                sku_map[sku] = item
        return list(sku_map.values())
