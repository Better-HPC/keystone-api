# Permissions & Access Control

Keystone uses role-based access control (RBAC) to manage permissions across API resources.
Access rules are evaluated per-request based on the authenticated user's relationship to the target resource.

## User Roles

Permissions are determined by a combination of system-level and team-level roles.

**System-level roles** are defined on the user account itself:

- **Staff**: Users with the `is_staff` flag enabled. Staff users have elevated access across most API resources,
  including the ability to create user accounts, modify any record, and access admin-only endpoints.
- **Authenticated**: Any user with an active session. Authenticated users can read most resources but are restricted in
  what they can modify.

**Team-level roles** are defined through team membership and control access to team-scoped resources:

- **Owner**: Full administrative control over the team and its associated resources.
- **Admin**: Administrative privileges equivalent to owners for most operations.
- **Member**: Standard read access to team resources with limited write access.

Team owners and admins are collectively referred to as *privileged members* throughout the API.

## Access Control by Resource

The tables below summarize the access rules enforced by each API resource.
"Read" refers to `GET`, `HEAD`, and `OPTIONS` requests.
"Write" refers to `POST`, `PUT`, `PATCH`, and `DELETE` requests.

### User Accounts

| Operation | Staff        | Account Owner         | Other Users       |
|-----------|--------------|-----------------------|-------------------|
| List      | All accounts | Own account           | All accounts      |
| Retrieve  | All fields   | Restricted fields     | Restricted fields |
| Create    | Yes          | No                    | No                |
| Update    | All fields   | Non-privileged fields | No                |
| Delete    | Yes          | Yes                   | No                |

Staff users are returned all fields through the privileged serializer, including administrative flags like `is_staff`
and `is_active`.
Non-staff users receive a restricted view that marks these fields as read-only.

### Teams

| Operation | Staff     | Privileged Members | Team Members |
|-----------|-----------|--------------------|--------------|
| List      | All teams | Own teams          | Own teams    |
| Retrieve  | Yes       | Yes                | Yes          |
| Create    | Yes       | Yes                | No           |
| Update    | Yes       | Yes                | No           |
| Delete    | Yes       | Yes                | No           |

Non-staff users only see teams they belong to when listing records.

### Team Membership

| Operation | Staff           | Privileged Members | Team Members        |
|-----------|-----------------|--------------------|---------------------|
| List      | All memberships | All memberships    | All memberships     |
| Retrieve  | Yes             | Yes                | Yes                 |
| Create    | Yes             | Yes                | No                  |
| Update    | Yes             | Yes                | No                  |
| Delete    | Yes             | Yes                | Own membership only |

Standard team members can remove their own membership but cannot modify other membership records.

### Allocation Requests

| Operation | Staff        | Privileged Members | Team Members      |
|-----------|--------------|--------------------|-------------------|
| List      | All requests | Own team requests  | Own team requests |
| Retrieve  | Yes          | Yes                | Yes               |
| Create    | Yes          | Yes                | No                |
| Update    | Yes          | No                 | No                |
| Delete    | Yes          | No                 | No                |

Non-staff users only see requests belonging to their teams when listing records.
Only staff users can modify or delete existing requests after creation.

### Allocations

| Operation | Staff           | Privileged Members   | Team Members         |
|-----------|-----------------|----------------------|----------------------|
| List      | All allocations | Own team allocations | Own team allocations |
| Retrieve  | Yes             | Read only            | Read only            |
| Create    | Yes             | No                   | No                   |
| Update    | Yes             | No                   | No                   |
| Delete    | Yes             | No                   | No                   |

### Allocation Reviews

| Operation | Staff       | Privileged Members | Team Members     |
|-----------|-------------|--------------------|------------------|
| List      | All reviews | Own team reviews   | Own team reviews |
| Retrieve  | Yes         | Read only          | Read only        |
| Create    | Yes         | No                 | No               |
| Update    | Yes         | No                 | No               |
| Delete    | Yes         | No                 | No               |

Non-staff users only see reviews belonging to their teams when listing records.

### Comments

| Operation | Staff                            | Privileged Members   | Team Members         |
|-----------|----------------------------------|----------------------|----------------------|
| List      | All comments (including private) | Public comments only | Public comments only |
| Retrieve  | Yes (including private)          | Public only          | Public only          |
| Create    | Yes (including private)          | Yes (public only)    | Yes (public only)    |
| Update    | Yes (including private)          | Public only          | Public only          |
| Delete    | Yes (including private)          | Public only          | Public only          |

Only staff users can create, read, or modify comments marked as private.
Non-staff users only see public comments belonging to their teams when listing records.

### Attachments

| Operation | Staff           | Privileged Members   | Team Members         |
|-----------|-----------------|----------------------|----------------------|
| List      | All attachments | Own team attachments | Own team attachments |
| Retrieve  | Yes             | Read only            | Read only            |
| Create    | Yes             | No                   | No                   |
| Update    | Yes             | No                   | No                   |
| Delete    | Yes             | No                   | No                   |

### Clusters

| Operation | Staff        | Other Users             |
|-----------|--------------|-------------------------|
| List      | All clusters | Filtered by access mode |
| Retrieve  | Yes          | Yes                     |
| Create    | Yes          | No                      |
| Update    | Yes          | No                      |
| Delete    | Yes          | No                      |

When listing clusters, non-staff users see a filtered set based on each cluster's access mode:

- **Open**: Visible to all users.
- **Whitelist**: Visible only to users belonging to an allowed team.
- **Blacklist**: Visible to all users *except* those belonging to a blocked team.

Retrieve operations are not filtered by access mode — any authenticated user can view a specific cluster by ID.

### Slurm Jobs

| Operation | Staff    | Team Members  |
|-----------|----------|---------------|
| List      | All jobs | Own team jobs |
| Retrieve  | Yes      | Own team jobs |
| Create    | No       | No            |
| Update    | No       | No            |
| Delete    | No       | No            |

Job statistics are read-only for all users.
Non-staff users only see jobs belonging to their teams.

### Grants

| Operation | Staff      | Team Members    | Other Users |
|-----------|------------|-----------------|-------------|
| List      | All grants | Own team grants | No          |
| Retrieve  | Yes        | Yes             | No          |
| Create    | Yes        | Yes             | No          |
| Update    | Yes        | Yes             | No          |
| Delete    | Yes        | Yes             | No          |

Non-staff users only see grants belonging to their teams when listing records.

### Publications

| Operation | Staff            | Team Members          | Other Users |
|-----------|------------------|-----------------------|-------------|
| List      | All publications | Own team publications | No          |
| Retrieve  | Yes              | Yes                   | No          |
| Create    | Yes              | Yes                   | No          |
| Update    | Yes              | Yes                   | No          |
| Delete    | Yes              | Yes                   | No          |

Non-staff users only see publications belonging to their teams when listing records.

### Notifications

| Operation | Staff             | Notification Owner      | Other Users |
|-----------|-------------------|-------------------------|-------------|
| List      | All notifications | Own notifications       | No          |
| Retrieve  | No                | Read and patch          | No          |
| Create    | No                | No                      | No          |
| Update    | No                | Patch `read` field only | No          |
| Delete    | No                | No                      | No          |

Notifications are system-generated and cannot be created, fully updated, or deleted through the API.
Users can only mark their own notifications as read via `PATCH` requests.

### Notification Preferences

| Operation | Staff           | Preference Owner | Other Users |
|-----------|-----------------|------------------|-------------|
| List      | All preferences | Own preferences  | No          |
| Retrieve  | Yes             | Yes              | No          |
| Create    | Yes             | Yes              | No          |
| Update    | Yes             | Yes              | No          |
| Delete    | Yes             | Yes              | No          |

The `user` field defaults to the authenticated user when creating a new preference.
Non-staff users cannot set the `user` field to a different user.

### Statistics

| Endpoint                 | Staff     | Other Users       |
|--------------------------|-----------|-------------------|
| Allocation request stats | All teams | Own teams         |
| Grant stats              | All teams | Own teams         |
| Publication stats        | All teams | Own teams         |
| Notification stats       | All users | Own notifications |

Statistics endpoints are read-only.
Non-staff users receive aggregated statistics scoped to their own team memberships (or their own notifications for
notification stats).

### Admin-Only Endpoints

The following endpoints are restricted to staff users.
Non-staff users cannot access these resources.

| Endpoint          | Description                     |
|-------------------|---------------------------------|
| `/logs/audit/`    | Audit trail for record changes. |
| `/logs/requests/` | Incoming HTTP request logs.     |
| `/logs/tasks/`    | Background task results.        |

## List Filtering Behavior

Several resources apply automatic filtering when non-staff users list records.
This means a `GET` request to a list endpoint may return different results depending on the requesting user's role and
team memberships.

- **Team-scoped resources** (allocation requests, allocations, reviews, comments, attachments, grants, publications,
  jobs): Non-staff users only see records belonging to teams where they hold membership.
- **User-scoped resources** (notifications, preferences): Non-staff users only see their own records.
- **Unfiltered resources** (clusters): Filtered by the cluster's access mode rather than team membership.

Staff users always receive unfiltered results across all list endpoints.
