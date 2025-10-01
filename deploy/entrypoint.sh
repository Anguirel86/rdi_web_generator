#!/bin/bash

# Handle db migrations and static files on container startup
python manage.py migrate
python manage.py collectstatic --no-input --clear

exec "$@"
