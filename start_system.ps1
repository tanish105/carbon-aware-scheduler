# Start API
Write-Host "Starting API..."
Start-Process -FilePath "python" -ArgumentList "-m uvicorn api.main:app --reload --port 8000"

# Start Worker
Write-Host "Starting Execution Worker..."
Start-Process -FilePath "python" -ArgumentList "-m celery -A worker.tasks worker -Q worker_queue --loglevel=info --pool=solo"

# Start Carbon Fetcher (Beat + Worker)
Write-Host "Starting Carbon Data Fetcher (Beat)..."
Start-Process -FilePath "python" -ArgumentList "-m celery -A carbon_data.fetcher beat --loglevel=info"
Write-Host "Starting Carbon Data Fetcher (Worker)..."
Start-Process -FilePath "python" -ArgumentList "-m celery -A carbon_data.fetcher worker -Q carbon_data_queue --loglevel=info --pool=solo"

# Start Scheduler (Beat + Worker)
Write-Host "Starting Scheduler (Beat)..."
Start-Process -FilePath "python" -ArgumentList "-m celery -A scheduler.main beat --loglevel=info"
Write-Host "Starting Scheduler (Worker)..."
Start-Process -FilePath "python" -ArgumentList "-m celery -A scheduler.main worker -Q scheduler_queue --loglevel=info --pool=solo"

Write-Host "All components started in separate windows."
