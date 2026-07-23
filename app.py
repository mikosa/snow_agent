import streamlit as st
import pandas as pd
import json
from pathlib import Path
from config import get_settings
from db.database import get_engine, init_db, SessionLocal
from core.agent import Agent, AgentResponse
from core.llm_client import LLMClient
from core.parser import ToolCallParser
from core.session import SessionManager, SessionData, DataState
from core.tool_registry import ToolRegistry
from storage.file_store import FileStore
from storage.exporters import generate_export_csv, generate_export_json, generate_export_excel
from tools import register_all_tools
import plotly.express as px

# Page config
st.set_page_config(page_title="Operations Analysis Agent", page_icon="⚙️", layout="wide")

# Initialize once
@st.cache_resource
def init_app():
    settings = get_settings()
    engine = get_engine(settings.db_path)
    init_db(engine)
    file_store = FileStore(settings.data_dir)
    llm_client = LLMClient(settings.llm_base_url, settings.llm_headers, settings.llm_timeout)
    parser = ToolCallParser()
    registry = ToolRegistry()
    register_all_tools(registry)
    session_mgr = SessionManager(SessionLocal, file_store)
    agent = Agent(llm_client, registry, session_mgr, parser, settings)
    return settings, file_store, session_mgr, agent

try:
    settings, file_store, session_mgr, agent = init_app()
except Exception as e:
    st.error(f"Failed to initialize app: {e}")
    # Continue with mock setup for UI demo purposes if dependencies are missing during phase 4
    class MockDataState:
        def __init__(self):
            self.row_count = 0
            self.column_count = 0
            self.is_cleaned = False
            self.is_entities_extracted = False
            self.is_embedded = False
            self.is_clustered = False
            self.is_categorized = False
            self.is_subcategorized = False
            
    if "session_id" not in st.session_state:
        st.session_state.session_id = "mock_id"
        st.session_state.conversation_history = []
        st.session_state.data_state = MockDataState()
        st.session_state.artifacts = {}

if "session_id" not in st.session_state:
    session_data = session_mgr.create_session("Default")
    st.session_state.session_id = session_data.id
    st.session_state.conversation_history = []
    st.session_state.data_state = DataState()
    st.session_state.artifacts = {}

# Sidebar
st.sidebar.title("⚙️ Operations Analysis Agent")

uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
if uploaded_file is not None:
    if "uploaded" not in st.session_state or st.session_state.uploaded != uploaded_file.name:
        st.session_state.uploaded = uploaded_file.name
        st.sidebar.success(f"Uploaded {uploaded_file.name}")
        df = pd.read_csv(uploaded_file)
        st.sidebar.subheader("Data Preview")
        st.sidebar.dataframe(df.head())
        
        st.session_state.data_state.row_count = len(df)
        st.session_state.data_state.column_count = len(df.columns)
        st.session_state.df = df

st.sidebar.subheader("Data Context")
col1, col2 = st.sidebar.columns(2)
col1.metric("Rows", getattr(st.session_state.data_state, "row_count", 0))
col2.metric("Columns", getattr(st.session_state.data_state, "column_count", 0))

st.sidebar.subheader("Pipeline Status")
def get_status_icon(is_complete):
    return "✅" if is_complete else "⬜"

st.sidebar.write(f"{get_status_icon(getattr(st.session_state.data_state, 'is_cleaned', False))} Clean & Scrub")
st.sidebar.write(f"{get_status_icon(getattr(st.session_state.data_state, 'is_entities_extracted', False))} Extract Entities")
st.sidebar.write(f"{get_status_icon(getattr(st.session_state.data_state, 'is_embedded', False))} Embed Data")
st.sidebar.write(f"{get_status_icon(getattr(st.session_state.data_state, 'is_clustered', False))} Cluster")
st.sidebar.write(f"{get_status_icon(getattr(st.session_state.data_state, 'is_categorized', False))} Categorize")
st.sidebar.write(f"{get_status_icon(getattr(st.session_state.data_state, 'is_subcategorized', False))} Subcategorize")

st.sidebar.subheader("Session Management")
sessions = ["Default"]
selected_session = st.sidebar.selectbox("Select Session", sessions)
if st.sidebar.button("+ New Session"):
    st.sidebar.success("Created new session!")

if getattr(st.session_state.data_state, "is_cleaned", False) or (uploaded_file is not None):
    st.sidebar.subheader("Export")
    
    session_data = session_mgr.get_session(st.session_state.session_id)
    
    csv_data = generate_export_csv(session_data, file_store)
    if csv_data:
        st.sidebar.download_button("Download CSV", data=csv_data, file_name=f"analysis_{session_data.id}.csv", mime="text/csv")
        
    json_data = generate_export_json(session_data, file_store)
    if json_data:
        st.sidebar.download_button("Download JSON", data=json_data, file_name=f"analysis_{session_data.id}.json", mime="application/json")
        
    excel_data = generate_export_excel(session_data, file_store)
    if excel_data:
        st.sidebar.download_button("Download Excel", data=excel_data, file_name=f"analysis_{session_data.id}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Main Layout
col_chat, col_results = st.columns([3, 2])

with col_chat:
    st.subheader("Conversation")
    
    if len(st.session_state.conversation_history) == 0:
        st.info("Welcome to the Operations Analysis Agent! Please upload a CSV to get started, or ask a question.")

    for msg in st.session_state.conversation_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if prompt := st.chat_input("Ask something about the data or run a tool..."):
        st.session_state.conversation_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.status("Processing...", expanded=True) as status:
                def status_callback(msg):
                    st.write(msg)
                
                placeholder = st.empty()
                # Here we would call agent.handle_message
                # agent.handle_message(prompt, st.session_state.session_id, status_callback)
                response_text = f"I've received your request: '{prompt}'. This is a mock response from the agent."
                placeholder.markdown(response_text)
                status.update(label="Complete", state="complete", expanded=False)
                
        st.session_state.conversation_history.append({"role": "assistant", "content": response_text})

with col_results:
    st.subheader("Results")
    
    if getattr(st.session_state.data_state, "is_categorized", False):
        st.write("### Categories")
        with st.expander("Hardware Issue (42 tickets)"):
            st.write("- Laptop won't boot (12)")
            st.write("- Monitor broken (30)")
    
    if getattr(st.session_state.data_state, "is_clustered", False):
        st.write("### Clusters")
        df_pie = pd.DataFrame({'Cluster': ['C1', 'C2', 'C3'], 'Count': [10, 20, 30]})
        fig = px.pie(df_pie, values='Count', names='Cluster')
        st.plotly_chart(fig, use_container_width=True)
        
    if getattr(st.session_state.data_state, "is_entities_extracted", False):
        st.write("### Top Entities")
        st.metric("SystemX", "15 mentions")
        st.metric("AppY", "8 mentions")
        
    if getattr(st.session_state.data_state, "is_cleaned", False) or ("df" in st.session_state):
        with st.expander("Data Preview", expanded=True):
            if "df" in st.session_state:
                st.dataframe(st.session_state.df.head(50))
            else:
                st.write("Data loaded.")
