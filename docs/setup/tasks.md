# Background Tasks

Keystone uses Celery and Celery Beat to schedule and execute background tasks.
These tasks run asynchronously from the main API process and handle recurring operations like user synchronization,
log maintenance, resource limit enforcement, and automated notifications.

## Architecture

Background task processing involves two separate services that must be running alongside the API:

- **Celery Worker**: Executes tasks as they are dispatched to the job queue.
- **Celery Beat**: Triggers tasks on a recurring schedule according to the configured intervals.

Both services use Redis as a message broker and store task results in the application database.
Task results are accessible to staff users through the `/logs/tasks/` API endpoint.

For deployment instructions, see the [Docker](../install/docker.md) or [Systemd](../install/systemd.md) installation
guides.

## Scheduled Tasks

The following tasks are registered with Celery Beat and run automatically at the intervals described below.

### LDAP User Synchronization

|               |                                                     |
|---------------|-----------------------------------------------------|
| **Task**      | `apps.users.tasks.ldap_update_users`                |
| **Schedule**  | Every 15 minutes                                    |
| **Condition** | Only runs when `AUTH_LDAP_SERVER_URI` is configured |

Synchronizes user account data against the configured LDAP directory.
New LDAP entries are created as application user accounts and existing accounts are updated to reflect their current
LDAP attributes.
The field mapping between LDAP attributes and user account fields is controlled by the
`AUTH_LDAP_ATTR_MAP` [setting](settings.md).

When an LDAP entry is removed from the directory, the corresponding user account is either deactivated or deleted
depending on the `AUTH_LDAP_PURGE_REMOVED` setting.

The task includes retry logic with exponential backoff, making up to three connection attempts before failing.
If all attempts fail, the error is logged and the task result is recorded as a failure.

!!! note

    This task does nothing if `AUTH_LDAP_SERVER_URI` is not set.
    LDAP synchronization can also be triggered manually using the `keystone-api ldap_update` management command.

### Log Record Cleanup

|              |                                        |
|--------------|----------------------------------------|
| **Task**     | `apps.logging.tasks.clear_log_records` |
| **Schedule** | Every hour (at minute 0)               |

Deletes log records from the application database that exceed their configured retention period.
Three categories of logs are pruned independently, each with its own retention setting:

| Log Type          | Setting                 | Default Retention |
|-------------------|-------------------------|-------------------|
| HTTP request logs | `LOG_REQ_RETENTION_SEC` | 30 days           |
| Audit logs        | `LOG_AUD_RETENTION_SEC` | 30 days           |
| Task result logs  | `LOG_TSK_RETENTION_SEC` | 30 days           |

Setting a retention value to `0` disables pruning for that log type, keeping all records indefinitely.

!!! warning

    Disabling log pruning in a production environment can lead to significant database growth over time.
    Monitor database size regularly if retention is set to `0` for any log type.

### Slurm Usage Limit Enforcement

|              |                                               |
|--------------|-----------------------------------------------|
| **Task**     | `apps.allocations.tasks.limits.update_limits` |
| **Schedule** | Every hour (at minute 0)                      |

Updates TRES billing limits for all Slurm accounts across all enabled clusters.
The task dispatches a separate subtask for each cluster, allowing limits to be updated concurrently.

For each Slurm account with a corresponding Keystone team, the task performs the following steps:

1. Calculates service units from active and expiring allocations.
2. Retrieves the current TRES limit and usage from Slurm.
3. Estimates historical usage not tied to current allocations.
4. Distributes current usage across expiring allocations proportionally and records final usage values.
5. Recalculates the TRES limit and pushes the updated value to Slurm.

Slurm accounts without a corresponding Keystone team and the `root` account are skipped.
Errors during processing of individual accounts are logged but do not prevent other accounts from being updated.

### Slurm Job Statistics Synchronization

|              |                                                          |
|--------------|----------------------------------------------------------|
| **Task**     | `apps.allocations.tasks.jobstats.slurm_update_job_stats` |
| **Schedule** | Every 5 minutes                                          |

Fetches job information from Slurm and synchronizes it with the application database.
Like limit enforcement, a separate subtask is dispatched for each enabled cluster.

Job records are matched by their Slurm job ID.
New jobs are inserted and existing jobs are updated with the latest state, timestamps, and resource usage data.
Each job is associated with a Keystone team based on the Slurm account name.

### Upcoming Expiration Notifications

|              |                                                                             |
|--------------|-----------------------------------------------------------------------------|
| **Task**     | `apps.notifications.tasks.upcoming_expirations.notify_upcoming_expirations` |
| **Schedule** | Daily at midnight                                                           |

Sends email notifications to users whose active allocations are approaching their expiration date.
Notifications are sent to all active members of the team associated with each expiring allocation request.

Whether a notification is sent depends on the user's notification preferences:

- The allocation must have an expiration date in the future.
- The number of days until expiration must fall within one of the user's configured expiry thresholds (default: 30 and
  14 days).
- The user must not have already received a notification for the same request at the same or earlier threshold.
- The user's account and the allocation request must both predate the notification threshold window.

Each notification is dispatched as an independent subtask, ensuring that a failure to notify one user does not
block notifications for others.
Notification preferences can be managed through the `/notifications/preferences/` API endpoint.

### Past Expiration Notifications

|              |                                                                     |
|--------------|---------------------------------------------------------------------|
| **Task**     | `apps.notifications.tasks.past_expirations.notify_past_expirations` |
| **Schedule** | Daily at midnight                                                   |

Sends email notifications to users whose allocations have expired within the last three days.
Notifications are sent to all active members of the team associated with each expired allocation request.

A notification is sent only if:

- The allocation has passed its expiration date.
- The user has not already been notified about this specific expiration.
- The user's notification preferences have `notify_on_expiration` enabled.

Like upcoming expiration notifications, each notification is dispatched as an independent subtask.

## Task Monitoring

Task outcomes are recorded in the application database and can be monitored through the following channels:

- **API endpoint**: Staff users can query task results at `/logs/tasks/`. Results include the task name, status,
  execution time, and any error tracebacks.
- **Admin interface**: Task results are also visible in the Django admin panel under the logging section.
- **Application logs**: Task-level logging is written to the application log file. The log level and file location are
  controlled by the `LOG_APP_LEVEL` and `LOG_APP_FILE` [settings](settings.md).

Task results are automatically pruned according to the `LOG_TSK_RETENTION_SEC` setting.

## Manual Execution

Some background tasks can be triggered outside of their regular schedule:

| Command                    | Description                                |
|----------------------------|--------------------------------------------|
| `keystone-api ldap_update` | Run LDAP user synchronization immediately. |

Tasks can also be triggered manually through the Django admin interface by navigating to the Celery Beat periodic
task configuration and using the "Run now" action.
