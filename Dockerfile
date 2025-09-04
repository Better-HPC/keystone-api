FROM python:3.13.7-slim

EXPOSE 80

# Disable Python byte code caching and output buffering
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    # Required for LDAP support
    build-essential \
    libsasl2-dev \
    libldap2-dev \
    # Required for running Celery
    redis \
    # Required for Docker HEALTHCHECK
    curl \
    # Required for static file serving
    nginx \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Install the application
COPY . src
RUN pip install --no-cache-dir ./src[all] && rm -rf src

# Create unprivliged users/directories for running services
RUN groupadd --gid 1001 keystone \
    && useradd -m -u 1001 -g keystone keystone \
    && mkdir -p /app/keystone /app/nginx \
    && chown -R keystone:keystone /app /var/lib/nginx/

USER keystone
WORKDIR /app/keystone

# Configure the application with container friendly defaults
ENV CONFIG_UPLOAD_DIR=/app/media
ENV CONFIG_STATIC_DIR=/app/static
ENV DB_NAME=/app/keystone.db
ENV LOG_APP_FILE=/app/keystone.log

# Copy config files for internal services
COPY --chown=keystone:keystone --chmod=770 conf/nginx.conf /etc/nginx/nginx.conf
COPY --chown=keystone:keystone --chmod=770 conf/entrypoint.sh /app/entrypoint.sh

# Use the API health checks to report container health
HEALTHCHECK CMD curl --fail --location localhost/health/ || exit 1

# Setup the container to launch the application
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["quickstart", "--all"]
