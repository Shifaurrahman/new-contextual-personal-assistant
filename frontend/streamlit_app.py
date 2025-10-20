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
    .due-date-box {
        background-color: #e8f4f8;
        padding: 10px;
        border-radius: 8px;
        border-left: 4px solid #0066cc;
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

def format_date_short(date_str):
    """Format date string to short format (for display)"""
    if not date_str:
        return "No date"
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%b %d, %Y")
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
        
        # Cards breakdown
        st.subheader("📋 Cards Breakdown")
        cards_by_type = stats['cards_by_type']
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("✅ Tasks", cards_by_type.get('tasks', 0))
        with col2:
            st.metric("⏰ Reminders", cards_by_type.get('reminders', 0))
        with col3:
            st.metric("💡 Ideas", cards_by_type.get('ideas', 0))
        with col4:
            st.metric("📝 Notes", cards_by_type.get('notes', 0))
        
        st.markdown("---")
        
        # Recent activity
        st.subheader("📌 Recent Cards")
        recent_cards = make_api_request("/cards?limit=5")
        
        if recent_cards:
            for card in recent_cards:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        desc_preview = card['description'][:80] + "..." if len(card['description']) > 80 else card['description']
                        st.markdown(f"**{get_type_emoji(card['card_type'])} {desc_preview}**")
                    with col2:
                        st.markdown(f"<span style='color: {get_priority_color(card['priority'])}'>{card['priority'].upper()}</span>", unsafe_allow_html=True)
                    with col3:
                        st.caption(format_date_short(card['date']))
                    
                    st.markdown("---")
        else:
            st.info("No cards yet. Start by adding a note!")

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
            placeholder="e.g., 'Schedule meeting with development team next Wednesday at 10:30 AM' or 'Reminder: pick up milk tomorrow'"
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
                        if card.get('date'):
                            st.markdown("**📅 Due Date**")
                            st.info(format_date(card.get('date')))
                        else:
                            st.metric("Date", "No date set")
                    
                    with col3:
                        envelope = result.get('envelope')
                        st.metric("Envelope", envelope['name'] if envelope else "None")
                        st.metric("Keywords", len(card.get('context_keywords', [])))
                    
                    # Show keywords
                    if card.get('context_keywords'):
                        st.write("**🏷️ Keywords:**", ", ".join(card['context_keywords']))
                    
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
                    if card['date']:
                        st.markdown("**📅 Due Date**")
                        st.markdown(f"<div class='due-date-box'>{format_date(card['date'])}</div>", unsafe_allow_html=True)
                    else:
                        st.caption("No due date")
                
                with col4:
                    if card['status'] == 'active':
                        if st.button("✓ Complete", key=f"complete_{card['id']}"):
                            make_api_request(f"/cards/{card['id']}/complete", "PATCH")
                            st.success("Marked as complete!")
                            st.rerun()
                    else:
                        st.markdown("✅ **Done**")
                
                with st.expander("📄 Details & Metadata"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**📝 Original Note:**")
                        st.info(card.get('raw_input', 'N/A'))
                        
                        if card.get('envelope_id'):
                            st.write("**📁 Envelope:**", f"ID {card['envelope_id']}")
                        else:
                            st.write("**📁 Envelope:**", "None")
                        
                        # Priority update
                        st.write("**🎯 Update Priority:**")
                        new_priority = st.selectbox(
                            "Change priority",
                            ["low", "medium", "high", "urgent"],
                            index=["low", "medium", "high", "urgent"].index(card['priority']),
                            key=f"priority_{card['id']}"
                        )
                        if new_priority != card['priority']:
                            if st.button("💾 Save Priority", key=f"save_priority_{card['id']}"):
                                make_api_request(
                                    f"/cards/{card['id']}", 
                                    "PUT", 
                                    {"priority": new_priority}
                                )
                                st.success(f"Priority updated to {new_priority}!")
                                st.rerun()
                    
                    with col2:
                        st.write("**📊 Metadata:**")
                        st.caption(f"🆔 Card ID: {card['id']}")
                        st.caption(f"📅 Created: {format_date(card['created_at'])}")
                        st.caption(f"🔄 Last updated: {format_date(card['updated_at'])}")
                        st.caption(f"📌 Status: {card['status']}")
                    
                    st.markdown("---")
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if st.button("🗑️ Delete", key=f"delete_{card['id']}", type="secondary"):
                            if st.button(f"⚠️ Confirm Delete?", key=f"confirm_delete_{card['id']}"):
                                make_api_request(f"/cards/{card['id']}", "DELETE")
                                st.success("Card deleted!")
                                st.rerun()
                
                st.markdown("---")
    else:
        st.info("No cards found. Try adjusting your filters or add some notes!")

# ==================== ENVELOPES PAGE ====================
elif page == "Envelopes":
    st.title("📁 Envelopes")
    
    st.markdown("Envelopes group related cards together by project, theme, or context.")
    
    envelopes = make_api_request("/envelopes")
    
    if envelopes:
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Envelopes", len(envelopes))
        with col2:
            total_cards = sum(e['card_count'] for e in envelopes)
            st.metric("Total Cards in Envelopes", total_cards)
        with col3:
            avg_cards = total_cards / len(envelopes) if envelopes else 0
            st.metric("Average Cards per Envelope", f"{avg_cards:.1f}")
        
        st.markdown("---")
        
        for envelope in envelopes:
            with st.expander(f"📁 {envelope['name']} ({envelope['card_count']} cards)", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**📂 Type:**", envelope.get('envelope_type', 'N/A').title())
                    st.write("**📝 Description:**", envelope.get('description', 'N/A'))
                
                with col2:
                    if envelope.get('keywords'):
                        st.write("**🏷️ Keywords:**", ", ".join(envelope.get('keywords', [])))
                    st.write("**📅 Created:**", format_date_short(envelope['created_at']))
                
                # Get statistics
                stats = make_api_request(f"/envelopes/{envelope['id']}/statistics")
                if stats:
                    st.subheader("📊 Statistics")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("✅ Tasks", stats['tasks'])
                    with col2:
                        st.metric("💡 Ideas", stats['ideas'])
                    with col3:
                        st.metric("🟢 Active", stats['active'])
                    with col4:
                        st.metric("✓ Completed", stats['completed'])
                
                # Show cards in envelope
                cards = make_api_request(f"/envelopes/{envelope['id']}/cards")
                if cards:
                    st.subheader("📋 Cards in this Envelope")
                    for card in cards:
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.markdown(f"- {get_type_emoji(card['card_type'])} **{card['description']}**")
                        with col2:
                            st.caption(f"{card['priority'].upper()}")
    else:
        st.info("No envelopes created yet. Add notes with project context to create envelopes automatically!")

# ==================== THINKING AGENT PAGE ====================
elif page == "Thinking Agent":
    st.title("🤔 Thinking Agent")
    
    st.markdown("""
    The Thinking Agent analyzes your cards and provides:
    - **Next step suggestions** based on completed tasks
    - **Conflict detection** for overlapping deadlines
    - **Reorganization recommendations** for better structure
    - **Pattern insights** from your work habits
    """)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("🚀 Run Analysis", type="primary"):
            with st.spinner("🤔 Analyzing your cards..."):
                result = make_api_request("/thinking/analyze", "POST")
                if result:
                    st.success(f"✅ Generated {result['total']} suggestions!")
                    st.session_state.refresh += 1
    
    st.markdown("---")
    
    # Show suggestions
    st.subheader("💡 Suggestions")
    
    suggestions = make_api_request("/thinking/suggestions")
    
    if suggestions:
        # Group by type
        next_steps = [s for s in suggestions if s['output_type'] == 'next_step']
        conflicts = [s for s in suggestions if s['output_type'] == 'conflict']
        recommendations = [s for s in suggestions if s['output_type'] == 'recommendation']
        
        # Show counts
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("➡️ Next Steps", len(next_steps))
        with col2:
            st.metric("⚠️ Conflicts", len(conflicts))
        with col3:
            st.metric("💡 Recommendations", len(recommendations))
        
        st.markdown("---")
        
        for suggestion in suggestions:
            icon_map = {
                "next_step": "➡️",
                "conflict": "⚠️",
                "recommendation": "💡"
            }
            
            color_map = {
                "next_step": "#3498db",
                "conflict": "#e74c3c",
                "recommendation": "#9b59b6"
            }
            
            icon = icon_map.get(suggestion['output_type'], "ℹ️")
            color = color_map.get(suggestion['output_type'], "#95a5a6")
            
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"<div style='border-left: 4px solid {color}; padding-left: 15px;'><h3>{icon} {suggestion['title']}</h3></div>", unsafe_allow_html=True)
                    st.write(suggestion['description'])
                    st.caption(f"Priority: **{suggestion['priority'].upper()}** | Created: {format_date(suggestion['created_at'])}")
                
                with col2:
                    if suggestion['status'] == 'pending':
                        if st.button("✓ Acknowledge", key=f"ack_{suggestion['id']}"):
                            make_api_request(f"/thinking/suggestions/{suggestion['id']}/acknowledge", "PATCH")
                            st.success("Acknowledged!")
                            st.rerun()
                    else:
                        st.caption("✓ Acknowledged")
                
                st.markdown("---")
    else:
        st.info("No suggestions available. Click 'Run Analysis' to generate suggestions based on your cards.")

# ==================== SETTINGS PAGE ====================
elif page == "Settings":
    st.title("⚙️ Settings")
    
    st.subheader("🔗 API Configuration")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("API URL", value=API_URL, disabled=True)
    with col2:
        # Test API connection
        if st.button("🔍 Test Connection"):
            health = make_api_request("/health")
            if health:
                st.success("✅ API is running!")
            else:
                st.error("❌ Cannot connect to API")
    
    st.markdown("---")
    
    st.subheader("💾 Database")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Refresh Data"):
            st.session_state.refresh += 1
            st.success("Data refreshed!")
            st.rerun()
    
    with col2:
        if st.button("📊 View Full Stats"):
            stats = make_api_request("/statistics/dashboard")
            if stats:
                st.json(stats)
    
    st.markdown("---")
    
    st.subheader("🧠 Context Summary")
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
            st.write("**📊 By Type:**")
            for ctx_type, count in context_summary['by_type'].items():
                st.write(f"- **{ctx_type.title()}:** {count}")
        
        # Show top contexts
        if context_summary.get('top_contexts'):
            st.markdown("---")
            st.write("**⭐ Top Contexts:**")
            for ctx in context_summary['top_contexts'][:5]:
                st.write(f"- **{ctx['name']}** ({ctx['context_type']}) - Importance: {ctx['importance_score']}/10")
    else:
        st.info("No context data available yet.")

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("🤖 Contextual Personal Assistant v1.0")
st.sidebar.caption("Powered by LangChain & OpenAI")
st.sidebar.caption(f"🔄 Refresh count: {st.session_state.refresh}")