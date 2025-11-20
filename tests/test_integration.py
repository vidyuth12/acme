import pytest
import io
from app.models.import_job import ImportJob

def test_upload_to_import_flow(client, mocker):
    # Mock Celery task
    mock_task = mocker.patch('app.tasks.csv_import.process_csv_import.delay')
    mock_task.return_value.id = 'import-job-id'
    
    # Create dummy CSV
    csv_content = b"sku,name,price\nTEST-INT-1,Integration Product,100.00"
    data = {
        'file': (io.BytesIO(csv_content), 'test_products.csv')
    }
    
    response = client.post('/api/products/upload', data=data, content_type='multipart/form-data')
    
    assert response.status_code == 202
    json_data = response.get_json()
    assert json_data['job_id'] is not None
    assert json_data['status'] == 'PENDING'
    
    # Verify Job created in DB
    job = ImportJob.query.filter_by(id=json_data['job_id']).first()
    assert job is not None
    assert job.filename == 'test_products.csv'
    
    # Verify task called
    mock_task.assert_called_once()
