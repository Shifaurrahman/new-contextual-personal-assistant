from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, HumanMessage
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import json

from config import Config
from src.agents.tools import get_all_tools
from src.services import CardService, EnvelopeService, ContextService
from src.utils import date_parser, entity_extractor


class IngestionAgent:
    """
    Main agent for ingesting and organizing notes into structured cards
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.card_service = CardService(db)
        self.envelope_service = EnvelopeService(db)
        self.context_service = ContextService(db)
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=0.1,
            api_key=Config.OPENAI_API_KEY
        )
        
        # Get tools
        self.tools = get_all_tools()
        
        # Create agent
        self.agent_executor = self._create_agent()
    
    def _create_agent(self) -> AgentExecutor:
        """Create the LangChain agent with tools"""
        
        system_message = """You are an intelligent personal assistant that processes unstructured notes and converts them into structured cards.

Your task is to analyze the user's input and extract the following information:

1. **Card Type**: Classify as 'task', 'reminder', 'idea', or 'note'
2. **Description**: Clean, clear description of the action or idea
3. **Date**: Parse any date/time mentioned (use parse_date tool)
4. **Assignee**: Extract person or team assigned (use extract_assignee tool)
5. **Priority**: Determine priority level - low, medium, high, urgent (use classify_priority tool)
6. **Keywords**: Extract relevant keywords (use extract_keywords tool)
7. **Project Context**: Identify any project or context mentioned (use extract_project_context tool)

Use the available tools to extract this information accurately. Return your analysis in JSON format.

Available tools:
- parse_date: Parse natural language dates
- extract_entities: Extract named entities
- extract_assignee: Find assigned person/team
- classify_card_type: Determine card type
- classify_priority: Determine priority level
- extract_keywords: Extract keywords
- extract_project_context: Find project/context

Always use tools to ensure accurate extraction. Return final result as JSON with keys:
card_type, description, date, assignee, priority, keywords, project_context"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=Config.AGENT_VERBOSE,
            max_iterations=Config.MAX_ITERATIONS,
            handle_parsing_errors=True
        )
    
    def process_note(self, raw_note: str) -> Dict[str, Any]:
        """
        Process a raw note and create a structured card
        
        Args:
            raw_note: Unstructured text input from user
            
        Returns:
            Dict containing the created card and envelope information
        """
        print(f"\n{'='*60}")
        print(f"Processing note: {raw_note}")
        print(f"{'='*60}\n")
        
        # Step 1: Run agent to extract structured information
        agent_input = f"""Analyze this note and extract structured information: "{raw_note}"

Use the tools to extract:
1. Card type (task/reminder/idea/note)
2. Clean description
3. Date (if mentioned)
4. Assignee (if mentioned)
5. Priority level
6. Keywords
7. Project context

Return the information in JSON format."""

        try:
            agent_result = self.agent_executor.invoke({"input": agent_input})
            extracted_info = self._parse_agent_output(agent_result['output'], raw_note)
        except Exception as e:
            print(f"⚠️  Agent error: {e}")
            # Fallback to direct extraction
            extracted_info = self._fallback_extraction(raw_note)
        
        print(f"\n📊 Extracted Information:")
        for key, value in extracted_info.items():
            print(f"  • {key}: {value}")
        
        # Step 2: Find or create appropriate envelope
        envelope = self._find_or_create_envelope(extracted_info)
        
        # Step 3: Create card
        card = self.card_service.create_card(
            description=extracted_info['description'],
            card_type=extracted_info['card_type'],
            raw_input=raw_note,
            date=extracted_info.get('date'),
            assignee=extracted_info.get('assignee'),
            priority=extracted_info['priority'],
            context_keywords=extracted_info['keywords'],
            envelope_id=envelope.id if envelope else None
        )
        
        # Step 4: Update user context
        self.context_service.refine_context_from_card(card)
        
        print(f"\n✅ Card created successfully!")
        print(f"  • ID: {card.id}")
        print(f"  • Type: {card.card_type}")
        print(f"  • Envelope: {envelope.name if envelope else 'None'}")
        print(f"{'='*60}\n")
        
        return {
            'card': card.to_dict(),
            'envelope': envelope.to_dict() if envelope else None,
            'extracted_info': extracted_info
        }
    
    def _parse_agent_output(self, output: str, raw_note: str) -> Dict[str, Any]:
        """Parse the agent's output into structured data"""
        
        # Try to extract JSON from output
        try:
            # Look for JSON in the output
            import re
            json_match = re.search(r'\{[\s\S]*\}', output)
            if json_match:
                data = json.loads(json_match.group())
                return self._validate_extracted_data(data, raw_note)
        except:
            pass
        
        # Fallback: parse from text output
        return self._fallback_extraction(raw_note)
    
    def _fallback_extraction(self, raw_note: str) -> Dict[str, Any]:
        """Fallback extraction using direct NLP tools"""
        print("🔄 Using fallback extraction...")
        
        # Extract all information directly
        card_type = entity_extractor.classify_card_type(raw_note)
        priority = entity_extractor.classify_priority(raw_note)
        keywords = entity_extractor.extract_keywords(raw_note)
        assignee = entity_extractor.extract_assignee(raw_note)
        date = date_parser.parse(raw_note)
        project_context = entity_extractor.extract_project_context(raw_note)
        
        return {
            'card_type': card_type,
            'description': raw_note.strip(),
            'date': date,
            'assignee': assignee,
            'priority': priority,
            'keywords': keywords,
            'project_context': project_context
        }
    
    def _validate_extracted_data(self, data: Dict[str, Any], raw_note: str) -> Dict[str, Any]:
        """Validate and clean extracted data"""
        
        # Ensure all required fields exist
        validated = {
            'card_type': data.get('card_type', 'note'),
            'description': data.get('description', raw_note).strip(),
            'date': None,
            'assignee': data.get('assignee'),
            'priority': data.get('priority', 'medium'),
            'keywords': data.get('keywords', []),
            'project_context': data.get('project_context', [])
        }
        
        # Parse date if it's a string
        if 'date' in data and data['date']:
            if isinstance(data['date'], str):
                validated['date'] = date_parser.parse(data['date'])
            else:
                validated['date'] = data['date']
        
        # Ensure keywords is a list
        if isinstance(validated['keywords'], str):
            validated['keywords'] = [k.strip() for k in validated['keywords'].split(',')]
        
        # Ensure project_context is a list
        if isinstance(validated['project_context'], str):
            validated['project_context'] = [validated['project_context']]
        
        # Validate card_type
        if validated['card_type'] not in Config.CARD_TYPES:
            validated['card_type'] = 'note'
        
        # Validate priority
        if validated['priority'] not in Config.PRIORITY_LEVELS:
            validated['priority'] = 'medium'
        
        return validated
    
    def _find_or_create_envelope(self, extracted_info: Dict[str, Any]):
        """Find matching envelope or create new one"""
        
        keywords = extracted_info['keywords']
        project_contexts = extracted_info.get('project_context', [])
        
        # First, try to find existing envelope by project context
        if project_contexts:
            for context_name in project_contexts:
                envelope = self.envelope_service.get_envelope_by_name(context_name)
                if envelope:
                    print(f"📁 Found existing envelope: {envelope.name}")
                    return envelope
        
        # Try to find by keyword matching
        if keywords:
            context_str = ' '.join(keywords)
            envelope = self.envelope_service.find_matching_envelope(keywords, context_str)
            if envelope:
                print(f"📁 Matched to envelope: {envelope.name}")
                return envelope
        
        # Create new envelope if project context is identified
        if project_contexts:
            context_name = project_contexts[0]
            print(f"📁 Creating new envelope: {context_name}")
            return self.envelope_service.create_envelope(
                name=context_name,
                envelope_type='project',
                keywords=keywords
            )
        
        # No envelope needed
        print("📁 No envelope assigned")
        return None
    
    def batch_process_notes(self, notes: list) -> list:
        """Process multiple notes at once"""
        results = []
        for note in notes:
            try:
                result = self.process_note(note)
                results.append(result)
            except Exception as e:
                print(f"❌ Error processing note '{note}': {e}")
                results.append({
                    'error': str(e),
                    'note': note
                })
        return results