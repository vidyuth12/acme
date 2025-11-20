import time
import requests
from celery import current_task
from app.extensions import celery
from app.services.webhook_service import WebhookService

@celery.task(bind=True)
def test_webhook_delivery(self, webhook_id: int, test_payload: dict):
    webhook = WebhookService.get_webhook_by_id(webhook_id)
    
    if not webhook:
        return {'error': 'Webhook not found'}
    
    try:
        start_time = time.time()
        
        response = requests.post(
            webhook.url,
            json=test_payload,
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        
        response_time = time.time() - start_time
        
        WebhookService.update_test_result(
            webhook_id,
            status='SUCCESS' if response.ok else 'FAILED',
            response_code=response.status_code,
            response_time=round(response_time, 3)
        )
        
        return {
            'status': 'SUCCESS' if response.ok else 'FAILED',
            'response_code': response.status_code,
            'response_time': round(response_time, 3),
            'webhook_id': webhook_id
        }
        
    except requests.exceptions.Timeout:
        WebhookService.update_test_result(webhook_id, status='TIMEOUT')
        return {
            'status': 'TIMEOUT',
            'webhook_id': webhook_id
        }
    except Exception as e:
        WebhookService.update_test_result(webhook_id, status='ERROR')
        return {
            'status': 'ERROR',
            'error': str(e),
            'webhook_id': webhook_id
        }

@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def deliver_webhook(self, webhook_id: int, event_payload: dict):
    webhook = WebhookService.get_webhook_by_id(webhook_id)
    
    if not webhook:
        return {'error': 'Webhook not found'}
    
    if not webhook.enabled:
        return {'error': 'Webhook is disabled', 'webhook_id': webhook_id}
    
    try:
        start_time = time.time()
        
        response = requests.post(
            webhook.url,
            json=event_payload,
            timeout=30,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Acme-Webhook-Delivery/1.0'
            }
        )
        
        response_time = time.time() - start_time
        
        WebhookService.update_test_result(
            webhook_id,
            status='SUCCESS' if response.ok else 'FAILED',
            response_code=response.status_code,
            response_time=round(response_time, 3)
        )
        
        if response.status_code >= 500:
            retry_delay = 60 * (2 ** self.request.retries)
            raise self.retry(countdown=retry_delay, exc=Exception(f'Server error: {response.status_code}'))
        
        return {
            'status': 'SUCCESS' if response.ok else 'FAILED',
            'response_code': response.status_code,
            'response_time': round(response_time, 3),
            'webhook_id': webhook_id,
            'retries': self.request.retries
        }
        
    except requests.exceptions.Timeout:
        WebhookService.update_test_result(webhook_id, status='TIMEOUT')
        retry_delay = 60 * (2 ** self.request.retries)
        raise self.retry(countdown=retry_delay, exc=Exception('Request timeout'))
        
    except requests.exceptions.ConnectionError as e:
        WebhookService.update_test_result(webhook_id, status='ERROR')
        retry_delay = 60 * (2 ** self.request.retries)
        raise self.retry(countdown=retry_delay, exc=e)
        
    except Exception as e:
        WebhookService.update_test_result(webhook_id, status='ERROR')
        
        if self.request.retries < self.max_retries:
            retry_delay = 60 * (2 ** self.request.retries)
            raise self.retry(countdown=retry_delay, exc=e)
        
        return {
            'status': 'ERROR',
            'error': str(e),
            'webhook_id': webhook_id,
            'retries': self.request.retries
        }
