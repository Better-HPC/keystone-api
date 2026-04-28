# Batch Jobs

The batch API allows users to group multiple API requests into a single atomic job.
If any request in the job fails, all changes made by the job are rolled back, ensuring the application is never left in
a partial state.

## Request Format

Batch jobs are submitted as a JSON object with a single top-level `job` key whose value describes the job to execute.
The job's `actions` list is used to define the HTTP requests to be processed in bulk by the API.
The following example demonstrates a job used to create two separate Grant records.

```json
{
  "job": {
    "actions": [
      {
        "method": "POST",
        "path": "/research/grants/",
        "payload": {
          "title": "First New Grant",
          "team": 1
        }
      },
      {
        "method": "POST",
        "path": "/research/grants/",
        "payload": {
          "title": "Second New Grant",
          "team": 1
        }
      }
    ]
  }
}
```

Entries in the `actions` list support the following fields:

| Field          | Required | Description                                                             |
|----------------|----------|-------------------------------------------------------------------------|
| `method`       | Yes      | The HTTP method to use (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`).       |
| `path`         | Yes      | The API endpoint path to call.                                          |
| `payload`      | No       | A JSON object to send as the request body.                              |
| `query_params` | No       | A JSON object of query parameters to append to the request URL.         |
| `ref`          | No       | An alias used to reference the action's response in subsequent actions. |

## Referencing Previous Actions

Actions can reference the response body of any previously executed requests using a reference token.
This allows the output of one action — such as a newly created record's ID — to be passed as input to a later action.

To use a reference, assign a `ref` alias to the action whose output you want to capture.
Then use the `@ref{alias.dotpath}` syntax in any subsequent `path`, `payload`, or `query_params` value.
References support both dictionary key access and integer list indexing, allowing deep traversal into nested objects.

In the following example, a grant is created in the first step and its `id` is injected into the path of the second
step:

```json
{
  "job": {
    "actions": [
      {
        "ref": "new_grant",
        "method": "POST",
        "path": "/research/grants/",
        "payload": {
          "title": "My Grant",
          "team": 1
        }
      },
      {
        "method": "PATCH",
        "path": "/research/grants/@ref{new_grant.id}/",
        "payload": {
          "title": "Updated Title"
        }
      }
    ]
  }
}
```

!!! note

    Actions are executed following the order in which they are defined.
    An action can only reference the output of previous steps in the execution order.
    Forward references are not supported.

## Uploading Files

Actions can include file attachments by submitting the job as a `multipart/form-data` request instead of JSON.
Include the job definition as a JSON string in the `job` form field, and attach each file as a separate form field.

File parts can be referenced using the `@file{name}` syntax, where `name` is the multipart field name of the uploaded
file.

```
POST /batch/
Content-Type: multipart/form-data

job = {
  "actions": [
    {
      "method": "POST",
      "path": "/research/grants/1/attachments/",
      "payload": {
        "file": "@file{upload}"
      }
    }
  ]
}
upload = <binary file content>
```

## Dry Runs

Setting `dry_run` to `true` executes all actions in a job and returns their results without persisting any database
changes.
This is useful for validating a job before committing it.

```json
{
  "job": {
    "dry_run": true,
    "actions": [
      {
        "method": "POST",
        "path": "/research/grants/",
        "payload": {
          "title": "My Grant",
          "team": 1
        }
      }
    ]
  }
}
```

## Response Format

A successful job returns a `200` status code with a `results` array containing one entry per executed step.
For example:

```json
{
  "results": [
    {
      "ref": "new_grant",
      "index": 1,
      "method": "POST",
      "path": "/research/grants/",
      "status": 201,
      "body": {
        "id": 42,
        "title": "My Grant",
        "team": 1
      }
    }
  ]
}
```

Each result contains the following fields:

| Field    | Description                                                                  |
|----------|------------------------------------------------------------------------------|
| `ref`    | The actions's alias, or `null` if none was provided.                         |
| `index`  | The one-based position of the step within the job.                           |
| `method` | The HTTP method executed.                                                    |
| `path`   | The resolved path that was called, after any `@ref` tokens were substituted. |
| `status` | The HTTP status code returned by the step.                                   |
| `body`   | The response body returned by the step.                                      |

### Step Failure

If any action encounters an error, the job halts immediately and all changes are rolled back.
In this case the API will return a `422` error along with a description of the failing step.
For example:

```json
{
  "detail": "Step #2 (POST /research/grants/) failed with status 400",
  "step": 2,
  "status": 400,
  "body": {
    "title": [
      "This field is required."
    ]
  }
}
```

### Reference Resolution Failure

If a `@ref` or `@file` token cannot be resolved — for example because the alias is undefined, the dotpath is
invalid, or a referenced file part was not uploaded — the job halts and a `422` error is returned:

```json
{
  "detail": "Cannot resolve reference \"@ref{missing_alias.id}\": Alias \"missing_alias\" has not been defined by a previous step",
  "token": "@ref{missing_alias.id}"
}
```
