from fastapi import HTTPException
from sqlalchemy.orm import Session
import models, schemas, auth
from datetime import datetime

def get_users(db: Session, user_id: int):
    """Get user by ID."""
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    """Get user by email."""
    return db.query(models.User).filter(models.User.email == email).first()

def get_user(db: Session, skip: int = 0, limit: int = 100):
    """Get list of users with pagination."""
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    """Create a new user."""
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        name=user.name,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str):
    """Authenticate user with email and password."""
    user = get_user_by_email(db, email)
    if not user or not auth.verify_password(password, user.hashed_password):
        return False
    
    # Update last_login timestamp
    user.last_login = datetime.now()
    db.commit()
    db.refresh(user)
    
    return user

