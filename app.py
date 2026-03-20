import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv

from src.agents.orchestrator import build_graph

load_dotenv()

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FPL Agent",
    page_icon=":soccer:",
    layout="wide",
)

# ── FPL-themed CSS ───────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ---------- colour tokens (FPL official palette) ---------- */
:root {
    --fpl-purple-dark: #37003C;
    --fpl-purple:      #963CFF;
    --fpl-green:       #00FF87;
    --fpl-cyan:        #04F5FF;
    --fpl-white:       #FFFFFF;
    --fpl-bg:          #1A0024;
    --fpl-card:        #2D0033;
    --fpl-text:        #E8E0EB;
    --fpl-muted:       #A89BAD;
}

/* ---------- main app background ---------- */
.stApp, [data-testid="stAppViewContainer"] {
    background: linear-gradient(170deg, var(--fpl-bg) 0%, #0D001A 100%) !important;
}

.stApp header, [data-testid="stHeader"] {
    background: transparent !important;
}

/* ---------- sidebar ---------- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--fpl-purple-dark) 0%, #1A0024 100%) !important;
    border-right: 1px solid rgba(0,255,135,0.15);
}

section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown li,
section[data-testid="stSidebar"] .stMarkdown label,
section[data-testid="stSidebar"] label {
    color: var(--fpl-text) !important;
}

/* ---------- titles ---------- */
h1 {
    background: linear-gradient(90deg, var(--fpl-green), var(--fpl-cyan)) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    font-weight: 900 !important;
    letter-spacing: -0.5px !important;
}

h2, h3 {
    color: var(--fpl-green) !important;
}

/* ---------- tabs ---------- */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    border-bottom: 2px solid rgba(150,60,255,0.3);
}

.stTabs [data-baseweb="tab"] {
    color: var(--fpl-muted) !important;
    background: transparent !important;
    border-radius: 8px 8px 0 0;
    padding: 10px 24px;
    font-weight: 600;
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
    color: var(--fpl-green) !important;
    border-bottom: 3px solid var(--fpl-green);
    background: rgba(0,255,135,0.05) !important;
}

/* ---------- chat messages ---------- */
[data-testid="stChatMessage"] {
    background: var(--fpl-card) !important;
    border: 1px solid rgba(150,60,255,0.2) !important;
    border-radius: 12px !important;
    padding: 16px !important;
    margin-bottom: 12px !important;
}

[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] span {
    color: var(--fpl-text) !important;
}

/* user messages: subtle green left border */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    border-left: 3px solid var(--fpl-green) !important;
}

/* assistant messages: subtle purple left border */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    border-left: 3px solid var(--fpl-purple) !important;
}

/* ---------- chat input (bottom bar) ---------- */
[data-testid="stBottom"] {
    background: var(--fpl-bg) !important;
    border-top: 1px solid rgba(150,60,255,0.2);
}

[data-testid="stChatInput"],
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] div,
[data-testid="stChatInput"] form,
[data-testid="stChatInput"] [data-baseweb],
[data-testid="stChatInput"] [data-baseweb] > div {
    background: var(--fpl-card) !important;
    background-color: var(--fpl-card) !important;
    border-color: rgba(150,60,255,0.35) !important;
}

[data-testid="stChatInput"]:focus-within,
[data-testid="stChatInput"]:focus-within > div,
[data-testid="stChatInput"]:focus-within div {
    border-color: var(--fpl-green) !important;
    box-shadow: none !important;
}

[data-testid="stChatInput"] textarea {
    color: var(--fpl-white) !important;
    background: transparent !important;
    caret-color: var(--fpl-green) !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: var(--fpl-muted) !important;
}

/* send button */
[data-testid="stChatInput"] button,
[data-testid="stChatInput"] button svg {
    color: var(--fpl-green) !important;
    background: transparent !important;
}

/* ---------- expanders (tool calls tab) ---------- */
.streamlit-expanderHeader {
    background: var(--fpl-card) !important;
    color: var(--fpl-cyan) !important;
    border: 1px solid rgba(4,245,255,0.15) !important;
    border-radius: 8px !important;
    font-family: 'SF Mono', 'Fira Code', monospace !important;
    font-size: 0.85em !important;
}

.streamlit-expanderContent {
    background: rgba(45,0,51,0.6) !important;
    border: 1px solid rgba(4,245,255,0.1) !important;
    border-top: none !important;
    border-radius: 0 0 8px 8px !important;
}

/* ---------- info boxes ---------- */
[data-testid="stAlert"] {
    background: var(--fpl-card) !important;
    border: 1px solid rgba(150,60,255,0.2) !important;
    color: var(--fpl-text) !important;
}

/* ---------- spinner ---------- */
.stSpinner > div {
    border-top-color: var(--fpl-green) !important;
}

/* ---------- general text ---------- */
.stMarkdown p, .stMarkdown li, .stCaption, .stText {
    color: var(--fpl-text) !important;
}

/* ---------- scrollbar ---------- */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--fpl-bg); }
::-webkit-scrollbar-thumb {
    background: rgba(150,60,255,0.4);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: var(--fpl-purple); }

/* ---------- sidebar logo container ---------- */
.logo-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 1rem 0 1.5rem 0;
    border-bottom: 1px solid rgba(0,255,135,0.15);
    margin-bottom: 1.5rem;
}

.logo-container img {
    width: 120px;
    height: 120px;
}

.logo-tagline {
    color: var(--fpl-muted);
    font-size: 0.75rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 0.5rem;
}
</style>
""", unsafe_allow_html=True)


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div class="logo-container">
            <img src="app/static/logo.svg" alt="FPL Agent" onerror="this.style.display='none'"/>
            <div class="logo-tagline">AI-Powered FPL Assistant</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # Also show with st.image as fallback (works reliably)
    try:
        st.image("assets/logo.svg", width=140)
    except Exception:
        pass

    st.markdown("---")
    st.markdown("**How it works**")
    st.markdown(
        "Ask anything about FPL. The agent searches **podcast transcripts** "
        "and the **official FPL API** to give you informed answers."
    )

# ── State init ───────────────────────────────────────────────────────────────
if "graph" not in st.session_state:
    st.session_state.graph = build_graph()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_tool_calls" not in st.session_state:
    st.session_state.last_tool_calls = []

# ── Main layout ──────────────────────────────────────────────────────────────
st.title("FPL Agent")

tab_chat, tab_context = st.tabs(["Chat", "Tool calls"])

# chat_input MUST be at the top level (outside tabs) so Streamlit pins it to the bottom
prompt = st.chat_input("Ask about FPL...")

with tab_chat:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        graph = st.session_state.graph

        # Build LangGraph message history
        lc_messages = []
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = graph.invoke({"messages": lc_messages})

            # Extract the final AI message
            ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage) and m.content and not m.tool_calls]
            final_response = ai_messages[-1].content if ai_messages else "I couldn't generate a response."

            # Collect tool call info for the context tab
            tool_calls_info = []
            for m in result["messages"]:
                if hasattr(m, "tool_calls") and m.tool_calls:
                    for tc in m.tool_calls:
                        tool_calls_info.append({
                            "tool": tc["name"],
                            "args": tc["args"],
                        })
                # ToolMessages contain the results
                if m.type == "tool":
                    for tc_info in tool_calls_info:
                        if tc_info["tool"] == m.name and "result" not in tc_info:
                            tc_info["result"] = m.content
                            break

            st.session_state.last_tool_calls = tool_calls_info
            st.markdown(final_response)

        st.session_state.messages.append({"role": "assistant", "content": final_response})

with tab_context:
    if st.session_state.last_tool_calls:
        for i, tc in enumerate(st.session_state.last_tool_calls):
            with st.expander(f"#{i+1} — {tc['tool']}({', '.join(f'{k}={v!r}' for k, v in tc['args'].items())})"):
                st.text(tc.get("result", "No result captured"))
    else:
        st.info("Send a message in the Chat tab to see tool calls here.")
