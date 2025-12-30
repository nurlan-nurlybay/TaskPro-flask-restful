from datetime import datetime, timedelta, timezone
from sqlalchemy import CheckConstraint, func
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    @property
    def password(self):
        # We raise an AttributeError because reading the password 
        # should be impossible (it's a write-only property).
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    tasks = db.relationship(
        'Task', 
        backref='owner', 
        lazy=True, 
        cascade="all, delete-orphan"
    )


def get_default_deadline():
    """Calculates tomorrow's date at 23:59."""
    tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
    return tomorrow.replace(hour=23, minute=59, second=0, microsecond=0)


class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)

    # Metadata
    date = db.Column(db.DateTime, server_default=func.now(), nullable=False)

    # Task Info
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    priority = db.Column(db.Integer, server_default="1")  # Priority: 1 (High) to 3 (Low)
    deadline = db.Column(db.DateTime, default=get_default_deadline)  # FORMAT_CODE = "%Y-%m-%d %H:%M"

    # Foreign Key
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id', ondelete="CASCADE"), 
        nullable=False
    )

    # Note: 'owner' is automatically created by the backref in User.

    __table_args__ = (
        CheckConstraint('priority >= 1 AND priority <= 3', name='priority_range'),
    )


"""
default=...: This is handled by SQLAlchemy in the python code—not a db feature.
server_default=...: This is written into the SQL schema—db feature.
"""