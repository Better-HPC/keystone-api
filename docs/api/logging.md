# Application Logging

Keystone-API provides access to application logs through dedicated API endpoints.
All log endpoints require [authentication](./authentication.md) with administrator privileges and support the
API's standard [query parameters](./filtering.md).

| Endpoint              | 	Description                                                      |
|-----------------------|-------------------------------------------------------------------|
| `/logging/requests/`	 | Logs of incoming HTTP requests and related metadata.              |
| `/logging/audit/`     | Audit trail of user actions against select application resources. |
| `/logging/apps/`	     | Application-level logs (e.g., debug, info, warning).              |
| `/logging/tasks/`     | Results and statuses of scheduled background tasks.               |

## Enabling Logging IDs

To support traceability, Keystone attaches a correlation ID (`cid`) to each incoming request.
This ID is propagated through internal logs, enabling log correlation across distributed systems.

Clients may provide a correlation ID explicitly using the `X-KEYSTONE-CID` header.
The value must be a valid UUIDv4 hex string (without dashes).
If the header is omitted, the API will generate a random UUIDv4 hex value automatically.

!!! important

    The `X-KEYSTONE-CID` must be preserved by upstream proxies for clients to specify custom CID values.
    If the header is not forwarded, the API will assign unique ID values to each incoming request.
    This may result in logs not being appropriatly correlated across requests originating from persistant user sessions.
