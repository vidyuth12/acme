import pytest
from app.models.product import Product
from app.extensions import db

def test_get_products_empty(client):
    response = client.get('/api/products')
    assert response.status_code == 200
    data = response.get_json()
    assert data['products'] == []
    assert data['total'] == 0

def test_create_product(client):
    payload = {
        'sku': 'TEST-CRUD-1',
        'name': 'CRUD Product',
        'price': 99.99,
        'description': 'A test product',
        'active': True
    }
    response = client.post('/api/products', json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data['sku'] == 'TEST-CRUD-1'
    assert data['id'] is not None

def test_get_product_by_id(client):
    # Create first
    p = Product(sku='GET-TEST', name='Get Me', price=10.0)
    db.session.add(p)
    db.session.commit()
    
    response = client.get(f'/api/products/{p.id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['sku'] == 'GET-TEST'

def test_update_product(client):
    p = Product(sku='UPDATE-TEST', name='Update Me', price=10.0)
    db.session.add(p)
    db.session.commit()
    
    payload = {'name': 'Updated Name', 'price': 20.0}
    response = client.put(f'/api/products/{p.id}', json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'Updated Name'
    assert data['price'] == 20.0

def test_delete_product(client):
    p = Product(sku='DELETE-TEST', name='Delete Me', price=10.0)
    db.session.add(p)
    db.session.commit()
    
    response = client.delete(f'/api/products/{p.id}')
    assert response.status_code == 200
    
    # Verify gone
    response = client.get(f'/api/products/{p.id}')
    assert response.status_code == 404

def test_bulk_delete_products(client, mocker):
    # Mock the Celery task
    mock_task = mocker.patch('app.tasks.bulk_delete.bulk_delete_products.delay')
    mock_task.return_value.id = 'fake-job-id'
    
    payload = {'confirmation': 'DELETE_ALL'}
    response = client.post('/api/products/delete_all', json=payload)
    assert response.status_code == 202
    data = response.get_json()
    assert data['job_id'] is not None
    mock_task.assert_called_once()
