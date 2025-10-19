from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ==================== INPUT SCHEMAS ====================

class NoteInput(BaseModel):
    """Input schema for processing a note"""
    text: str = Field(..., description="Raw unstructured note text", min_length=1)


class CardCreate(BaseModel):
    """Schema for manually creating a card"""
    description: str
    card_type: str = Field(..., pattern="^(task|reminder|idea|note)$")
    raw_input: str
    date: Optional[datetime] = None
    assignee: Optional[str] = None
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")
    context_keywords: List[str] = []
    envelope_id: Optional[int] = None


class CardUpdate(BaseModel):
    """Schema for updating a card"""
    description: Optional[str] = None
    card_type: Optional[str] = Field(None, pattern="^(task|reminder|idea|note)$")
    date: Optional[datetime] = None
    assignee: Optional[str] = None
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|urgent)$")
    context_keywords: Optional[List[str]] = None
    status: Optional[str] = Field(None, pattern="^(active|completed|archived)$")
    envelope_id: Optional[int] = None


# ==================== RESPONSE SCHEMAS ====================

class CardResponse(BaseModel):
    """Response schema for card data"""
    id: int
    card_type: str
    description: str
    date: Optional[str] = None
    assignee: Optional[str] = None
    priority: str
    context_keywords: List[str]
    status: str
    envelope_id: Optional[int] = None
    created_at: str
    updated_at: str
    raw_input: Optional[str] = None

    class Config:
        from_attributes = True


class EnvelopeResponse(BaseModel):
    """Response schema for envelope data"""
    id: int
    name: str
    description: Optional[str] = None
    envelope_type: Optional[str] = None
    keywords: List[str]
    card_count: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ContextResponse(BaseModel):
    """Response schema for user context"""
    id: int
    context_type: str
    name: str
    description: Optional[str] = None
    keywords: List[str]
    importance_score: int
    created_at: str
    updated_at: str
    last_referenced: str

    class Config:
        from_attributes = True


class ThinkingSuggestionResponse(BaseModel):
    """Response schema for thinking agent suggestions"""
    id: int
    output_type: str
    title: str
    description: str
    related_card_ids: List[int]
    priority: str
    status: str
    created_at: str

    class Config:
        from_attributes = True


class ProcessNoteResponse(BaseModel):
    """Response schema for processed note"""
    card: Dict[str, Any]
    envelope: Optional[Dict[str, Any]] = None
    extracted_info: Dict[str, Any]