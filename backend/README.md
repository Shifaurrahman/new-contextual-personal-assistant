# 🤖 Contextual Personal Assistant

A powerful AI-powered system that transforms unstructured notes into a highly structured and actionable knowledge base using LangChain agents and OpenAI.

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [System Design](#system-design)
- [API Documentation](#api-documentation)
- [Examples](#examples)

## ✨ Features

### Ingestion & Organization Agent
- **Intelligent Card Classification**: Automatically classifies notes into tasks, reminders, ideas, or notes
- **Natural Language Date Parsing**: Understands "next Monday", "in 3 days", "tomorrow at 3pm", etc.
- **Named Entity Recognition**: Extracts people, organizations, locations, and dates
- **Priority Detection**: Automatically determines priority levels (low, medium, high, urgent)
- **Smart Keyword Extraction**: Identifies relevant keywords for search and categorization
- **Automatic Envelope Assignment**: Groups related cards into project envelopes

### Thinking Agent
- **Next Step Suggestions**: Recommends follow-up actions based on completed tasks
- **Conflict Detection**: Identifies overlapping deadlines and resource conflicts
- **Pattern Recognition**: Analyzes work patterns and provides insights
- **Reorganization Recommendations**: Suggests creating new envelopes or consolidating similar items

### Context Management
- **Dynamic User Context**: Maintains up-to-date understanding of projects, people, and themes
- **Context Refinement**: Continuously updates context based on new notes
- **Relevance Scoring**: Tracks importance of different context items

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        User Input                            │
│                   (Unstructured Notes)                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Ingestion & Organization Agent                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  LangChain Agent Executor with Tools:                │   │
│  │  • parse_date        • extract_entities              │   │
│  │  • extract_assignee  • classify_card_type            │   │
│  │  • classify_priority • extract_keywords              │   │
│  │  • extract_project_context                           │   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Structured Data Layer                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐     │
│  │  Cards   │  │ Envelopes│  │   User Context       │     │
│  │          │  │          │  │                      │     │
│  │ • Task   │  │ Projects │  │ • Active Projects    │     │
│  │ • Reminder│ │ Companies│  │ • Key People         │     │
│  │ • Idea   │  │ People   │  │ • Themes             │     │
│  │ • Note   │  │ Themes   │  │                      │     │
│  └──────────┘  └──────────┘  └──────────────────────┘     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    SQLite Database                           │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Thinking Agent                            │
│  (Runs Periodically)                                         │
│  • Analyzes cards and envelopes                              │
│  • Generates proactive suggestions                           │
│  • Detects conflicts and patterns                            │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **Agent Framework**: LangChain with OpenAI Functions
- **LLM**: OpenAI GPT-4 Turbo
- **NLP**: spaCy for NER, transformers for advanced NLP
- **Date Parsing**: dateparser with custom relative date handlers
- **Database**: SQLAlchemy with SQLite
- **CLI Interface**: Rich for beautiful terminal output

### Design Decisions

#### Why LangChain?
- **Agent Executor Framework**: Built-in support for tool-using agents
- **OpenAI Functions Integration**: Seamless function calling for structured outputs
- **Extensibility**: Easy to add new tools and capabilities
- **Community Support**: Well-documented with active community

#### Why SQLite?
- **Local-First**: No server setup required
- **Portability**: Single file database
- **ACID Compliance**: Reliable for personal use
- **Python Integration**: Excellent SQLAlchemy support

#### Tool-Based Architecture
Each NLP capability is exposed as a LangChain tool, allowing the agent to:
- Decide which tools to use based on the input
- Chain multiple tools together
- Self-correct if tool outputs are insufficient

## 🚀 Installation

### Prerequisites

- Python 3.9 or higher
- OpenAI API key
- 4GB+ RAM (for NLP models)

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/contextual-assistant.git
cd contextual-assistant
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Download spaCy Model

```bash
python -m spacy download en_core_web_sm
```

### Step 5: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=your_actual_api_key_here
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory:

```bash
# Required
OPENAI_API_KEY=sk-...your-key-here

# Optional
OPENAI_MODEL=gpt-4-turbo-preview
DATABASE_URL=sqlite:///./contextual_assistant.db
AGENT_VERBOSE=True
MAX_ITERATIONS=5
```

### Configuration Options

Edit `config.py` to customize:

- **Card Types**: Add custom card types beyond task/reminder/idea/note
- **Priority Levels**: Adjust priority classification
- **Context Settings**: Configure context retention and importance scoring
- **Agent Behavior**: Tune LLM temperature, max iterations, etc.

## 💻 Usage

### Running the Application

```bash
python main.py
```

### First Run - Demo Mode

On first run, the system will offer to run a demo with sample notes:

```
Would you like to run a demo with sample notes? (y/n)
```

This will create sample cards and envelopes to explore the system.

### Main Menu Options

```
1. Add a new note       - Process a new unstructured note
2. View all cards       - Display all created cards
3. View envelopes       - Show envelope organization
4. Run thinking agent   - Generate suggestions and insights
5. View suggestions     - See pending recommendations
6. View context summary - Display user context overview
7. Search cards         - Search through your cards
8. Exit                 - Close the application
```

### Adding Notes

When you select option 1, you can enter any unstructured note:

```
Examples:
- "Call Sarah about the Q3 budget next Monday"
- "Reminder: pick up milk on the way home"
- "Idea: new logo should be blue and green"
- "Send proposal to marketing team by Friday urgent"
- "Meeting with John tomorrow at 3pm about project X"
```

The system will:
1. Classify the note type
2. Extract entities (dates, people, keywords)
3. Determine priority
4. Assign to appropriate envelope or create new one
5. Update user context

### Running the Thinking Agent

Select option 4 to run analysis:
- Analyzes all active cards and envelopes
- Generates suggestions for next steps
- Detects conflicts (overlapping deadlines, etc.)
- Recommends reorganization when beneficial
- Identifies work patterns

## 📁 Project Structure

```
contextual-assistant/
├── src/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── ingestion_agent.py    # Main ingestion logic
│   │   ├── thinking_agent.py     # Analysis and suggestions
│   │   └── tools.py               # LangChain tools
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py            # Database management
│   │   └── schemas.py             # SQLAlchemy models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── card_service.py        # Card CRUD operations
│   │   ├── envelope_service.py    # Envelope management
│   │   └── context_service.py     # Context management
│   └── utils/
│       ├── __init__.py
│       ├── date_parser.py         # Natural language date parsing
│       └── entity_extractor.py    # NER and classification
├── tests/
│   └── __init__.py
├── .env.example                   # Environment template
├── .gitignore
├── config.py                      # Configuration
├── main.py                        # CLI application
├── requirements.txt               # Dependencies
└── README.md                      # This file
```

## 🎯 System Design

### Ingestion Agent Flow

```
1. User Input
   ↓
2. Agent receives note → Uses LangChain Agent Executor
   ↓
3. Agent decides which tools to use
   ├─→ parse_date("next Monday") → 2024-10-27
   ├─→ extract_assignee("Call Sarah") → "Sarah"
   ├─→ classify_card_type(...) → "task"
   ├─→ classify_priority(...) → "high"
   ├─→ extract_keywords(...) → ["call", "budget", "Q3"]
   └─→ extract_project_context(...) → ["Q3 Budget"]
   ↓
4. Agent returns structured JSON
   ↓
5. Create Card in database
   ↓
6. Find/Create Envelope
   ↓
7. Update User Context
   ↓
8. Return result to user
```

### Thinking Agent Design

The Thinking Agent operates on a scheduled basis (configurable):

```python
def analyze_and_suggest():
    # 1. Gather all active data
    cards = get_all_cards(status="active")
    envelopes = get_all_envelopes()
    
    # 2. Run analysis strategies
    suggestions = []
    suggestions += suggest_next_steps(cards, envelopes)
    suggestions += detect_conflicts(cards)
    suggestions += recommend_reorganization(cards, envelopes)
    suggestions += identify_patterns(cards)
    
    # 3. Save and return suggestions
    return save_suggestions(suggestions)
```

**Analysis Strategies:**

1. **Next Steps**: After completing tasks in an envelope, suggests related tasks
2. **Conflict Detection**: Finds overlapping deadlines, overdue tasks
3. **Reorganization**: Identifies unorganized cards with common themes
4. **Pattern Recognition**: Analyzes completion rates, priority distributions

### Date Parsing Logic

Supports:
- **Absolute dates**: "October 25, 2024", "2024-10-25"
- **Relative dates**: "tomorrow", "next Monday", "in 3 days"
- **Time expressions**: "at 3pm", "9:00 AM"
- **Combined**: "next Monday at 3pm"

Implementation:
1. Try `dateparser` library (handles most cases)
2. Custom patterns for relative dates
3. Fallback to `dateutil.parser`

### Entity Extraction

Uses spaCy's NER with custom patterns:
- **PERSON**: Names of people
- **ORG**: Companies, teams
- **GPE/LOC**: Locations
- **DATE/TIME**: Date expressions

Custom extractors for:
- Assignees (action patterns like "call John")
- Project contexts (patterns like "Q3 Budget Project")

## 📚 Examples

### Example 1: Task with Deadline

**Input:**
```
"Send quarterly report to John by Friday urgent"
```

**Extracted:**
- Type: `task`
- Description: "Send quarterly report to John by Friday"
- Date: `2024-10-25` (next Friday)
- Assignee: `John`
- Priority: `urgent`
- Keywords: `["send", "quarterly", "report", "friday"]`

### Example 2: Project Idea

**Input:**
```
"Idea: Launch a customer loyalty program with points and rewards"
```

**Extracted:**
- Type: `idea`
- Description: "Launch a customer loyalty program with points and rewards"
- Priority: `medium`
- Keywords: `["customer", "loyalty", "program", "points", "rewards"]`
- Envelope: Auto-created "Customer Loyalty" or matched to existing

### Example 3: Meeting Reminder

**Input:**
```
"Team standup tomorrow at 9am with marketing team"
```

**Extracted:**
- Type: `reminder`
- Description: "Team standup with marketing team"
- Date: `2024-10-21 09:00` (tomorrow 9am)
- Assignee: `marketing team`
- Priority: `medium`
- Keywords: `["team", "standup", "marketing"]`

## 🔧 Troubleshooting

### Common Issues

**1. OpenAI API Key Error**
```
ValueError: OPENAI_API_KEY must be set in environment variables
```
Solution: Add your API key to `.env` file

**2. spaCy Model Not Found**
```
OSError: [E050] Can't find model 'en_core_web_sm'
```
Solution: Run `python -m spacy download en_core_web_sm`

**3. Database Locked**
```
sqlite3.OperationalError: database is locked
```
Solution: Close any other instances of the application

**4. Import Errors**
```
ModuleNotFoundError: No module named 'langchain'
```
Solution: Ensure virtual environment is activated and run `pip install -r requirements.txt`

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- LangChain for the agent framework
- OpenAI for GPT-4
- spaCy for NLP capabilities
- dateparser for natural language date parsing

## 📞 Support

For issues or questions, please open an issue on GitHub.

---

Built with ❤️ using LangChain and OpenAI