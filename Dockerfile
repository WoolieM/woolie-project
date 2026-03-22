# Start with a clean Python 3.13 image (matching your dev environment)
FROM python:3.13-slim


# 2. Prevent Python from writing .pyc files and enable real-time logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# Copy ONLY the ingestion-specific requirements
COPY requirements_ingest.txt .
RUN pip install --no-cache-dir -r requirements_ingest.txt

# Copy only the necessary application folders
# This keeps the image small and excludes dbt_project/notebooks
COPY app/ ./app/

# Run the simulation script
# To run smoke test: docker run --rm --env-file .env --entrypoint python bitcoin-ingest:dev -m app.simulation.smoke_test
ENTRYPOINT ["python", "-m", "app.simulation.main"]
CMD ["--minutes", "2"]