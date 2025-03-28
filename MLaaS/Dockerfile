FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your project files
COPY . .

# Create the /app/media/ml_models directory inside the container
RUN mkdir -p /app/media/ml_models

# Copy the local "ml_models/3feature_regression_model.pkl" file into /app/media/ml_models/
COPY ml_models/3feature_regression_model.pkl /app/media/ml_models/

EXPOSE 8009

# Run gunicorn on container startup
CMD ["gunicorn", "--bind", "0.0.0.0:8009", "config.wsgi:application"]
