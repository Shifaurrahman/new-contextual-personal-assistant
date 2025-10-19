from langchain.tools import Tool, StructuredTool
from langchain.pydantic_v1 import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from src.utils import date_parser, entity_extractor


class ParseDateInput(BaseModel):
    """Input for parse_date tool"""
    text: str = Field(description="Text containing date information to parse")


class ExtractEntitiesInput(BaseModel):
    """Input for extract_entities tool"""
    text: str = Field(description="Text to extract entities from")


class ClassifyCardTypeInput(BaseModel):
    """Input for classify_card_type tool"""
    text: str = Field(description="Text to classify card type from")


class ClassifyPriorityInput(BaseModel):
    """Input for classify_priority tool"""
    text: str = Field(description="Text to determine priority level from")


class ExtractKeywordsInput(BaseModel):
    """Input for extract_keywords tool"""
    text: str = Field(description="Text to extract keywords from")
    max_keywords: int = Field(default=10, description="Maximum number of keywords to extract")


def create_parse_date_tool() -> Tool:
    """Create a tool for parsing dates from natural language"""
    
    def parse_date(text: str) -> str:
        """Parse natural language date to datetime"""
        result = date_parser.extract_date_info(text)
        
        if result['has_date']:
            return f"Parsed date: {result['date_string']}\nRelative: {result['relative_description']}"
        return "No date found in text"
    
    return Tool(
        name="parse_date",
        func=parse_date,
        description="Parse natural language dates like 'next Monday', 'in 3 days', 'tomorrow' into actual datetime. Input should be text containing date information.",
        args_schema=ParseDateInput
    )


def create_extract_entities_tool() -> Tool:
    """Create a tool for extracting entities from text"""
    
    def extract_entities(text: str) -> str:
        """Extract named entities from text"""
        entities = entity_extractor.extract_entities(text)
        
        result = []
        if entities['persons']:
            result.append(f"Persons: {', '.join(entities['persons'])}")
        if entities['organizations']:
            result.append(f"Organizations: {', '.join(entities['organizations'])}")
        if entities['locations']:
            result.append(f"Locations: {', '.join(entities['locations'])}")
        if entities['dates']:
            result.append(f"Dates: {', '.join(entities['dates'])}")
        
        return "\n".join(result) if result else "No entities found"
    
    return Tool(
        name="extract_entities",
        func=extract_entities,
        description="Extract named entities like persons, organizations, locations from text. Useful for identifying assignees and context.",
        args_schema=ExtractEntitiesInput
    )


def create_extract_assignee_tool() -> Tool:
    """Create a tool for extracting assignee from text"""
    
    def extract_assignee(text: str) -> str:
        """Extract assignee (person or team) from text"""
        assignee = entity_extractor.extract_assignee(text)
        return f"Assignee: {assignee}" if assignee else "No assignee found"
    
    return Tool(
        name="extract_assignee",
        func=extract_assignee,
        description="Extract the person or team assigned to a task from text. Looks for patterns like 'call John', 'ask Sarah', 'with marketing team'.",
        args_schema=ExtractEntitiesInput
    )


def create_classify_card_type_tool() -> Tool:
    """Create a tool for classifying card type"""
    
    def classify_card_type(text: str) -> str:
        """Classify the type of card"""
        card_type = entity_extractor.classify_card_type(text)
        return f"Card type: {card_type}"
    
    return Tool(
        name="classify_card_type",
        func=classify_card_type,
        description="Classify text into card types: 'task' (action required), 'reminder' (time-based alert), 'idea' (concept/brainstorm), or 'note' (general information).",
        args_schema=ClassifyCardTypeInput
    )


def create_classify_priority_tool() -> Tool:
    """Create a tool for classifying priority"""
    
    def classify_priority(text: str) -> str:
        """Classify priority level"""
        priority = entity_extractor.classify_priority(text)
        return f"Priority: {priority}"
    
    return Tool(
        name="classify_priority",
        func=classify_priority,
        description="Determine priority level (low, medium, high, urgent) based on text content and urgency indicators.",
        args_schema=ClassifyPriorityInput
    )


def create_extract_keywords_tool() -> Tool:
    """Create a tool for extracting keywords"""
    
    def extract_keywords(text: str, max_keywords: int = 10) -> str:
        """Extract keywords from text"""
        keywords = entity_extractor.extract_keywords(text, max_keywords)
        return f"Keywords: {', '.join(keywords)}" if keywords else "No keywords found"
    
    return Tool(
        name="extract_keywords",
        func=extract_keywords,
        description="Extract relevant keywords from text for categorization and search. Returns important nouns, verbs, and concepts.",
        args_schema=ExtractKeywordsInput
    )


def create_extract_project_context_tool() -> Tool:
    """Create a tool for extracting project context"""
    
    def extract_project_context(text: str) -> str:
        """Extract project or context identifiers"""
        contexts = entity_extractor.extract_project_context(text)
        return f"Project contexts: {', '.join(contexts)}" if contexts else "No project context found"
    
    return Tool(
        name="extract_project_context",
        func=extract_project_context,
        description="Extract project names or context identifiers from text. Looks for patterns like 'Q3 Budget', 'Marketing Campaign', 'Project X'.",
        args_schema=ExtractEntitiesInput
    )


def get_all_tools() -> List[Tool]:
    """Get all available tools for the agent"""
    return [
        create_parse_date_tool(),
        create_extract_entities_tool(),
        create_extract_assignee_tool(),
        create_classify_card_type_tool(),
        create_classify_priority_tool(),
        create_extract_keywords_tool(),
        create_extract_project_context_tool()
    ]