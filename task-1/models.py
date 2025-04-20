from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table, DateTime, LargeBinary, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(250), nullable=False)  
    permissions = Column(String(1000), nullable=True)  # Store permissions as JSON string
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime, nullable=True)

    def has_permission(self, permission: str) -> bool:
        if not self.permissions:
            return False
        return permission in self.permissions.split(',')
