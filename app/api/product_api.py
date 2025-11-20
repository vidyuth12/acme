from flask import Blueprint, request, jsonify
from app.services.product_service import ProductService

product_bp = Blueprint('products', __name__)

@product_bp.route('', methods=['GET'])
def list_products():
    sku = request.args.get('sku')
    name = request.args.get('name')
    description = request.args.get('description')
    active = request.args.get('active')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    
    if active is not None:
        active = active.lower() in ('true', '1', 'yes')
    
    result = ProductService.get_products(
        sku=sku,
        name=name,
        description=description,
        active=active,
        limit=limit,
        offset=offset
    )
    
    return jsonify(result), 200

@product_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id: int):
    product = ProductService.get_product_by_id(product_id)
    
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    return jsonify(product.to_dict()), 200

@product_bp.route('', methods=['POST'])
def create_product():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    required_fields = ['sku', 'name', 'price']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    try:
        product = ProductService.create_product(data)
        return jsonify(product.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@product_bp.route('/<int:product_id>', methods=['PUT'])
def update_product(product_id: int):
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        product = ProductService.update_product(product_id, data)
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        return jsonify(product.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@product_bp.route('/<int:product_id>', methods=['DELETE'])
def delete_product(product_id: int):
    success = ProductService.delete_product(product_id)
    
    if not success:
        return jsonify({'error': 'Product not found'}), 404
    
    return jsonify({'message': 'Product deleted successfully'}), 200

@product_bp.route('/delete_all', methods=['POST'])
def delete_all_products():
    data = request.get_json() or {}
    confirmation = data.get('confirmation')
    
    if confirmation != 'DELETE_ALL':
        return jsonify({'error': 'Confirmation required. Send {"confirmation": "DELETE_ALL"}'}), 400
    
    from app.services.import_service import ImportService
    from app.tasks.bulk_delete import bulk_delete_products
    
    job = ImportService.create_import_job('bulk_delete_products.csv')
    
    bulk_delete_products.delay(job.id)
    
    return jsonify({
        'job_id': job.id,
        'message': 'Bulk delete started',
        'status': 'PENDING'
    }), 202

