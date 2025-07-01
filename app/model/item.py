from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Item(Base):
    __tablename__ = "items"  
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String(500))
    price = Column(Float, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_default = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationship: Each item belongs to one user
    owner = relationship("User", back_populates="items")