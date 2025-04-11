#!/usr/bin/env sh

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Running migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

echo "Starting Django server..."
exec "$@"
