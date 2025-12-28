# Deploying with Docker

The Keystone API can be deployed as a single container using Docker, or as several containers using Docker Compose.
Single-container deployments are best suited for those looking to test-drive Keystone's capabilities.
Multi-container deployments are strongly recommended for teams operating in production.

!!! danger

    The API container deploys with default settings that are **not** suitable for secure production use.
    See the [Settings](../setup/settings.md) page for a complete overview of configurable options and recommended settings.

## Using Docker Standalone

The latest API image can be pulled and launched using the Docker command below.
This example runs the image as a container called `keystone` and maps the API to port `8000` on the local machine.

```bash
docker run \
  --detach \
  --publish 8000:80 \
  --name keystone \
  docker.cloudsmith.io/better-hpc/keystone/keystone-api
```

The container will automatically execute the API quickstart utility and initialize core system dependencies (Postgres, Redis, etc.) within the container.
The container will also check for existing user accounts and, if no accounts are found, create an admin account with username `admin` and password `quickstart`.

To verify the container's health, check the running container status or query the API's health endpoint.

```bash
docker inspect --format='{{.State.Health.Status}}' keystone
curl -L http://localhost:8000/health/json | jq .
```

## Using Docker Compose

The following compose recipe provides a functional starting point for building a scalable API deployment.
Application dependencies are defined as separate services and setting values are configured using environment
variables in various `.env` files.

```yaml
services:
  cache: # (1)!
    image: redis
    container_name: keystone-cache
    command: redis-server
    restart: unless-stopped
    volumes:
      - cache_data:/data

  db: # (2)!
    image: postgres
    container_name: keystone-db
    restart: unless-stopped
    env_file:
      - db.env
    volumes:
      - postgres_data:/var/lib/postgresql/data/

  api: # (3)!
    image: docker.cloudsmith.io/better-hpc/keystone/keystone-api
    container_name: keystone-api
    entrypoint: sh
    command: |
      -c '
        sleep 3 # Give dependent services time to start
        keystone-api migrate --no-input
        keystone-api collectstatic --no-input
        uvicorn --host 0.0.0.0 --port 8000 keystone_api.main.asgi:application'
    restart: unless-stopped
    depends_on:
      - cache
      - db
    ports:
      - "8000:8000"
    env_file:
      - api.env
    volumes:
      - static_files:/app/static
      - uploaded_files:/app/upload_files

  celery-worker: # (4)!
    image: docker.cloudsmith.io/better-hpc/keystone/keystone-api
    container_name: keystone-celery-worker
    entrypoint: celery -A keystone_api.apps.scheduler worker
    restart: unless-stopped
    depends_on:
      - cache
      - db
      - api
    env_file:
      - api.env

  celery-beat: # (5)!
    image: docker.cloudsmith.io/better-hpc/keystone/keystone-api
    container_name: keystone-celery-beat
    entrypoint: celery -A keystone_api.apps.scheduler beat --scheduler django_celery_beat.schedulers:DatabaseScheduler
    restart: unless-stopped
    depends_on:
      - cache
      - db
      - api
      - celery-worker
    env_file:
      - api.env

volumes:
  static_files:
  uploaded_files:
  postgres_data:
  cache_data:
```

1. The `cache` service acts as a job queue for background tasks. Note that cache data is mounted onto the host machine to ensure data persistence between container restarts.
2. The `db` service defines the application database. User credentials are provided as environmental variables in the `db.env` file. Note the mounting of database data onto the host machine to ensure data persistence between container restarts.
3. The `api` service defines the Keystone-API application. It migrates the database schema, configures static file hosting, and launches the API behind a production quality web server.
4. The `celery-worker` service executes background tasks for the API application. It uses the same base image as the `api` service.
5. The `celery-beat` service handles task scheduling for the `celery-worker` service. It uses the same base image as the `api` service.

The following examples define the minimal required settings to deploy the recipe.
The `DJANGO_SETTINGS_MODULE="keystone_api.main.settings"` setting is required by the application.

!!! warning

    The settings provided below are intended for demonstrative purposes only.
    These values are not secure and should be customized to meet the needs at hand.

=== "api.env"

    ```bash
    # General Settings
    DJANGO_SETTINGS_MODULE="keystone_api.main.settings"
    STORAGE_STATIC_DIR="/app/static"
    STORAGE_UPLOAD_DIR="/app/upload_files"
    
    # Security Settings
    SECURE_ALLOWED_HOSTS="*"
    
    # Redis Settings
    REDIS_HOST="cache" # (1)!
    
    # Database settings
    DB_POSTGRES_ENABLE="true"
    DB_NAME="keystone"
    DB_USER="db_user"
    DB_PASSWORD="foobar123"
    DB_HOST="db" # (2)!
    ```

    1. This value should match the service name defined in the compose file.
    2. This value should match the service name defined in the compose file.

=== "db.env"

    ```bash
    # Credential values must match api.env
    POSTGRES_DB="keystone"
    POSTGRES_USER="db_user" # (1)!
    POSTGRES_PASSWORD="foobar123"
    ```

    1. Database credentials must match those defined in `api.env`.
