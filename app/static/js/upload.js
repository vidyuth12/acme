class UploadManager {
    constructor() {
        this.fileInput = document.getElementById('fileInput');
        this.uploadButton = document.getElementById('uploadButton');
        this.retryButton = document.getElementById('retryButton');
        this.progressSection = document.getElementById('progressSection');
        this.statusText = document.getElementById('statusText');
        this.progressBar = document.getElementById('progressBar');
        this.progressBarText = document.getElementById('progressBarText');
        this.progressPercentage = document.getElementById('progressPercentage');
        this.fileInfo = document.getElementById('fileInfo');
        
        this.selectedFile = null;
        this.currentJobId = null;
        this.eventSource = null;
        
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        this.uploadButton.addEventListener('click', () => this.handleUpload());
        this.retryButton.addEventListener('click', () => this.handleRetry());
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        
        if (!file) {
            this.selectedFile = null;
            this.uploadButton.disabled = true;
            this.fileInfo.classList.remove('active');
            return;
        }

        if (!file.name.endsWith('.csv')) {
            this.showError('Please select a valid CSV file');
            this.fileInput.value = '';
            this.uploadButton.disabled = true;
            return;
        }

        this.selectedFile = file;
        this.uploadButton.disabled = false;
        
        const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);
        this.fileInfo.innerHTML = `<strong>Selected:</strong> ${file.name} (${fileSizeMB} MB)`;
        this.fileInfo.classList.add('active');
    }

    async handleUpload() {
        if (!this.selectedFile) return;

        this.uploadButton.disabled = true;
        this.fileInput.disabled = true;
        this.showProgress();
        this.updateStatus('Uploading file...', false);
        this.updateProgressBar(0);

        const formData = new FormData();
        formData.append('file', this.selectedFile);

        try {
            const response = await fetch('/api/products/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Upload failed');
            }

            const data = await response.json();
            this.currentJobId = data.job_id;
            
            this.subscribeToProgress(this.currentJobId);
            
        } catch (error) {
            this.showError(`Upload failed: ${error.message}`);
            this.showRetryButton();
        }
    }

    subscribeToProgress(jobId) {
        if (this.eventSource) {
            this.eventSource.close();
        }

        this.eventSource = new EventSource(`/api/jobs/${jobId}/events`);

        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleProgressUpdate(data);
            } catch (error) {
                console.error('Error parsing SSE data:', error);
            }
        };

        this.eventSource.onerror = (error) => {
            console.error('SSE connection error:', error);
            this.eventSource.close();
            
            if (this.statusText.textContent !== 'Import Complete') {
                this.showError('Connection lost. Please retry.');
                this.showRetryButton();
            }
        };
    }

    handleProgressUpdate(data) {
        const { status, progress, message, state } = data;

        if (state === 'PENDING') {
            this.updateStatus('Queued for processing...', false);
            this.updateProgressBar(0);
        } else if (state === 'STARTED' || state === 'PROGRESS') {
            const progressPercent = progress || 0;
            this.updateProgressBar(progressPercent);
            
            if (message) {
                this.updateStatus(message, false);
            } else if (progressPercent < 25) {
                this.updateStatus('Parsing CSV', false);
            } else if (progressPercent < 75) {
                this.updateStatus('Validating', false);
            } else {
                this.updateStatus('Importing products...', false);
            }
        } else if (state === 'SUCCESS') {
            this.updateProgressBar(100);
            this.updateStatus('Import Complete', true);
            this.eventSource.close();
            this.resetUploadForm();
        } else if (state === 'FAILURE') {
            this.showError(message || 'Import failed');
            this.showRetryButton();
            this.eventSource.close();
        }
    }

    updateStatus(text, isSuccess = false) {
        this.statusText.textContent = text;
        this.statusText.classList.remove('success', 'error', 'processing');
        
        if (isSuccess) {
            this.statusText.classList.add('success');
        } else if (text.toLowerCase().includes('failed') || text.toLowerCase().includes('error')) {
            this.statusText.classList.add('error');
        } else {
            this.statusText.classList.add('processing');
        }
    }

    updateProgressBar(percent) {
        const clampedPercent = Math.min(100, Math.max(0, percent));
        this.progressBar.style.width = `${clampedPercent}%`;
        this.progressBarText.textContent = `${Math.round(clampedPercent)}%`;
        this.progressPercentage.textContent = `${Math.round(clampedPercent)}% Complete`;
    }

    showProgress() {
        this.progressSection.classList.add('active');
        this.retryButton.classList.add('hidden');
    }

    showError(message) {
        this.updateStatus(message, false);
        this.statusText.classList.add('error');
    }

    showRetryButton() {
        this.retryButton.classList.remove('hidden');
        this.uploadButton.disabled = false;
        this.fileInput.disabled = false;
    }

    handleRetry() {
        this.retryButton.classList.add('hidden');
        this.progressSection.classList.remove('active');
        this.updateProgressBar(0);
        
        if (this.selectedFile) {
            this.handleUpload();
        }
    }

    resetUploadForm() {
        setTimeout(() => {
            this.fileInput.value = '';
            this.fileInput.disabled = false;
            this.uploadButton.disabled = true;
            this.selectedFile = null;
            this.fileInfo.classList.remove('active');
        }, 2000);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new UploadManager();
});
