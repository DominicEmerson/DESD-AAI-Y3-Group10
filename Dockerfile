# Use the official Python image
FROM python:3.13

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y netcat-openbsd  # Keep netcat if needed

# Upgrade pip
RUN pip install --upgrade pip

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files into the container
COPY . .

# Expose the port Django runs on
EXPOSE 8000

# Start Django directly
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

