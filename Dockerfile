# Use the official Python image
FROM python:3.10

# Set the working directory inside the container
WORKDIR /app

# Copy wait-for-mysql.sh early to ensure it exists in the container
COPY wait-for-mysql.sh /app/wait-for-mysql.sh
RUN chmod +x /app/wait-for-mysql.sh  # Ensure it is executable

# Install system dependencies (including MySQL client)
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    default-mysql-client  #

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

# Run the wait-for-mysql script before starting Django
CMD ["/app/wait-for-mysql.sh", "python", "manage.py", "runserver", "0.0.0.0:8000"]
