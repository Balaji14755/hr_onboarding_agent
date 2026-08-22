import os
import streamlit as st
from pathlib import Path
from langchain_core.messages import HumanMessage, AIMessage

# Configure Streamlit Page
st.set_page_config(
    page_title="HR Onboarding AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import backend modules
from config import Config
import database as db
from rag.vectorstore import initialize_vectorstore, get_vectorstore
from agent.graph import run_agent, get_groq_llm

# ==========================================
# CHATGPT-STYLE DARK UI (USER LEFT, AI RIGHT)
# ==========================================
CUSTOM_CSS = """
<style>
/* ═══════════════════════════════════════════
   GOOGLE FONTS & BASE THEME
   ═══════════════════════════════════════════ */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
    --bg-primary: #212121;
    --bg-secondary: #171717;
    --bg-surface: #2F2F2F;
    --bg-hover: #3A3A3A;
    --text-primary: #ECECEC;
    --text-secondary: #B4B4B4;
    --text-muted: #737373;
    --accent: #8B5CF6;
    --accent-hover: #7C3AED;
    --accent-glow: rgba(139, 92, 246, 0.25);
    --border-subtle: rgba(255, 255, 255, 0.08);
    --border-hover: rgba(255, 255, 255, 0.15);
    --green: #10B981;
    --amber: #F59E0B;
    --blue: #3B82F6;
    --radius-sm: 8px;
    --radius-md: 14px;
    --radius-lg: 24px;
    --radius-full: 9999px;
}

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    color: var(--text-primary);
}

.stApp {
    background-color: var(--bg-primary) !important;
}

/* Hide Streamlit branding */
#MainMenu, header, footer, .stDeployButton {
    display: none !important;
}

/* ═══════════════════════════════════════════
   LAYOUT CONTAINERS & CHAT COLUMN
   ═══════════════════════════════════════════ */
.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

section[data-testid="stMain"] {
    background-color: var(--bg-primary) !important;
}

.stMainBlockContainer,
div[data-testid="stMainBlockContainer"] {
    background-color: var(--bg-primary) !important;
    max-width: 860px !important;
    margin: 0 auto !important;
    padding-top: 32px !important;
    padding-bottom: 140px !important;
}

/* ═══════════════════════════════════════════
   CHAT MESSAGES: USER LEFT, AI RIGHT
   ═══════════════════════════════════════════ */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 10px 16px !important;
    margin-bottom: 18px !important;
    width: 100% !important;
    gap: 14px !important;
}

/* User Message: LEFT Side, Compact Bubble */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]),
[data-testid="stChatMessage"][data-testid-kind="user"] {
    flex-direction: row !important;
    justify-content: flex-start !important;
    margin-right: auto !important;
    margin-left: 0 !important;
    max-width: 85% !important;
}

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"],
[data-testid="stChatMessage"][data-testid-kind="user"] [data-testid="stChatMessageContent"] {
    background-color: var(--bg-surface) !important;
    color: var(--text-primary) !important;
    padding: 11px 16px !important;
    border-radius: 16px 16px 16px 4px !important;
    border: 1px solid var(--border-subtle) !important;
    max-width: fit-content !important;
    margin-left: 0 !important;
    margin-right: auto !important;
    text-align: left !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15) !important;
    word-break: break-word !important;
}

/* AI Assistant Message: RIGHT Side, Natural Conversational Text */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]),
[data-testid="stChatMessage"][data-testid-kind="assistant"] {
    flex-direction: row-reverse !important;
    justify-content: flex-start !important;
    margin-left: auto !important;
    margin-right: 0 !important;
    max-width: 88% !important;
}

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stChatMessageContent"],
[data-testid="stChatMessage"][data-testid-kind="assistant"] [data-testid="stChatMessageContent"] {
    background-color: transparent !important;
    color: var(--text-primary) !important;
    padding: 4px 10px !important;
    max-width: 780px !important;
    margin-left: auto !important;
    margin-right: 0 !important;
    text-align: left !important;
    border: none !important;
    box-shadow: none !important;
}

/* Typography inside Messages */
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
    font-size: 15px !important;
    line-height: 1.7 !important;
    color: var(--text-primary) !important;
}

[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {
    color: var(--text-primary) !important;
    margin-bottom: 12px !important;
}

[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p:last-child {
    margin-bottom: 0 !important;
}

[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] ul,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] ol {
    margin: 8px 0 14px 0 !important;
    padding-left: 22px !important;
}

[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li {
    margin-bottom: 6px !important;
    color: var(--text-primary) !important;
}

[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] strong {
    color: #FFFFFF !important;
    font-weight: 600 !important;
}

/* Avatars */
[data-testid="chatAvatarIcon-assistant"],
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stChatMessageAvatar"] {
    background: linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%) !important;
    border-radius: 50% !important;
    color: #FFFFFF !important;
    width: 32px !important;
    height: 32px !important;
    min-width: 32px !important;
    box-shadow: 0 0 14px var(--accent-glow) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

[data-testid="chatAvatarIcon-user"],
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageAvatar"] {
    background: #3F3F46 !important;
    border-radius: 50% !important;
    color: #FFFFFF !important;
    width: 32px !important;
    height: 32px !important;
    min-width: 32px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* ═══════════════════════════════════════════
   EXPANDABLE SOURCES COMPONENT
   ═══════════════════════════════════════════ */
[data-testid="stExpander"] {
    background: rgba(255, 255, 255, 0.02) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-sm) !important;
    margin-top: 10px !important;
    max-width: fit-content !important;
    transition: all 0.2s ease !important;
}

[data-testid="stExpander"]:hover {
    border-color: var(--border-hover) !important;
    background: rgba(255, 255, 255, 0.04) !important;
}

[data-testid="stExpander"] summary {
    font-size: 12px !important;
    color: var(--text-secondary) !important;
    padding: 6px 12px !important;
    cursor: pointer !important;
    font-weight: 500 !important;
    list-style: none !important;
}

[data-testid="stExpander"] summary:hover {
    color: var(--text-primary) !important;
}

[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    padding: 8px 12px !important;
    border-top: 1px solid var(--border-subtle) !important;
}

[data-testid="stExpander"] [data-testid="stMarkdownContainer"] {
    font-size: 12.5px !important;
    color: var(--text-secondary) !important;
    line-height: 1.6 !important;
}

/* ═══════════════════════════════════════════
   WELCOME / EMPTY STATE
   ═══════════════════════════════════════════ */
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 60px 16px 24px 16px;
    max-width: 640px;
    margin: 0 auto;
}

.greeting-icon {
    width: 52px;
    height: 52px;
    border-radius: 16px;
    background: linear-gradient(135deg, #8B5CF6 0%, #6D28D9 50%, #4C1D95 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    margin-bottom: 18px;
    box-shadow: 0 0 28px rgba(139, 92, 246, 0.35);
    animation: float-pulse 3s ease-in-out infinite;
}

@keyframes float-pulse {
    0%, 100% { transform: translateY(0); box-shadow: 0 0 28px rgba(139, 92, 246, 0.35); }
    50% { transform: translateY(-5px); box-shadow: 0 0 36px rgba(139, 92, 246, 0.5); }
}

.greeting-title {
    font-size: 26px;
    font-weight: 700;
    color: #FFFFFF;
    margin: 0 0 8px 0;
    letter-spacing: -0.5px;
}

.greeting-sub {
    font-size: 14.5px;
    color: var(--text-secondary);
    margin: 0 0 32px 0;
    line-height: 1.55;
    max-width: 480px;
}

/* ═══════════════════════════════════════════
   SUGGESTION BUTTONS
   ═══════════════════════════════════════════ */
div[data-testid="stHorizontalBlock"] .stButton > button {
    background: var(--bg-surface) !important;
    color: var(--text-secondary) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 12px !important;
    font-size: 13px !important;
    font-weight: 400 !important;
    padding: 12px 14px !important;
    text-align: left !important;
    height: auto !important;
    min-height: 56px !important;
    white-space: normal !important;
    line-height: 1.4 !important;
    transition: all 0.2s ease !important;
}

div[data-testid="stHorizontalBlock"] .stButton > button:hover {
    background: var(--bg-hover) !important;
    border-color: var(--accent) !important;
    color: #FFFFFF !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35), 0 0 0 1px var(--accent) !important;
}

/* ═══════════════════════════════════════════
   FLOATING BOTTOM CHAT INPUT
   ═══════════════════════════════════════════ */
[data-testid="stBottom"],
[data-testid="stBottom"] > div,
div[data-testid="stBottomBlockContainer"],
div[data-testid="stBottomBlockContainer"] > div {
    background-color: var(--bg-primary) !important;
    border-top: 1px solid var(--border-subtle) !important;
    padding-bottom: 20px !important;
}

.stChatInput,
[data-testid="stChatInput"],
[data-testid="stChatInputContainer"] {
    max-width: 760px !important;
    margin: 0 auto !important;
}

[data-testid="stChatInput"] > div,
.stChatInput > div {
    background-color: var(--bg-surface) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-lg) !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}

[data-testid="stChatInput"] > div:focus-within,
.stChatInput > div:focus-within {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px var(--accent-glow), 0 4px 20px rgba(0, 0, 0, 0.4) !important;
}

[data-testid="stChatInput"] textarea,
.stChatInput textarea {
    color: var(--text-primary) !important;
    background-color: transparent !important;
    font-size: 14.5px !important;
    caret-color: var(--accent) !important;
}

[data-testid="stChatInput"] textarea::placeholder,
.stChatInput textarea::placeholder {
    color: var(--text-muted) !important;
}

/* Send Button */
[data-testid="stChatInput"] button,
.stChatInput button {
    background-color: var(--bg-hover) !important;
    color: #FFFFFF !important;
    border-radius: 50% !important;
    border: none !important;
    transition: all 0.2s ease !important;
}

[data-testid="stChatInput"] button:hover {
    background-color: var(--accent) !important;
}

/* ═══════════════════════════════════════════
   SIDEBAR STYLING
   ═══════════════════════════════════════════ */
section[data-testid="stSidebar"] {
    background-color: var(--bg-secondary) !important;
    border-right: 1px solid var(--border-subtle) !important;
}

section[data-testid="stSidebar"] .block-container {
    padding: 16px 14px !important;
}

section[data-testid="stSidebar"] hr {
    border-color: var(--border-subtle) !important;
    margin: 12px 0 !important;
}

/* Action Buttons in Sidebar */
section[data-testid="stSidebar"] .stButton > button {
    background: var(--bg-surface) !important;
    color: var(--text-secondary) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-sm) !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    padding: 6px 10px !important;
    transition: all 0.15s ease !important;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    background: var(--bg-hover) !important;
    border-color: var(--border-hover) !important;
    color: var(--text-primary) !important;
}

/* Sidebar Metrics */
[data-testid="stMetric"] {
    background: var(--bg-surface) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-sm) !important;
    padding: 8px 10px !important;
}

[data-testid="stMetricValue"] {
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 16px !important;
}

[data-testid="stMetricLabel"] {
    color: var(--text-muted) !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.4px !important;
}

/* Task Item in Sidebar */
.task-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 10px;
    border-radius: 8px;
    margin-bottom: 4px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.04);
    transition: background 0.15s ease;
}

.task-item:hover {
    background: rgba(255, 255, 255, 0.05);
}

.task-status-dot {
    width: 8px;
    height: 8px;
    min-width: 8px;
    border-radius: 50%;
}

.dot-pending { background: var(--amber); box-shadow: 0 0 6px rgba(245, 158, 11, 0.5); }
.dot-progress { background: var(--blue); box-shadow: 0 0 6px rgba(59, 130, 246, 0.5); }
.dot-completed { background: var(--green); box-shadow: 0 0 6px rgba(16, 185, 129, 0.5); }

.task-label {
    font-size: 12.5px;
    color: var(--text-primary);
    flex: 1;
    line-height: 1.35;
}

.task-label-completed {
    font-size: 12.5px;
    color: var(--text-muted);
    text-decoration: line-through;
    flex: 1;
    line-height: 1.35;
}

.task-badge {
    font-size: 10px;
    font-weight: 600;
    padding: 2px 7px;
    border-radius: var(--radius-full);
    text-transform: uppercase;
    letter-spacing: 0.3px;
}

.badge-pending {
    background: rgba(245, 158, 11, 0.15);
    color: #FCD34D;
}

.badge-progress {
    background: rgba(59, 130, 246, 0.15);
    color: #93C5FD;
}

.badge-completed {
    background: rgba(16, 185, 129, 0.15);
    color: #6EE7B7;
}

/* Spinner & Scrollbars */
.stSpinner > div {
    border-top-color: var(--accent) !important;
}

::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}

::-webkit-scrollbar-track {
    background: transparent;
}

::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.12);
    border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.22);
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ==========================================
# INITIALIZE SESSION STATE & SERVICES
# ==========================================
def init_session_state():
    """Initialize persistent Streamlit session variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_history_objects" not in st.session_state:
        st.session_state.chat_history_objects = []
    if "groq_model" not in st.session_state:
        st.session_state.groq_model = Config.GROQ_MODEL
    if "api_key" not in st.session_state:
        st.session_state.api_key = Config.GROQ_API_KEY

init_session_state()

@st.cache_resource(show_spinner="Setting up knowledge base...")
def get_initialized_system():
    db.init_db()
    vectorstore = initialize_vectorstore()
    return vectorstore

try:
    vectorstore = get_initialized_system()
    doc_count = vectorstore._collection.count()
except Exception as e:
    st.error(f"System initialization notice: {e}")
    doc_count = 0


# ==========================================
# SIDEBAR: Task Tracker & Settings
# ==========================================
with st.sidebar:
    # Branding
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; padding: 4px 0 12px 0;">
        <div style="width: 30px; height: 30px; border-radius: 8px; background: linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%);
                    display: flex; align-items: center; justify-content: center; font-size: 15px;
                    box-shadow: 0 0 14px rgba(139, 92, 246, 0.35);">✨</div>
        <div>
            <div style="font-size: 14.5px; font-weight: 700; color: #ECECEC; letter-spacing: -0.2px;">HR Onboarding AI</div>
            <div style="font-size: 11px; color: #737373;">Acme Corp Assistant</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Action Buttons: Refresh & Clear
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("↻ Refresh", use_container_width=True):
            st.rerun()
    with col_btn2:
        if st.button("✕ Clear", use_container_width=True):
            st.session_state.messages = []
            st.session_state.chat_history_objects = []
            st.rerun()

    st.markdown("---")

    # Task metrics
    tasks = db.list_tasks()
    pending_count = len([t for t in tasks if t["status"] == "pending"])
    in_progress_count = len([t for t in tasks if t["status"] == "in_progress"])
    completed_count = len([t for t in tasks if t["status"] == "completed"])

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Pending", pending_count)
    col_m2.metric("Active", in_progress_count)
    col_m3.metric("Done", completed_count)

    st.markdown("")

    # Task list header
    st.markdown("<div style='font-size: 12px; font-weight: 600; color: #A0A0A0; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px;'>Onboarding Tasks</div>", unsafe_allow_html=True)

    # Task list items
    if not tasks:
        st.markdown("""
        <div style="text-align: center; padding: 16px 8px; color: #737373; font-size: 12.5px;">
            No tasks yet. Ask me to create your onboarding checklist!
        </div>
        """, unsafe_allow_html=True)
    else:
        for t in tasks:
            status = t["status"]
            if status == "completed":
                dot_cls = "dot-completed"
                label_cls = "task-label-completed"
                badge_cls = "badge-completed"
                badge_text = "Done"
            elif status == "in_progress":
                dot_cls = "dot-progress"
                label_cls = "task-label"
                badge_cls = "badge-progress"
                badge_text = "Active"
            else:
                dot_cls = "dot-pending"
                label_cls = "task-label"
                badge_cls = "badge-pending"
                badge_text = "Pending"

            st.markdown(f"""
            <div class="task-item">
                <div class="task-status-dot {dot_cls}"></div>
                <div class="{label_cls}">{t['title']}</div>
                <span class="task-badge {badge_cls}">{badge_text}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # Settings Expander
    with st.expander("⚙ Settings", expanded=False):
        current_key = os.getenv("GROQ_API_KEY", "") or st.session_state.api_key
        api_key_input = st.text_input(
            "API Key",
            value=current_key,
            type="password",
            help="Groq API Key — get at console.groq.com/keys"
        )
        if api_key_input != Config.GROQ_API_KEY:
            Config.GROQ_API_KEY = api_key_input
            st.session_state.api_key = api_key_input

        model_selected = st.selectbox(
            "Model",
            options=Config.AVAILABLE_MODELS,
            index=0 if Config.GROQ_MODEL not in Config.AVAILABLE_MODELS else Config.AVAILABLE_MODELS.index(Config.GROQ_MODEL)
        )
        if model_selected != Config.GROQ_MODEL:
            Config.GROQ_MODEL = model_selected
            st.session_state.groq_model = model_selected

        st.caption(f"{doc_count} document chunks indexed")
        if st.button("Re-index", use_container_width=True):
            initialize_vectorstore(force_reload=True)
            st.success("Knowledge base refreshed!")
            st.rerun()


# ==========================================
# MAIN AREA — EMPTY STATE OR CHAT
# ==========================================
has_messages = len(st.session_state.messages) > 0

preset_query = None

if not has_messages:
    # Empty State Welcome Screen
    st.markdown("""
    <div class="empty-state">
        <div class="greeting-icon">✨</div>
        <h1 class="greeting-title">HR Onboarding AI</h1>
        <p class="greeting-sub">
            Your assistant for a smooth onboarding experience. Ask me about benefits, IT setup, policies, or your onboarding tasks.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Clickable Suggestion Prompts
    suggestions = [
        ("🏥", "When can I enroll in health insurance?"),
        ("🔐", "How do I set up VPN access?"),
        ("📋", "What do I need to complete before my first day?"),
        ("📝", "What are my onboarding tasks?"),
    ]

    col1, col2 = st.columns(2)
    for i, (icon, text) in enumerate(suggestions):
        target_col = col1 if i % 2 == 0 else col2
        with target_col:
            if st.button(f"{icon}  {text}", key=f"sug_{i}", use_container_width=True):
                preset_query = text


# ==========================================
# CHAT MESSAGES DISPLAY (USER LEFT, AI RIGHT)
# ==========================================
for idx, msg in enumerate(st.session_state.messages):
    avatar_icon = "✨" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar_icon):
        st.markdown(msg["content"])

        # Subtle, Compact Expandable Sources for Assistant Messages
        sources = msg.get("sources") or []
        if sources and msg["role"] == "assistant":
            num_sources = len(sources)
            source_label = f"▸ {num_sources} source{'s' if num_sources > 1 else ''} referenced"
            with st.expander(source_label, expanded=False):
                for s in sources:
                    title = s.get("document_title", "HR Document")
                    page = s.get("page", 1)
                    st.markdown(f"{title} — Page {page}")


# ==========================================
# CHAT INPUT & EXECUTION
# ==========================================
user_input = st.chat_input("Ask anything about your onboarding...") or (preset_query if not has_messages else None)

if user_input:
    # 1. Append & render user message (LEFT)
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    # 2. Process with LangGraph Agent & render AI message (RIGHT)
    with st.chat_message("assistant", avatar="✨"):
        with st.spinner("Thinking..."):
            try:
                result = run_agent(
                    query=user_input,
                    chat_history=st.session_state.chat_history_objects
                )

                response_text = result.get("response", "I couldn't process your request.")
                sources = result.get("sources", [])

                # Render clean AI response
                st.markdown(response_text)

                # Render subtle expandable sources
                if sources:
                    num_sources = len(sources)
                    source_label = f"▸ {num_sources} source{'s' if num_sources > 1 else ''} referenced"
                    with st.expander(source_label, expanded=False):
                        for s in sources:
                            title = s.get("document_title", "HR Document")
                            page = s.get("page", 1)
                            st.markdown(f"{title} — Page {page}")

                # Store message in session
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "sources": sources
                })

                # Maintain LangChain memory
                st.session_state.chat_history_objects.append(HumanMessage(content=user_input))
                st.session_state.chat_history_objects.append(AIMessage(content=response_text))

                st.rerun()

            except Exception as e:
                friendly_error = "Sorry, I couldn't process that request. Please try again."
                st.markdown(friendly_error)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": friendly_error,
                    "sources": []
                })
                print(f"Agent execution error: {e}")
