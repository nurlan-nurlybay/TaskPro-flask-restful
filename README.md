# TaskPro-flask-restful

A robust, production-ready Task Management API built with **Flask-RESTful**, **SQLAlchemy**, and **Marshmallow**. This repository is developed with a TDD-first approach and ships with clear patterns for HATEOAS, standardized error handling, and secure bulk operations.

## Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Running Tests](#-running-tests)
- [API Contract](#-api-contract)
  - [Error Format](#error-format)
  - [Resource Endpoints](#resource-endpoints)
  - [HATEOAS Link Mapping](#hateoas-link-mapping-)
- [Security Considerations](#️-security-considerations)

## 🚀 Features

- **HATEOAS Integration:** Responses include hypermedia links to guide clients through available actions.
- **Hierarchical Routing:** Tasks are nested under users (`/users/<id>/tasks`) to enforce ownership.
- **Standardized Error Responses:** Consistent JSON error payloads with `code`, `message`, `details`, and `request_id`.
- **Strict Validation & Security:** Schemas use `unknown=RAISE`, ownership checks are enforced, and bulk operations have protective limits.
- **SQLite Cascade Deletes:** Deleting a user cascades to tasks via SQLAlchemy events.

## 🛠 Tech Stack

- **Python:** 3.12
- **Framework:** Flask + Flask-RESTful
- **DB:** SQLite (foreign keys enforced)
- **ORM:** SQLAlchemy
- **Serialization & Validation:** Marshmallow (`SQLAlchemyAutoSchema`)
- **Testing:** Pytest
- **Logging:** RotatingFileHandler (logs/)

## 📂 Project Structure

```text
.
├── app/
│   ├── extensions.py   # DB + Marshmallow initialization
│   ├── models.py       # SQLAlchemy models (User, Task)
│   ├── resources.py    # Flask-RESTful resources & error handling
│   ├── schemas.py      # Marshmallow schemas
│   └── __init__.py     # App factory + logging configuration
├── tests/              # Pytest test suites & helpers
├── migrations/         # Alembic migration files
├── config.py           # Config management
└── run.py              # App entrypoint
```

## ✅ Quick Start

```bash
git clone <repository_url>
cd TaskPro-flask-restful
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# configure environment variables or edit config.py if needed
python run.py
```

> The app creates a `logs/` directory automatically for rotating logs.

## 🧪 Running Tests

The test suite uses an in-memory SQLite DB and provides fast, isolated tests.

```bash
# Run all tests
python3 -m pytest

# Verbose
python3 -m pytest -v
```

## 🔌 API Contract

### Error Format

When an error occurs the API responds with a structured error object and an appropriate 4xx/5xx status code.

```json
{
  "error": {
    "code": "validation_error",
    "message": "Invalid data provided.",
    "details": {
      "username": ["Length must be between 3 and 80."]
    },
    "request_id": "abc-123-xyz"
  }
}
```

### Resource Endpoints

| Method | Endpoint             | Description                            |
|--------|----------------------|----------------------------------------|
| POST   | `/users`             | Create a new user                      |
| GET    | `/users`             | List all users                         |
| DELETE | `/users`             | Bulk delete users (JSON body required) |
| PATCH  | `/users/<id>`        | Update user details                    |
| GET    | `/users/<id>/tasks`  | List tasks for a user                  |
| POST   | `/users/<id>/tasks`  | Create a task for a user               |
| DELETE | `/users/<id>/tasks`  | Bulk delete tasks for a user           |

### HATEOAS Link Mapping 🔗

This project includes HATEOAS links in resource representations to help clients discover available actions. The tests use a small mapping and helpers in `tests/utils.py` to validate link presence and correctness.

Common link relations (examples):

- `self`: URL for the current resource.
- `tasks`: URL to list the user's tasks (for user resources).
- `create`: URL for creating a resource.
- `delete`: URL to remove a resource (or bulk delete endpoint).
- `owner`: URL pointing to the owning user (for task resources).

Example user payload returned by GET /users/1:

```json
{
  "id": 1,
  "username": "alice",
  "links": {
    "self": "/users/1",
    "tasks": "/users/1/tasks",
    "delete": "/users"
  }
}
```

Example task payload returned by GET /users/1/tasks/5:

```json
{
  "id": 5,
  "title": "Write tests",
  "completed": false,
  "links": {
    "self": "/users/1/tasks/5",
    "owner": "/users/1",
    "delete": "/users/1/tasks"
  }
}
```

Tip: use the helpers in `tests/utils.py` to assert correct link `rel` keys and URL templates when writing new tests.

---

## 🛡️ Security Considerations

- **Bulk Delete Limits:** Batch operations are capped at 100 IDs to prevent abuse.
- **Defense in Depth:** Ownership is validated at schema level and enforced in SQL WHERE clauses.
- **Foreign Keys:** SQLite is configured with `PRAGMA foreign_keys = ON` to maintain integrity.

---

If you'd like, I can also add a short example test that demonstrates how to assert HATEOAS links using `tests/utils.py` (Y/N).
