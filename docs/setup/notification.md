# Notification Templates

Keystone issues automated notifications regarding changes to user accounts and resource allocations.
Administrators can customize these notifications using templates to reflect organization-specific branding and
messaging.

## Overriding Templates

Keystone generates notifications using HTML templates and the Jinja2 templating engine.
The location of custom templates is configurable via [application settings](settings.md).

When a notification is triggered, Keystone first checks for a custom template file.
If no custom template is available, Keystone falls back to an internal default.
The selected template is then rendered using the context data outlined below.

For security reasons, data is sanitized before being injected into the template.
Certain Jinja features — such as access to application internals — are also disabled.

### Base Template

**Template file:** `base.html`

The base template serves as the parent layout for all notification content, providing top-level styling and structure.
The template defines two content blocks that child templates override to inject content.

??? info "Available Template Fields"

    | Block Name | Description                                            |
    |------------|--------------------------------------------------------|
    | `main`     | Main body content of the email notification.           |
    | `footer`   | Footer content displayed at the bottom of the message. |

??? abstract "Default Template Content"

    ```
    {% include "../../keystone_api/templates/base.html" %}
    ```

### Upcoming Resource Expiration

**Template file:** `upcoming_expiration.html`

The _upcoming expiration_ notification alerts users that one or more of their active resource allocations is nearing
its expiration date.

??? info "Available Template Fields"
    
    | Field Name           | Type             | Description                                                               |
    |----------------------|------------------|---------------------------------------------------------------------------|
    | `user_name`          | `str`            | Username of the notified user.                                            |
    | `user_first`         | `str`            | First name of the notified user.                                          |
    | `user_last`          | `str`            | Last name of the notified user.                                           |
    | `req_id`             | `int`            | ID of the allocation request being notified about.                        |
    | `req_title`          | `str`            | Title or of the allocation request.                                       |
    | `req_team`           | `str`            | Name of the team associated with the allocation request.                  |
    | `req_submitted`      | `date`           | Date when the allocation request was submitted.                           |
    | `req_active`         | `date`           | Date when the allocation request became active.                           |
    | `req_expire`         | `date` or `None` | Date when the allocation request expires.                                 |
    | `req_days_left`      | `int` or `None`  | Number of days remaining until expiration (calculated from current date). |
    | `allocations`        | `list[dict]`     | List of allocated resources tied to the request. Each item includes:      |
    | ├─ `alloc_cluster`   | `str`            | Name of the cluster where the resource is allocated.                      |
    | ├─ `alloc_requested` | `int`            | Number of service units requested (or `0` if unavailable).                |
    | └─ `alloc_awarded`   | `int`            | Number of service units awarded (or `0` if unavailable).                  |

??? abstract "Default Template Content"

    ```
    {% include "../../keystone_api/templates/upcoming_expiration.html" %}
    ```

### Expired Resource Allocation

**Template file:** `past_expiration.html`

The _past expiration_ notification alerts users that one or more of their active resource allocations has expired
and that the resources granted under that allocation are no longer available for use.

??? info "Available Template Fields"
    
    | Field Name           | Type             | Description                                                          |
    |----------------------|------------------|----------------------------------------------------------------------|
    | `user_name`          | `str`            | Username of the notified user.                                       |
    | `user_first`         | `str`            | First name of the notified user.                                     |
    | `user_last`          | `str`            | Last name of the notified user.                                      |
    | `req_id`             | `int`            | ID of the allocation request being notified about.                   |
    | `req_title`          | `str`            | Title or of the allocation request.                                  |
    | `req_team`           | `str`            | Name of the team associated with the allocation request.             |
    | `req_submitted`      | `date`           | Date when the allocation request was submitted.                      |
    | `req_active`         | `date`           | Date when the allocation request became active.                      |
    | `req_expire`         | `date` or `None` | Date when the allocation request expires.                            |
    | `allocations`        | `list[dict]`     | List of allocated resources tied to the request. Each item includes: |
    | ├─ `alloc_cluster`   | `str`            | Name of the cluster where the resource is allocated.                 |
    | ├─ `alloc_requested` | `int`            | Number of service units requested (or `0` if unavailable).           |
    | └─ `alloc_awarded`   | `int`            | Number of service units awarded (or `0` if unavailable).             |
    | └─ `alloc_awarded`   | `int`            | Number of service unitss used by the team (or `0` if unavailable).   |

??? abstract "Default Template Content"

    ```
    {% include "../../keystone_api/templates/past_expiration.html" %}
    ```
