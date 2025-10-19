from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.models.schemas import Envelope, Card


class EnvelopeService:
    """Service for managing Envelope operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_envelope(
        self,
        name: str,
        description: Optional[str] = None,
        envelope_type: Optional[str] = None,
        keywords: List[str] = None
    ) -> Envelope:
        """Create a new envelope"""
        envelope = Envelope(
            name=name,
            description=description,
            envelope_type=envelope_type,
            keywords=keywords or []
        )
        
        self.db.add(envelope)
        self.db.commit()
        self.db.refresh(envelope)
        return envelope
    
    def get_envelope(self, envelope_id: int) -> Optional[Envelope]:
        """Get an envelope by ID"""
        return self.db.query(Envelope).filter(Envelope.id == envelope_id).first()
    
    def get_envelope_by_name(self, name: str) -> Optional[Envelope]:
        """Get an envelope by name"""
        return self.db.query(Envelope).filter(Envelope.name == name).first()
    
    def get_all_envelopes(self) -> List[Envelope]:
        """Get all envelopes"""
        return self.db.query(Envelope).order_by(Envelope.updated_at.desc()).all()
    
    def update_envelope(self, envelope_id: int, **kwargs) -> Optional[Envelope]:
        """Update an envelope"""
        envelope = self.get_envelope(envelope_id)
        if not envelope:
            return None
        
        for key, value in kwargs.items():
            if hasattr(envelope, key):
                setattr(envelope, key, value)
        
        envelope.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(envelope)
        return envelope
    
    def delete_envelope(self, envelope_id: int) -> bool:
        """Delete an envelope"""
        envelope = self.get_envelope(envelope_id)
        if not envelope:
            return False
        
        self.db.delete(envelope)
        self.db.commit()
        return True
    
    def find_matching_envelope(self, keywords: List[str], context: str) -> Optional[Envelope]:
        """
        Find the most matching envelope based on keywords and context
        
        Args:
            keywords: List of keywords from the card
            context: Context string from the card
            
        Returns:
            Best matching envelope or None
        """
        envelopes = self.get_all_envelopes()
        
        if not envelopes:
            return None
        
        best_match = None
        best_score = 0
        
        for envelope in envelopes:
            score = self._calculate_match_score(envelope, keywords, context)
            if score > best_score:
                best_score = score
                best_match = envelope
        
        # Only return if score is above threshold
        if best_score > 0.3:
            return best_match
        
        return None
    
    def _calculate_match_score(
        self, 
        envelope: Envelope, 
        keywords: List[str], 
        context: str
    ) -> float:
        """Calculate match score between envelope and card"""
        score = 0.0
        total_possible = 0
        
        # Check keyword overlap
        envelope_keywords = set(kw.lower() for kw in envelope.keywords)
        card_keywords = set(kw.lower() for kw in keywords)
        
        if envelope_keywords and card_keywords:
            overlap = len(envelope_keywords.intersection(card_keywords))
            total_keywords = len(envelope_keywords.union(card_keywords))
            if total_keywords > 0:
                score += (overlap / total_keywords) * 0.6
                total_possible += 0.6
        
        # Check name match
        if envelope.name.lower() in context.lower():
            score += 0.3
        total_possible += 0.3
        
        # Check description match
        if envelope.description and envelope.description.lower() in context.lower():
            score += 0.1
        total_possible += 0.1
        
        # Normalize score
        if total_possible > 0:
            return score / total_possible
        return 0.0
    
    def get_or_create_envelope(
        self,
        name: str,
        envelope_type: Optional[str] = None,
        keywords: List[str] = None
    ) -> Envelope:
        """Get existing envelope or create new one"""
        envelope = self.get_envelope_by_name(name)
        
        if envelope:
            # Update keywords if new ones provided
            if keywords:
                existing_keywords = set(envelope.keywords)
                new_keywords = existing_keywords.union(set(keywords))
                envelope.keywords = list(new_keywords)
                self.db.commit()
                self.db.refresh(envelope)
            return envelope
        
        return self.create_envelope(
            name=name,
            envelope_type=envelope_type,
            keywords=keywords
        )
    
    def get_envelope_statistics(self, envelope_id: int) -> Dict[str, Any]:
        """Get statistics for an envelope"""
        envelope = self.get_envelope(envelope_id)
        if not envelope:
            return {}
        
        cards = envelope.cards
        
        return {
            "total_cards": len(cards),
            "tasks": len([c for c in cards if c.card_type == "task"]),
            "reminders": len([c for c in cards if c.card_type == "reminder"]),
            "ideas": len([c for c in cards if c.card_type == "idea"]),
            "notes": len([c for c in cards if c.card_type == "note"]),
            "active": len([c for c in cards if c.status == "active"]),
            "completed": len([c for c in cards if c.status == "completed"]),
            "high_priority": len([c for c in cards if c.priority in ["high", "urgent"]])
        }
    
    def merge_envelopes(self, source_id: int, target_id: int) -> bool:
        """Merge two envelopes"""
        source = self.get_envelope(source_id)
        target = self.get_envelope(target_id)
        
        if not source or not target:
            return False
        
        # Move all cards from source to target
        for card in source.cards:
            card.envelope_id = target_id
        
        # Merge keywords
        target_keywords = set(target.keywords)
        target_keywords.update(source.keywords)
        target.keywords = list(target_keywords)
        
        # Delete source envelope
        self.db.delete(source)
        self.db.commit()
        
        return True