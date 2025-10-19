from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn

from config import Config
from src.models import init_db, get_db
from src.agents import IngestionAgent, ThinkingAgent
from src.services import CardService, EnvelopeService, ContextService

from api.schemas import (
    NoteInput,
    CardResponse,
    CardCreate,
    EnvelopeResponse,
    ContextResponse,
    ThinkingSuggestionResponse,
    ProcessNoteResponse,
    CardUpdate
)

# Initialize FastAPI app
app = FastAPI(
    title="Contextual Personal Assistant API",
    description="AI-powered note processing and organization system",
    version="1.0.0"
)

# CORS middleware - Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this in production to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        Config.validate()
        init_db()
        print("✅ API Server started successfully!")
    except Exception as e:
        print(f"❌ Startup error: {e}")
        raise


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Contextual Personal Assistant API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# ==================== NOTE PROCESSING ENDPOINTS ====================

@app.post("/notes/process", response_model=ProcessNoteResponse)
async def process_note(note: NoteInput, db: Session = Depends(get_db)):
    """
    Process a raw note and create a structured card
    
    - **note**: Raw unstructured text from user
    """
    try:
        agent = IngestionAgent(db)
        result = agent.process_note(note.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/notes/batch-process")
async def batch_process_notes(notes: List[NoteInput], db: Session = Depends(get_db)):
    """Process multiple notes at once"""
    try:
        agent = IngestionAgent(db)
        note_texts = [n.text for n in notes]
        results = agent.batch_process_notes(note_texts)
        return {"results": results, "total": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CARD ENDPOINTS ====================

@app.get("/cards", response_model=List[CardResponse])
async def get_cards(
    status: Optional[str] = None,
    card_type: Optional[str] = None,
    limit: Optional[int] = 100,
    db: Session = Depends(get_db)
):
    """
    Get all cards with optional filters
    
    - **status**: Filter by status (active, completed, archived)
    - **card_type**: Filter by type (task, reminder, idea, note)
    - **limit**: Maximum number of cards to return
    """
    try:
        card_service = CardService(db)
        cards = card_service.get_all_cards(status=status)
        
        # Filter by card_type if provided
        if card_type:
            cards = [c for c in cards if c.card_type == card_type]
        
        # Limit results
        cards = cards[:limit]
        
        return [c.to_dict() for c in cards]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cards/{card_id}", response_model=CardResponse)
async def get_card(card_id: int, db: Session = Depends(get_db)):
    """Get a specific card by ID"""
    try:
        card_service = CardService(db)
        card = card_service.get_card(card_id)
        
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        
        return card.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cards", response_model=CardResponse)
async def create_card(card: CardCreate, db: Session = Depends(get_db)):
    """Create a new card manually"""
    try:
        card_service = CardService(db)
        new_card = card_service.create_card(**card.dict())
        return new_card.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/cards/{card_id}", response_model=CardResponse)
async def update_card(
    card_id: int,
    card_update: CardUpdate,
    db: Session = Depends(get_db)
):
    """Update a card"""
    try:
        card_service = CardService(db)
        updated_card = card_service.update_card(
            card_id,
            **card_update.dict(exclude_unset=True)
        )
        
        if not updated_card:
            raise HTTPException(status_code=404, detail="Card not found")
        
        return updated_card.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/cards/{card_id}")
async def delete_card(card_id: int, db: Session = Depends(get_db)):
    """Delete a card"""
    try:
        card_service = CardService(db)
        success = card_service.delete_card(card_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Card not found")
        
        return {"message": "Card deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/cards/{card_id}/complete")
async def mark_card_complete(card_id: int, db: Session = Depends(get_db)):
    """Mark a card as completed"""
    try:
        card_service = CardService(db)
        card = card_service.mark_completed(card_id)
        
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        
        return card.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cards/search/{query}")
async def search_cards(query: str, db: Session = Depends(get_db)):
    """Search cards by keyword"""
    try:
        card_service = CardService(db)
        cards = card_service.search_cards(query)
        return [c.to_dict() for c in cards]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cards/upcoming/tasks")
async def get_upcoming_tasks(days: int = 7, db: Session = Depends(get_db)):
    """Get upcoming tasks within specified days"""
    try:
        card_service = CardService(db)
        tasks = card_service.get_upcoming_tasks(days)
        return [t.to_dict() for t in tasks]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cards/overdue/tasks")
async def get_overdue_tasks(db: Session = Depends(get_db)):
    """Get overdue tasks"""
    try:
        card_service = CardService(db)
        tasks = card_service.get_overdue_tasks()
        return [t.to_dict() for t in tasks]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENVELOPE ENDPOINTS ====================

@app.get("/envelopes", response_model=List[EnvelopeResponse])
async def get_envelopes(db: Session = Depends(get_db)):
    """Get all envelopes"""
    try:
        envelope_service = EnvelopeService(db)
        envelopes = envelope_service.get_all_envelopes()
        return [e.to_dict() for e in envelopes]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/envelopes/{envelope_id}", response_model=EnvelopeResponse)
async def get_envelope(envelope_id: int, db: Session = Depends(get_db)):
    """Get a specific envelope by ID"""
    try:
        envelope_service = EnvelopeService(db)
        envelope = envelope_service.get_envelope(envelope_id)
        
        if not envelope:
            raise HTTPException(status_code=404, detail="Envelope not found")
        
        return envelope.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/envelopes/{envelope_id}/cards")
async def get_envelope_cards(envelope_id: int, db: Session = Depends(get_db)):
    """Get all cards in an envelope"""
    try:
        card_service = CardService(db)
        cards = card_service.get_cards_by_envelope(envelope_id)
        return [c.to_dict() for c in cards]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/envelopes/{envelope_id}/statistics")
async def get_envelope_statistics(envelope_id: int, db: Session = Depends(get_db)):
    """Get statistics for an envelope"""
    try:
        envelope_service = EnvelopeService(db)
        stats = envelope_service.get_envelope_statistics(envelope_id)
        
        if not stats:
            raise HTTPException(status_code=404, detail="Envelope not found")
        
        return stats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CONTEXT ENDPOINTS ====================

@app.get("/context", response_model=List[ContextResponse])
async def get_contexts(
    context_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all user contexts"""
    try:
        context_service = ContextService(db)
        contexts = context_service.get_all_contexts(context_type=context_type)
        return [c.to_dict() for c in contexts]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/context/summary")
async def get_context_summary(db: Session = Depends(get_db)):
    """Get summary of user context"""
    try:
        context_service = ContextService(db)
        summary = context_service.get_context_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== THINKING AGENT ENDPOINTS ====================

@app.post("/thinking/analyze")
async def run_thinking_agent(db: Session = Depends(get_db)):
    """Run the thinking agent to generate suggestions"""
    try:
        thinking_agent = ThinkingAgent(db)
        suggestions = thinking_agent.analyze_and_suggest()
        return {
            "suggestions": suggestions,
            "total": len(suggestions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/thinking/suggestions", response_model=List[ThinkingSuggestionResponse])
async def get_suggestions(
    status: Optional[str] = "pending",
    db: Session = Depends(get_db)
):
    """Get thinking agent suggestions"""
    try:
        thinking_agent = ThinkingAgent(db)
        
        if status == "pending":
            suggestions = thinking_agent.get_pending_suggestions()
        else:
            from src.models.schemas import ThinkingOutput
            suggestions = db.query(ThinkingOutput).filter(
                ThinkingOutput.status == status
            ).all()
        
        return [s.to_dict() for s in suggestions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/thinking/suggestions/{suggestion_id}/acknowledge")
async def acknowledge_suggestion(suggestion_id: int, db: Session = Depends(get_db)):
    """Acknowledge a suggestion"""
    try:
        thinking_agent = ThinkingAgent(db)
        success = thinking_agent.acknowledge_suggestion(suggestion_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Suggestion not found")
        
        return {"message": "Suggestion acknowledged"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== STATISTICS ENDPOINTS ====================

@app.get("/statistics/dashboard")
async def get_dashboard_statistics(db: Session = Depends(get_db)):
    """Get overall dashboard statistics"""
    try:
        card_service = CardService(db)
        envelope_service = EnvelopeService(db)
        context_service = ContextService(db)
        
        all_cards = card_service.get_all_cards()
        envelopes = envelope_service.get_all_envelopes()
        context_summary = context_service.get_context_summary()
        
        return {
            "total_cards": len(all_cards),
            "active_cards": len([c for c in all_cards if c.status == "active"]),
            "completed_cards": len([c for c in all_cards if c.status == "completed"]),
            "cards_by_type": {
                "tasks": len([c for c in all_cards if c.card_type == "task"]),
                "reminders": len([c for c in all_cards if c.card_type == "reminder"]),
                "ideas": len([c for c in all_cards if c.card_type == "idea"]),
                "notes": len([c for c in all_cards if c.card_type == "note"]),
            },
            "total_envelopes": len(envelopes),
            "context_summary": context_summary,
            "overdue_tasks": len(card_service.get_overdue_tasks()),
            "upcoming_tasks": len(card_service.get_upcoming_tasks(7))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )