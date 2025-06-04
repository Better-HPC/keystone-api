# Application Logging

Keystone-API provides access to application logs through dedicated API endpoints.
All log endpoints require [authentication](./authentication.md) with administrator privileges and support the
API's standard [query parameters](./filtering.md).

| Endpoint             | 	Description                                                       |
|----------------------|--------------------------------------------------------------------|
| `/logging/requests/` | Logs incoming HTTP requests and related metadata.                  |
| `/logging/audit/`    | Audit trail for user actions against select application resources. |
| `/logging/apps/`	    | Application-level logs (e.g., debug, info, warning).               |
| `/logging/tasks/`    | Results and status of scheduled background tasks.                  |

## Enabling Log IDs

Keystone automatically attaches a correlation ID (`cid`) to each incoming request.
This unique value is propagated through internal logs, enabling record correlation across logging endpoints.

Clients may optionally specify the correlation ID using the `X-KEYSTONE-CID` header.
The value must be a valid UUIDv4 string, including dashes (e.g. `d61eef0b-258d-42ca-b14b-852860a54259`).
This enables clients to self-organize their generated logs around a common transaction or user session.
