#!/bin/sh

# Environment check: waits for the database to be available
if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    # Check the connection using netcat (which you install in your Dockerfile)
    while ! nc -z $SQL_HOST $SQL_PORT; do
        sleep 0.1
    done

    echo "PostgreSQL started"
fi

# =================================================================
# Application Setup (Un-comment as needed for Django/Flask/other apps)
# =================================================================

# 1. Run database migrations (necessary for database setup)
# If using Django, you would un-comment the line below:
echo "Running migrations..."
python manage.py migrate --no-input

# 2. Collect static files (necessary for serving assets in production)
# If using Django, you would un-comment the line below:
# echo "Collecting static files..."
# python manage.py collectstatic --no-input

# 3. If you have custom initialization commands, place them here.

# =================================================================
# Start the WSGI server
# =================================================================

# IMPORTANT: Replace 'portfolio.wsgi:application' with the correct module path 
# and callable name for your application (e.g., 'app:app' for a simple Flask app).
echo "Starting Gunicorn..."
exec gunicorn portfolio.wsgi:application --bind 0.0.0.0:8000 --workers 4 


# #!/bin/sh

# if [ "$DATABASE" = "postgres" ]
# then
#     echo "Waiting for postgres..."

#     while ! nc -z $SQL_HOST $SQL_PORT; do
#         sleep 0.1
#     done

#     echo "PostgreSQL started"
# fi

# # python manage.py flush --no-input
# # python manage.py migrate

# exec "$@"