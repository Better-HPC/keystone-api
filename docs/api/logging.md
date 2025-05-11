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

This header enables consistent log correlation by assigning a unique identifier to each incoming request, making it
easier to trace activity across distributed systems and services.

Clients may explicitly provide a correlation ID using the X-KEYSTONE-CID header.
The value must be a valid UUIDv4 hex string (without dashes).
If the header is not included in the request, Keystone will automatically generate a random UUIDv4 hex value for
internal use.

The correlation ID is attached to internal logs and any outgoing service calls, allowing developers and operators to
trace a single request across the full execution path.

=== "python"

    ```python
    import uuid
    import requests
    
    headers = {
        "X-KEYSTONE-CID": uuid.uuid4().hex  # Optional: explicitly set the correlation ID
    }
    
    response = requests.get(
        url="https://keystone.domain.com/users/users/",
        headers=headers,
    )
    
    response.raise_for_status()
    print(response.json())
    ```

=== "bash"

    ```bash
    CID=$(uuidgen | tr -d '-')
    
    curl -s -H "X-KEYSTONE-CID: $CID" \
      "https://keystone.domain.com/users/users/"
    ```
