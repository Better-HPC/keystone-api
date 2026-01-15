# API Settings

Keystone-API reads application settings from environment variables.
Individual settings are listed below by category and use case.

## Security Settings

Security settings are used to configure application networking and request signing.
These values should be chosen with care.
Improperly configured settings can introduce dangerous vulnerabilities and may damage your production deployment.

### Core Security

Keystone-API requires a random secret key to sign and verify requests.
Secret keys are conventionally 50 characters long and can be generated using common unities like `openssl`.
For example: `openssl rand -base64 48 | cut -c1-50`

| Setting Name        | Default Value      | Description                                      |
|---------------------|--------------------|--------------------------------------------------|
| `SECURE_SECRET_KEY` | Randomly generated | Key value used to enforce cryptographic signing. |

### SSL/TLS

Enabling TLS is strongly recommended in production.
Enabling HSTS is also recommended, but only when TLS is already fully configured.
Administrators are cautioned to consider the potentially irreversible side effects of HSTS before enabling it.

| Setting Name             | Default Value  | Description                                       |
|--------------------------|----------------|---------------------------------------------------|
| `SECURE_SSL_REDIRECT`    | `False`        | Automatically redirect all HTTP traffic to HTTPS. |
| `SECURE_HSTS_SECONDS`    | `0` (Disabled) | HSTS cache duration in seconds.                   |
| `SECURE_HSTS_SUBDOMAINS` | `False`        | Enable HSTS for subdomains.                       |
| `SECURE_HSTS_PRELOAD`    | `False`        | Enable HSTS preload functionality.                |

### CORS/CSRF

CORS and CSRF settings define which domains are allowed to interact with the Keystone-API.

| Setting Name             | Default Value                        <br/><br/> | Description                                                                                      |
|--------------------------|-------------------------------------------------|--------------------------------------------------------------------------------------------------|
| `SECURE_ALLOWED_HOSTS`   | <code>localhost,127.0.0.1</code>                | Comma-separated list of accepted host/domain names (**without** protocol).                       |
| `SECURE_ALLOWED_ORIGINS` | _See default local addresses._                  | Comma-separated list of accepted CORS origin domains (**with** protocol).                        |
| `SECURE_CSRF_ORIGINS`    | _See default local addresses._                  | Comma-separated list of accepted CSRF origin domains (**with** protocol).                        |
| `SECURE_SSL_TOKENS`      | `False`                                         | Only issue session/CSRF tokens over secure connections.                                          |
| `SECURE_SESSION_AGE`     | `1209600` (2 weeks)                             | Number of seconds before session tokens expire.                                                  |
| `SECURE_TOKEN_DOMAIN`    | None                                            | Domain attribute for session/csrf cookies. Set for cross-subdomain usage (e.g., `.example.com`). | 

Default values are defined relative to the following list of _default local addresses_:

- `http://localhost:80`
- `https://localhost:443`
- `http://localhost:4200`
- `http://localhost:8000`
- `http://127.0.0.1:80`
- `https://127.0.0.1:443`
- `http://127.0.0.1:4200`
- `http://127.0.0.1:8000`

## General Configuration

Keystone uses various static files and user content to facilitate operation.
By default, these files are stored in subdirectories of the installed application directory (`<app>`).

| Setting Name           | Default Value         | Description                                                              |
|------------------------|-----------------------|--------------------------------------------------------------------------|
| `CONFIG_TIMEZONE`      | `UTC`                 | The timezone to use when rendering date/time values.                     |
| `CONFIG_STATIC_DIR`    | `<app>/static_files`  | Where to store internal static files required by the application.        |
| `CONFIG_UPLOAD_DIR`    | `<app>/media`         | Where to store file data uploaded by users.                              |
| `CONFIG_UPLOAD_SIZE`   | `2621440` (2.5 MB)    | Maximum allowed file upload size in bytes.                               |
| `CONFIG_METRICS_PORTS` | `9101` through `9150` | Port numbers used to expose prometheus metrics (e.g., `9101,9102,9103`). |

## Logging

Keystone automatically purges log recordss according to the policy settings below.
Application logs are written to disk using a size-based policy that rotates files according to a maximum file
size/count.
Audit, request, and task logs are maintained in the application database and are removed once they exceed a configured
age (in seconds).

| Setting Name              | Default Value        | Description                                                                                                 |
|---------------------------|----------------------|-------------------------------------------------------------------------------------------------------------|
| `LOG_APP_LEVEL`           | `WARNING`            | Only record application logs above this level (accepts `CRITICAL`, `ERROR`, `WARNING`, `INFO`, or `DEBUG`). |
| `LOG_APP_FILE`            | `<app>/keystone.log` | Destination file path for application logs.                                                                 |
| `LOG_APP_RETENTION_BYTES` | `10485760` (10 MB)   | Maximum log file size before rotating log files.                                                            |
| `LOG_APP_RETENTION_FILES` | `5`                  | Maximum rotated log files to keep.                                                                          |
| `LOG_REQ_RETENTION_SEC`   | `2592000` (30 days)  | How long to store request logs in seconds. Set to 0 to keep all records.                                    |
| `LOG_AUD_RETENTION_SEC`   | `2592000` (30 days)  | How long to store audit logs in seconds. Set to 0 to keep all records.                                      |
| `LOG_TSK_RETENTION_SEC`   | `2592000` (30 days)  | How long to store task logs in seconds. Set to 0 to keep all records.                                       |

## API Throttling

API settings are used to throttle incoming API requests against a maximum limit.
Limits are specified as the maximum number of requests per `day`, `minute`, `hour`, or `second`.

| Setting Name        | Default Value | Description                                          |
|---------------------|---------------|------------------------------------------------------|
| `API_THROTTLE_ANON` | `120/min`     | Rate limiting for anonymous (unauthenticated) users. |
| `API_THROTTLE_USER` | `300/min`     | Rate limiting for authenticated users.               |

## Database Connection

Official support is included for both SQLite and PostgreSQL database backends.
Using SQLite is intended for development and demonstrative use cases only.
The PostgreSQL backend should always be used in production settings.

| Setting Name         | Default Value | Description                                             |
|----------------------|---------------|---------------------------------------------------------|
| `DB_POSTGRES_ENABLE` | `False`       | Use PostgreSQL instead of the default Sqlite driver.    |
| `DB_NAME`            | `keystone`    | The name of the application database.                   |
| `DB_USER`            |               | Username for database authentication (PostgreSQL only). |
| `DB_PASSWORD`        |               | Password for database authentication (PostgreSQL only). |
| `DB_HOST`            | `localhost`   | Database host address (PostgreSQL only).                |
| `DB_PORT`            | `5432`        | Database host port (PostgreSQL only).                   |

## Redis Connection

Redis settings define the network location and connection information for the application Redis cache.
Enabling password authentication is strongly recommended.

| Setting Name     | Default Value | Description                                  |
|------------------|---------------|----------------------------------------------|
| `REDIS_HOST`     | `127.0.0.1`   | URL for the Redis message cache.             |
| `REDIS_PORT`     | `6379`        | Port number for the Redis message cache.     |
| `REDIS_DB`       | `0`           | The Redis database number to use.            |
| `REDIS_PASSWORD` |               | Optionally connect using the given password. |

## Email Notifications

Keystone will default to using the local server when issuing email notifications.
An alternative SMTP server can be sepcified using the settings below.
Securing your production email server with a username/password is strongly recommended.

| Setting Name          | Default Value             | Description                                             |
|-----------------------|---------------------------|---------------------------------------------------------|
| `EMAIL_HOST`          | `localhost`               | The host server to use for sending email.               |
| `EMAIL_HOST_USER`     |                           | Username to use for the SMTP server.                    |
| `EMAIL_HOST_PASSWORD` |                           | Password to use for the SMTP server.                    |
| `EMAIL_PORT`          | `25`                      | Port to use for the SMTP server.                        |
| `EMAIL_USE_TLS`       | `False`                   | Use a TLS connection to the SMTP server.                |
| `EMAIL_FROM_ADDRESS`  | `noreply@keystone.bot`    | The default "from" address used in email notifications. |
| `EMAIL_TEMPLATE_DIR`  | `/etc/keystone/templates` | Directory to search for customized email templates.     |
| `EMAIL_DEBUG_DIR`     |                           | Write emails to disk instead of using the SMTP server.  |

## LDAP Authentication

Using LDAP for authentication is optional and disabled by default.
To enable LDAP, set the `AUTH_LDAP_SERVER_URI` value to the desired LDAP endpoint.
Enabling LDAP integration will also add LDAP related health checks to the
[API health endpoint](../api/logging.md#system-health).

Application user fields are mapped to LDAP attributes by specifying the `AUTH_LDAP_ATTR_MAP` setting.
The following example maps the `first_name` and `last_name` fields used by Keystone to the LDAP attributes `givenName`
and `sn`:

```bash
AUTH_LDAP_ATTR_MAP="first_name=givenName,last_name=sn"
```

A full list of available Keystone fields can be found in the project's [OpenApi specification](../api/openapi.md).

| Setting Name              | Default Value           | Description                                                       |
|---------------------------|-------------------------|-------------------------------------------------------------------|
| `AUTH_LDAP_SERVER_URI`    |                         | The URI of the LDAP server.                                       |
| `AUTH_LDAP_START_TLS`     | `True`                  | Whether to use TLS when connecting to the LDAP server.            |
| `AUTH_LDAP_BIND_DN`       |                         | Optionally bind LDAP queries to the given DN.                     |
| `AUTH_LDAP_BIND_PASSWORD` |                         | The password to use when binding to the LDAP server.              |
| `AUTH_LDAP_USER_SEARCH`   |                         | The base DN for searching users in the LDAP server.               |
| `AUTH_LDAP_USER_FILTER`   | `(objectClass=account)` | The LDAP filter used to identify user entries during sync.        |
| `AUTH_LDAP_LOGIN_FILTER`  | `(uid=%(user)s)`        | The LDAP filter used to find a user during authentication.        |
| `AUTH_LDAP_REQUIRE_CERT`  | `False`                 | Whether to require certificate verification.                      |
| `AUTH_LDAP_ATTR_MAP`      |                         | A mapping of user fields to LDAP attribute names.                 |
| `AUTH_LDAP_PURGE_REMOVED` | `False`                 | Delete users when removed from LDAP instead of deactivating them. |
| `AUTH_LDAP_TIMEOUT`       | `10`                    | The number of seconds before timing out an LDAP connection/query. |