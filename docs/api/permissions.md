# Access Control

Keystone uses role-based access control (RBAC) to manage permissions across API resources.
Access rules are evaluated per-request based on the authenticated user's relationship to the target resource.

## User Roles

User permissions are determined by a combination of system-level and team-level roles.

### System Level Roles

System-level roles are defined on the user account itself:

- **Authenticated users**: Any user with an active, authenticated session. Authenticated users can read most resources
  but are restricted in what they can modify.
- **Staff**: Users with the `is_staff` flag enabled on their account. Staff users have elevated access across most API
  resources, including the ability to create user accounts, modify most records, and access admin-only endpoints.

### Team Level Roles

Team-level roles are defined through team membership and control access to team-scoped resources:

- **Owner**: Full administrative control over the team and its associated resources.
- **Admin**: Administrative privileges equivalent to owners for most operations.
- **Member**: Standard read access to team resources with limited write access.

Team owners and admins are collectively referred to as *privileged members* throughout the API.

## Access Control Model

The following sections describe the general access patterns enforced across the API. For documentation on specific
per-endpoint permissions, please refer to the official [OpenAPI specification](openapi.md).

### Staff Users

Staff users have the broadest access across the API.
In most cases, staff users can read and write all records regardless of team membership.
Staff users are also the only role that can access admin-only endpoints such as logging and audit trails.

### Team-Scoped Resources

Most resources in Keystone are associated with a team, either directly (e.g., grants, publications) or through a parent
record (e.g., allocations, reviews, comments, and attachments). For these resources, access generally adheres to the
following pattern:

- **Read access** is granted to all members of the associated team.
- **Write access** is granted only to staff users and team members. Some resources grant write access to all team
  members while others restrict it to privileged members (i.e., team owners and admins).

When retrieving a list of team-scoped records, non-staff users are only returned records belonging to teams where
they hold membership. Staff users always receive unfiltered results, and have access to all records across all teams.

### User-Scoped Resources

Some resources are scoped to an individual user rather than a team.
These resources grant elevated permissions to the user who owns the record.
For example, users can modify their own user account (with restrictions on privileged fields like `is_staff`)
and team members can delete their own membership records.
