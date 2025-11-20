class WebhookManager {
    constructor() {
        this.editingWebhookId = null;
        this.pollingInterval = null;
        this.initializeEventListeners();
        this.loadWebhooks();
        this.startProgressPolling();
    }

    initializeEventListeners() {
        document.getElementById('webhookForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveWebhook();
        });
    }

    async loadWebhooks() {
        try {
            const response = await fetch('/api/webhooks');
            const webhooks = await response.json();

            this.renderWebhooks(webhooks);
        } catch (error) {
            console.error('Error loading webhooks:', error);
            this.showError('Failed to load webhooks');
        }
    }

    renderWebhooks(webhooks) {
        const tbody = document.getElementById('webhookTableBody');

        if (webhooks.length === 0) {
            tbody.innerHTML = '<tr class="empty-state"><td colspan="6">No webhooks configured</td></tr>';
            return;
        }

        tbody.innerHTML = webhooks.map(webhook => {
            const eventTypes = Array.isArray(webhook.event_types)
                ? webhook.event_types.join(', ')
                : webhook.event_types;

            const testResult = this.formatTestResult(webhook);

            return `
                <tr>
                    <td>${this.escapeHtml(webhook.name)}</td>
                    <td style="word-break: break-all; max-width: 300px;">${this.escapeHtml(webhook.url)}</td>
                    <td><span class="event-types">${this.escapeHtml(eventTypes)}</span></td>
                    <td>
                        <span class="status-badge ${webhook.enabled ? 'status-enabled' : 'status-disabled'}">
                            ${webhook.enabled ? 'Enabled' : 'Disabled'}
                        </span>
                    </td>
                    <td>${testResult}</td>
                    <td>
                        <div class="actions">
                            <button class="button button-small button-success" onclick="webhookManager.testWebhook(${webhook.id})">Test</button>
                            <button class="button button-small button-primary" onclick="webhookManager.editWebhook(${webhook.id})">Edit</button>
                            <button class="button button-small button-danger" onclick="webhookManager.deleteWebhook(${webhook.id})">Delete</button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
    }

    formatTestResult(webhook) {
        if (!webhook.last_test_status) {
            return '<span class="test-result">Not tested</span>';
        }

        const statusClass = webhook.last_test_status === 'SUCCESS' ? 'success' : 'error';
        const responseCode = webhook.last_test_response_code || 'N/A';
        const responseTime = webhook.last_test_response_time
            ? `${(webhook.last_test_response_time * 1000).toFixed(0)}ms`
            : 'N/A';

        return `
            <span class="test-result ${statusClass}">
                ${webhook.last_test_status}<br>
                Code: ${responseCode} | Time: ${responseTime}
            </span>
        `;
    }

    openCreateModal() {
        this.editingWebhookId = null;
        document.getElementById('modalTitle').textContent = 'Create Webhook';
        document.getElementById('webhookForm').reset();
        document.getElementById('webhookEnabled').checked = true;
        document.getElementById('webhookModal').classList.add('active');
    }

    async editWebhook(webhookId) {
        try {
            const response = await fetch(`/api/webhooks/${webhookId}`);
            const webhook = await response.json();

            this.editingWebhookId = webhookId;
            document.getElementById('modalTitle').textContent = 'Edit Webhook';
            document.getElementById('webhookName').value = webhook.name;
            document.getElementById('webhookUrl').value = webhook.url;
            document.getElementById('webhookEnabled').checked = webhook.enabled;

            // Set event type checkboxes
            document.getElementById('eventUploadCompleted').checked = webhook.event_types.includes('upload.completed');
            document.getElementById('eventUploadFailed').checked = webhook.event_types.includes('upload.failed');
            document.getElementById('eventProductCreated').checked = webhook.event_types.includes('product.created');
            document.getElementById('eventProductUpdated').checked = webhook.event_types.includes('product.updated');
            document.getElementById('eventProductDeleted').checked = webhook.event_types.includes('product.deleted');

            document.getElementById('webhookModal').classList.add('active');
        } catch (error) {
            console.error('Error loading webhook:', error);
            this.showError('Failed to load webhook');
        }
    }

    async saveWebhook() {
        const eventTypes = [];
        if (document.getElementById('eventUploadCompleted').checked) eventTypes.push('upload.completed');
        if (document.getElementById('eventUploadFailed').checked) eventTypes.push('upload.failed');
        if (document.getElementById('eventProductCreated').checked) eventTypes.push('product.created');
        if (document.getElementById('eventProductUpdated').checked) eventTypes.push('product.updated');
        if (document.getElementById('eventProductDeleted').checked) eventTypes.push('product.deleted');

        if (eventTypes.length === 0) {
            this.showError('Please select at least one event type');
            return;
        }

        const data = {
            name: document.getElementById('webhookName').value,
            url: document.getElementById('webhookUrl').value,
            event_types: eventTypes,
            enabled: document.getElementById('webhookEnabled').checked
        };

        try {
            const url = this.editingWebhookId
                ? `/api/webhooks/${this.editingWebhookId}`
                : '/api/webhooks';

            const method = this.editingWebhookId ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to save webhook');
            }

            this.closeModal();
            this.loadWebhooks();
            this.showToast('Webhook saved successfully', 'success');
        } catch (error) {
            console.error('Error saving webhook:', error);
            this.showError(error.message);
        }
    }

    async deleteWebhook(webhookId) {
        if (!confirm('Are you sure you want to delete this webhook?')) {
            return;
        }

        try {
            const response = await fetch(`/api/webhooks/${webhookId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('Failed to delete webhook');
            }

            this.loadWebhooks();
            this.showToast('Webhook deleted successfully', 'success');
        } catch (error) {
            console.error('Error deleting webhook:', error);
            this.showError('Failed to delete webhook');
        }
    }

    async testWebhook(webhookId) {
        try {
            this.showToast('Testing webhook...', 'info');

            const response = await fetch(`/api/webhooks/${webhookId}/test`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error('Failed to initiate webhook test');
            }

            const result = await response.json();

            // Poll for test result
            setTimeout(() => this.checkTestResult(webhookId), 2000);
        } catch (error) {
            console.error('Error testing webhook:', error);
            this.showError('Failed to test webhook');
        }
    }

    async checkTestResult(webhookId) {
        try {
            const response = await fetch(`/api/webhooks/${webhookId}`);
            const webhook = await response.json();

            if (webhook.last_test_status) {
                const message = webhook.last_test_status === 'SUCCESS'
                    ? `Test successful! Response: ${webhook.last_test_response_code} (${(webhook.last_test_response_time * 1000).toFixed(0)}ms)`
                    : `Test failed: ${webhook.last_test_status}`;

                const type = webhook.last_test_status === 'SUCCESS' ? 'success' : 'error';
                this.showToast(message, type);
                this.loadWebhooks();
            }
        } catch (error) {
            console.error('Error checking test result:', error);
        }
    }

    closeModal() {
        document.getElementById('webhookModal').classList.remove('active');
        document.getElementById('webhookForm').reset();
        this.editingWebhookId = null;
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

    async loadRecentUploads() {
        try {
            const response = await fetch('/api/uploads/recent');
            const uploads = await response.json();

            this.renderUploadHistory(uploads);
        } catch (error) {
            console.error('Error loading recent uploads:', error);
        }
    }

    renderUploadHistory(uploads) {
        const tbody = document.getElementById('uploadHistoryBody');

        if (uploads.length === 0) {
            tbody.innerHTML = '<tr class="empty-state"><td colspan="7">No upload history</td></tr>';
            return;
        }

        tbody.innerHTML = uploads.map(upload => {
            const statusClass = upload.status === 'SUCCESS' ? 'upload-status-success' :
                upload.status === 'FAILURE' ? 'upload-status-failure' :
                    upload.status === 'PROGRESS' || upload.status === 'STARTED' ? 'upload-status-progress' :
                        'upload-status-pending';

            const progressClass = upload.status === 'SUCCESS' ? 'completed' :
                upload.status === 'FAILURE' ? 'failed' : '';

            const createdAt = upload.created_at ? new Date(upload.created_at).toLocaleString() : 'N/A';
            const completedAt = upload.completed_at ? new Date(upload.completed_at).toLocaleString() :
                (upload.status === 'SUCCESS' || upload.status === 'FAILURE' ? 'N/A' : 'In Progress');

            return `
                <tr>
                    <td style="word-break: break-all; max-width: 200px;">${this.escapeHtml(upload.filename)}</td>
                    <td><span class="upload-status-badge ${statusClass}">${upload.status}</span></td>
                    <td style="min-width: 120px;">
                        <div class="progress-bar-cell">
                            <div class="progress-fill ${progressClass}" style="width: ${upload.progress}%"></div>
                        </div>
                        <span style="font-size: 11px; color: #666;">${upload.progress}%</span>
                    </td>
                    <td>${upload.success_count || 0}</td>
                    <td>${upload.error_count || 0}</td>
                    <td style="font-size: 12px;">${createdAt}</td>
                    <td style="font-size: 12px;">${completedAt}</td>
                </tr>
            `;
        }).join('');
    }

    startProgressPolling() {
        // Load immediately
        this.loadRecentUploads();

        // Poll every 2 seconds
        this.pollingInterval = setInterval(() => {
            this.loadRecentUploads();
        }, 2000);
    }

    stopProgressPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.webhookManager = new WebhookManager();
});
