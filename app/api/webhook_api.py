from flask import Blueprint, request, jsonify
from app.services.webhook_service import WebhookService
from app.tasks.webhook_delivery import test_webhook_delivery

webhook_bp = Blueprint('webhooks', __name__)

@webhook_bp.route('', methods=['GET'])
def list_webhooks():
    webhooks = WebhookService.get_webhooks()
    return jsonify([w.to_dict() for w in webhooks]), 200

@webhook_bp.route('/<int:webhook_id>', methods=['GET'])
def get_webhook(webhook_id: int):
    webhook = WebhookService.get_webhook_by_id(webhook_id)
    
    if not webhook:
        return jsonify({'error': 'Webhook not found'}), 404
    
    return jsonify(webhook.to_dict()), 200

@webhook_bp.route('', methods=['POST'])
def create_webhook():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    required_fields = ['name', 'url', 'event_types']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    try:
        webhook = WebhookService.create_webhook(data)
        return jsonify(webhook.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@webhook_bp.route('/<int:webhook_id>', methods=['PUT'])
def update_webhook(webhook_id: int):
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        webhook = WebhookService.update_webhook(webhook_id, data)
        
        if not webhook:
            return jsonify({'error': 'Webhook not found'}), 404
        
        return jsonify(webhook.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@webhook_bp.route('/<int:webhook_id>', methods=['DELETE'])
def delete_webhook(webhook_id: int):
    success = WebhookService.delete_webhook(webhook_id)
    
    if not success:
        return jsonify({'error': 'Webhook not found'}), 404
    
    return jsonify({'message': 'Webhook deleted successfully'}), 200

@webhook_bp.route('/<int:webhook_id>/test', methods=['POST'])
def test_webhook(webhook_id: int):
    webhook = WebhookService.get_webhook_by_id(webhook_id)
    
    if not webhook:
        return jsonify({'error': 'Webhook not found'}), 404
    
    test_payload = {
        'event': 'test',
        'webhook_id': webhook_id,
        'webhook_name': webhook.name,
        'timestamp': '2025-11-19T00:00:00Z',
        'data': {
            'message': 'This is a test webhook delivery'
        }
    }
    
    result = test_webhook_delivery.delay(webhook_id, test_payload)
    
    return jsonify({
        'message': 'Webhook test initiated',
        'task_id': result.id,
        'webhook_id': webhook_id
    }), 202
