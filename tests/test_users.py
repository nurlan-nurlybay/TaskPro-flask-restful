import pytest
from app.extensions import db
from app.models import User
from utils import validate_hateoas_links

# region test post

def test_create_user_success(client):
    response = client.post('/users', json={
        "username": "testuser",
        "password": "securepassword123"
    })
    assert response.status_code == 201
    data = response.get_json()
    assert "id" in data
    assert data["username"] == "testuser"

@pytest.mark.parametrize("payload, expected_error_key", [
    ({"username": "ab", "password": "securepassword123"}, "username"),
    ({"username": "testuser", "password": "short"}, "password"),
    ({"password": "securepassword123"}, "username"),
    ({"username": "testuser"}, "password"),
])
def test_create_user_validation_errors(client, payload, expected_error_key):
    response = client.post('/users', json=payload)
    assert response.status_code == 422
    data = response.get_json()
    # Drilling into standardized error format
    assert expected_error_key in data["error"]["details"]

def test_create_user_strict_schema(client):
    """Verifies that unknown fields cause a validation error (unknown=RAISE)."""
    response = client.post('/users', json={
        "username": "validuser",
        "password": "validpassword",
        "extra_field": "not_allowed"
    })
    assert response.status_code == 422
    data = response.get_json()
    assert "extra_field" in data["error"]["details"]

def test_create_user_no_json(client):
    response = client.post('/users', json=dict())
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "empty_payload"

def test_create_same_username(client, existing_users):
    test_user, _ = existing_users
    response = client.post('/users', json={"username": test_user.username, "password": "whatever"})
    # Changed to 409 as per resource update
    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "unique_constraint_violation"

# endregion

# region test get

def test_get_users_success(client, app, existing_users):
    user1, _ = existing_users
    response = client.get('/users')
    assert response.status_code == 200
    data = response.get_json()

    # Collection level links - Adjusted to match 'bulk_delete' snake_case in resource
    coll_rels = {
        "self": ("GET", "userlistresource", {}),
        "bulk_delete": ("DELETE", "userlistresource", {})
    }
    with app.app_context():
        validate_hateoas_links(data["links"], coll_rels)

    returned_user = data["users"][0]
    u_id = returned_user["id"]
    user_rels = {
        "self": ("GET", "userresource", {"user_id": u_id}),
        "update": ("PATCH", "userresource", {"user_id": u_id}),
        "delete": ("DELETE", "userresource", {"user_id": u_id}),
        "tasks": ("GET", "tasksresource", {"user_id": u_id})
    }
    with app.app_context():
        validate_hateoas_links(returned_user["links"], user_rels)

def test_get_nonexistent_user(client):
    response = client.get('/users/999')
    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "user_not_found"

# endregion

# region test patch 

def test_patch_user_success(client, existing_users):
    test_user, _ = existing_users
    response = client.patch(f'/users/{test_user.id}', json={
        "username": "updated_username"
    })
    assert response.status_code == 200
    db.session.expire_all() # Ensure we fetch fresh from DB
    same_user = db.session.get(User, test_user.id)
    assert same_user.username == "updated_username"

@pytest.mark.parametrize("payload, expected_error_key", [
    ({"username": "ab"}, "username"),
    ({"password": "short"}, "password"),
])
def test_patch_user_validation_errors(client, payload, expected_error_key, existing_users):
    test_user, _ = existing_users
    response = client.patch(f'/users/{test_user.id}', json=payload)
    assert response.status_code == 422
    assert expected_error_key in response.get_json()["error"]["details"]

def test_patch_same_username(client, existing_users):
    user1, user2 = existing_users
    response = client.patch(f'/users/{user1.id}', json={"username": user2.username})
    assert response.status_code == 409

# endregion

# region test delete

def test_delete_bulk_mismatch(client, existing_users):
    """Tests the new validation check for non-existent IDs in bulk delete."""
    response = client.delete("/users", json={"users": [1, 999]})
    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "resource_mismatch"

def test_delete_bulk_success(client, existing_users):
    user1, user2 = existing_users
    payload = {"users": [user1.id, user2.id]}
    response = client.delete("/users", json=payload)
    assert response.status_code == 200
    
    users = db.session.execute(db.select(User)).scalars().all()
    assert len(users) == 0

# endregion
