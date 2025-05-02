# Use the official Python image
FROM python:3.12

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y netcat-openbsd  # Keep netcat if needed

# Upgrade pip
RUN pip install --upgrade pip

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create staticfiles directory with proper permissions
RUN mkdir -p /app/staticfiles && chown -R 1000:1000 /app/staticfiles

# Copy the rest of the project files into the container
COPY . .

# Expose the port Django runs on
EXPOSE 8000

# Start Django using wsgi and gunicorn instead of manage.py runserver
# CMD: >
#   sh -c "python manage.py migrate &&
#   python manage.py collectstatic --noinput &&
#   gunicorn --bind 0.0.0.0:8000 --workers 4 insurance_ai.wsgi:application"