# Keystone API

This repository contains source code for the Keystone REST API.

A quickstart guide for project developers is provided below.
For the full Keystone project documentation, see [keystone.bhpc.dev](https://keystone.bhpc.dev).

## Developer Setup

This project uses [Poetry](https://python-poetry.org/) to manage software dependencies.
Optional dependencies are defined using the following groups:

| Group  | Description                                                                  |
|--------|------------------------------------------------------------------------------|
| `dev`  | Development dependencies, including those required to run application tests. |
| `prod` | Runtime dependencies bundled into the published Docker image.                |

To install the project with one or more dependency groups, use Poetry's `install` command:

```bash
poetry install --with dev
```

The `keystone-api` command is used for most project management tasks.
Poetry exposes this CLI using the `poetry run` syntax (e.g. `poetry run keystone-api`).
however, it is generally more convenient to install the CLI directly in to their working environemnt:

```bash
pip install -e .
keystone-api enable_autocomplete # For Bash and Zsh shells 
```

## Common Tasks

### Launching a Server

The `quickstart` command allows developers to execute several common tasks with a single CLI call.
This includes initializing application dependencies, creating an admin user account, and deploying the API server.
For example:

```bash
keystone-api quickstart --migrate --demo-user --celery --smtp --server
```

The `--all` option can also be used to conveniently execute all quickstart tasks at once:

```bash
keystone-api quickstart --all
```

**Note:** The `--demo-user` option will only create an admin user account if no user accounts already exist.
This is a safety feature to avoid insecure admin accounts being accidentally created in production settings.

### Populating Mock Data

The `genseeddata` command will populate the application database with semi-realistic mock data.
The generated data is suitable for evaluating API behavior and for demonstrating/testing the application frontend.

```bash
keystone-api gensseeddata
```

### Application Cleanup

The `clean` command will remove application files and restore the package to a clean working state.

```bash
keystone-api clean --static --uploads --sqlite --log
```

Similar to the `quickstart` command, the `--all` option is provided for convenience:

```bash
keystone-api clean --all
```

### Updating Database Migrations

The backend database schema - including logic for migrating between schema versions - is derived dynamically from the
application ORM classes.
New schema migrations need to be generated any time changes are made to the ORM.

```bash
keystone-api makemigrations
```

**Note:** While the `django` framework is known for its reliable database management, dynamically generated migrations
should be manually reviewed by the developer

### Generating OpenAPI Schemas

This project maintains an official OpenAPI schema for use by downstream developers and customers.
Similar to the project's database schema, the OpenAPI schema is derived dynamically from the project source code.
To update the official OpenAPI file:

```bash
keystone-api spectacular --fail-on-warn --file ./docs/api/openapi.yml 
```
