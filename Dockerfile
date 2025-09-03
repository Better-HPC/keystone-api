FROM python:3.11.4-slim

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

# Configure the NGINX proxy
RUN groupadd nginx && useradd -m -g nginx nginx
COPY conf/nginx.conf /etc/nginx/nginx.conf

# Create an unprivliged user/directory for running services
RUN groupadd --gid 900 keystone \
    && useradd -m -u 900 -g keystone keystone \
    && mkdir -p /app \
    && chown keystone:keystone /app

USER keystone
WORKDIR /app

# Install the application
COPY --chown=keystone:keystone . src
RUN pip install --user ./src[all] && rm -rf src

# Configure the application with container friendly defaults
ENV CONFIG_UPLOAD_DIR=/app/media
ENV LOG_APP_FILE=/app/app.log
RUN mkdir $CONFIG_UPLOAD_DIR && touch LOG_APP_FILE

# Use the API health checks to report container health
HEALTHCHECK CMD curl --fail --location localhost/health/ || exit 1

# Setup the container to launch the application
COPY --chmod=755 conf/entrypoint.sh /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["quickstart", "--all"]
