from typing import List, Dict, Any, Optional
from app.extensions import db
from app.models.webhook import Webhook

class WebhookService:
    
    @staticmethod
    def get_webhooks() -> List[Webhook]:
        return db.session.query(Webhook).order_by(Webhook.created_at.desc()).all()
    
    @staticmethod
    def get_webhook_by_id(webhook_id: int) -> Optional[Webhook]:
        return db.session.query(Webhook).filter_by(id=webhook_id).first()
    
    @staticmethod
    def create_webhook(data: Dict[str, Any]) -> Webhook:
        webhook = Webhook.from_dict(data)
        db.session.add(webhook)
        db.session.commit()
        return webhook
    
    @staticmethod
    def update_webhook(webhook_id: int, data: Dict[str, Any]) -> Optional[Webhook]:
        webhook = WebhookService.get_webhook_by_id(webhook_id)
        if not webhook:
            return None
        
        webhook.update_from_dict(data)
        db.session.commit()
        return webhook
    
    @staticmethod
    def delete_webhook(webhook_id: int) -> bool:
        webhook = WebhookService.get_webhook_by_id(webhook_id)
        if not webhook:
            return False
        
        db.session.delete(webhook)
        db.session.commit()
        return True
    
    @staticmethod
    def update_test_result(webhook_id: int, status: str, response_code: int = None, response_time: float = None):
        webhook = WebhookService.get_webhook_by_id(webhook_id)
        if webhook:
            webhook.update_test_result(status, response_code, response_time)
            db.session.commit()
    
    @staticmethod
    def get_webhooks_by_event(event_type: str) -> List[Webhook]:
        """Get all enabled webhooks that listen to a specific event type."""
        return db.session.query(Webhook).filter(
            Webhook.enabled == True,
            Webhook.event_types.contains([event_type])
        ).all()
    
    @staticmethod
    def trigger_webhooks(event_type: str, payload: Dict[str, Any]):
        """Trigger all webhooks for a specific event type."""
        from app.tasks.webhook_delivery import deliver_webhook
        
        webhooks = WebhookService.get_webhooks_by_event(event_type)
        
        for webhook in webhooks:
            deliver_webhook.delay(webhook.id, payload)
        
        return len(webhooks)
