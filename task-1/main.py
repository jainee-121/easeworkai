from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse
import crud, models, schemas, auth
from database import engine, get_db
from middleware import add_cors_middleware, add_security_middleware
import os
import uvicorn
import email_service
import io
import base64
from typing import List, Dict, Any

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Email Management System",
    description="API for managing emails and user authentication",
    version="1.0.0"
)

# Add middleware
add_cors_middleware(app)
add_security_middleware(app)

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Authenticate user and return access token."""
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))
    access_token = auth.create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/logout")
async def logout(current_user: schemas.User = Depends(auth.get_current_user)):
    """Logout user."""
    return {"message": "Logged out successfully"}

@app.post("/users", response_model=schemas.User)
async def register_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    """Register new user."""
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.get("/emails", response_model=List[Dict[str, Any]])
async def get_emails(
    max_results: int = 10,
    current_user: schemas.User = Depends(auth.get_current_user)
):
    """Get list of emails."""
    try:
        service = email_service.get_gmail_service()
        return email_service.fetch_emails(service, max_results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/emails/{message_id}")
async def get_email(
    message_id: str,
    current_user: schemas.User = Depends(auth.get_current_user)
):
    """Get specific email details."""
    try:
        service = email_service.get_gmail_service()
        return email_service.get_email_data(service, message_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/emails/{message_id}/attachments/{attachment_id}")
async def get_attachment(
    message_id: str,
    attachment_id: str,
    current_user: schemas.User = Depends(auth.get_current_user)
):
    """Download email attachment."""
    try:
        service = email_service.get_gmail_service()
        attachment_data = email_service.download_attachment(service, message_id, attachment_id)
        
        return StreamingResponse(
            io.BytesIO(attachment_data),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename=attachment_{attachment_id}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/emails/{message_id}/attachments/{attachment_id}/base64")
async def get_attachment_base64(
    message_id: str,
    attachment_id: str,
    current_user: schemas.User = Depends(auth.get_current_user)
):
    """Get email attachment in base64 format."""
    try:
        service = email_service.get_gmail_service()
        attachment_data = email_service.download_attachment(service, message_id, attachment_id)
        base64_data = base64.b64encode(attachment_data).decode('utf-8')
        
        return {"attachment_data": base64_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
