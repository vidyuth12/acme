import pytest
from app.models.webhook import Webhook
from app.extensions import db
from app.tasks.webhook_delivery import deliver_webhook

def test_create_webhook(client):
    payload = {
        'name': 'Test Webhook',
        'url': 'http://example.com/hook',
        'event_types': ['product.created'],
        'enabled': True
    }
    response = client.post('/api/webhooks', json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == 'Test Webhook'
    assert data['event_types'] == ['product.created']

def test_deliver_webhook_success(app, mocker):
    # Setup webhook
    webhook = Webhook(name='Test', url='http://example.com', event_types=['test'])
    db.session.add(webhook)
    db.session.commit()
    
    # Mock requests.post
    mock_post = mocker.patch('requests.post')
    mock_post.return_value.ok = True
    mock_post.return_value.status_code = 200
    
    # Run task synchronously
    result = deliver_webhook(webhook.id, {'event': 'test'})
    
    assert result['status'] == 'SUCCESS'
    assert result['response_code'] == 200
    mock_post.assert_called_once()

def test_deliver_webhook_retry(app, mocker):
    webhook = Webhook(name='Test Retry', url='http://example.com', event_types=['test'])
    db.session.add(webhook)
    db.session.commit()
    
    # Mock requests.post to fail with 500
    mock_post = mocker.patch('requests.post')
    mock_post.return_value.ok = False
    mock_post.return_value.status_code = 500
    
    # Mock self.retry to raise exception (to stop infinite loop in test)
    mocker.patch('app.tasks.webhook_delivery.deliver_webhook.retry', side_effect=Exception('Retry triggered'))
    
    with pytest.raises(Exception, match='Retry triggered'):
        deliver_webhook(webhook.id, {'event': 'test'})
