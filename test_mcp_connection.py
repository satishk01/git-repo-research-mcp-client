#!/usr/bin/env python

"""
Test script to verify MCP server connection and tool availability
"""

import asyncio
import logging
import os
from mcp_integration import MCPIntegration

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

async def test_mcp_integration():
    """Test MCP integration setup and tool calls."""
    print("=" * 60)
    print("Testing MCP Integration for Git Repository Research")
    print("=" * 60)
    
    # Test without GitHub token (public repo access)
    print("\n1. Testing PUBLIC repository access (no GitHub token)")
    print("-" * 50)
    
    mcp = MCPIntegration()
    
    try:
        # Setup client
        setup_success = await mcp.setup_client()
        print(f"Setup success: {setup_success}")
        
        # List tools
        tools = await mcp.list_tools()
        print(f"Available tools: {len(tools)}")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")
        
        # Test tool call with public repository
        print("\n2. Testing tool call with public repository")
        print("-" * 50)
        
        test_repo = "https://github.com/microsoft/vscode"
        tool_args = {
            'repository_url': test_repo,
            'repository_type': 'Public',
            'token_available': False
        }
        
        result = await mcp.call_tool('analyze_repository', tool_args)
        print(f"Tool call result length: {len(result)} characters")
        print(f"Result preview: {result[:300]}...")
        
        # Check if real data was returned
        if "Real Repository Data from MCP Server" in result:
            print("✅ SUCCESS: Got real data from MCP server!")
        elif "Manual Analysis Steps" in result:
            print("📋 INFO: Got fallback guidance (MCP server not available)")
        else:
            print("❓ UNKNOWN: Unexpected result format")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    
    print("\n3. Testing with GitHub token (if available)")
    print("-" * 50)
    
    # Check if GitHub token is available in environment
    github_token = os.environ.get('GITHUB_TOKEN', '')
    if github_token:
        print(f"GitHub token found: {github_token[:10]}...")
        
        mcp_with_token = MCPIntegration(github_token)
        try:
            await mcp_with_token.setup_client()
            tools = await mcp_with_token.list_tools()
            print(f"Tools with token: {len(tools)}")
            
            # Test with private repo access
            tool_args = {
                'repository_url': test_repo,
                'repository_type': 'Public',  # Still public, but with token
                'token_available': True
            }
            
            result = await mcp_with_token.call_tool('analyze_repository', tool_args)
            print(f"Tool call with token result length: {len(result)} characters")
            
            if "Real Repository Data from MCP Server" in result:
                print("✅ SUCCESS: Got real data with GitHub token!")
            else:
                print("📋 INFO: Got fallback guidance with token")
                
        except Exception as e:
            print(f"❌ ERROR with token: {str(e)}")
    else:
        print("No GitHub token found in environment variables")
    
    print("\n" + "=" * 60)
    print("MCP Integration Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_mcp_integration())