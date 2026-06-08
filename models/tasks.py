from database import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class Tasks(Base):
    __tablename__ = "tasks"

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, nullable=False, index=True)
    priority = Column(String,nullable=False, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    due_date = Column(DateTime, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("Users", back_populates="tasks")