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

| Block Name | Description                                            |
|------------|--------------------------------------------------------|
| `main`     | Main body content of the email notification.           |
| `footer`   | Footer content displayed at the bottom of the message. |

??? example "Default Template Content"

    ```
    {% include "../../keystone_api/templates/base.html" %}
    ```

### Upcoming Resource Expiration

**Template file:** `upcoming_expiration.html`

The _upcoming expiration_ notification alerts users that one or more of their active resource allocations is nearing
its expiration date.

??? example "Default Template Content"

    ```
    {% include "../../keystone_api/templates/upcoming_expiration.html" %}
    ```

### Expired Resource Allocation

**Template file:** `past_expiration.html`

The _past expiration_ notification alerts users that one or more of their active resource allocations has expired
and that the resources granted under that allocation are no longer availible for use.

??? example "Default Template Content"

    ```
    {% include "../../keystone_api/templates/past_expiration.html" %}
    ```
