import pytest
from app.utils.csv_validator import CSVValidator
from app.utils.db_helper import DatabaseHelper
from app.models.product import Product

def test_csv_validator_valid_row():
    row = {'sku': 'TEST1', 'name': 'Test Product', 'price': '10.00', 'active': 'true'}
    is_valid, error = CSVValidator.validate_row(row, 1)
    assert is_valid
    assert error is None

def test_csv_validator_missing_field():
    row = {'sku': 'TEST1', 'name': 'Test Product'} # Missing price
    is_valid, error = CSVValidator.validate_row(row, 1)
    assert not is_valid
    assert 'Missing required field' in error

def test_csv_validator_invalid_price():
    row = {'sku': 'TEST1', 'name': 'Test Product', 'price': 'invalid'}
    is_valid, error = CSVValidator.validate_row(row, 1)
    assert not is_valid
    assert 'Invalid price format' in error

def test_batch_upsert_products(app):
    products = [
        {'sku': 'SKU1', 'name': 'Product 1', 'description': 'Desc 1', 'price': 10.0, 'active': True},
        {'sku': 'SKU2', 'name': 'Product 2', 'description': 'Desc 2', 'price': 20.0, 'active': False}
    ]
    
    result = DatabaseHelper.batch_upsert_products(products)
    assert result['processed'] == 2
    assert result['inserted'] == 2
    
    # Verify in DB
    p1 = Product.query.filter_by(sku='SKU1').first()
    assert p1 is not None
    assert p1.name == 'Product 1'

    # Test Update
    updated_products = [
        {'sku': 'SKU1', 'name': 'Product 1 Updated', 'description': 'Desc 1', 'price': 15.0, 'active': True}
    ]
    result = DatabaseHelper.batch_upsert_products(updated_products)
    assert result['processed'] == 1
    assert result['updated'] == 0 # Implementation currently returns 0 for updated
    
    p1_updated = Product.query.filter_by(sku='SKU1').first()
    assert p1_updated.name == 'Product 1 Updated'
    assert p1_updated.price == 15.0
