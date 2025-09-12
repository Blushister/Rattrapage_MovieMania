#!/bin/bash

# Script d'initialisation pour le conteneur Django
echo "Initialisation du frontend Django..."

# Attendre que la base de données soit prête
echo "Attente de la base de données..."
sleep 10

# Effectuer les migrations Django
echo "Exécution des migrations..."
python manage.py migrate --noinput

# Collecter les fichiers statiques
echo "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Créer un superutilisateur si nécessaire
echo "Création du superutilisateur..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@moviemania.com', 'admin123')
    print('Superutilisateur créé: admin/admin123')
else:
    print('Superutilisateur existe déjà')
"

echo "Initialisation terminée!"
