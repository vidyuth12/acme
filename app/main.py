from flask import Blueprint, render_template, jsonify

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('upload.html')

@main_bp.route('/products')
def products():
    return render_template('products.html')

@main_bp.route('/webhooks')
def webhooks():
    return render_template('webhooks.html')

@main_bp.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'acme-product-importer'
    }), 200
