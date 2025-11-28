"""
Minimal Streamlit App for Restaurant Chain Advisor
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.enhanced_orchestrator import EnhancedAgentOrchestrator
from kb.mongodb_kb import MongoKnowledgeBase
from kg.neo4j_kg import Neo4jKnowledgeGraph
from utils.auth import authenticate_user, create_user

# Page configuration
st.set_page_config(
    page_title="Restaurant Chain Advisor",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for minimal design
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 600;
        color: #1f1f1f;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .stTextInput > div > div > input {
        border-radius: 5px;
    }
    .stButton > button {
        border-radius: 5px;
        width: 100%;
    }
    .source-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 5px;
        border-left: 3px solid #007bff;
        margin-top: 1rem;
    }
    .response-box {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 5px;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = None
if "messages" not in st.session_state:
    st.session_state.messages = []

def initialize_system():
    """Initialize the orchestrator and knowledge bases"""
    if st.session_state.orchestrator is None:
        with st.spinner("Initializing system..."):
            try:
                kb = MongoKnowledgeBase()
                kg = Neo4jKnowledgeGraph()
                st.session_state.orchestrator = EnhancedAgentOrchestrator(kb, kg)
                return True
            except Exception as e:
                st.error(f"Failed to initialize system: {str(e)}")
                return False
    return True

def login_page():
    """Display login page"""
    st.markdown('<div class="main-header">Restaurant Chain Advisor</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AI-powered location and market intelligence for restaurant chains</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if username and password:
                    user = authenticate_user(username, password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.warning("Please enter both username and password")
    
    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            full_name = st.text_input("Full Name")
            role = st.selectbox("Role", ["basic", "premium", "admin"])
            submit_reg = st.form_submit_button("Register")
            
            if submit_reg:
                if new_username and new_password and full_name:
                    if create_user(new_username, new_password, role, full_name):
                        st.success("Account created successfully! Please login.")
                    else:
                        st.error("Username already exists")
                else:
                    st.warning("Please fill in all fields")

def main_app():
    """Display main application interface"""
    # Initialize system
    if not initialize_system():
        return
    
    # Sidebar
    with st.sidebar:
        st.markdown("### User Information")
        st.write(f"**Name:** {st.session_state.user.get('full_name', 'N/A')}")
        st.write(f"**Role:** {st.session_state.user.get('role', 'basic').title()}")
        
        st.markdown("---")
        
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.messages = []
            st.rerun()
        
        st.markdown("---")
        st.markdown("### Quick Help")
        st.markdown("""
        **Example queries:**
        - Find best location for Chinese restaurant in Chennai
        - What regulations for opening restaurant in Mumbai?
        - Market analysis for Italian restaurant in Bangalore
        - Demographics of T Nagar area
        """)
    
    # Main content
    st.markdown('<div class="main-header">Restaurant Chain Advisor</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Ask questions about locations, regulations, and market insights</div>', unsafe_allow_html=True)
    
    # Chat history
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
        else:
            with st.chat_message("assistant"):
                st.markdown(f'<div class="response-box">{message["content"]}</div>', unsafe_allow_html=True)
    
    # Query input
    query = st.chat_input("Ask your question here...")
    
    if query:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": query})
        
        # Display user message
        with st.chat_message("user"):
            st.write(query)
        
        # Get response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                try:
                    response = st.session_state.orchestrator.run(
                        query, 
                        st.session_state.user
                    )
                    
                    # Display response
                    st.markdown(f'<div class="response-box">{response}</div>', unsafe_allow_html=True)
                    
                    # Store assistant message
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    error_msg = f"Error processing query: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Main application logic
if st.session_state.authenticated:
    main_app()
else:
    login_page()
