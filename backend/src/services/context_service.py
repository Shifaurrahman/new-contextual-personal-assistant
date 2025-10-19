from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from collections import Counter

from src.models.schemas import UserContext, Card, Envelope
from config import Config


class ContextService:
    """Service for managing User Context"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_context(
        self,
        context_type: str,
        name: str,
        description: Optional[str] = None,
        keywords: List[str] = None,
        importance_score: int = 5
    ) -> UserContext:
        """Create a new user context item"""
        context = UserContext(
            context_type=context_type,
            name=name,
            description=description,
            keywords=keywords or [],
            importance_score=importance_score
        )
        
        self.db.add(context)
        self.db.commit()
        self.db.refresh(context)
        return context
    
    def get_context(self, context_id: int) -> Optional[UserContext]:
        """Get a context by ID"""
        return self.db.query(UserContext).filter(UserContext.id == context_id).first()
    
    def get_all_contexts(self, context_type: Optional[str] = None) -> List[UserContext]:
        """Get all contexts, optionally filtered by type"""
        query = self.db.query(UserContext)
        if context_type:
            query = query.filter(UserContext.context_type == context_type)
        return query.order_by(UserContext.importance_score.desc()).all()
    
    def update_context(self, context_id: int, **kwargs) -> Optional[UserContext]:
        """Update a context"""
        context = self.get_context(context_id)
        if not context:
            return None
        
        for key, value in kwargs.items():
            if hasattr(context, key):
                setattr(context, key, value)
        
        context.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(context)
        return context
    
    def delete_context(self, context_id: int) -> bool:
        """Delete a context"""
        context = self.get_context(context_id)
        if not context:
            return False
        
        self.db.delete(context)
        self.db.commit()
        return True
    
    def update_last_referenced(self, context_id: int):
        """Update the last referenced timestamp"""
        context = self.get_context(context_id)
        if context:
            context.last_referenced = datetime.utcnow()
            self.db.commit()
    
    def refine_context_from_card(self, card: Card) -> List[UserContext]:
        """
        Refine user context based on new card
        
        This analyzes the card and updates/creates relevant context items
        """
        updated_contexts = []
        
        # Extract potential context items
        if card.assignee:
            context = self._get_or_create_person_context(card.assignee)
            if context:
                updated_contexts.append(context)
        
        # Extract from keywords
        for keyword in card.context_keywords:
            if len(keyword) > 3 and keyword.isalpha():
                context = self._get_or_create_theme_context(keyword)
                if context:
                    updated_contexts.append(context)
        
        # Increment importance scores for referenced contexts
        self._increment_importance_scores(card.context_keywords)
        
        # Cleanup old contexts
        self._cleanup_old_contexts()
        
        return updated_contexts
    
    def _get_or_create_person_context(self, name: str) -> Optional[UserContext]:
        """Get or create a person context"""
        context = self.db.query(UserContext).filter(
            UserContext.context_type == "person",
            UserContext.name == name
        ).first()
        
        if context:
            context.last_referenced = datetime.utcnow()
            context.importance_score = min(context.importance_score + 1, 10)
            self.db.commit()
            return context
        
        return self.create_context(
            context_type="person",
            name=name,
            importance_score=5
        )
    
    def _get_or_create_theme_context(self, theme: str) -> Optional[UserContext]:
        """Get or create a theme context"""
        # Check if theme already exists
        context = self.db.query(UserContext).filter(
            UserContext.context_type == "theme",
            UserContext.name.ilike(f"%{theme}%")
        ).first()
        
        if context:
            # Update keywords if theme is new
            if theme.lower() not in [k.lower() for k in context.keywords]:
                context.keywords.append(theme)
            context.last_referenced = datetime.utcnow()
            self.db.commit()
            return context
        
        # Only create if theme appears to be significant
        return None
    
    def _increment_importance_scores(self, keywords: List[str]):
        """Increment importance scores for contexts matching keywords"""
        for keyword in keywords:
            contexts = self.db.query(UserContext).filter(
                UserContext.keywords.contains([keyword])
            ).all()
            
            for context in contexts:
                context.importance_score = min(context.importance_score + 1, 10)
                context.last_referenced = datetime.utcnow()
        
        self.db.commit()
    
    def _cleanup_old_contexts(self):
        """Remove old, low-importance contexts"""
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        old_contexts = self.db.query(UserContext).filter(
            UserContext.last_referenced < cutoff_date,
            UserContext.importance_score < 3
        ).all()
        
        for context in old_contexts:
            self.db.delete(context)
        
        self.db.commit()
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of user context"""
        contexts = self.get_all_contexts()
        
        # Group by type
        by_type = {}
        for context in contexts:
            if context.context_type not in by_type:
                by_type[context.context_type] = []
            by_type[context.context_type].append(context)
        
        # Get top contexts
        top_contexts = sorted(
            contexts, 
            key=lambda x: x.importance_score, 
            reverse=True
        )[:10]
        
        return {
            "total_contexts": len(contexts),
            "by_type": {k: len(v) for k, v in by_type.items()},
            "top_contexts": [c.to_dict() for c in top_contexts],
            "active_projects": len([c for c in contexts if c.context_type == "project"]),
            "key_people": len([c for c in contexts if c.context_type == "person"])
        }
    
    def get_relevant_contexts(self, keywords: List[str]) -> List[UserContext]:
        """Get contexts relevant to given keywords"""
        if not keywords:
            return []
        
        relevant = []
        for context in self.get_all_contexts():
            # Check keyword overlap
            context_keywords = set(k.lower() for k in context.keywords)
            card_keywords = set(k.lower() for k in keywords)
            
            if context_keywords.intersection(card_keywords):
                relevant.append(context)
        
        # Sort by importance
        return sorted(relevant, key=lambda x: x.importance_score, reverse=True)
    
    def extract_projects_from_envelopes(self):
        """Extract project contexts from envelopes"""
        envelopes = self.db.query(Envelope).filter(
            Envelope.envelope_type == "project"
        ).all()
        
        for envelope in envelopes:
            context = self.db.query(UserContext).filter(
                UserContext.context_type == "project",
                UserContext.name == envelope.name
            ).first()
            
            if not context:
                self.create_context(
                    context_type="project",
                    name=envelope.name,
                    description=envelope.description,
                    keywords=envelope.keywords,
                    importance_score=7
                )