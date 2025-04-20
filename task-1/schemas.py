from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class NoteBase(BaseModel):
    """Base note schema."""
    email: str
    subject: Optional[str] = None
    file_data: Optional[bytes] = None

class NoteCreate(NoteBase):
    """Schema for creating a note."""
    pass

class Note(NoteBase):
    """Schema for note response."""
    id: int

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    """Base user schema."""
    email: str
    name: str

class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str

class User(UserBase):
    """Schema for user response."""
    id: int
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    """Schema for authentication token."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Schema for token data."""
    email: str 

# Email schemas
class Attachment(BaseModel):
    """Schema for email attachment."""
    id: str
    filename: str
    mimeType: str

class Email(BaseModel):
    """Schema for email."""
    message_id: str
    subject: str
    sender: str
    timestamp: datetime
    attachments: List[Attachment]

class EmailWithAttachment(Email):
    """Schema for email with attachment data."""
    attachment_data: str  # Base64 encoded attachment data
    
