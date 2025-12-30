import pytest
from datetime import datetime, date, timedelta
from utils import validate_hateoas_links
from flask import url_for
from app.extensions import db
from app.models import Task

FORMAT_CODE = "%Y-%m-%d %H:%M"

# region test post

@pytest.mark.parametrize("payload", [
    {
        "name": "Skillbox hw", 
        "description": "Study flask-restful and complete the hw", 
        "priority": 2, 
        "deadline": "2025-12-31 23:59"
    }
])
def test_create_task_success(client, payload, existing_users):
    test_user, _ = existing_users
    response = client.post(f"/users/{test_user.id}/tasks", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert "id" in data
    assert datetime.strptime(data["date"], FORMAT_CODE).date() == date.today()

def test_create_task_strict_schema(client, existing_users):
    """Verifies unknown=RAISE for tasks."""
    test_user, _ = existing_users
    payload = {
        "name": "Valid Task",
        "invalid_field": "not_allowed"
    }
    response = client.post(f"/users/{test_user.id}/tasks", json=payload)
    assert response.status_code == 422
    data = response.get_json()
    assert "invalid_field" in data["error"]["details"]

def test_create_task_default_priority(existing_tasks):
    _, test_task = existing_tasks
    assert test_task.priority == 1

def test_create_task_owner_not_found(client):
    response = client.post("/users/999/tasks", json={"name": "Ghost Task"})
    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "user_not_found"

# endregion

# region test get

def test_get_tasks_success(client, app, existing_tasks):
    task1, _ = existing_tasks
    u_id = task1.user_id
    response = client.get(f"/users/{u_id}/tasks")
    assert response.status_code == 200
    data = response.get_json()

    assert len(data["tasks"]) == 2
    
    # Collection links
    collection_rels = {
        "self": ("GET", "tasksresource", {"user_id": u_id}),
        "bulk_delete": ("DELETE", "tasksresource", {"user_id": u_id})
    }
    with app.app_context():
        validate_hateoas_links(data["links"], collection_rels)

    # Item links
    returned_task = data["tasks"][0]
    t_id = returned_task["id"]
    task_item_rels = {
        "self": ("GET", "taskresource", {"user_id": u_id, "task_id": t_id}),
        "update": ("PATCH", "taskresource", {"user_id": u_id, "task_id": t_id}),
        "delete": ("DELETE", "taskresource", {"user_id": u_id, "task_id": t_id}),
        "owner": ("GET", "userresource", {"user_id": u_id})
    }
    with app.app_context():
        validate_hateoas_links(returned_task["links"], task_item_rels)

def test_get_task_wrong_owner(client, existing_users, existing_tasks):
    # user1 owns task1. We try to access task1 using user2's ID.
    user1, user2 = existing_users
    task1, _ = existing_tasks 
    
    response = client.get(f"/users/{user2.id}/tasks/{task1.id}")
    
    assert response.status_code == 403
    data = response.get_json()
    assert data["error"]["code"] == "access_denied"

# endregion

# region test PATCH

def test_patch_task_validation_error(client, existing_tasks):
    task, _ = existing_tasks
    response = client.patch(f"/users/{task.user_id}/tasks/{task.id}", json={"priority": 5})
    assert response.status_code == 422
    data = response.get_json()
    assert "priority" in data["error"]["details"]

# endregion

# region test delete

def test_delete_bulk_tasks_mismatch(client, existing_tasks):
    """Verify TaskListResource.delete checks that tasks actually belong to the user."""
    task1, task2 = existing_tasks
    # Attempt to delete task1 but targeting user 999
    response = client.delete("/users/999/tasks", json={"tasks": [task1.id]})
    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "user_not_found"

def test_delete_task_success(client, existing_tasks):
    task, _ = existing_tasks
    response = client.delete(f"/users/{task.user_id}/tasks/{task.id}")
    assert response.status_code == 204
    assert db.session.get(Task, task.id) is None

# endregion