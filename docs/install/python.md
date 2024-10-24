# Deploying with Python

Keystone-API can be installed using system packages and managed using the systemd service manager.
Doing so requires administrative privileges and assumes you are managing system services via systemd.
These instructions also assume you are installing applications under a dedicated, unprivileged user account called `keystone`. 

## Installing the API

The `keystone_api` package can be installed using the `pip` or `pipx` package managers.

=== "pipx (recommended)"

    ```bash
    pipx install --include-deps keystone-api
    ```

=== "pip"

    ```bash
    pip install keystone-api
    ```

If you intend to authenticate users via LDAP credentials, you will need to manually specify LDAP support in the `install` command.
This will require the LDAP development binaries to be available on the host machine.


=== "pipx (recommended)"

    ```bash
    pipx install --include-deps keystone-api[ldap]
    ```

=== "pip"

    ```bash
    pip install keystone-api[ldap]
    ```

If the installation was successful, the packaged CLI tool will be available in your working environment.
Use the `--help` option to view the available commands.

```bash
keystone-api --help
```

The `keystone-api` utility does not support tab autocompletion by default.
To enable autocomplete for the Bash shell, use the `enable_autocomplete` command.

```bash
keystone-api enable_autocomplete
```

## Deploying Dependencies

Keystone-API requires several backend services to support its operation.
Specific instructions are provided below on configuring each dependency.

### Redis

Most Redis server instances will work out of the box so long as the connection and authentication values are set correctly in the API settings.

### PostgreSQL

Using PostgreSQL for the application database is strongly recommended.
After deploying a PostgreSQL server, you will need to create a dedicated database and user account. 
Start by launching a new SQL session with admin permissions.

```bash
sudo -u postgres psql
```

Next, create a database and a `keystone` service account.
Make sure to replace the password field with a secure value.

```postgresql
create database keystone;
create user keystone_sa with encrypted password '[PASSWORD]';
grant all privileges on database keystone to keystone_sa;
```

### Celery

Celery and Celery Beat are both included when installing the `keystone_api` package.
Both applications should be launched using `keystone_api.apps.scheduler` as the target application.

```bash
celery -A keystone_api.apps.scheduler worker
celery -A keystone_api.apps.scheduler beat --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

The `celery` command executes as a foreground process by default.
The following unit files are provided as a starting point to daemonize the process via the systemd service manager.

!!! warning 

    Celery can fill up it's log directory fairly quickly, especially when running multiple workers simultaneously.
    Rotating the Celery log files to prevent excessive storage is strongly recommended.

=== "keystone-worker.service"

    ```toml
    [Unit]
    Description=Celery workers for Keystone
    After=network.target
    
    [Service]
    Type=forking
    User=keystone
    Group=keystone
    RuntimeDirectory=celery
    WorkingDirectory=/home/keystone
    EnvironmentFile=/home/keystone/keystone.env
    ExecStart=/bin/sh -c '/home/keystone/.local/bin/celery multi start w1 -A keystone_api.apps.scheduler'
    ExecStop=/bin/sh -c '/home/keystone/.local/bin/celery multi stopwait w1'
    ExecReload=/bin/sh -c '/home/keystone/.local/bin/celery multi restart w1'
    
    [Install]
    WantedBy=multi-user.target
    ```

=== "keystone-beat.service"
    
    ```toml
    [Unit]
    Description=Celery Beat scheduler for keystone
    After=network.target
    
    [Service]
    Type=simple
    User=keystone
    Group=keystone
    RuntimeDirectory=beat
    WorkingDirectory=/home/keystone
    EnvironmentFile=/home/keystone/keystone.env
    ExecStart=/bin/sh -c '/home/keystone/.local/bin/celery -A keystone_api.apps.scheduler beat --scheduler django_celery_beat.schedulers:DatabaseScheduler'
    Restart=always
    
    [Install]
    WantedBy=multi-user.target
    ```

## Deploying the Application

Before launching the API, migrate the database to the latest schema version and collect any static files.
See the [Settings](settings.md) page for details on configuring database credentials and the static files location.

```bash
keystone-api migrate
keystone-api collectstatic
```

Gunicorn is the recommended webserver for running the Keystone-API.
When launching the webserver, use the WSGI entrypoint located under `keystone_api.main.wsgi:application`.

```bash
gunicorn --bind 0.0.0.0:8000 keystone_api.main.wsgi:application
```

The `gunicorn` command executes as a foreground process by default.
The following unit files are provided as a starting point to daemonize the process via the systemd service manager.

=== "keystone-server.service"

    ```toml
    [Unit]
    Description=Gunicorn server daemon for Keystone
    Requires=keystone-server.socket
    After=network.target
    
    [Service]
    Type=notify
    User=keystone
    Group=keystone
    RuntimeDirectory=gunicorn
    WorkingDirectory=/home/keystone
    EnvironmentFile=/home/keystone/keystone.env
    ExecStart=/home/keystone/.local/bin/gunicorn keystone_api.main.wsgi
    ExecReload=/bin/kill -s HUP $MAINPID
    KillMode=mixed
    TimeoutStopSec=5
    PrivateTmp=true
    
    [Install]
    WantedBy=multi-user.target
    ```

=== "keystone-server.socket"

    ```toml
    [Unit]
    Description=Gunicorn socket for Keystone
    
    [Socket]
    ListenStream=/run/gunicorn.sock
    SocketUser=nginx
    
    [Install]
    WantedBy=sockets.target
    ```

## Configuring the Proxy

Using a web proxy in front of the API server is recommended to improve load balancing, security, and static file handling. 
Nginx is recommended, but administrators are welcome to use a proxy of their choice.
A starter Nginx configuration file is provided below for convenience.

```nginx
upstream keystone_api {
    server localhost:8000;
}

server {
    listen 80 default_server;
    listen [::]:80 default_server;

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;

    ssl_certificate     /etc/pki/tls/certs/keystone.crt; 
    ssl_certificate_key /etc/pki/tls/private/keystone.key;

    location / {
        proxy_pass http://unix:/run/gunicorn.sock;
    }

    location /uploads { # (1)!
        alias /var/keystone-api/upload_files;
    }
}
```

1. The `/uploads` alias must match the `CONFIG_UPLOAD_DIR` in application settings.

## Upgrading Application Versions

API upgrades are handled by the Python package manager.
System services should be taken offline before upgrading to a new version.

!!! danger
    Always ensure the production database is backed up before applying application updates.

!!! note
    The `keystone-server` systemd configuration outlined above is defined to start the API server on demand.
    When taking the system offline, it is best to also prevent system restarts by stopping incoming traffic from the upstream proxy.
    This is achievable by or by modifying the proxy config and restarting the proxy service

=== "pipx (recommended)"

    ```bash
    systemctl stop nginx
    systemctl stop keystone-server
    systemctl stop keystone-beat
    systemctl stop keystone-worker

    pipx upgrade keystone-api
    keystone-api migrate
    keystone-api collectstatic
    
    systemctl start keystone-worker
    systemctl start keystone-beat
    systemctl start keystone-server
    systemctl start nginx
    ```

=== "pip"

    ```bash
    systemctl stop nginx
    systemctl stop keystone-server
    systemctl stop keystone-beat
    systemctl stop keystone-worker
    
    pip install --upgrade keystone-api
    keystone-api migrate
    keystone-api collectstatic
    
    systemctl start keystone-worker
    systemctl start keystone-beat
    systemctl start keystone-server
    systemctl start nginx
    ```
