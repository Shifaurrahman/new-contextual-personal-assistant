import re
from typing import List, Dict, Any, Optional
import spacy
from collections import Counter

class EntityExtractor:
    """Extract entities and keywords from text"""
    
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("⚠️  Downloading spacy model 'en_core_web_sm'...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract all entities from text
        
        Returns:
            Dict containing persons, organizations, dates, locations, etc.
        """
        doc = self.nlp(text)
        
        entities = {
            'persons': [],
            'organizations': [],
            'dates': [],
            'locations': [],
            'money': [],
            'other': []
        }
        
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                entities['persons'].append(ent.text)
            elif ent.label_ in ['ORG', 'PRODUCT']:
                entities['organizations'].append(ent.text)
            elif ent.label_ in ['DATE', 'TIME']:
                entities['dates'].append(ent.text)
            elif ent.label_ in ['GPE', 'LOC']:
                entities['locations'].append(ent.text)
            elif ent.label_ == 'MONEY':
                entities['money'].append(ent.text)
            else:
                entities['other'].append(ent.text)
        
        return entities
    
    def extract_assignee(self, text: str) -> Optional[str]:
        """
        Extract assignee (person or team) from text
        
        Looks for patterns like:
        - "ask John"
        - "tell Sarah"
        - "with the marketing team"
        - "@username"
        """
        # Check for @ mentions
        mention_match = re.search(r'@(\w+)', text)
        if mention_match:
            return mention_match.group(1)
        
        # Extract persons using NER
        entities = self.extract_entities(text)
        if entities['persons']:
            return entities['persons'][0]
        
        # Look for action patterns
        action_patterns = [
            r'(?:ask|tell|contact|call|email|message)\s+(\w+)',
            r'(?:with|to)\s+(?:the\s+)?(\w+(?:\s+\w+)?)\s+team',
            r'assigned?\s+to\s+(\w+)',
        ]
        
        for pattern in action_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract meaningful keywords from text
        
        Args:
            text: Input text
            max_keywords: Maximum number of keywords to return
            
        Returns:
            List of keywords
        """
        doc = self.nlp(text.lower())
        
        # Extract nouns, proper nouns, and important verbs
        keywords = []
        for token in doc:
            if (token.pos_ in ['NOUN', 'PROPN', 'VERB'] and 
                not token.is_stop and 
                not token.is_punct and 
                len(token.text) > 2):
                keywords.append(token.lemma_)
        
        # Count frequency and return most common
        keyword_freq = Counter(keywords)
        return [kw for kw, _ in keyword_freq.most_common(max_keywords)]
    
    def classify_priority(self, text: str) -> str:
        """
        Classify priority level based on text content
        
        Returns:
            Priority level: 'low', 'medium', 'high', 'urgent'
        """
        text_lower = text.lower()
        
        # Urgent indicators
        urgent_keywords = [
            'urgent', 'asap', 'immediately', 'emergency', 'critical',
            'right now', 'right away', 'crucial'
        ]
        if any(keyword in text_lower for keyword in urgent_keywords):
            return 'urgent'
        
        # High priority indicators
        high_keywords = [
            'important', 'priority', 'must', 'need to', 'deadline',
            'due', 'required', 'essential'
        ]
        if any(keyword in text_lower for keyword in high_keywords):
            return 'high'
        
        # Low priority indicators
        low_keywords = [
            'maybe', 'someday', 'eventually', 'when possible',
            'if time', 'optional', 'consider'
        ]
        if any(keyword in text_lower for keyword in low_keywords):
            return 'low'
        
        # Default to medium
        return 'medium'
    
    def classify_card_type(self, text: str) -> str:
        """
        Classify the type of card based on text content
        
        Returns:
            Card type: 'task', 'reminder', 'idea', 'note'
        """
        text_lower = text.lower()
        
        # Task indicators
        task_keywords = [
            'call', 'email', 'send', 'write', 'create', 'build',
            'finish', 'complete', 'do', 'make', 'schedule', 'book',
            'buy', 'order', 'prepare', 'review', 'check', 'update'
        ]
        if any(text_lower.startswith(keyword) for keyword in task_keywords):
            return 'task'
        
        # Reminder indicators
        reminder_keywords = [
            'remind', 'remember', 'don\'t forget', 'pick up',
            'bring', 'take', 'grab'
        ]
        if any(keyword in text_lower for keyword in reminder_keywords):
            return 'reminder'
        
        # Idea indicators
        idea_keywords = [
            'idea', 'concept', 'thought', 'what if', 'maybe we could',
            'we should', 'consider', 'brainstorm'
        ]
        if any(keyword in text_lower for keyword in idea_keywords):
            return 'idea'
        
        # Default to note
        return 'note'
    
    def extract_project_context(self, text: str) -> List[str]:
        """
        Extract project or context identifiers
        
        Looks for patterns like:
        - "for the Q3 budget"
        - "regarding the marketing campaign"
        - "about project X"
        """
        patterns = [
            r'(?:for|regarding|about|re:)\s+(?:the\s+)?([A-Z][\w\s]+?)(?:\s|$|\.)',
            r'(?:project|campaign|initiative)\s+([A-Z\w]+)',
            r'([A-Z][A-Z0-9]+)\s+(?:project|budget|meeting)',
        ]
        
        contexts = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            contexts.extend(matches)
        
        # Also check for organizations
        entities = self.extract_entities(text)
        contexts.extend(entities['organizations'])
        
        return list(set(contexts))  # Remove duplicates


# Global entity extractor instance
entity_extractor = EntityExtractor()