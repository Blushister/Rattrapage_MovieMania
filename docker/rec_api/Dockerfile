# Utiliser une image de base officielle Python
FROM python:3.12-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers requirements.txt et installer les dépendances
COPY ./recommendations_api/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le contenu du répertoire 'recommendations_api/app' dans le répertoire de travail
COPY ./recommendations_api/app /app

# Exposer le port sur lequel l'application sera disponible
EXPOSE 8000

# Démarrer l'application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
