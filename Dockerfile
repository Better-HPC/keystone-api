# --- Build image ---
FROM python:3.11.13-alpine AS builder

# Install build dependencies
RUN apk add --no-cache \
    build-base \
    gcc \
    musl-dev \
    openldap-dev \
    cyrus-sasl-dev

# Compile application wheels
WORKDIR /src
COPY . .
RUN pip wheel --no-cache-dir --wheel-dir /wheels ./[all]


# --- Runtime image ---
FROM python:3.11.13-alpine

EXPOSE 80

# Disable Python byte code caching and output buffering
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Configure the application with container friendly defaults
ENV CONFIG_UPLOAD_DIR=/app/media
ENV CONFIG_STATIC_DIR=/app/static
ENV DB_NAME=/app/keystone.db
ENV LOG_APP_FILE=/app/keystone.log

# Install runtime dependencies only
RUN apk add --no-cache \
    redis \
    curl \
    nginx \
    openldap \
    cyrus-sasl

# Install application wheels
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Create unprivileged users/directories for running services
RUN addgroup -g 121 keystone \
    && adduser -D -u 1001 -G keystone keystone \
    && mkdir -p /app/keystone /app/nginx \
    && chown -R keystone:keystone /app /var/lib/nginx \
    && mkdir -p /var/lib/nginx/logs /var/log/nginx \
    && chown -R keystone:keystone /var/lib/nginx /var/log/nginx

# Switch to non-root user
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
