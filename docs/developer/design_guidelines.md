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

## Data Serialization

### Serializing Records

To ensure consistent and predictable API responses, database records must be serialized into JSON according to the following standards:

- The resulting JSON fields must map directly to a database/ORM model field with the same name.
- Field types must remain consistent with their database counterparts (e.g., integers remain integers, booleans remain booleans).
- Primary key values must be read-only and cannot be modified by clients.

!!! example "Example: Serializing a Record"

    Consider a `User` model with the following attributes:
    
    ```mermaid
    classDiagram
        class User {
            +id: int
            +username: string
            +email: string
            +is_active: bool
        }
    ```

    A serialized `User` record should appear as follows:
    
    ```json
    {
      "id": 42,
      "username": "johndoe",
      "email": "johndoe@example.com",
      "is_active": true
    }
    ```

### Serializing One-to-One

When serializing one-to-one or many-to-one relationships, the related entity should be represented using two fields:

1. A writable field, matching the name of the database or ORM field, that stores the related record's primary key. 
2. A read-only field, prefixed with an underscore (_), providing a nested representation of the related entity.

Nested representations do not need to be complete, and should only include data explicitly required by the frontend application.

!!! example "Example: Serializing a One-to-One"

    Consider a `User` model associated with a `Post` model.
    
    ```mermaid
    classDiagram
        direction LR
        User "1" -- "1" Post
        class User {
            +id: int
            +username: string
            +profile: int
        }
        class Post {
            +id: int
            +bio: string
            +avatar_url: string
        }
    ```
    
    A serialized `User` record should include both the primary key reference and a nested representation:
    
    ```json
    {
      "id": 1,
      "username": "johndoe",
      "profile": 10,
      "_profile": {
        "bio": "Software engineer and open-source contributor.",
        "avatar_url": "https://example.com/avatar.jpg"
      }
    }
    ```

### Serializing One-to-Many

One-to-many and many-to-many relationships are serialized similarly to other relationships, except the relational
data is represented as an array of objects. Serialized relationships should include:

1. A writable field, matching the name of the database or ORM field, that stores an array of related primary keys. 
2. A read-only field, prefixed with an underscore (_), providing an array of nested representations for the related entity.

!!! example "Example: Serializing a One-to-Many"

    The following schema demonstrates a one-to-many relationship between the `User` and `Message` models.

    ```mermaid
    classDiagram
        direction LR
        User "1" *-- "0..*" Message
        class User {
          +id: int
          +name: string
        }
        class Message {
          +id: int
          +author: int
          +body: string
        }
    ```

    When serializing a `User` record, the `messages` field is required and contains a list of primary key values.
    The `_messages` field provides a nested representation with select attributes.

    ```json
    {
      "id": 1,
      "name": "John Smith",
      "messages": [1, 2],
      "_messages": [
        {
          "id": 1,
          "body": "Keep it secret."
        }, {
          "id": 2,
          "body": "Keep it safe."
        }
      ]
    }
    ```

### Serializing Many-to-Many

Serializing many-to-many relationships follows the same general guidelines as a one-to-many relationship.
However, special consideration is given to relationships which include additional data as attributes in the through table.
In this case attributes stored in the through table must be included within the nested representation as writable fields.

!!! example "Example: Serializing a Through Table"

    Consider a `Student` and `Course` model related by an `Enrollment` table.
    
    ```mermaid
    classDiagram
        direction LR
        Student "1" *-- "0..*" Enrollment
        Course "1" *-- "0..*" Enrollment
        class Student {
          +id: int
          +name: string
        }
        class Course {
          +id: int
          +title: string
        }
        class Enrollment {
          +id: int
          +student: int
          +course: int
          +enrolled_on: date
          +grade: string
        }
    ```
    
    When serializing a `Student` record, the `courses` field contains a list of course IDs, while `_courses` provides additional enrollment details.  
    
    ```json
    {
      "id": 1,
      "name": "Alice",
      "courses": [
        {
          "id": 1 
          "enrolled_on": "2025-01-15",
          "grade": "A",
          "course": 101,
          "_course": {
            "id": 101,
            "title": "Intro to Proofs"
          }
        },
        {
          "is": 2,
          "enrolled_on": "2025-02-10",
          "grade": "B+",
          "course": 102,
          "_course": {
            "id": 102,
            "title": "Advanced Proofs"
          }
        }
      ]
    }
    ```
