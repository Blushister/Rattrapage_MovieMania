#!/bin/bash

echo "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

echo "Démarrage de Django..."
gunicorn moviemania_frontend.wsgi:application --bind 0.0.0.0:8000 --workers 2