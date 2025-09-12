FROM python:3.11-slim

# Définir les variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        default-libmysqlclient-dev \
        pkg-config \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY . /app/

# Créer un utilisateur non-root
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app
USER appuser

# Exposer le port
EXPOSE 8000

# Commande par défaut
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "moviemania_frontend.wsgi:application"]
