FROM python:3.12-slim

WORKDIR /app/

# Install curl and Poetry
RUN apt-get update && apt-get install -y curl && \
    curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Copy poetry.lock* in case it doesn't exist in the repo
COPY ./users_api/pyproject.toml ./users_api/poetry.lock* /app/

# Allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --only main ; fi"

ENV PYTHONPATH=/app

COPY ./users_api/alembic.ini /app/

COPY ./users_api/app /app/app
COPY ./docker/users_api/clear-users-startup.py /app/clear-users-startup.py
COPY ./docker/users_api/startup.sh /app/startup.sh

RUN chmod +x /app/startup.sh

EXPOSE 8888

CMD ["/app/startup.sh"]
