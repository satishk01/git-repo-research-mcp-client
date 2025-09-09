#!/usr/bin/env python

import streamlit as st
import logging
import asyncio
from datetime import datetime
from typing import Dict, List

from config import Config
from agent_manager import AgentManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "github_token" not in st.session_state:
        st.session_state.github_token = ""
    
    if "agent_manager" not in st.session_state:
        st.session_state.agent_manager = None
    
    if "agent_initialized" not in st.session_state:
        st.session_state.agent_initialized = False
    
    if "query_history" not in st.session_state:
        st.session_state.query_history = []
    
    if "current_tools" not in st.session_state:
        st.session_state.current_tools = []

def setup_page_config():
    """Configure Streamlit page settings."""
    st.set_page_config(**Config.PAGE_CONFIG)

def render_sidebar():
    """Render the sidebar with configuration options."""
    with st.sidebar:
        st.header("Configuration")
        
        # GitHub Token Input
        st.subheader("GitHub Authentication")
        github_token = st.text_input(
            "GitHub Access Token",
            type="password",
            value=st.session_state.github_token,
            help="Enter your GitHub personal access token for repository access"
        )
        
        if github_token != st.session_state.github_token:
            st.session_state.github_token = github_token
            st.session_state.agent_initialized = False
            st.rerun()
        
        # Connection Status
        st.subheader("Connection Status")
        if st.session_state.agent_manager:
            status = st.session_state.agent_manager.get_connection_status()
            
            st.write("🤖 Agent:", "✅ Ready" if status["agent_initialized"] else "❌ Not Ready")
            st.write("🧠 Bedrock:", "✅ Connected" if status["bedrock_model"] else "❌ Disconnected")
            st.write("🔧 MCP Server:", "✅ Connected" if status["mcp_connected"] else "❌ Disconnected")
            st.write("🔑 GitHub Token:", "✅ Set" if status["github_token_set"] else "❌ Not Set")
        else:
            st.write("🤖 Agent: ❌ Not Initialized")
            st.write("🧠 Bedrock: ❌ Not Connected")
            st.write("🔧 MCP Server: ❌ Not Connected")
            st.write("🔑 GitHub Token: ❌ Not Set")
        
        # Available Tools
        if st.session_state.current_tools:
            st.subheader("Available Tools")
            st.write(f"📊 {len(st.session_state.current_tools)} tools available")
            
            with st.expander("View Tools"):
                for tool in st.session_state.current_tools:
                    tool_name = tool.get('name', 'Unknown')
                    tool_desc = tool.get('description', 'No description')
                    st.write(f"**{tool_name}**")
                    st.write(tool_desc)
                    st.write("---")

def initialize_agent():
    """Initialize the agent manager and agent."""
    try:
        with st.spinner("Initializing AI agent and connecting to services..."):
            # Create agent manager
            st.session_state.agent_manager = AgentManager(st.session_state.github_token)
            
            # Initialize agent (async)
            asyncio.run(st.session_state.agent_manager.initialize_agent())
            
            # Get available tools (async)
            st.session_state.current_tools = asyncio.run(st.session_state.agent_manager.get_available_tools())
            
            st.session_state.agent_initialized = True
            st.success("✅ Agent initialized successfully!")
            
    except Exception as e:
        st.error(f"❌ Failed to initialize agent: {str(e)}")
        logger.error(f"Agent initialization failed: {str(e)}")
        st.session_state.agent_initialized = False

def render_main_interface():
    """Render the main application interface."""
    st.title(Config.APP_TITLE)
    st.markdown(Config.APP_DESCRIPTION)
    
    # Check if agent needs initialization
    if not st.session_state.agent_initialized or not st.session_state.agent_manager:
        st.info("🚀 Click the button below to initialize the AI agent and connect to services.")
        
        if st.button("Initialize Agent", type="primary"):
            initialize_agent()
        
        # Show token requirement message
        if not st.session_state.github_token:
            st.warning("⚠️ For full functionality, please provide a GitHub access token in the sidebar.")
        
        return
    
    # Main query interface
    st.subheader("Ask about Git repositories")
    
    # Example queries
    with st.expander("💡 Example Queries"):
        st.markdown("""
        - Analyze the structure of repository https://github.com/user/repo
        - What are the main dependencies in this project?
        - Show me the recent commit activity and contributors
        - What security issues might exist in this codebase?
        - Compare the architecture of two similar repositories
        - What are the most active files in this repository?
        """)
    
    # Query input
    query = st.text_area(
        "Enter your question about Git repositories:",
        height=100,
        placeholder="e.g., Analyze the repository structure of https://github.com/microsoft/vscode"
    )
    
    # Submit button
    col1, col2 = st.columns([1, 4])
    with col1:
        submit_button = st.button("🔍 Analyze", type="primary", disabled=not query.strip())
    
    with col2:
        if st.button("🔄 Reinitialize Agent"):
            st.session_state.agent_initialized = False
            st.rerun()
    
    # Process query
    if submit_button and query.strip():
        process_query(query.strip())

def process_query(query: str):
    """Process a user query and display results."""
    try:
        with st.spinner("🤖 Analyzing repository... This may take a moment."):
            # Process query with agent (async)
            response = asyncio.run(st.session_state.agent_manager.process_query(query))
            
            # Create query record (async)
            query_record = asyncio.run(st.session_state.agent_manager.create_query_record(
                query, response, success=True
            ))
            
            # Add to history
            st.session_state.query_history.append(query_record)
            
            # Display results
            st.subheader("📊 Analysis Results")
            st.markdown(response)
            
            # Add timestamp
            st.caption(f"Analysis completed at {query_record['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
            
    except Exception as e:
        error_msg = f"Failed to process query: {str(e)}"
        st.error(f"❌ {error_msg}")
        logger.error(error_msg)
        
        # Add error to history (async)
        error_record = asyncio.run(st.session_state.agent_manager.create_query_record(
            query, error_msg, success=False
        ))
        st.session_state.query_history.append(error_record)

def render_query_history():
    """Render query history section."""
    if st.session_state.query_history:
        st.subheader("📝 Query History")
        
        for i, record in enumerate(reversed(st.session_state.query_history[-5:])):  # Show last 5
            with st.expander(f"Query {len(st.session_state.query_history) - i}: {record['query'][:50]}..."):
                st.write("**Query:**", record['query'])
                st.write("**Response:**", record['response'])
                st.write("**Time:**", record['timestamp'].strftime('%Y-%m-%d %H:%M:%S'))
                st.write("**Status:**", "✅ Success" if record['success'] else "❌ Error")

def main():
    """Main application function."""
    setup_page_config()
    initialize_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Render main interface
    render_main_interface()
    
    # Render query history
    if st.session_state.query_history:
        st.markdown("---")
        render_query_history()
    
    # Cleanup on app termination
    if st.session_state.agent_manager:
        # Note: Streamlit doesn't have a reliable way to detect app termination
        # Cleanup will happen when session expires
        pass

if __name__ == "__main__":
    main()