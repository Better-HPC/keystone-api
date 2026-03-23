# Background Tasks

Keystone leverages background tasks to help drive user experiences and maintain application state.
These tasks run asynchronously from the main API process and handle recurring operations like user synchronization,
log maintenance, and HPC limit enforcement.

## Scheduled Tasks

### LDAP Synchronization

*Task Name:* `apps.users.tasks.ldap_update_users` <br>
*Schedule:* Every 15 minutes

Synchronizes user account data against the configured LDAP directory.
New LDAP entries are created as application user accounts and existing accounts are updated to reflect their current
LDAP attributes. When an LDAP entry is removed from the directory, the corresponding user account is either deactivated
or deleted depending on the `AUTH_LDAP_PURGE_REMOVED` setting.

!!! note

    This task does nothing if the `AUTH_LDAP_SERVER_URI` setting is not set.

### Log Cleanup

*Task Name:* `apps.logging.tasks.clear_log_records` <br>
*Schedule:* Every hour (at minute 0)

Deletes log records from the application database that exceed their configured retention period.
The default retention period for each log type is configurable via [application settings](settings.md)

### HPC Limit Enforcement

*Task Name:* `apps.allocations.tasks.limits.update_limits` <br>
*Schedule:* Every hour (at minute 0)

Synchronizes resource allocation limits on each HPC cluster for all Keystone accounts.

### HPC Job Synchronization

*Task Name:* `apps.allocations.tasks.jobstats.slurm_update_job_stats` <br>
*Schedule:* Every 5 minutes

Fetches job information from the HPC scheduler and synchronizes it with the application database.

### Upcoming Expiration Notifications

*Task Name:* `apps.notifications.tasks.upcoming_expirations.notify_upcoming_expirations` <br>
*Schedule:* Daily at midnight

Sends email notifications to users whose active allocations are approaching their expiration date.
Notifications are sent to all active members of the team associated with each expiring allocation request.

### Past Expiration Notifications

*Task Name:* `apps.notifications.tasks.past_expirations.notify_past_expirations` <br>
*Schedule:* Daily at midnight

Sends email notifications to users whose allocations have expired within the last three days.
Notifications are sent to all active members of the team associated with each expired allocation request.

## Task Monitoring

Task outcomes are recorded in the application database and can be monitored through the API logging endpoint.
Results include the task name, status, execution time, and any error tracebacks.
See the [Status Monitoring](../api/logging.md) documentation for details.

