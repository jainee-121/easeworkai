from fastapi import HTTPException
from sqlalchemy.orm import Session
import models, schemas, auth

# user
def get_users(db:Session,user_id:int):
    return db.query(models.User).filter(models.User.id==user_id).first()

def get_user_by_email(db:Session, email:str):
    user=db.query(models.User).filter(models.User.email== email).first()
    return user

def get_user(db:Session,skip:int=0,limit:int=100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db:Session,user:schemas.UserCreate):
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
    user = get_user_by_email(db, email)
    if not user or not auth.verify_password(password, user.hashed_password):
        return False
    return user

