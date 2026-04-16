# Batch Jobs

Keystone workflows frequently involve creating or modifying several related resources together.
Rather than issuing these requests individually, the batch API allows them to be grouped into a single atomic job.
If any step in the job fails, all changes made by the job are rolled back, ensuring the database is never left in
a partial state.

## Defining Steps

Batch job are defined using a JSON object with an `actions` array.
Every element of `actions` is a step describing a single API request to execute.

```json
{
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
```

Each step supports the following fields:

| Field          | Required | Description                                                             |
|----------------|----------|-------------------------------------------------------------------------|
| `method`       | Yes      | The HTTP method to use (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`).       |
| `path`         | Yes      | The API endpoint path to call, including any path parameters.           |
| `payload`      | No       | A JSON object to send as the request body. Defaults to an empty object. |
| `query_params` | No       | A JSON object of query string parameters to append to the request URL.  |
| `ref`          | No       | An alias used to reference this step's response in subsequent steps.    |

## Referencing Previous Steps

Steps can reference the response body of any previously executed step using a reference token.
This allows the output of one step - such as a newly created record's ID - to be passed as input to a later step.

To use a reference, first assign a `ref` alias to the step whose output you want to capture, then use the
`@ref{alias.dotpath}` syntax in any `path`, `payload`, or `query_params` value of subsequent steps.
The dotpath supports both dictionary key access and integer list indexing, separated by dots.

In the following example, a grant is created in the first step and its `id` is injected into the path of the second
step:

```json
{
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
```

!!! note

    Job steps are executed following the order in which they are defined. 
    A step can only reference the output of previous steps in the execution order.
    Forward references are not supported.

## Dry Runs

Setting `dry_run` to `true` executes all steps and returns their results without persisting any database changes.
This is useful for validating a job before committing it.

```json
{
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
```

## Response Format

A successful job returns `HTTP 200` with a `results` array containing one entry per executed step.

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
| `ref`    | The step's alias, or `null` if none was provided.                            |
| `index`  | The one-based position of the step within the job.                           |
| `method` | The HTTP method executed.                                                    |
| `path`   | The resolved path that was called, after any `@ref` tokens were substituted. |
| `status` | The HTTP status code returned by the step.                                   |
| `body`   | The response body returned by the step.                                      |
