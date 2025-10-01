FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        pkg-config \
        gcc \
        curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

# Install TailwindCSS dependencies and build CSS
RUN cd /app/tailwind && \
    npm install && \
    npm run build

RUN mkdir -p /app/logs && \
    adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

RUN chmod +x /app/start.sh

EXPOSE 8000

CMD ["/app/start.sh"]