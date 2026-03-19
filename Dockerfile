# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definitions first to leverage layer caching
COPY pyproject.toml .
COPY README.md .

# Install dependencies
RUN pip install --no-cache-dir .

# Copy source code after dependencies are installed
COPY src/ src/
COPY scripts/ scripts/
COPY backend/ backend/

# Install the package itself (verify dependencies are satisfied)
RUN pip install --no-cache-dir --no-deps .

# Make port 10859 available to the world outside this container
EXPOSE 10859

# Run the application
CMD ["python", "scripts/run_webapp.py"]
