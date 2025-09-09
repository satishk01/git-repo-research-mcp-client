#!/usr/bin/env python

import logging
from typing import List, Dict, Optional
from shutil import which

from mcp import stdio_client, StdioServerParameters
from strands.tools.mcp.mcp_client import MCPClient

from config import Config

logger = logging.getLogger(__name__)

class MCPIntegration:
    """Handles MCP server connection and tool management for Git Repository Research."""
    
    def __init__(self, github_token: Optional[str] = None):
        """Initialize MCP integration with optional GitHub token."""
        self.github_token = github_token
        self.mcp_client = None
        self._tools_cache = None
        
    def setup_client(self) -> MCPClient:
        """Set up and return MCP client with proper configuration."""
        try:
            # Prepare environment variables
            env_vars = Config.MCP_ENV_VARS.copy()
            if self.github_token:
                env_vars["GITHUB_TOKEN"] = self.github_token
            
            # Create MCP client
            self.mcp_client = MCPClient(lambda: stdio_client(
                StdioServerParameters(
                    command=which(Config.MCP_SERVER_COMMAND),
                    args=Config.MCP_SERVER_ARGS,
                    env=env_vars,
                    disabled=False,
                    autoApprove=[]
                )
            ))
            
            logger.info("MCP client setup completed successfully")
            return self.mcp_client
            
        except Exception as e:
            logger.error(f"Failed to setup MCP client: {str(e)}")
            raise
    
    def list_tools(self) -> List[Dict]:
        """List all available tools from the MCP server."""
        if not self.mcp_client:
            raise RuntimeError("MCP client not initialized. Call setup_client() first.")
        
        try:
            if self._tools_cache is None:
                self._tools_cache = self.mcp_client.list_tools_sync()
                logger.info(f"Retrieved {len(self._tools_cache)} tools from MCP server")
            
            return self._tools_cache
            
        except Exception as e:
            logger.error(f"Failed to list MCP tools: {str(e)}")
            raise
    
    def update_github_token(self, token: str):
        """Update GitHub token and reinitialize client if needed."""
        self.github_token = token
        # Clear tools cache to force refresh with new token
        self._tools_cache = None
        
        # If client exists, we need to reinitialize it with new token
        if self.mcp_client:
            try:
                self.setup_client()
                logger.info("MCP client reinitialized with new GitHub token")
            except Exception as e:
                logger.error(f"Failed to reinitialize MCP client with new token: {str(e)}")
                raise
    
    def get_client(self) -> MCPClient:
        """Get the current MCP client, initializing if necessary."""
        if not self.mcp_client:
            self.setup_client()
        return self.mcp_client
    
    def is_connected(self) -> bool:
        """Check if MCP client is connected and functional."""
        try:
            if not self.mcp_client:
                return False
            
            # Try to list tools as a connectivity test
            self.list_tools()
            return True
            
        except Exception:
            return False
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get a dictionary of tool names and their descriptions."""
        try:
            tools = self.list_tools()
            return {
                tool.get('name', 'Unknown'): tool.get('description', 'No description available')
                for tool in tools
            }
        except Exception as e:
            logger.error(f"Failed to get tool descriptions: {str(e)}")
            return {}
    
    def close(self):
        """Clean up MCP client resources."""
        if self.mcp_client:
            try:
                # MCP client cleanup if needed
                self.mcp_client = None
                self._tools_cache = None
                logger.info("MCP client resources cleaned up")
            except Exception as e:
                logger.error(f"Error during MCP client cleanup: {str(e)}")