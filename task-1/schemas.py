from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
import enum

class NoteBase(BaseModel):
    email: str
    subject: Optional[str] = None
    file_data: Optional[bytes] = None

class NoteCreate(NoteBase):
    pass

class Note(NoteBase):
    id: int

    class config:
        orm_node=True


class UserBase(BaseModel):
    email:str
    name:str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id:int
    is_active:bool

    class config:
        orm_model=True


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str 

# Email schemas
class Attachment(BaseModel):
    id: str
    filename: str
    mimeType: str

class Email(BaseModel):
    message_id: str
    subject: str
    sender: str
    timestamp: datetime
    attachments: List[Attachment]

class EmailWithAttachment(Email):
    attachment_data: str  # Base64 encoded attachment data
    
