#!/bin/bash

# Script de démarrage pour Django
echo "Suppression des utilisateurs existants..."

# Attendre que MariaDB soit prêt
sleep 5

# Supprimer les utilisateurs de la base de données
mysql -h mariadb -u moviemania -pmoviemania_password_2024 moviemania -e "DELETE FROM Users;" 2>/dev/null || echo "Table Users n'existe pas encore"
mysql -h mariadb -u moviemania -pmoviemania_password_2024 moviemania -e "DELETE FROM UserGenre;" 2>/dev/null || echo "Table UserGenre n'existe pas encore"
mysql -h mariadb -u moviemania -pmoviemania_password_2024 moviemania -e "DELETE FROM django_session;" 2>/dev/null || echo "Table django_session n'existe pas encore"

echo "Base de données nettoyée. Démarrage de Django..."

# Démarrer Django
exec gunicorn --bind 0.0.0.0:8000 moviemania_frontend.wsgi:application
