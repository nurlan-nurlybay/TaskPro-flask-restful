import os
from dotenv import load_dotenv

# Load variables from .env into the system environment
load_dotenv()

class Config:
    # Retrieve the URI from the environment using os
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    
    # Disable a feature that signals the app every time a change is made in the DB (saves resources)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-if-missing")
