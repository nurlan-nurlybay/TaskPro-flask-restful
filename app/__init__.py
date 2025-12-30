from flask import Flask
from config import Config
from app.extensions import db, ma, migrate, api
import logging
from logging.handlers import RotatingFileHandler
import os
from flask_restful import Api
import sqlite3
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    # For testing
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def configure_logging(app):
    # 1. Define the format
    log_format = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )

    # 2. Setup a file handler (Linux path)
    # RotatingFileHandler keeps files from getting too large
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    file_handler = RotatingFileHandler(os.path.join(log_dir, 'taskpro.log'), maxBytes=10240, backupCount=10)
    file_handler.setFormatter(log_format)
    file_handler.setLevel(logging.INFO)
    
    # 3. Add to the app logger
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)

    # Use a stream handler for the terminal during development
    if app.debug:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(log_format)
        app.logger.addHandler(stream_handler)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Call the logging configuration right after creating the app
    configure_logging(app)

    app.logger.info('TaskPro startup')

    # Initialize Extensions
    db.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)
    api = Api(app)
    
    from app.resources import UserResource, UserListResource, TaskListResource, TaskResource
    api.add_resource(UserListResource, '/users')
    api.add_resource(UserResource, '/users/<int:user_id>')
    api.add_resource(TaskListResource, '/users/<int:user_id>/tasks', endpoint='tasksresource')
    api.add_resource(TaskResource, '/users/<int:user_id>/tasks/<int:task_id>')

    # Register API Resources (we will add these shortly)
    api.init_app(app)

    # Import models to register them with SQLAlchemy
    from app import models

    return app
