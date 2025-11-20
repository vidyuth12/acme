class ProductManager {
    constructor() {
        this.currentPage = 0;
        this.limit = 20;
        this.filters = {};
        this.editingProductId = null;

        this.initializeEventListeners();
        this.loadProducts();
    }

    initializeEventListeners() {
        document.getElementById('productForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveProduct();
        });
    }

    async loadProducts() {
        const params = new URLSearchParams({
            limit: this.limit,
            offset: this.currentPage * this.limit,
            ...this.filters
        });

        try {
            const response = await fetch(`/api/products?${params}`);
            const data = await response.json();

            this.renderProducts(data.products);
            this.updatePagination(data);
        } catch (error) {
            console.error('Error loading products:', error);
            this.showError('Failed to load products');
        }
    }

    renderProducts(products) {
        const tbody = document.getElementById('productTableBody');

        if (products.length === 0) {
            tbody.innerHTML = '<tr class="empty-state"><td colspan="5">No products found</td></tr>';
            return;
        }

        tbody.innerHTML = products.map(product => `
            <tr>
                <td>${this.escapeHtml(product.sku)}</td>
                <td>${this.escapeHtml(product.name)}</td>
                <td>${this.escapeHtml(product.description || '')}</td>
                <td>
                    <span class="status-badge ${product.active ? 'status-active' : 'status-inactive'}">
                        ${product.active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td>
                    <div class="actions">
                        <button class="button button-small button-primary" onclick="productManager.editProduct(${product.id})">Edit</button>
                        <button class="button button-small button-danger" onclick="productManager.deleteProduct(${product.id})">Delete</button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    updatePagination(data) {
        const info = document.getElementById('paginationInfo');
        const start = this.currentPage * this.limit + 1;
        const end = Math.min(start + data.products.length - 1, data.total);

        info.textContent = `Showing ${start}-${end} of ${data.total} products`;

        document.getElementById('prevButton').disabled = this.currentPage === 0;
        document.getElementById('nextButton').disabled = (this.currentPage + 1) * this.limit >= data.total;
    }

    applyFilters() {
        this.filters = {};

        const sku = document.getElementById('filterSku').value.trim();
        const name = document.getElementById('filterName').value.trim();
        const active = document.getElementById('filterActive').value;

        if (sku) this.filters.sku = sku;
        if (name) this.filters.name = name;
        if (active) this.filters.active = active;

        this.currentPage = 0;
        this.loadProducts();
    }

    previousPage() {
        if (this.currentPage > 0) {
            this.currentPage--;
            this.loadProducts();
        }
    }

    nextPage() {
        this.currentPage++;
        this.loadProducts();
    }

    openCreateModal() {
        this.editingProductId = null;
        document.getElementById('modalTitle').textContent = 'Create Product';
        document.getElementById('productForm').reset();
        document.getElementById('productModal').classList.add('active');
    }

    async editProduct(productId) {
        try {
            const response = await fetch(`/api/products/${productId}`);
            const product = await response.json();

            this.editingProductId = productId;
            document.getElementById('modalTitle').textContent = 'Edit Product';
            document.getElementById('productSku').value = product.sku;
            document.getElementById('productName').value = product.name;
            document.getElementById('productDescription').value = product.description || '';
            document.getElementById('productPrice').value = product.price;
            document.getElementById('productActive').value = product.active.toString();

            document.getElementById('productModal').classList.add('active');
        } catch (error) {
            console.error('Error loading product:', error);
            this.showError('Failed to load product');
        }
    }

    async saveProduct() {
        const data = {
            sku: document.getElementById('productSku').value,
            name: document.getElementById('productName').value,
            description: document.getElementById('productDescription').value,
            price: parseFloat(document.getElementById('productPrice').value),
            active: document.getElementById('productActive').value === 'true'
        };

        try {
            const url = this.editingProductId
                ? `/api/products/${this.editingProductId}`
                : '/api/products';

            const method = this.editingProductId ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to save product');
            }

            this.closeModal();
            this.loadProducts();
            this.showToast('Product saved successfully', 'success');
        } catch (error) {
            console.error('Error saving product:', error);
            this.showError(error.message);
        }
    }

    async deleteProduct(productId) {
        if (!confirm('Are you sure you want to delete this product?')) {
            return;
        }

        try {
            const response = await fetch(`/api/products/${productId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('Failed to delete product');
            }

            this.loadProducts();
            this.showToast('Product deleted successfully', 'success');
        } catch (error) {
            console.error('Error deleting product:', error);
            this.showError('Failed to delete product');
        }
    }

    async deleteAllProducts() {
        if (!confirm('Are you sure you want to delete ALL products? This cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch('/api/products/delete_all', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ confirmation: 'DELETE_ALL' })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to start bulk delete');
            }

            const result = await response.json();
            this.showToast(`Bulk delete started. Job ID: ${result.job_id}`, 'info');

            this.monitorBulkDelete(result.job_id);
        } catch (error) {
            console.error('Error starting bulk delete:', error);
            this.showError(error.message);
        }
    }

    async monitorBulkDelete(jobId) {
        const eventSource = new EventSource(`/api/jobs/${jobId}/events`);

        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Bulk delete progress:', data);

            if (data.state === 'SUCCESS') {
                eventSource.close();
                this.showToast('Bulk delete completed successfully!', 'success');
                this.loadProducts();
            } else if (data.state === 'FAILURE') {
                eventSource.close();
                this.showError(`Bulk delete failed: ${data.message}`);
            }
        };

        eventSource.onerror = () => {
            eventSource.close();
            console.error('Connection to bulk delete progress lost');
        };
    }

    closeModal() {
        document.getElementById('productModal').classList.remove('active');
        document.getElementById('productForm').reset();
        this.editingProductId = null;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showError(message) {
        this.showToast(message, 'error');
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        toast.innerHTML = `
            <span>${message}</span>
            <button onclick="this.parentElement.remove()" style="background:none;border:none;color:white;cursor:pointer;font-size:18px;">&times;</button>
        `;

        container.appendChild(toast);

        // Auto remove after 3 seconds
        setTimeout(() => {
            toast.style.animation = 'fadeOut 0.3s ease-out forwards';
            toast.addEventListener('animationend', () => {
                toast.remove();
            });
        }, 3000);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.productManager = new ProductManager();
});
