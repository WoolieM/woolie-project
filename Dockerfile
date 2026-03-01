# Start with a clean Python 3.13 image (matching your dev environment)
FROM python:3.13-slim

WORKDIR /app

# Copy ONLY the ingestion-specific requirements
COPY requirements_ingest.txt .
RUN pip install --no-cache-dir -r requirements_ingest.txt

# Copy only the necessary application folders
# This keeps the image small and excludes dbt_project/notebooks
COPY app/ ./app/

# Run the simulation script
CMD ["python", "app/main.py"]