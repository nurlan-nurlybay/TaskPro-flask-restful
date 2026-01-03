from flask import request, url_for, current_app
from flask_restful import Resource
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from app.models import User, Task
from app.schemas import UserSchema, TaskSchema
from app.extensions import db
from marshmallow import ValidationError

def error_response(code, message, details=None, status_code=400):
    """Standardized error format for the entire API."""
    response = {
        "error": {
            "code": code,
            "message": message,
            "details": details or "No additional details provided.",
            "request_id": request.environ.get('FLASK_REQUEST_ID', 'N/A')
        }
    }
    return response, status_code

user_schema = UserSchema()
task_schema = TaskSchema()

# region User Resources

class UserResource(Resource):
    def get(self, user_id):
        current_app.logger.info(f"Fetching user: {user_id}")
        user = db.session.get(User, user_id)
        if not user:
            return error_response("user_not_found", f"User with ID {user_id} does not exist.", status_code=404)
        return user_schema.dump(user), 200
    
    def patch(self, user_id):
        current_app.logger.info(f"Patching user: {user_id}")
        user = db.session.get(User, user_id)
        if not user:
            return error_response("user_not_found", "Cannot update non-existent user.", status_code=404)

        json_data = request.get_json()
        if not json_data:
            return error_response("empty_payload", "No data provided for update.", status_code=400)

        try:
            updated_user = user_schema.load(json_data, instance=user, partial=True, session=db.session)
            db.session.commit()
            return user_schema.dump(updated_user), 200
        except ValidationError as err:
            db.session.rollback()
            return error_response("validation_error", "Invalid data provided.", details=err.messages, status_code=422)
        except IntegrityError:
            db.session.rollback()
            return error_response("unique_constraint_violation", "Username is already taken.", status_code=409)
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"User patch error: {str(e)}")
            return error_response("internal_error", "An unexpected error occurred.", status_code=500)

    def delete(self, user_id):
        current_app.logger.info(f"Deleting user: {user_id}")
        user = db.session.get(User, user_id)
        if not user:
            return error_response("user_not_found", "Cannot delete non-existent user.", status_code=404)

        try:
            db.session.delete(user)
            db.session.commit()
            return '', 204
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"User delete error: {str(e)}")
            return error_response("internal_error", "Database error during deletion.", status_code=500)

class UserListResource(Resource):
    def get(self):
        current_app.logger.info("Fetching user list.")
        users = db.session.execute(db.select(User)).scalars().all()
        return {
            "users": user_schema.dump(users, many=True),
            "links": [
                {"rel": "self", "href": url_for("userlistresource"), "method": "GET"},
                {"rel": "bulk_delete", "href": url_for("userlistresource"), "method": "DELETE"}
            ]
        }, 200

    def post(self):
        json_data = request.get_json()
        if not json_data:
            return error_response("empty_payload", "No input data provided.", status_code=400)

        try:
            new_user = user_schema.load(json_data, session=db.session)
            db.session.add(new_user)
            db.session.commit()
            return user_schema.dump(new_user), 201
        except ValidationError as err:
            db.session.rollback()
            return error_response("validation_error", "Creation failed.", details=err.messages, status_code=422)
        except IntegrityError:
            db.session.rollback()
            return error_response("unique_constraint_violation", "Username already exists.", status_code=409)
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"User creation error: {str(e)}")
            return error_response("internal_error", "Server error during registration.", status_code=500)

    def delete(self):
        json_data = request.get_json() or {}
        user_ids = json_data.get("users")

        if not user_ids or not isinstance(user_ids, list):
            return error_response("invalid_input", "A list of 'users' IDs is required.", status_code=400)

        if len(user_ids) > 100:
            return error_response("request_too_large", "Batch limit exceeded (Max: 100).", status_code=413)

        try:
            # Atomic validation check
            existing_count = db.session.query(User.id).filter(User.id.in_(user_ids)).count()
            if existing_count != len(user_ids):
                return error_response("resource_mismatch", "One or more user IDs do not exist.", status_code=404)

            db.session.execute(delete(User).where(User.id.in_(user_ids)))
            db.session.commit()
            return {"message": f"Successfully deleted {len(user_ids)} users."}, 200
        except Exception as e:
            db.session.rollback()
            return error_response("internal_error", str(e), status_code=500)

# endregion

# region Task Resources

class TaskResource(Resource):
    def get(self, user_id, task_id):
        current_app.logger.info(f"Fetching task '{task_id}' owned by '{user_id}'")
        # 1. Check if the user exists
        if not db.session.get(User, user_id):
            return error_response("user_not_found", "User not found.", status_code=404)
            
        # 2. Check if the task exists globally
        task = db.session.get(Task, task_id)
        if not task:
            return error_response("task_not_found", "Task not found.", status_code=404)

        # 3. Check ownership (This triggers the 403)
        if task.user_id != user_id:
            current_app.logger.warning(f"Unauthorized access: User {user_id} tried Task {task_id}")
            return error_response("access_denied", "This task does not belong to you.", status_code=403)
                
        return task_schema.dump(task), 200

    def patch(self, user_id, task_id):
        task = db.session.get(Task, task_id)
        if not task or task.user_id != user_id:
            return error_response("task_not_found", "Task not found for this user.", status_code=404)

        json_data = request.get_json()
        try:
            updated_task = task_schema.load(json_data, instance=task, partial=True, session=db.session)
            db.session.commit()
            return task_schema.dump(updated_task), 200
        except ValidationError as err:
            db.session.rollback()
            return error_response("validation_error", "Update failed.", details=err.messages, status_code=422)
        except Exception as e:
            db.session.rollback()
            return error_response("internal_error", str(e), status_code=500)

    def delete(self, user_id, task_id):
        task = db.session.get(Task, task_id)
        if not task or task.user_id != user_id:
            return error_response("task_not_found", "Task not found.", status_code=404)

        try:
            db.session.delete(task)
            db.session.commit()
            return '', 204
        except Exception as e:
            db.session.rollback()
            return error_response("internal_error", str(e), status_code=500)

class TaskListResource(Resource):
    def get(self, user_id):
        if not db.session.get(User, user_id):
            return error_response("user_not_found", "Owner not found.", status_code=404)
        
        tasks = db.session.execute(db.select(Task).where(Task.user_id == user_id)).scalars().all()
        return {
            "tasks": task_schema.dump(tasks, many=True),
            "links": [
                {"rel": "self", "href": url_for("tasksresource", user_id=user_id), "method": "GET"},
                {"rel": "bulk_delete", "href": url_for("tasksresource", user_id=user_id), "method": "DELETE"}
            ]
        }, 200

    def post(self, user_id):
        if not db.session.get(User, user_id):
            return error_response("user_not_found", "Cannot assign task to non-existent user.", status_code=404)
        
        json_data = request.get_json()
        try:
            new_task = task_schema.load(json_data, session=db.session)
            new_task.user_id = user_id
            db.session.add(new_task)
            db.session.commit()
            return task_schema.dump(new_task), 201
        except ValidationError as err:
            return error_response("validation_error", "Task creation failed.", details=err.messages, status_code=422)
        except Exception as e:
            db.session.rollback()
            return error_response("internal_error", str(e), status_code=500)

    def delete(self, user_id):
        # 1. Existence check for the owner
        if not db.session.get(User, user_id):
            return error_response("user_not_found", "User not found.", status_code=404)
        
        json_data = request.get_json() or {}
        task_ids = json_data.get("tasks")

        # 2. Basic validation: Must be a list and not empty
        if not task_ids or not isinstance(task_ids, list):
            return error_response("invalid_input", "A list of 'tasks' IDs is required.", status_code=400)

        # 3. Size protection (Stall attack prevention)
        if len(task_ids) > 100:
            current_app.logger.warning(f"Excessive IDs in task delete request from User {user_id}")
            return error_response("request_too_large", "Cannot delete more than 100 tasks at once.", status_code=413)

        # 4. Type validation (Integer safety)
        if not all(isinstance(tid, int) for tid in task_ids):
            return error_response("invalid_input", "Task IDs must be integers.", status_code=400)

        try:
            # 5. Ownership validation: All IDs must exist AND belong to the URL user_id
            existing_count = db.session.query(Task.id).filter(
                Task.id.in_(task_ids), 
                Task.user_id == user_id
            ).count()

            if existing_count != len(task_ids):
                current_app.logger.warning(f"User {user_id} attempted to delete tasks they don't own or that don't exist.")
                return error_response("resource_mismatch", "One or more tasks not found for this user.", status_code=404)

            # 6. Secure Execution: Double-filter by user_id for safety
            stmt = delete(Task).where(
                Task.id.in_(task_ids), 
                Task.user_id == user_id
            )
            
            db.session.execute(stmt)
            db.session.commit()
            
            current_app.logger.info(f"User {user_id} successfully deleted {len(task_ids)} tasks.")
            return {"message": f"Successfully deleted {len(task_ids)} tasks."}, 200

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Task bulk delete error for User {user_id}: {str(e)}")
            return error_response("internal_error", "A database error occurred.", status_code=500)

# endregion
