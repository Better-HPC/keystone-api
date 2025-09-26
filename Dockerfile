FROM python:3.11.13 AS builder

# Install compile tools and build dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    libsasl2-dev \
    libldap2-dev \
    gcc \
  && rm -rf /var/lib/apt/lists/*

# Compile application installer
COPY . .
RUN pip wheel --no-cache-dir --wheel-dir /wheels ./[all]

FROM python:3.11.13-slim

EXPOSE 80

# Disable Python byte code caching and output buffering
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Configure the application with container friendly defaults
ENV CONFIG_UPLOAD_DIR=/app/media
ENV CONFIG_STATIC_DIR=/app/static
ENV DB_NAME=/app/keystone.db
ENV LOG_APP_FILE=/app/keystone.log

# Install system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    redis \
    curl \
    nginx \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Install the application
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Create unprivliged users/directories for running services
RUN groupadd --gid 121 keystone \
    && useradd -m -u 1001 -g keystone keystone \
    && mkdir -p /app/keystone /app/nginx \
    && chown -R keystone:keystone /app /var/lib/nginx/

# Set unprivliged user as default
USER keystone
WORKDIR /app/keystone

# Copy config files for internal services
COPY --chown=keystone:keystone --chmod=770 conf/nginx.conf /etc/nginx/nginx.conf
COPY --chown=keystone:keystone --chmod=770 conf/entrypoint.sh /app/entrypoint.sh

# Use the API health checks to report container health
HEALTHCHECK CMD curl --fail --location localhost/health/ || exit 1

# Setup the container to launch the application
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["quickstart", "--all"]
