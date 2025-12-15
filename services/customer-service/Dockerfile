FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
COPY services/customer-service/requirements.txt ./service-requirements.txt

# Install shared and service dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r service-requirements.txt

# Copy shared code
COPY shared/ /app/shared/

# Copy service code
COPY services/customer-service/app /app/app

# Create non-root user
RUN useradd -m -u 1000 customerservice && chown -R customerservice:customerservice /app
USER customerservice

# Expose port
EXPOSE 8007

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8007"]
