FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8009
CMD ["gunicorn", "--bind", "0.0.0.0:8009", "your_project.wsgi"]
