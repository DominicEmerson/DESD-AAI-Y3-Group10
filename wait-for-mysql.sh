#!/bin/sh

echo "Waiting for MySQL to start..."

TIMEOUT=30  # Max wait time of 30 seconds
while ! nc -z mysql_db 3306; do
  sleep 1
  TIMEOUT=$((TIMEOUT - 1))
  echo "Waiting for MySQL... ($TIMEOUT seconds left)"
  if [ "$TIMEOUT" -le 0 ]; then
    echo "Error: MySQL did not start in time."
    exit 1
  fi
done

echo "MySQL started!"
exec "$@"
