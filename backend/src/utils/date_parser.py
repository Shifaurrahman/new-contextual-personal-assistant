import dateparser
from datetime import datetime, timedelta
from dateutil import parser as dateutil_parser
import re
from typing import Optional, Dict, Any

class DateParser:
    """Advanced date parser for natural language dates"""
    
    def __init__(self):
        self.settings = {
            'PREFER_DATES_FROM': 'future',
            'RETURN_AS_TIMEZONE_AWARE': False,
            'RELATIVE_BASE': datetime.now()
        }
    
    def parse(self, text: str) -> Optional[datetime]:
        """
        Parse natural language date from text
        
        Args:
            text: Input text containing date information
            
        Returns:
            datetime object or None if no date found
        """
        if not text:
            return None
        
        # First, try to extract specific time patterns (HH:MM format)
        time_match = re.search(r'(\d{1,2})[:\.](\d{2})\s*(a\.?m\.?|p\.?m\.?|am|pm)?', text, re.IGNORECASE)
        extracted_time = None
        
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            meridiem = time_match.group(3)
            
            # Handle AM/PM
            if meridiem:
                meridiem = meridiem.lower().replace('.', '')
                if meridiem in ['pm', 'p.m'] and hour != 12:
                    hour += 12
                elif meridiem in ['am', 'a.m'] and hour == 12:
                    hour = 0
            
            extracted_time = (hour, minute)
        
        # Try dateparser first (handles most natural language)
        parsed_date = dateparser.parse(text, settings=self.settings)
        
        # If we found a specific time, update the parsed date
        if parsed_date and extracted_time:
            hour, minute = extracted_time
            parsed_date = parsed_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            return parsed_date
        
        if parsed_date:
            return parsed_date
        
        # Try specific patterns
        parsed_date = self._parse_relative_dates(text)
        
        # Apply extracted time if we found one
        if parsed_date and extracted_time:
            hour, minute = extracted_time
            parsed_date = parsed_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            return parsed_date
        
        if parsed_date:
            return parsed_date
        
        # Try dateutil as fallback
        try:
            return dateutil_parser.parse(text, fuzzy=True)
        except:
            pass
        
        return None
    
    def _parse_relative_dates(self, text: str) -> Optional[datetime]:
        """Parse relative date expressions"""
        text_lower = text.lower()
        now = datetime.now()
        
        # Today/Tomorrow/Yesterday
        if 'today' in text_lower:
            return now.replace(hour=9, minute=0, second=0, microsecond=0)
        elif 'tomorrow' in text_lower:
            return (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        elif 'yesterday' in text_lower:
            return (now - timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Next/This week patterns
        if 'next week' in text_lower:
            return now + timedelta(weeks=1)
        elif 'this week' in text_lower:
            return now
        
        # Next/This month patterns
        if 'next month' in text_lower:
            return now + timedelta(days=30)
        elif 'this month' in text_lower:
            return now
        
        # Specific day patterns (next Monday, this Friday, etc.)
        days = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        for day_name, day_num in days.items():
            if day_name in text_lower:
                current_day = now.weekday()
                days_ahead = day_num - current_day
                
                if 'next' in text_lower:
                    if days_ahead <= 0:
                        days_ahead += 7
                    return (now + timedelta(days=days_ahead)).replace(hour=9, minute=0, second=0, microsecond=0)
                elif 'this' in text_lower or days_ahead > 0:
                    if days_ahead <= 0:
                        days_ahead += 7
                    return (now + timedelta(days=days_ahead)).replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Time patterns (in X hours/days/weeks)
        time_patterns = [
            (r'in (\d+) hour', 'hours'),
            (r'in (\d+) day', 'days'),
            (r'in (\d+) week', 'weeks'),
            (r'in (\d+) month', 'months'),
        ]
        
        for pattern, unit in time_patterns:
            match = re.search(pattern, text_lower)
            if match:
                value = int(match.group(1))
                if unit == 'hours':
                    return now + timedelta(hours=value)
                elif unit == 'days':
                    return now + timedelta(days=value)
                elif unit == 'weeks':
                    return now + timedelta(weeks=value)
                elif unit == 'months':
                    return now + timedelta(days=value * 30)
        
        return None
    
    def extract_date_info(self, text: str) -> Dict[str, Any]:
        """
        Extract comprehensive date information from text
        
        Returns:
            Dict with 'date', 'date_string', 'has_date' keys
        """
        parsed_date = self.parse(text)
        
        return {
            'date': parsed_date,
            'date_string': parsed_date.strftime('%Y-%m-%d %H:%M:%S') if parsed_date else None,
            'has_date': parsed_date is not None,
            'relative_description': self._get_relative_description(parsed_date) if parsed_date else None
        }
    
    def _get_relative_description(self, date: datetime) -> str:
        """Get human-readable relative description of date"""
        if not date:
            return None
        
        now = datetime.now()
        delta = date - now
        
        if delta.days == 0:
            return "Today"
        elif delta.days == 1:
            return "Tomorrow"
        elif delta.days == -1:
            return "Yesterday"
        elif 0 < delta.days < 7:
            return f"In {delta.days} days ({date.strftime('%A')})"
        elif delta.days < 0 and delta.days > -7:
            return f"{abs(delta.days)} days ago"
        elif delta.days >= 7:
            weeks = delta.days // 7
            return f"In {weeks} week(s)"
        else:
            return date.strftime('%Y-%m-%d')


# Global date parser instance
date_parser = DateParser()