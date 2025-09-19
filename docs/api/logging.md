# Status Monitoring

Keystone-API provides multiple endpoints to support operational monitoring and troubleshooting.

## System Health

System health checks offer a high-level overview of the Keystone application stack and its operational status.
These endpoints evaluate various system tests on demand and return the current state of the API and its dependencies.

!!! note

    To avoid exposure to DOS style attacks, API health checks are run on the server a maximum of once every 60 seconds.
    Any additional requests during this time limit will receive a cached result.

| Endpoint        | Description                                                                 |
|-----------------|-----------------------------------------------------------------------------|
| `/health/`      | Returns HTTP 200 if all system checks pass, or HTTP 500 if any check fails. |
| `/health/json/` | Returns detailed health check results in JSON format.                       |
| `/health/prom/` | Returns detailed health check results in Prometheus format.                 |

## Application Logging

Keystone-API exposes application logs through the API endpoints listed below.
All log endpoints require [authentication](./authentication.md) with administrator privileges and support the
API's standard [query parameters](./filtering.md).

| Endpoint             | Description                                                        |
|----------------------|--------------------------------------------------------------------|
| `/logging/requests/` | Logs incoming HTTP requests and related metadata.                  |
| `/logging/audit/`    | Audit trail for user actions against select application resources. |
| `/logging/apps/`     | Application-level logs (e.g., debug, info, warning).               |
| `/logging/tasks/`    | Results and status of scheduled background tasks.                  |

Clients may optionally specify a unique correlation ID (`cid`) using the `X-KEYSTONE-CID` header.
This value is propagated through internal logs, enabling record correlation across logging endpoints.
Clients should leverage this feature to organize log records around a common transaction or user session.
If A CID value is not provided, a unique value is assigned to each incoming request.

CID values must be a valid UUIDv4 string, including dashes (e.g. `d61eef0b-258d-42ca-b14b-852860a54259`).

## Performance Metrics

Keystone exposes comprehensive health and performance metrics using the Prometheus format.
Each webserver worker exposes metrics on a different port selected from the port range defined by application settings.
In accordance with Prometheus conventions, these metrics are accessible via the `/metrics/` endpoint on each port.
No authentication is required to access these endpoints.
