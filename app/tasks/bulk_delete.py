from celery import current_task
from app.extensions import celery, db
from app.models.product import Product
from app.utils.progress_tracker import ProgressTracker
from app.services.import_service import ImportService

@celery.task(bind=True)
def bulk_delete_products(self, job_id: str):
    tracker = ProgressTracker()
    
    try:
        tracker.publish_progress(job_id, 'STARTED', 0, 'Starting bulk delete')
        ImportService.update_job_status(job_id, 'STARTED')
        
        total_count = db.session.query(Product).count()
        tracker.publish_progress(job_id, 'PROGRESS', 10, f'Found {total_count} products to delete', total=total_count)
        ImportService.update_job_status(job_id, 'PROGRESS', total_rows=total_count)
        
        batch_size = 1000
        deleted = 0
        
        while True:
            products = db.session.query(Product).limit(batch_size).all()
            
            if not products:
                break
            
            for product in products:
                db.session.delete(product)
            
            db.session.commit()
            deleted += len(products)
            
            progress = int((deleted / total_count) * 100) if total_count > 0 else 100
            tracker.publish_progress(
                job_id, 'PROGRESS', progress,
                f'Deleted {deleted} of {total_count} products',
                deleted=deleted,
                total=total_count
            )
            ImportService.update_job_status(job_id, 'PROGRESS', processed_rows=deleted)
        
        tracker.publish_progress(job_id, 'SUCCESS', 100, f'Deleted {deleted} products', deleted=deleted)
        ImportService.update_job_status(
            job_id, 
            'SUCCESS', 
            processed_rows=deleted,
            success_count=deleted,
            error_count=0
        )
        
        return {
            'status': 'SUCCESS',
            'job_id': job_id,
            'deleted': deleted
        }
        
    except Exception as e:
        error_message = str(e)
        tracker.publish_progress(job_id, 'FAILURE', 0, f'Failed: {error_message}')
        ImportService.update_job_status(job_id, 'FAILURE', error_message=error_message)
        raise
