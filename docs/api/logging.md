# Session Logging

Keystone supports request tracing through the use of the `X-KEYSTONE-CID` header.
This header enables consistent log correlation by assigning a unique identifier to each incoming request, making it easier to trace activity across distributed systems and services.

## How It Works

Clients may explicitly provide a correlation ID using the X-KEYSTONE-CID header.
The value must be a valid UUIDv4 hex string (without dashes).
If the header is not included in the request, Keystone will automatically generate a random UUIDv4 hex value for internal use.

The correlation ID is attached to internal logs and any outgoing service calls, allowing developers and operators to trace a single request across the full execution path.

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
