# Use the official Python image
FROM python:3.10

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y netcat-openbsd  # Keep netcat if needed

# Install Pipenv globally
RUN pip install --no-cache-dir pipenv

# Copy Pipfile and Pipfile.lock first (to leverage Docker cache)
COPY Pipfile Pipfile.lock ./

# Ensure system dependencies are installed properly
RUN pip install --upgrade pip && pipenv install --deploy --system

# Explicitly install Django
RUN pip install django

# Copy the rest of the project files into the container
COPY . .

# Expose the port Django runs on
EXPOSE 8000

# Start Django directly
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
