from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Card(Base):
    """Card model representing a structured note"""
    __tablename__ = "cards"
    
    id = Column(Integer, primary_key=True, index=True)
    card_type = Column(String(50), nullable=False)  # task, reminder, idea, note
    description = Column(Text, nullable=False)
    date = Column(DateTime, nullable=True)
    assignee = Column(String(255), nullable=True)
    priority = Column(String(20), default="medium")  # low, medium, high, urgent
    context_keywords = Column(JSON, default=list)  # List of keywords
    status = Column(String(50), default="active")  # active, completed, archived
    
    # Relationships
    envelope_id = Column(Integer, ForeignKey("envelopes.id"), nullable=True)
    envelope = relationship("Envelope", back_populates="cards")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    raw_input = Column(Text, nullable=True)  # Original user input
    
    def to_dict(self):
        return {
            "id": self.id,
            "card_type": self.card_type,
            "description": self.description,
            "date": self.date.isoformat() if self.date else None,
            "assignee": self.assignee,
            "priority": self.priority,
            "context_keywords": self.context_keywords,
            "status": self.status,
            "envelope_id": self.envelope_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "raw_input": self.raw_input
        }


class Envelope(Base):
    """Envelope model representing a collection of related cards"""
    __tablename__ = "envelopes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    envelope_type = Column(String(50), nullable=True)  # project, company, person, theme
    keywords = Column(JSON, default=list)  # Associated keywords
    
    # Relationships
    cards = relationship("Card", back_populates="envelope", cascade="all, delete-orphan")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "envelope_type": self.envelope_type,
            "keywords": self.keywords,
            "card_count": len(self.cards),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class UserContext(Base):
    """User context model for storing user's current focus areas"""
    __tablename__ = "user_context"
    
    id = Column(Integer, primary_key=True, index=True)
    context_type = Column(String(50), nullable=False)  # project, company, person, theme
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    keywords = Column(JSON, default=list)
    importance_score = Column(Integer, default=5)  # 1-10 scale
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_referenced = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "context_type": self.context_type,
            "name": self.name,
            "description": self.description,
            "keywords": self.keywords,
            "importance_score": self.importance_score,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_referenced": self.last_referenced.isoformat()
        }


class ThinkingOutput(Base):
    """Thinking agent output model"""
    __tablename__ = "thinking_outputs"
    
    id = Column(Integer, primary_key=True, index=True)
    output_type = Column(String(50), nullable=False)  # next_step, recommendation, conflict
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    related_card_ids = Column(JSON, default=list)
    priority = Column(String(20), default="medium")
    status = Column(String(50), default="pending")  # pending, acknowledged, dismissed
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "output_type": self.output_type,
            "title": self.title,
            "description": self.description,
            "related_card_ids": self.related_card_ids,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at.isoformat()
        }