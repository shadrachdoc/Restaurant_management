FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Python, PostgreSQL, and Prophet (ML)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY shared/ /app/shared/

# Copy Alembic migration files
COPY services/order-service/alembic.ini /app/
COPY services/order-service/alembic /app/alembic

# Copy service code
COPY services/order-service/app /app/app

# Expose port
EXPOSE 8004

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
