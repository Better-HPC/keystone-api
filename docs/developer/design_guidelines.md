# Design Guidelines

Keystone API uses the following design principles to ensure project consistency and maintainability.

## Request Error Handling

When an HTTP request fails, the response should provide a clear and unambiguous indication of the failure reason.
Since multiple validation steps may apply to a single request, the system follows a standardized order of validation
to determine the appropriate error response.
The first failing validation step dictates the returned status code to maintain consistency across all endpoints.

### Request Validation Hierarchy

1. **User authentication status:**
   Requests from unauthenticated users attempting to access protected resources must return a `403 Forbidden` error.
2. **Support for the requested method:**
   Requests using unsupported HTTP methods (e.g., `TRACE`, `CONNECT`) must return a `405 Method Not Allowed` error.
3. **Role Based Access Controls (RBAC):**
   Requests that fail RBAC or business logic authorization checks must return a `403 Forbidden` error.
4. **Additional request verification:**
   Any further request-specific validation logic must be processed in this step, with response codes adhering to
   industry-standard practices.

## Record Serialization

Consistent data serialization ensures predictable API behavior and simplifies integration with client applications.
API responses must adhere to the following serialization rules:

- JSON fields must map directly to a database or ORM model field with the same name.
- Primary key values must be read-only and cannot be modified by clients.
- Fields should maintain type consistency (e.g., integers remain integers, booleans remain booleans).
- Timestamps should follow the ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).

## Serializing Relationships

When serializing relational data, all relationships must be represented using primary key values.
While an individual record’s primary key remains immutable via the API, primary key fields within nested relationships 
are writable when modifying associations (e.g., when adding a record to a relationship).

Nested representations of related entities should be included alongside primary keys.
These nested representations must use the same field name as the corresponding ID field prefixed with an underscore (_).
Nested representations must read-only and should only include fields required by downstream applications.

!!! example "Example: Serializing a One-to-Many"

    The following schema demonstrates a one-to-many relationship between the `Author` and `Book` models.

    ```mermaid

    classDiagram
        direction LR
        Author "1" *-- "0..*" Book
        class Author {
          +id: int
          +name: string
        }
        class Book {
          +id: int
          +title: string
          +publisher: string
        }
    ```

    When serializing an `Author` record, the `books` field is required and contains a list of primary key values.
    The `_books` field provides a nested representation with selected attributes.
    ```
    {
      "id": 1,
      "title": "Book A",
      "author": 1,
      "_author": {
        "name": "John Smith"
      }
    }
    ```

    Serializing the relationship works similarly in the reverse direction, and while including reverse relationships is encouraged for consistency, it is not strictly required unless explicitly defined by the API contract.

    ```json
    {
      "id": 1,
      "name": "John Smith",
      "books": [1, 2],
      "_books": [
        {"title": "Book A"},
        {"title": "Book B"}
      ]
    }
    ```
