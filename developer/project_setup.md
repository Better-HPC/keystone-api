# Developer Quickstart

The following sections outline common tasks for application developers and contributors.

## Environment Setup

Start by cloning the project repository from GitHub.

```bash
git clone https://github.com/better-hpc/keystone-api
```

Keystone-API uses [Poetry](https://python-poetry.org/docs/) to manage application dependencies.
Certain dependencies, such as those required by optional features, are excluded by default.
To install all optional dependencies, execute the following command from the root of the cloned repository:

```bash
poetry install --all-extras
```

The API package itself is installed using the `pip` command.
The use of editable mode (`-e`) is recommended:

```bash
pip install -e .
```

!!! note

    Using the `-e` option installs packages in _editable_ mode.
    When this option is enabled, `pip` will point to the local source tree as the installed package instead of
    copying the source files to the standard install location. This allows any file changes to take immediate effect
    without requiring a reinstall.

If the installation was successful, the packaged CLI tool will be available in your working environment.
Use the `enable_autocomplete` command to enable autocomplete for the Bash and Zsh shells.

```bash
keystone-api enable_autocomplete
```

!!! note

    Developers are **strongly** encouraged to review the latest availible CLI commands as described by the CLI
    help text: `keystone-api --help`.

## Running a Server

Keystone-API comes bundled with the `keystone-api` utility which wraps the standard Django management commands.
The most common way to launch an API instance during development is with the runserver command:

```bash
keystone-api runserver --noreload
```

The `runserver` command launches a development server that automatically reloads when source files change.
This server is intended for local development only, and is not safe for use in a production deployment.

In addition to Django’s built-in commands, keystone-api includes several custom utilities for automating common
development tasks.
Select commands are demonstrated below.
For a full list of commands, see `keystone-api --help`.

```bash
keystone-api clean --all #(1)! 
keystone-api quickstart --all #(2)! 
keystone-api genseeddata #(3)! 
```

1. Delete local application data.
2. Bootstrap application dependencies and create an initial database.
3. Load seed data for testing.

## Running Application Tests

Application tests are organized by the testing methodology.
Function tests are packaged in the top level `keystone_api/tests/` directory.
Unit tests are contained within the module being tested under `keystone_api/<module_path>/tests/`.

Use the `test` command to execute all available tests:

```bash
keystone-api test
```

Subsets of tests are run by specifying the desired test path(s) relative to the package root.
For example, tests under the `apps/users` and `apps/allocations` directories are executed as:

```bash
keystone-api test apps.users apps.allocations
```

Test coverage is measured using the standard `coverage` command.
The command will automatically load settings relevant to coverage measurement from the Keystone's `pyproject.toml` file.

```bash
coverage run keystone_api/manage.py test
coverage report
```

## Running System Checks

System checks are used to identify configuration problems, such as missing database migrations or invalid application settings.
These checks are executed using the standard Django commands:

```bash
keystone-api check #(1)! 
keystone-api makemigrations --check #(2)! 
keystone-api health_check #(3)! 
```

1. Check for system configuration errors.
2. Check for missing database migrations.
3. Check the status of backend services.

## OpenAPI Generation

The `spectacular` command will dynamically generate an OpenAPI schema in YAML format.
Rendering the specification into HTML is left to the developer using the documentation tool of their choice.

```bash
keystone-api spectacular --file docs/api/openapi.yml
```
