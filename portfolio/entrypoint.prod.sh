#!/bin/sh

# Environment check: waits for the database to be available
if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for PostgreSQL..."

    # Check the connection using netcat. The -z flag means "zero-I/O" (just check)
    # The variables $SQL_HOST and $SQL_PORT must be set in your .env.prod file
    while ! nc -z $SQL_HOST $SQL_PORT; do
        sleep 0.5 # Increased sleep for a slightly slower check, which is fine
    done

    echo "PostgreSQL started and ready!"
fi

# =================================================================
# Application Setup
# =================================================================

# 1. Run database migrations
echo "Running database migrations..."
python manage.py migrate --no-input

# 2. Collect static files
# This is CRITICAL for production. It moves all static assets 
# into the STATIC_ROOT folder (which is mounted by the volume).
echo "Collecting static files..."
python manage.py collectstatic --no-input

# 3. (Optional) Create a Superuser
# If you need an initial admin user created only once, uncomment this
# python manage.py createsuperuser --noinput || true

# =================================================================
# Start the WSGI server
# =================================================================

echo "Starting Gunicorn..."
# Use 'exec' to replace the current shell process with Gunicorn, 
# ensuring signals (like SIGTERM for shutdown) are handled correctly.
exec gunicorn portfolio.wsgi:application --bind 0.0.0.0:8000 --workers 4