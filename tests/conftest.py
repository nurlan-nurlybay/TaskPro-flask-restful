from datetime import datetime
import pytest
from app import create_app
from app.extensions import db
from config import Config

FORMAT_CODE = "%Y-%m-%d %H:%M"

class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' # Fast, in-memory DB for tests
    TESTING = True

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def existing_users(app):
    from app.models import User
    from app.extensions import db
    
    user1 = User(username="preexisting1", password="password123")
    user2 = User(username="preexisting2", password="password123")
    db.session.add(user1)
    db.session.add(user2)
    db.session.commit()
    return user1, user2

@pytest.fixture
def existing_tasks(app, existing_users):
    from app.models import Task
    from app.extensions import db
    
    user1, _ = existing_users 
    
    task1 = Task(
        name="Skillbox hw", 
        description="Study flask-restful and complete the hw",
        priority=2,
        deadline=datetime.strptime("2025-12-31 23:59", FORMAT_CODE),
        owner=user1
    )

    task2 = Task(owner=user1)
    
    db.session.add(task1)
    db.session.add(task2)
    db.session.commit()
    return task1, task2
