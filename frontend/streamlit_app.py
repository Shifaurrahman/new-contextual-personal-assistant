import streamlit as st
import requests
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="Contextual Personal Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_URL = "http://localhost:8000"

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
    }
    .card-container {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin-bottom: 10px;
    }
    h1 {
        color: #1f77b4;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'refresh' not in st.session_state:
    st.session_state.refresh = 0

def make_api_request(endpoint, method="GET", data=None):
    """Make API request with error handling"""
    try:
        url = f"{API_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        elif method == "PATCH":
            response = requests.patch(url)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None

def format_date(date_str):
    """Format date string to readable format"""
    if not date_str:
        return "No date"
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%b %d, %Y %I:%M %p")
    except:
        return date_str

def get_priority_color(priority):
    """Get color based on priority"""
    colors = {
        "low": "#95a5a6",
        "medium": "#f39c12",
        "high": "#e74c3c",
        "urgent": "#c0392b"
    }
    return colors.get(priority, "#95a5a6")

def get_type_emoji(card_type):
    """Get emoji for card type"""
    emojis = {
        "task": "✅",
        "reminder": "⏰",
        "idea": "💡",
        "note": "📝"
    }
    return emojis.get(card_type, "📄")

# Sidebar Navigation
st.sidebar.title("🤖 Personal Assistant")
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Add Note", "View Cards", "Envelopes", "Thinking Agent", "Settings"]
)

# ==================== DASHBOARD PAGE ====================
if page == "Dashboard":
    st.title("📊 Dashboard")
    
    # Load statistics
    stats = make_api_request("/statistics/dashboard")
    
    if stats:
        # Top metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Cards", stats['total_cards'])
        with col2:
            st.metric("Active Cards", stats['active_cards'])
        with col3:
            st.metric("Envelopes", stats['total_envelopes'])
        with col4:
            st.metric("Overdue Tasks", stats['overdue_tasks'], 
                     delta=f"-{stats['overdue_tasks']}" if stats['overdue_tasks'] > 0 else "0",
                     delta_color="inverse")
        
        st.markdown("---")
        
        
        
        # Recent activity
        st.subheader("📌 Recent Cards")
        recent_cards = make_api_request("/cards?limit=5")
        
        if recent_cards:
            for card in recent_cards:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{get_type_emoji(card['card_type'])} {card['description'][:80]}...**")
                    with col2:
                        st.markdown(f"<span style='color: {get_priority_color(card['priority'])}'>{card['priority'].upper()}</span>", unsafe_allow_html=True)
                    with col3:
                        st.caption(format_date(card['date']))
                    
                    st.markdown("---")

# ==================== ADD NOTE PAGE ====================
elif page == "Add Note":
    st.title("📝 Add New Note")
    
    st.markdown("""
    Enter your note in natural language, and the AI will automatically:
    - Classify the type (task, reminder, idea, note)
    - Extract dates, assignees, and keywords
    - Determine priority level
    - Organize into appropriate envelopes
    """)
    
    with st.form("note_form"):
        note_text = st.text_area(
            "Your Note",
            height=150,
            placeholder="e.g., 'Call Sarah about Q3 budget next Monday' or 'Reminder: pick up milk tomorrow'"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            submit = st.form_submit_button("🚀 Process Note", type="primary")
        
        if submit and note_text:
            with st.spinner("Processing your note..."):
                result = make_api_request("/notes/process", "POST", {"text": note_text})
                
                if result:
                    st.success("✅ Note processed successfully!")
                    
                    # Display extracted information
                    st.subheader("📊 Extracted Information")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    card = result['card']
                    
                    with col1:
                        st.metric("Type", card['card_type'].title())
                        st.metric("Priority", card['priority'].title())
                    
                    with col2:
                        st.metric("Assignee", card.get('assignee') or "None")
                        st.metric("Date", format_date(card.get('date')))
                    
                    with col3:
                        envelope = result.get('envelope')
                        st.metric("Envelope", envelope['name'] if envelope else "None")
                        st.metric("Keywords", len(card.get('context_keywords', [])))
                    
                    # Show full card details
                    with st.expander("View Full Details"):
                        st.json(card)
                    
                    st.session_state.refresh += 1
    
    # Batch processing
    st.markdown("---")
    st.subheader("🔄 Batch Process Notes")
    
    batch_notes = st.text_area(
        "Enter multiple notes (one per line)",
        height=200,
        placeholder="Line 1: Call John tomorrow\nLine 2: Review reports by Friday\nLine 3: Idea for new feature"
    )
    
    if st.button("Process All Notes"):
        if batch_notes:
            lines = [line.strip() for line in batch_notes.split('\n') if line.strip()]
            notes_data = [{"text": line} for line in lines]
            
            with st.spinner(f"Processing {len(lines)} notes..."):
                result = make_api_request("/notes/batch-process", "POST", notes_data)
                
                if result:
                    st.success(f"✅ Processed {result['total']} notes successfully!")
                    st.session_state.refresh += 1

# ==================== VIEW CARDS PAGE ====================
elif page == "View Cards":
    st.title("📋 All Cards")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        filter_type = st.selectbox("Type", ["All", "task", "reminder", "idea", "note"])
    with col2:
        filter_status = st.selectbox("Status", ["All", "active", "completed", "archived"])
    with col3:
        filter_priority = st.selectbox("Priority", ["All", "urgent", "high", "medium", "low"])
    with col4:
        search_query = st.text_input("Search", placeholder="Search cards...")
    
    # Build API query
    params = []
    if filter_type != "All":
        params.append(f"card_type={filter_type}")
    if filter_status != "All":
        params.append(f"status={filter_status}")
    
    query_string = "?" + "&".join(params) if params else ""
    
    # Load cards
    if search_query:
        cards = make_api_request(f"/cards/search/{search_query}")
    else:
        cards = make_api_request(f"/cards{query_string}")
    
    if cards:
        # Filter by priority if needed
        if filter_priority != "All":
            cards = [c for c in cards if c['priority'] == filter_priority]
        
        st.caption(f"Showing {len(cards)} cards")
        
        # Display cards
        for card in cards:
            with st.container():
                col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
                
                with col1:
                    st.markdown(f"### {get_type_emoji(card['card_type'])} {card['description']}")
                    if card.get('assignee'):
                        st.caption(f"👤 Assigned to: {card['assignee']}")
                    if card.get('context_keywords'):
                        keywords = ", ".join(card['context_keywords'][:5])
                        st.caption(f"🏷️ {keywords}")
                
                with col2:
                    st.markdown(f"<div style='background-color: {get_priority_color(card['priority'])}; color: white; padding: 5px 10px; border-radius: 5px; text-align: center;'>{card['priority'].upper()}</div>", unsafe_allow_html=True)
                
                with col3:
                    st.caption(format_date(card['date']))
                
                with col4:
                    if card['status'] == 'active':
                        if st.button("✓ Complete", key=f"complete_{card['id']}"):
                            make_api_request(f"/cards/{card['id']}/complete", "PATCH")
                            st.success("Marked as complete!")
                            st.rerun()
                    else:
                        st.caption("✓ Completed")
                
                with st.expander("Details"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Raw Input:**", card.get('raw_input', 'N/A'))
                        st.write("**Created:**", format_date(card['created_at']))
                    with col2:
                        st.write("**Envelope ID:**", card.get('envelope_id', 'None'))
                        st.write("**Updated:**", format_date(card['updated_at']))
                    
                    if st.button("🗑️ Delete", key=f"delete_{card['id']}"):
                        make_api_request(f"/cards/{card['id']}", "DELETE")
                        st.success("Card deleted!")
                        st.rerun()
                
                st.markdown("---")
    else:
        st.info("No cards found.")

# ==================== ENVELOPES PAGE ====================
elif page == "Envelopes":
    st.title("📁 Envelopes")
    
    envelopes = make_api_request("/envelopes")
    
    if envelopes:
        for envelope in envelopes:
            with st.expander(f"📁 {envelope['name']} ({envelope['card_count']} cards)"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Type:**", envelope.get('envelope_type', 'N/A'))
                    st.write("**Description:**", envelope.get('description', 'N/A'))
                
                with col2:
                    st.write("**Keywords:**", ", ".join(envelope.get('keywords', [])))
                    st.write("**Created:**", format_date(envelope['created_at']))
                
                # Get statistics
                stats = make_api_request(f"/envelopes/{envelope['id']}/statistics")
                if stats:
                    st.subheader("Statistics")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Tasks", stats['tasks'])
                    with col2:
                        st.metric("Ideas", stats['ideas'])
                    with col3:
                        st.metric("Active", stats['active'])
                    with col4:
                        st.metric("Completed", stats['completed'])
                
                # Show cards in envelope
                if st.button(f"View Cards", key=f"view_env_{envelope['id']}"):
                    cards = make_api_request(f"/envelopes/{envelope['id']}/cards")
                    if cards:
                        for card in cards:
                            st.markdown(f"- {get_type_emoji(card['card_type'])} {card['description']}")
    else:
        st.info("No envelopes found.")

# ==================== THINKING AGENT PAGE ====================
elif page == "Thinking Agent":
    st.title("🤔 Thinking Agent")
    
    st.markdown("""
    The Thinking Agent analyzes your cards and provides:
    - Next step suggestions
    - Conflict detection (overlapping deadlines)
    - Reorganization recommendations
    - Pattern insights
    """)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("🚀 Run Analysis", type="primary"):
            with st.spinner("Analyzing..."):
                result = make_api_request("/thinking/analyze", "POST")
                if result:
                    st.success(f"✅ Generated {result['total']} suggestions!")
                    st.session_state.refresh += 1
    
    st.markdown("---")
    
    # Show suggestions
    st.subheader("💡 Suggestions")
    
    suggestions = make_api_request("/thinking/suggestions")
    
    if suggestions:
        for suggestion in suggestions:
            icon_map = {
                "next_step": "➡️",
                "conflict": "⚠️",
                "recommendation": "💡"
            }
            
            icon = icon_map.get(suggestion['output_type'], "ℹ️")
            
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"### {icon} {suggestion['title']}")
                    st.write(suggestion['description'])
                    st.caption(f"Priority: {suggestion['priority']} | Created: {format_date(suggestion['created_at'])}")
                
                with col2:
                    if suggestion['status'] == 'pending':
                        if st.button("✓ Acknowledge", key=f"ack_{suggestion['id']}"):
                            make_api_request(f"/thinking/suggestions/{suggestion['id']}/acknowledge", "PATCH")
                            st.success("Acknowledged!")
                            st.rerun()
                
                st.markdown("---")
    else:
        st.info("No suggestions available. Run analysis to generate suggestions.")

# ==================== SETTINGS PAGE ====================
elif page == "Settings":
    st.title("⚙️ Settings")
    
    st.subheader("API Configuration")
    st.text_input("API URL", value=API_URL, disabled=True)
    
    st.markdown("---")
    
    st.subheader("Database")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Refresh Data"):
            st.session_state.refresh += 1
            st.success("Data refreshed!")
    
    with col2:
        if st.button("📊 View Stats"):
            stats = make_api_request("/statistics/dashboard")
            if stats:
                st.json(stats)
    
    st.markdown("---")
    
    st.subheader("Context Summary")
    context_summary = make_api_request("/context/summary")
    
    if context_summary:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Contexts", context_summary['total_contexts'])
        with col2:
            st.metric("Active Projects", context_summary['active_projects'])
        with col3:
            st.metric("Key People", context_summary['key_people'])
        
        if context_summary.get('by_type'):
            st.write("**By Type:**")
            for ctx_type, count in context_summary['by_type'].items():
                st.write(f"- {ctx_type}: {count}")

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("🤖 Contextual Personal Assistant v1.0")
st.sidebar.caption("Powered by LangChain & OpenAI")