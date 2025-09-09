#!/usr/bin/env python

"""
Simple script to list available tools from the MCP server
"""

import asyncio
import logging
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def list_mcp_tools():
    """List all available tools from the MCP server."""
    try:
        print("🔍 Connecting to awslabs.git-repo-research-mcp-server...")
        
        # Set up environment
        env = os.environ.copy()
        env["AWS_REGION"] = "us-east-1"
        env["FASTMCP_LOG_LEVEL"] = "ERROR"
        env["GITHUB_TOKEN"] = ""  # Public access
        
        # Create server parameters
        server_params = StdioServerParameters(
            command="uvx",
            args=["awslabs.git-repo-research-mcp-server@latest"],
            env=env
        )
        
        # Connect and list tools
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize
                await session.initialize()
                
                # List tools
                tools_result = await session.list_tools()
                
                print(f"\n✅ Found {len(tools_result.tools)} tools:")
                print("=" * 50)
                
                for i, tool in enumerate(tools_result.tools, 1):
                    print(f"{i}. {tool.name}")
                    if tool.description:
                        print(f"   Description: {tool.description}")
                    if hasattr(tool, 'inputSchema') and tool.inputSchema:
                        print(f"   Input Schema: {tool.inputSchema}")
                    print()
                
                return [tool.name for tool in tools_result.tools]
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

if __name__ == "__main__":
    tools = asyncio.run(list_mcp_tools())
    print(f"Available tool names: {tools}")