from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

from config import Config
from src.models.schemas import Card, Envelope, ThinkingOutput
from src.services import CardService, EnvelopeService


class ThinkingAgent:
    """
    Agent that analyzes cards and envelopes to generate proactive suggestions
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.card_service = CardService(db)
        self.envelope_service = EnvelopeService(db)
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=0.3,
            api_key=Config.OPENAI_API_KEY
        )
    
    def analyze_and_suggest(self) -> List[Dict[str, Any]]:
        """
        Main method to analyze all cards and generate suggestions
        
        Returns:
            List of suggestions/recommendations
        """
        print(f"\n{'='*60}")
        print(f"🤔 Thinking Agent Analysis Started")
        print(f"{'='*60}\n")
        
        suggestions = []
        
        # Get all active cards and envelopes
        cards = self.card_service.get_all_cards(status="active")
        envelopes = self.envelope_service.get_all_envelopes()
        
        print(f"📊 Analyzing {len(cards)} cards and {len(envelopes)} envelopes...")
        
        # Run different analysis strategies
        suggestions.extend(self._suggest_next_steps(cards, envelopes))
        suggestions.extend(self._detect_conflicts(cards))
        suggestions.extend(self._recommend_reorganization(cards, envelopes))
        suggestions.extend(self._identify_patterns(cards))
        
        # Save suggestions to database
        saved_suggestions = self._save_suggestions(suggestions)
        
        print(f"\n✅ Generated {len(saved_suggestions)} suggestions")
        print(f"{'='*60}\n")
        
        return saved_suggestions
    
    def _suggest_next_steps(
        self, 
        cards: List[Card], 
        envelopes: List[Envelope]
    ) -> List[Dict[str, Any]]:
        """Suggest next steps based on completed tasks"""
        suggestions = []
        
        # Group cards by envelope
        envelope_cards = defaultdict(list)
        for card in cards:
            if card.envelope_id:
                envelope_cards[card.envelope_id].append(card)
        
        # Also check cards without envelopes
        unassigned_cards = [c for c in cards if not c.envelope_id]
        if len(unassigned_cards) > 0:
            envelope_cards[None] = unassigned_cards
        
        # Analyze each envelope
        for envelope_id, envelope_card_list in envelope_cards.items():
            if envelope_id:
                envelope = self.envelope_service.get_envelope(envelope_id)
                envelope_name = envelope.name if envelope else f"Envelope {envelope_id}"
            else:
                envelope_name = "Unorganized"
            
            # Check for completed tasks
            completed = [c for c in envelope_card_list if c.status == "completed"]
            active = [c for c in envelope_card_list if c.status == "active"]
            
            # Suggest next task if there are active tasks (even without completed ones)
            if active:
                next_task = self._find_next_logical_task(active, completed)
                if next_task:
                    if completed:
                        suggestions.append({
                            'output_type': 'next_step',
                            'title': f"Next Step in {envelope_name}",
                            'description': f"You've completed {len(completed)} task(s) in {envelope_name}. Consider working on: {next_task.description}",
                            'related_card_ids': [next_task.id] + [c.id for c in completed[-2:]],
                            'priority': 'medium'
                        })
                    else:
                        # Suggest starting with highest priority task
                        suggestions.append({
                            'output_type': 'next_step',
                            'title': f"Start Working on {envelope_name}",
                            'description': f"You have {len(active)} active task(s) in {envelope_name}. Start with: {next_task.description}",
                            'related_card_ids': [next_task.id],
                            'priority': 'low'
                        })
        
        return suggestions
    
    def _detect_conflicts(self, cards: List[Card]) -> List[Dict[str, Any]]:
        """Detect conflicts like overlapping deadlines"""
        suggestions = []
        
        # Group tasks by assignee and date
        assignee_tasks = defaultdict(list)
        for card in cards:
            if card.card_type == "task" and card.assignee and card.date:
                assignee_tasks[card.assignee].append(card)
        
        # Check for same-day conflicts
        for assignee, tasks in assignee_tasks.items():
            # Sort by date
            tasks.sort(key=lambda x: x.date)
            
            # Check for tasks on the same day
            date_groups = defaultdict(list)
            for task in tasks:
                date_key = task.date.date()
                date_groups[date_key].append(task)
            
            for date_key, day_tasks in date_groups.items():
                if len(day_tasks) > 2:
                    suggestions.append({
                        'output_type': 'conflict',
                        'title': f"Multiple Tasks for {assignee} on {date_key}",
                        'description': f"{assignee} has {len(day_tasks)} tasks scheduled for {date_key}. Consider reprioritizing or rescheduling some tasks.",
                        'related_card_ids': [t.id for t in day_tasks],
                        'priority': 'high'
                    })
        
        # Check for overdue tasks
        now = datetime.utcnow()
        overdue = [c for c in cards if c.card_type == "task" and c.date and c.date < now and c.status == "active"]
        
        if len(overdue) > 0:
            suggestions.append({
                'output_type': 'conflict',
                'title': f"{len(overdue)} Overdue Task{'s' if len(overdue) > 1 else ''}",
                'description': f"You have {len(overdue)} overdue task{'s' if len(overdue) > 1 else ''}. Consider reviewing and updating their status or deadlines.",
                'related_card_ids': [t.id for t in overdue[:5]],
                'priority': 'urgent' if len(overdue) > 5 else 'high'
            })
        
        # Check for upcoming deadlines (within 48 hours)
        upcoming_deadline = now + timedelta(hours=48)
        upcoming = [
            c for c in cards 
            if c.card_type == "task" 
            and c.date 
            and now < c.date < upcoming_deadline
            and c.status == "active"
        ]
        
        if len(upcoming) > 0:
            suggestions.append({
                'output_type': 'conflict',
                'title': f"{len(upcoming)} Task{'s' if len(upcoming) > 1 else ''} Due Soon",
                'description': f"You have {len(upcoming)} task{'s' if len(upcoming) > 1 else ''} due within the next 48 hours. Make sure you're prepared!",
                'related_card_ids': [t.id for t in upcoming],
                'priority': 'high'
            })
        
        return suggestions
    
    def _recommend_reorganization(
        self, 
        cards: List[Card], 
        envelopes: List[Envelope]
    ) -> List[Dict[str, Any]]:
        """Recommend creating new envelopes or reorganizing cards"""
        suggestions = []
        
        # Find unorganized cards (no envelope)
        unorganized = [c for c in cards if not c.envelope_id]
        
        if len(unorganized) > 3:
            # Analyze keywords to find common themes
            keyword_frequency = defaultdict(int)
            for card in unorganized:
                for keyword in card.context_keywords:
                    keyword_frequency[keyword] += 1
            
            # Find common keywords (appear in at least 2 cards)
            common_keywords = [
                kw for kw, freq in keyword_frequency.items() 
                if freq >= 2
            ]
            
            if common_keywords:
                suggestions.append({
                    'output_type': 'recommendation',
                    'title': "Organize Unassigned Cards",
                    'description': f"You have {len(unorganized)} unorganized cards with common themes: {', '.join(common_keywords[:3])}. Consider creating envelopes to better organize them.",
                    'related_card_ids': [c.id for c in unorganized[:5]],
                    'priority': 'medium'
                })
            else:
                suggestions.append({
                    'output_type': 'recommendation',
                    'title': "Organize Your Cards",
                    'description': f"You have {len(unorganized)} cards without envelopes. Consider grouping related cards into projects or themes.",
                    'related_card_ids': [c.id for c in unorganized[:5]],
                    'priority': 'low'
                })
        
        # Find similar ideas that could be combined
        ideas = [c for c in cards if c.card_type == "idea"]
        if len(ideas) >= 3:
            # Group by keywords
            keyword_groups = defaultdict(list)
            for idea in ideas:
                for keyword in idea.context_keywords:
                    keyword_groups[keyword].append(idea)
            
            for keyword, idea_list in keyword_groups.items():
                if len(idea_list) >= 3:
                    suggestions.append({
                        'output_type': 'recommendation',
                        'title': f"Consolidate Ideas About '{keyword}'",
                        'description': f"You have {len(idea_list)} ideas related to '{keyword}'. Consider consolidating them into a project or action plan.",
                        'related_card_ids': [i.id for i in idea_list],
                        'priority': 'medium'
                    })
        
        # Check for envelopes with too many cards
        for envelope in envelopes:
            if len(envelope.cards) > 10:
                suggestions.append({
                    'output_type': 'recommendation',
                    'title': f"Large Envelope: {envelope.name}",
                    'description': f"The '{envelope.name}' envelope has {len(envelope.cards)} cards. Consider breaking it into smaller, more focused envelopes.",
                    'related_card_ids': [c.id for c in envelope.cards[:5]],
                    'priority': 'low'
                })
        
        # Suggest creating envelope if many tasks without one
        tasks_without_envelope = [c for c in cards if c.card_type == "task" and not c.envelope_id]
        if len(tasks_without_envelope) > 5:
            suggestions.append({
                'output_type': 'recommendation',
                'title': "Group Your Tasks",
                'description': f"You have {len(tasks_without_envelope)} tasks without a project envelope. Organizing them by project can help you stay focused.",
                'related_card_ids': [t.id for t in tasks_without_envelope[:5]],
                'priority': 'medium'
            })
        
        return suggestions
    
    def _identify_patterns(self, cards: List[Card]) -> List[Dict[str, Any]]:
        """Identify patterns in user behavior and work"""
        suggestions = []
        
        # Analyze task completion patterns
        completed_tasks = [
            c for c in cards 
            if c.card_type == "task" and c.status == "completed"
        ]
        
        if len(completed_tasks) >= 5:
            # Calculate average completion time
            completion_times = []
            for task in completed_tasks:
                if task.date and task.updated_at:
                    delta = task.updated_at - task.created_at
                    completion_times.append(delta.total_seconds() / 3600)  # hours
            
            if completion_times:
                avg_time = sum(completion_times) / len(completion_times)
                suggestions.append({
                    'output_type': 'recommendation',
                    'title': "Task Completion Insights",
                    'description': f"Great work! You've completed {len(completed_tasks)} tasks with an average completion time of {avg_time:.1f} hours. Keep up the momentum!",
                    'related_card_ids': [],
                    'priority': 'low'
                })
        
        # Check for high-priority task accumulation
        high_priority = [
            c for c in cards 
            if c.priority in ['high', 'urgent'] and c.status == 'active'
        ]
        
        if len(high_priority) > 3:
            suggestions.append({
                'output_type': 'recommendation',
                'title': "High Priority Task Overload",
                'description': f"You have {len(high_priority)} high/urgent priority tasks. Consider breaking them into smaller tasks or delegating some.",
                'related_card_ids': [t.id for t in high_priority[:5]],
                'priority': 'high'
            })
        
        # Check card type distribution
        type_counts = defaultdict(int)
        for card in cards:
            type_counts[card.card_type] += 1
        
        # Too many ideas?
        if type_counts.get('idea', 0) > 10:
            suggestions.append({
                'output_type': 'recommendation',
                'title': "Ideas to Action",
                'description': f"You have {type_counts['idea']} ideas stored. Consider converting some of them into actionable tasks to make progress!",
                'related_card_ids': [c.id for c in cards if c.card_type == 'idea'][:5],
                'priority': 'medium'
            })
        
        # Check for cards with no dates
        no_date_tasks = [c for c in cards if c.card_type == 'task' and not c.date and c.status == 'active']
        if len(no_date_tasks) > 5:
            suggestions.append({
                'output_type': 'recommendation',
                'title': "Add Deadlines to Tasks",
                'description': f"You have {len(no_date_tasks)} tasks without deadlines. Adding due dates can help with prioritization and time management.",
                'related_card_ids': [t.id for t in no_date_tasks[:5]],
                'priority': 'medium'
            })
        
        # Overall productivity insight
        total_cards = len(cards)
        if total_cards >= 10:
            active_ratio = len([c for c in cards if c.status == 'active']) / total_cards
            
            if active_ratio > 0.8:
                suggestions.append({
                    'output_type': 'recommendation',
                    'title': "High Activity Level",
                    'description': f"You're managing {total_cards} cards with {int(active_ratio * 100)}% active. Great job staying organized! Consider completing or archiving finished items.",
                    'related_card_ids': [],
                    'priority': 'low'
                })
        
        return suggestions
    
    def _find_next_logical_task(
        self, 
        active_tasks: List[Card], 
        completed_tasks: List[Card]
    ) -> Card:
        """Find the next logical task to work on"""
        if not active_tasks:
            return None
        
        # Prioritize by: 1) Priority, 2) Date, 3) Creation order
        sorted_tasks = sorted(
            active_tasks,
            key=lambda x: (
                {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}.get(x.priority, 2),
                x.date if x.date else datetime.max,
                x.created_at
            )
        )
        
        return sorted_tasks[0]
    
    def _save_suggestions(self, suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Save suggestions to database"""
        saved = []
        
        for suggestion in suggestions:
            thinking_output = ThinkingOutput(
                output_type=suggestion['output_type'],
                title=suggestion['title'],
                description=suggestion['description'],
                related_card_ids=suggestion.get('related_card_ids', []),
                priority=suggestion.get('priority', 'medium')
            )
            
            self.db.add(thinking_output)
            self.db.commit()
            self.db.refresh(thinking_output)
            
            saved.append(thinking_output.to_dict())
        
        return saved
    
    def get_pending_suggestions(self) -> List[ThinkingOutput]:
        """Get all pending suggestions"""
        return self.db.query(ThinkingOutput).filter(
            ThinkingOutput.status == "pending"
        ).order_by(ThinkingOutput.created_at.desc()).all()
    
    def acknowledge_suggestion(self, suggestion_id: int) -> bool:
        """Mark a suggestion as acknowledged"""
        suggestion = self.db.query(ThinkingOutput).filter(
            ThinkingOutput.id == suggestion_id
        ).first()
        
        if suggestion:
            suggestion.status = "acknowledged"
            self.db.commit()
            return True
        return False