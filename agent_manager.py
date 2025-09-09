#!/usr/bin/env python

import logging
from typing import Optional, List, Dict
from datetime import datetime

from botocore.config import Config as BotoConfig
from strands import Agent
from strands.models.bedrock import BedrockModel

from config import Config
from mcp_integration import MCPIntegration

logger = logging.getLogger(__name__)

class AgentManager:
    """Manages Strands Agent lifecycle and configuration for Git Repository Research."""
    
    def __init__(self, github_token: Optional[str] = None):
        """Initialize agent manager with optional GitHub token."""
        self.github_token = github_token
        self.agent = None
        self.mcp_integration = None
        self.model = None
        self._initialized = False
        
    def initialize_agent(self) -> Agent:
        """Initialize and return the Strands Agent with Bedrock model and MCP tools."""
        try:
            # Initialize Bedrock model
            self.model = BedrockModel(
                model_id=Config.BEDROCK_MODEL_ID,
                max_tokens=Config.MAX_TOKENS,
                boto_client_config=BotoConfig(
                    read_timeout=Config.READ_TIMEOUT,
                    connect_timeout=Config.CONNECT_TIMEOUT,
                    retries=dict(max_attempts=Config.MAX_RETRIES, mode="adaptive"),
                ),
                temperature=Config.TEMPERATURE
            )
            
            # Initialize MCP integration
            self.mcp_integration = MCPIntegration(self.github_token)
            mcp_client = self.mcp_integration.setup_client()
            
            # Get available tools
            tools = self.mcp_integration.list_tools()
            
            # Create system prompt
            system_prompt = self._create_system_prompt()
            
            # Initialize Strands Agent
            self.agent = Agent(
                system_prompt=system_prompt,
                model=self.model,
                tools=tools
            )
            
            self._initialized = True
            logger.info("Strands Agent initialized successfully with Bedrock and MCP tools")
            return self.agent
            
        except Exception as e:
            logger.error(f"Failed to initialize agent: {str(e)}")
            raise
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for the Git Repository Research agent."""
        return """You are a Git Repository Research assistant with access to comprehensive repository analysis tools.

Use the available tools to:
- Analyze Git repositories and their structure
- Research code patterns, dependencies, and architecture
- Examine commit history, contributors, and development patterns
- Investigate issues, pull requests, and project documentation
- Provide insights on code quality, security, and best practices
- Compare repositories and analyze trends

When analyzing repositories:
1. Always provide clear, actionable insights
2. Use multiple tools to get comprehensive information
3. Explain technical concepts in an accessible way
4. Highlight important findings and potential issues
5. Suggest improvements or next steps when appropriate

Provide accurate analysis based on the repository data and research tools available."""
    
    def process_query(self, query: str) -> str:
        """Process a user query using the initialized agent."""
        if not self._initialized or not self.agent:
            raise RuntimeError("Agent not initialized. Call initialize_agent() first.")
        
        try:
            logger.info(f"Processing query: {query[:100]}...")
            response = self.agent(query)
            logger.info("Query processed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Failed to process query: {str(e)}")
            raise
    
    def get_available_tools(self) -> List[Dict]:
        """Get list of available MCP tools."""
        if not self.mcp_integration:
            return []
        
        try:
            return self.mcp_integration.list_tools()
        except Exception as e:
            logger.error(f"Failed to get available tools: {str(e)}")
            return []
    
    def update_github_token(self, token: str):
        """Update GitHub token and reinitialize agent if needed."""
        self.github_token = token
        
        if self.mcp_integration:
            try:
                self.mcp_integration.update_github_token(token)
                # Reinitialize agent with updated MCP client
                if self._initialized:
                    self.initialize_agent()
                logger.info("GitHub token updated successfully")
            except Exception as e:
                logger.error(f"Failed to update GitHub token: {str(e)}")
                raise
    
    def is_initialized(self) -> bool:
        """Check if agent is properly initialized."""
        return self._initialized and self.agent is not None
    
    def get_connection_status(self) -> Dict[str, bool]:
        """Get status of various connections."""
        status = {
            "agent_initialized": self.is_initialized(),
            "bedrock_model": self.model is not None,
            "mcp_connected": False,
            "github_token_set": bool(self.github_token)
        }
        
        if self.mcp_integration:
            status["mcp_connected"] = self.mcp_integration.is_connected()
        
        return status
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get descriptions of available tools."""
        if not self.mcp_integration:
            return {}
        
        return self.mcp_integration.get_tool_descriptions()
    
    def cleanup(self):
        """Clean up agent resources."""
        try:
            if self.mcp_integration:
                self.mcp_integration.close()
            
            self.agent = None
            self.model = None
            self.mcp_integration = None
            self._initialized = False
            
            logger.info("Agent manager resources cleaned up")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    def create_query_record(self, query: str, response: str, success: bool = True) -> Dict:
        """Create a record of a query and response for history tracking."""
        return {
            "query": query,
            "response": response,
            "timestamp": datetime.now(),
            "success": success,
            "tools_available": len(self.get_available_tools()) if self.mcp_integration else 0
        }