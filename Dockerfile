# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definitions first to leverage layer caching
COPY pyproject.toml .
COPY requirements.txt .
COPY README.md .

# Install dependencies - this layer will be cached unless requirements.txt changes
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code after dependencies are installed
COPY src/ src/
COPY scripts/ scripts/
COPY backend/ backend/

# Install the package itself (verify dependencies are satisfied)
RUN pip install --no-cache-dir --no-deps .

# Make port 15000 available to the world outside this container
EXPOSE 15000

# Run the application
CMD ["python", "scripts/run_webapp.py"]
