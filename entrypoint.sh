#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q'; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is up - executing commands"

# Run database migrations
echo "Running migrations..."
python manage.py migrate --no-input

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input --clear

# Create cache table for Django caching
echo "Creating cache table..."
python manage.py createcachetable || true

# Create superuser if it doesn't exist
echo "Creating superuser if needed..."
python manage.py shell <<EOF
from APP01.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print('Superuser created: admin/admin')
else:
    print('Superuser already exists')
EOF

# Execute the command passed to docker-compose (runserver or gunicorn)
echo "Starting application..."
exec "$@"
