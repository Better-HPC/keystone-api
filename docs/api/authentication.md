# Authentication

Keystone uses session tokens to manage user authentication and permissions.
New sessions are generated using the `authentication/login/` endpoint.
Once successfully authenticated, the endpoint will issue a `200`
response and include cookies for the session ID and CSRF token.

=== "python"

    ```python
    import requests
    
    credentials = {"username": "user", "password": "userpassword"} 

    # Session objects will automatically store and manage authentication cookies
    session = requests.Session()
    auth_response = session.post(
        url="https://keystone.domain.com/authentication/login/",
        data=credentials)

    auth_response.raise_for_status()
    print(auth_response.cookies)
    ```

=== "bash"

    ```bash
    credentials='{"username": "user", "password": "userpassword"}'
    headers='Content-Type: application/json'

    curl -s -X POST \
      -c cookies.txt \
      -H "$headers" \
      -d "$credentials" \
      https://keystone.domain.com/authentication/login/

    cat cookies.txt
    ```

Future requests to API endpoints are authorized by including the session cookie.
Write operations (`POST`, `PUT`, `PATCH`, `DELETE`) will also require the CSRF token in the request header.

=== "python"

    ```python
    # Read operations only require session cookies
    get_response = session.get(url="https://keystone.domain.com/users/users/")
    get_response.raise_for_status()
    print(get_response.json())

    # Write operations require CSRF headers and session cookies
    patch_response = session.patch(
        url="https://keystone.domain.com/users/users/1", 
        headers={'X-CSRFToken': session.cookies['csrftoken']})

    patch_response.raise_for_status()
    print(patch_response.json())
    ```

=== "bash"

    ```bash
    # Read operations only require session cookies
    get_response=$(curl -s -b cookies.txt "https://keystone.domain.com/users/users/")
    echo "$get_response"

    # Write operations require CSRF headers and session cookies
    csrf_token=$(grep 'csrftoken' cookies.txt | awk '{print $7}')
    patch_response=$(curl -s -X PATCH \
      -b cookies.txt \
      -H "X-CSRFToken: $csrf_token" \
      "https://keystone.domain.com/users/users/1")

    echo "$patch_response"
    ```

Users can manually invalidate their session using the `authentication/logout/` endpoint.

=== "python"

    ```python
    logout_request = session.post(
        url="https://keystone.domain.com/authentication/logout/", 
        headers={'X-CSRFToken': session.cookies['csrftoken']})

    logout_request.raise_for_status()
    print(logout_request.json())
    ```

=== "bash"

    ```bash
    logout_response=$(curl -s -X POST \
      -b cookies.txt \ 
      -H "X-CSRFToken: $csrf_token" \
      "https://keystone.domain.com/authentication/logout/")
    
    echo "$logout_response"
    ```