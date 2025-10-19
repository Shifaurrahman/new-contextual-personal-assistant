from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.models.schemas import Card
from src.utils import date_parser, entity_extractor


class CardService:
    """Service for managing Card operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_card(
        self,
        description: str,
        card_type: str,
        raw_input: str,
        date: Optional[datetime] = None,
        assignee: Optional[str] = None,
        priority: str = "medium",
        context_keywords: List[str] = None,
        envelope_id: Optional[int] = None
    ) -> Card:
        """Create a new card"""
        card = Card(
            card_type=card_type,
            description=description,
            raw_input=raw_input,
            date=date,
            assignee=assignee,
            priority=priority,
            context_keywords=context_keywords or [],
            envelope_id=envelope_id
        )
        
        self.db.add(card)
        self.db.commit()
        self.db.refresh(card)
        return card
    
    def get_card(self, card_id: int) -> Optional[Card]:
        """Get a card by ID"""
        return self.db.query(Card).filter(Card.id == card_id).first()
    
    def get_all_cards(self, status: Optional[str] = None) -> List[Card]:
        """Get all cards, optionally filtered by status"""
        query = self.db.query(Card)
        if status:
            query = query.filter(Card.status == status)
        return query.order_by(Card.created_at.desc()).all()
    
    def update_card(self, card_id: int, **kwargs) -> Optional[Card]:
        """Update a card"""
        card = self.get_card(card_id)
        if not card:
            return None
        
        for key, value in kwargs.items():
            if hasattr(card, key):
                setattr(card, key, value)
        
        card.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(card)
        return card
    
    def delete_card(self, card_id: int) -> bool:
        """Delete a card"""
        card = self.get_card(card_id)
        if not card:
            return False
        
        self.db.delete(card)
        self.db.commit()
        return True
    
    def get_cards_by_envelope(self, envelope_id: int) -> List[Card]:
        """Get all cards in an envelope"""
        return self.db.query(Card).filter(Card.envelope_id == envelope_id).all()
    
    def get_cards_by_assignee(self, assignee: str) -> List[Card]:
        """Get all cards assigned to a person"""
        return self.db.query(Card).filter(Card.assignee == assignee).all()
    
    def get_cards_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Card]:
        """Get cards within a date range"""
        return self.db.query(Card).filter(
            Card.date >= start_date,
            Card.date <= end_date
        ).all()
    
    def search_cards(self, query: str) -> List[Card]:
        """Search cards by description or keywords"""
        return self.db.query(Card).filter(
            Card.description.contains(query) | 
            Card.raw_input.contains(query)
        ).all()
    
    def mark_completed(self, card_id: int) -> Optional[Card]:
        """Mark a card as completed"""
        return self.update_card(card_id, status="completed")
    
    def get_overdue_tasks(self) -> List[Card]:
        """Get all overdue tasks"""
        now = datetime.utcnow()
        return self.db.query(Card).filter(
            Card.card_type == "task",
            Card.date < now,
            Card.status == "active"
        ).all()
    
    def get_upcoming_tasks(self, days: int = 7) -> List[Card]:
        """Get upcoming tasks within specified days"""
        from datetime import timedelta
        now = datetime.utcnow()
        future = now + timedelta(days=days)
        
        return self.db.query(Card).filter(
            Card.card_type == "task",
            Card.date >= now,
            Card.date <= future,
            Card.status == "active"
        ).order_by(Card.date).all()