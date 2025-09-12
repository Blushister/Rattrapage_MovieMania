# Frontend Django - MovieMania

## Description
Frontend Django pour l'application MovieMania qui communique avec les APIs FastAPI existantes.

## Structure
```
frontend/
├── Dockerfile                 # Configuration Docker
├── requirements.txt           # Dépendances Python
├── manage.py                 # Script de gestion Django
├── moviemania_frontend/      # Configuration principale Django
│   ├── settings.py          # Paramètres Django
│   ├── urls.py              # URLs principales
│   ├── wsgi.py              # Configuration WSGI
│   └── asgi.py              # Configuration ASGI
├── apps/                    # Applications Django
│   ├── movies/              # Gestion des films
│   ├── users/               # Gestion des utilisateurs
│   └── recommendations/     # Gestion des recommandations
├── templates/               # Templates HTML
├── static/                  # Fichiers statiques (CSS, JS, images)
└── media/                   # Fichiers média uploadés
```

## Configuration Docker

Le frontend Django est configuré pour fonctionner avec Docker et communiquer avec :
- **Users API** : `http://users_api:8888`
- **Recommendations API** : `http://recos_api:8000`

## Variables d'environnement

Les variables suivantes doivent être définies dans le fichier `.env` :

```bash
# Configuration Django
DEBUG=true
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,django_frontend

# URLs des APIs
USERS_API_URL=http://users_api:8888
RECOMMENDATIONS_API_URL=http://recos_api:8000
```

## Démarrage

Pour démarrer le frontend Django avec Docker :

```bash
# Depuis la racine du projet
docker-compose up django_frontend
```

Le frontend sera accessible sur : `https://localhost`

## Applications Django

### Movies App
- Liste des films populaires
- Détails d'un film
- Recherche de films
- Films par genre

### Users App
- Connexion/Déconnexion
- Inscription
- Profil utilisateur
- Modification du profil

### Recommendations App
- Recommandations générales
- Recommandations personnalisées
- Films similaires
- Films tendance

## Intégration avec les APIs

Le frontend Django communique avec les APIs FastAPI via des appels HTTP en utilisant la bibliothèque `requests`. Les tokens d'authentification sont stockés dans les sessions Django.
