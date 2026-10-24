# Backend Dockerfile for Meru Coders - Sanskrit Meter Identification System
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Tesseract OCR and other requirements
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-san \
    tesseract-ocr-hin \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend directory
COPY backend/ /app/backend/


# Copy data files
COPY backend/data/ /app/backend/data/

# Copy GCP credentials for Cloud Vision OCR
COPY backend/secrets/ /app/backend/secrets/

# Create necessary directories
RUN mkdir -p /app/backend/uploads/photos \
    /app/backend/uploads/texts \
    /app/backend/uploads/results

# Set Python path
ENV PYTHONPATH=/app

# Expose port (Cloud Run will override this with PORT env var)
EXPOSE 5000

# Run the application
CMD ["python", "backend/run.py"]
