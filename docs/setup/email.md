# Notification Templates

Keystone issues automated notifications regarding changes to user accounts and resource allocations.
Administrators can customize these notifications using templates to reflect organization-specific branding and
messaging.

## Overriding Templates

Keystone generates notifications using HTML templates rendered using the Jinja2 templating engine.
For security reasons, some Jinja features — such as access to application internals — are disabled.

Custom templates are stored in a location defined in the [application settings](settings.md).
When a notification is triggered, Keystone first checks the configured directory for a matching template.
If a custom template is found, its rendered using the provided context variables (see below for details).
If no custom template is available, Keystone falls back to an internal default.

Summaries of available templates, along with their supported variables, are provided in the sections below.

### Base Template

**Template file:** `base.html`

The base template serves as the parent layout for all notification content, providing top-level styling and structure.
The template defines two content blocks that child templates can override to inject custom content.

| Block Name | Description                                            |
|------------|--------------------------------------------------------|
| `main`     | Main body content of the email notification.           |
| `footer`   | Footer content displayed at the bottom of the message. |

??? example "Default Template Content"

### Upcoming Resource Expiration

**Template file:** `upcoming_expiration.html`

??? example "Default Template Content"

### Expired Resource Allocation

**Template file:** `past_expiration.html`

??? example "Default Template Content"
