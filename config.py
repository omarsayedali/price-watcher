import os
from dotenv import load_dotenv

load_dotenv() # This is fine, but Railway variables will now take priority

class Config:
    # It must check os.environ first!
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') 
    
    # Fix for the "postgres://" vs "postgresql://" issue on Railway
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False