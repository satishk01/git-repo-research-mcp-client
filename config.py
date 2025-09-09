#!/usr/bin/env python

import os
from typing import List

class Config:
    """Configuration settings for the Git Repository Research Streamlit application."""
    
    # AWS Bedrock Configuration
    BEDROCK_REGION = os.getenv("BEDROCK_REGION", "us-east-1")
    BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.amazon.nova-pro-v1:0")
    AWS_PROFILE = os.getenv("AWS_PROFILE", "default")
    
    # MCP Server Configuration
    MCP_SERVER_COMMAND = "uvx"
    MCP_SERVER_ARGS = ["awslabs.git-repo-research-mcp-server@latest"]
    
    # Application Settings
    APP_TITLE = "Git Repository Research Assistant"
    APP_DESCRIPTION = "AI-powered Git repository analysis using Amazon Nova Pro"
    
    # Bedrock Model Configuration
    MAX_TOKENS = 4096
    TEMPERATURE = 0.1
    READ_TIMEOUT = 120
    CONNECT_TIMEOUT = 120
    MAX_RETRIES = 3
    
    # MCP Environment Variables
    MCP_ENV_VARS = {
        "AWS_PROFILE": "default",
        "AWS_REGION": "us-east-1",
        "FASTMCP_LOG_LEVEL": "ERROR"
    }
    
    # Streamlit Configuration
    PAGE_CONFIG = {
        "page_title": APP_TITLE,
        "page_icon": "🔍",
        "layout": "wide",
        "initial_sidebar_state": "expanded"
    }