#!/usr/bin/env python

import logging
from typing import List, Dict, Optional
from shutil import which
import asyncio
import json

from mcp import stdio_client, StdioServerParameters

from config import Config

logger = logging.getLogger(__name__)

class MCPIntegration:
    """Handles MCP server connection and tool management for Git Repository Research."""
    
    def __init__(self, github_token: Optional[str] = None):
        """Initialize MCP integration with optional GitHub token."""
        self.github_token = github_token
        self.mcp_client = None
        self._tools_cache = None
        
    async def setup_client(self):
        """Set up and return MCP client with proper configuration."""
        try:
            # Prepare environment variables
            env_vars = Config.MCP_ENV_VARS.copy()
            if self.github_token:
                env_vars["GITHUB_TOKEN"] = self.github_token
            
            # Create MCP client
            self.mcp_client = await stdio_client(
                StdioServerParameters(
                    command=which(Config.MCP_SERVER_COMMAND),
                    args=Config.MCP_SERVER_ARGS,
                    env=env_vars
                )
            )
            
            logger.info("MCP client setup completed successfully")
            return self.mcp_client
            
        except Exception as e:
            logger.error(f"Failed to setup MCP client: {str(e)}")
            raise
    
    async def list_tools(self) -> List[Dict]:
        """List all available tools from the MCP server."""
        if not self.mcp_client:
            raise RuntimeError("MCP client not initialized. Call setup_client() first.")
        
        try:
            if self._tools_cache is None:
                result = await self.mcp_client.list_tools()
                self._tools_cache = result.tools
                logger.info(f"Retrieved {len(self._tools_cache)} tools from MCP server")
            
            return [{"name": tool.name, "description": tool.description} for tool in self._tools_cache]
            
        except Exception as e:
            logger.error(f"Failed to list MCP tools: {str(e)}")
            raise
    
    async def call_tool(self, tool_name: str, arguments: Dict = None) -> str:
        """Call a specific MCP tool with arguments."""
        if not self.mcp_client:
            raise RuntimeError("MCP client not initialized. Call setup_client() first.")
        
        try:
            result = await self.mcp_client.call_tool(tool_name, arguments or {})
            return json.dumps(result.content, indent=2)
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {str(e)}")
            raise
    
    def update_github_token(self, token: str):
        """Update GitHub token and reinitialize client if needed."""
        self.github_token = token
        # Clear tools cache to force refresh with new token
        self._tools_cache = None
        self.mcp_client = None
    
    def is_connected(self) -> bool:
        """Check if MCP client is connected and functional."""
        return self.mcp_client is not None
    
    async def get_tool_descriptions(self) -> Dict[str, str]:
        """Get a dictionary of tool names and their descriptions."""
        try:
            tools = await self.list_tools()
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