from app.extensions import ma
from app.models import User, Task
from marshmallow import fields, validate
from flask import url_for
from marshmallow import RAISE

FORMAT_CODE = "%Y-%m-%d %H:%M"

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        sqla_session = None
        exclude = ("password_hash",)
        unknown = RAISE

    username = fields.String(required=True, validate=validate.Length(min=3, max=80))
    password = fields.String(required=True, load_only=True, validate=validate.Length(min=8))
    links = fields.Method("get_links")

    def get_links(self, obj):
        return [
            {"rel": "self", "href": url_for("userresource", user_id=obj.id), "method": "GET"},
            {"rel": "update", "href": url_for("userresource", user_id=obj.id), "method": "PATCH"},
            {"rel": "delete", "href": url_for("userresource", user_id=obj.id), "method": "DELETE"},
            {"rel": "tasks", "href": url_for("tasksresource", user_id=obj.id), "method": "GET"}
        ]

class TaskSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Task
        load_instance = True
        sqla_session = None
        include_fk = True 
        unknown = RAISE

    user_id = fields.Integer(dump_only=True)

    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    description = fields.String(required=False)
    priority = fields.Integer(required=False, validate=validate.Range(min=1, max=3))
    date = fields.DateTime(dump_only=True, format=FORMAT_CODE)
    deadline = fields.DateTime(required=False, format=FORMAT_CODE)

    owner = fields.Nested("UserSchema", only=("id", "username"), dump_only=True)
    links = fields.Method("get_links")

    def get_links(self, obj):
        return [
            {"rel": "self", "href": url_for("taskresource", user_id=obj.user_id, task_id=obj.id), "method": "GET"},
            {"rel": "update", "href": url_for("taskresource", user_id=obj.user_id, task_id=obj.id), "method": "PATCH"},
            {"rel": "delete", "href": url_for("taskresource", user_id=obj.user_id, task_id=obj.id), "method": "DELETE"},
            {"rel": "owner", "href": url_for("userresource", user_id=obj.user_id), "method": "GET"}
        ]
