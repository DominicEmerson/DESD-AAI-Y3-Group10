#!/bin/sh

echo "Waiting for MySQL to start..."

while ! nc -z mysql_db 3306; do
  sleep 1
  echo "Waiting for MySQL..."
done

echo "MySQL started!"

exec "$@"
