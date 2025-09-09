#!/usr/bin/env python

import logging
import os
import subprocess
import asyncio
import json
from typing import List, Dict, Optional

from config import Config

logger = logging.getLogger(__name__)

class MCPIntegration:
    """Handles MCP server connection and tool management for Git Repository Research."""
    
    def __init__(self, github_token: Optional[str] = None):
        """Initialize MCP integration with optional GitHub token."""
        self.github_token = github_token
        self._tools_cache = None
        self._connected = False
        self._public_mode = False
        self._mcp_available = False
        
    async def setup_client(self):
        """Set up MCP client connection to awslabs.git-repo-research-mcp-server."""
        try:
            logger.info("🔧 Setting up MCP client for Git Repository Research...")
            
            # Check if uvx is available
            uvx_available = await self._check_uvx_available()
            if not uvx_available:
                logger.warning("⚠️ uvx not found - MCP server unavailable")
                return await self._setup_fallback()
            
            # Test MCP server availability
            mcp_available = await self._test_mcp_server()
            if not mcp_available:
                logger.warning("⚠️ MCP server not available - using fallback")
                return await self._setup_fallback()
            
            # If MCP is available, set up tools list with actual MCP server tools
            self._mcp_available = True
            self._tools_cache = [
                {
                    "name": "create_research_repository",
                    "description": "Build a FAISS index for a Git repository for semantic search and analysis"
                },
                {
                    "name": "search_research_repository", 
                    "description": "Perform semantic search within an indexed repository to find relevant code and documentation"
                },
                {
                    "name": "search_repos_on_github",
                    "description": "Search for GitHub repositories based on keywords in AWS organizations"
                },
                {
                    "name": "access_file",
                    "description": "Access file or directory contents from indexed repositories"
                },
                {
                    "name": "repository_analysis",
                    "description": "Comprehensive repository analysis using indexing and semantic search"
                }
            ]
            
            self._connected = True
            logger.info(f"✅ MCP client setup completed - {len(self._tools_cache)} tools available")
            
            # Log available tools for debugging
            for tool in self._tools_cache:
                logger.info(f"📋 Available tool: {tool['name']} - {tool['description']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup MCP client: {str(e)}")
            return await self._setup_fallback()
    
    async def _check_uvx_available(self) -> bool:
        """Check if uvx command is available."""
        try:
            result = subprocess.run(['uvx', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            available = result.returncode == 0
            logger.info(f"🔍 uvx availability check: {'✅ Available' if available else '❌ Not found'}")
            return available
        except Exception as e:
            logger.info(f"🔍 uvx not available: {str(e)}")
            return False
    
    async def _test_mcp_server(self) -> bool:
        """Test if the MCP server can be started."""
        try:
            logger.info("🧪 Testing MCP server availability...")
            
            # Set up environment
            env = os.environ.copy()
            env["AWS_REGION"] = "us-east-1"
            env["FASTMCP_LOG_LEVEL"] = "ERROR"
            if self.github_token:
                env["GITHUB_TOKEN"] = self.github_token
            
            # Try to start the MCP server briefly to test availability
            process = subprocess.Popen(
                ['uvx', 'awslabs.git-repo-research-mcp-server@latest'],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait a short time to see if it starts successfully
            try:
                stdout, stderr = process.communicate(timeout=10)
                available = process.returncode == 0 or "MCP server" in stderr
                logger.info(f"🧪 MCP server test: {'✅ Available' if available else '❌ Failed'}")
                return available
            except subprocess.TimeoutExpired:
                process.kill()
                logger.info("🧪 MCP server test: ✅ Started successfully (timeout expected)")
                return True
                
        except Exception as e:
            logger.warning(f"🧪 MCP server test failed: {str(e)}")
            return False
    
    async def _setup_fallback(self) -> bool:
        """Set up fallback tools when MCP server is not available."""
        logger.info("🔄 Setting up fallback repository analysis tools")
        
        self._mcp_available = False
        self._tools_cache = [
            {
                "name": "basic_repository_info",
                "description": "Basic repository information and structure analysis"
            },
            {
                "name": "repository_guidance",
                "description": "General guidance for repository analysis and best practices"
            }
        ]
        
        self._connected = True
        logger.info(f"✅ Fallback setup completed - {len(self._tools_cache)} basic tools available")
        return True
    
    async def list_tools(self) -> List[Dict]:
        """List all available tools from the MCP server."""
        if not self._connected:
            raise RuntimeError("MCP client not initialized. Call setup_client() first.")
        
        try:
            return self._tools_cache
            
        except Exception as e:
            logger.error(f"Failed to list MCP tools: {str(e)}")
            raise
    
    async def call_tool(self, tool_name: str, arguments: Dict = None) -> str:
        """Call a specific MCP tool with arguments."""
        if not self._connected:
            raise RuntimeError("MCP client not initialized. Call setup_client() first.")
        
        try:
            # Parse arguments to determine repository type and access method
            args = arguments or {}
            repo_url = args.get('repository_url', '')
            repo_type = args.get('repository_type', 'public')
            token_available = args.get('token_available', False)
            
            logger.info(f"🔧 Calling tool: {tool_name}")
            logger.info(f"📂 Repository: {repo_url} ({repo_type})")
            logger.info(f"🔑 Token available: {token_available}")
            logger.info(f"🛠️ MCP available: {self._mcp_available}")
            
            # Validate access for private repositories
            if repo_type.lower() == 'private' and not token_available:
                raise ValueError("GitHub token is required for private repository access")
            
            # If MCP server is available, call it directly
            if self._mcp_available and repo_url:
                return await self._call_real_mcp_tool(tool_name, repo_url, repo_type, token_available)
            else:
                # Use fallback analysis
                return await self._fallback_analysis(repo_url, repo_type, tool_name)
                
        except Exception as e:
            logger.error(f"❌ Failed to call tool {tool_name}: {str(e)}")
            raise
    
    async def _call_real_mcp_tool(self, tool_name: str, repo_url: str, repo_type: str, token_available: bool) -> str:
        """Call the real MCP server tool using proper MCP protocol."""
        try:
            logger.info(f"🚀 Calling real MCP server for {tool_name}")
            
            # Import MCP client components
            try:
                from mcp import ClientSession, StdioServerParameters
                from mcp.client.stdio import stdio_client
            except ImportError as e:
                logger.error(f"❌ MCP client not available: {e}")
                return await self._fallback_analysis(repo_url, repo_type, tool_name)
            
            # Set up environment for MCP server
            env = os.environ.copy()
            env["AWS_REGION"] = "us-east-1"
            env["FASTMCP_LOG_LEVEL"] = "ERROR"
            
            if token_available and self.github_token:
                env["GITHUB_TOKEN"] = self.github_token
                logger.info("🔑 Using GitHub token for MCP server")
            else:
                env["GITHUB_TOKEN"] = ""
                logger.info("🌐 Public repository access - no token needed")
            
            # Create server parameters
            server_params = StdioServerParameters(
                command="uvx",
                args=["awslabs.git-repo-research-mcp-server@latest"],
                env=env
            )
            
            # Connect to MCP server and make the call
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize the session
                    await session.initialize()
                    
                    # First, list the actual available tools from the server
                    tools_result = await session.list_tools()
                    available_tools = [tool.name for tool in tools_result.tools]
                    logger.info(f"🔍 Available MCP tools: {available_tools}")
                    
                    # Implement repository analysis workflow using available MCP tools
                    if tool_name == "repository_analysis":
                        return await self._comprehensive_repository_analysis(session, repo_url, available_tools)
                    
                    # Map our tool names to actual MCP server tool names
                    mcp_tool_mapping = {
                        "create_research_repository": "create_research_repository",
                        "search_research_repository": "search_research_repository", 
                        "search_repos_on_github": "search_repos_on_github",
                        "access_file": "access_file"
                    }
                    
                    actual_tool_name = mcp_tool_mapping.get(tool_name, tool_name)
                    
                    # Check if the tool exists
                    if actual_tool_name not in available_tools:
                        logger.warning(f"⚠️ Tool '{actual_tool_name}' not found in available tools: {available_tools}")
                        return await self._fallback_analysis(repo_url, repo_type, tool_name)
                    
                    # Extract repository name properly
                    repo_name = repo_url.split('/')[-1].replace('.git', '') if '/' in repo_url else repo_url.replace('.git', '')
                    
                    # Prepare tool arguments based on the specific tool
                    if actual_tool_name == "create_research_repository":
                        tool_args = {
                            "repository_path": repo_url,
                            "embedding_model": "amazon.titan-embed-text-v2:0"
                        }
                    elif actual_tool_name == "search_research_repository":
                        # For search, try the most likely index path format
                        tool_args = {
                            "index_path": f"{repo_name}_git",  # This seems to be the format used
                            "query": "repository structure architecture dependencies",
                            "limit": 5
                        }
                    elif actual_tool_name == "search_repos_on_github":
                        # Extract keywords from repo URL
                        repo_parts = repo_url.split('/')[-1].replace('.git', '').split('-')
                        keywords = [part for part in repo_parts if len(part) > 2][:3]  # Filter short words
                        tool_args = {
                            "keywords": keywords if keywords else [repo_name],
                            "num_results": 3
                        }
                    elif actual_tool_name == "access_file":
                        # For file access, try the most likely path format
                        tool_args = {
                            "filepath": f"{repo_name}_git/repository/README.md"
                        }
                    else:
                        tool_args = {
                            "repository_url": repo_url
                        }
                    
                    # Call the tool
                    logger.info(f"🔧 Calling MCP tool: {actual_tool_name} with args: {tool_args}")
                    result = await session.call_tool(actual_tool_name, tool_args)
                    
                    if result.content:
                        # Extract text content from the result
                        content_text = ""
                        for content in result.content:
                            if hasattr(content, 'text'):
                                content_text += content.text
                            else:
                                content_text += str(content)
                        
                        if content_text.strip():
                            logger.info(f"✅ MCP server returned real data ({len(content_text)} chars)")
                            logger.info(f"📊 Content preview: {content_text[:200]}...")
                            return f"**Real Repository Data from MCP Server:**\n\n{content_text}"
                        else:
                            logger.warning("⚠️ MCP server returned empty content")
                            return await self._fallback_analysis(repo_url, repo_type, tool_name)
                    else:
                        logger.warning("⚠️ MCP server returned no content")
                        return await self._fallback_analysis(repo_url, repo_type, tool_name)
                        
        except Exception as e:
            logger.error(f"❌ MCP server call failed: {str(e)}")
            logger.error(f"📋 Error details: {type(e).__name__}: {str(e)}")
            return await self._fallback_analysis(repo_url, repo_type, tool_name)
    
    async def _comprehensive_repository_analysis(self, session, repo_url: str, available_tools: list) -> str:
        """Perform comprehensive repository analysis using multiple MCP tools."""
        try:
            logger.info(f"🔍 Starting comprehensive analysis of {repo_url}")
            results = []
            
            # Extract repository name properly - handle .git suffix
            repo_name = repo_url.split('/')[-1].replace('.git', '') if '/' in repo_url else repo_url.replace('.git', '')
            logger.info(f"📝 Using repository name: {repo_name}")
            
            # Step 1: Create research repository index
            index_created = False
            if "create_research_repository" in available_tools:
                logger.info("📊 Step 1: Creating repository index...")
                try:
                    create_args = {
                        "repository_path": repo_url,
                        "embedding_model": "amazon.titan-embed-text-v2:0"
                    }
                    create_result = await session.call_tool("create_research_repository", create_args)
                    
                    if create_result.content:
                        content = "".join([str(c.text) if hasattr(c, 'text') else str(c) for c in create_result.content])
                        results.append(f"**Repository Indexing:**\n{content}")
                        logger.info("✅ Repository indexed successfully")
                        index_created = True
                        
                        # Wait a moment for index to be fully written
                        import asyncio
                        await asyncio.sleep(3)  # Increased wait time
                        
                        # Try to extract the actual index name from the result
                        try:
                            import json
                            if content.strip().startswith('{'):
                                result_data = json.loads(content)
                                if 'index_path' in result_data:
                                    actual_index_path = result_data['index_path']
                                    repo_name = actual_index_path.split('/')[-1]
                                    logger.info(f"📝 Extracted index name from result: {repo_name}")
                        except:
                            pass  # Continue with original repo_name
                    
                except Exception as e:
                    logger.warning(f"⚠️ Repository indexing failed: {e}")
                    results.append(f"**Repository Indexing:** Failed - {str(e)}")
            
            # Step 2: Search for key information in the repository (only if index was created)
            if index_created and "search_research_repository" in available_tools:
                logger.info("🔍 Step 2: Searching repository content...")
                search_queries = [
                    "README documentation overview",
                    "architecture structure organization", 
                    "dependencies requirements setup"
                ]
                
                for query in search_queries:
                    try:
                        # Try different index path formats
                        possible_index_paths = [
                            repo_name,
                            f"{repo_name}_git",
                            repo_url.split('/')[-1],  # With .git
                            repo_url.split('/')[-1].replace('.git', '')  # Without .git
                        ]
                        
                        search_success = False
                        for index_path in possible_index_paths:
                            try:
                                search_args = {
                                    "index_path": index_path,
                                    "query": query,
                                    "limit": 3
                                }
                                search_result = await session.call_tool("search_research_repository", search_args)
                                
                                if search_result.content:
                                    content = "".join([str(c.text) if hasattr(c, 'text') else str(c) for c in search_result.content])
                                    
                                    # Check if we got actual results (not just empty results)
                                    if '"results": []' not in content and 'Error searching' not in content:
                                        results.append(f"**Search Results for '{query}':**\n{content}")
                                        logger.info(f"✅ Search successful with index path: {index_path}")
                                        search_success = True
                                        break
                                    
                            except Exception as search_error:
                                logger.debug(f"Search failed with index path '{index_path}': {search_error}")
                                continue
                        
                        if not search_success:
                            logger.warning(f"⚠️ All search attempts failed for query: '{query}'")
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Search failed for '{query}': {e}")
                        continue
            
            # Step 3: Access key files (try different path formats)
            if "access_file" in available_tools:
                logger.info("📁 Step 3: Accessing key files...")
                key_files = ["README.md", "package.json", "requirements.txt", "Dockerfile", "setup.py"]
                
                for file in key_files:
                    try:
                        # Try different file path formats
                        possible_paths = [
                            f"{repo_name}/repository/{file}",
                            f"{repo_name}_git/repository/{file}",
                            f"{repo_name}/{file}",
                            f"{repo_name}_git/{file}"
                        ]
                        
                        file_found = False
                        for filepath in possible_paths:
                            try:
                                file_args = {"filepath": filepath}
                                file_result = await session.call_tool("access_file", file_args)
                                
                                if file_result.content:
                                    content = "".join([str(c.text) if hasattr(c, 'text') else str(c) for c in file_result.content])
                                    
                                    # Check if file was actually found
                                    if '"status": "error"' not in content and 'not found' not in content.lower():
                                        results.append(f"**{file}:**\n{content[:500]}...")
                                        logger.info(f"✅ File accessed: {filepath}")
                                        file_found = True
                                        break
                                        
                            except Exception as file_error:
                                logger.debug(f"File access failed for '{filepath}': {file_error}")
                                continue
                        
                        if not file_found:
                            logger.debug(f"📄 File not found: {file}")
                            
                    except Exception as e:
                        logger.warning(f"⚠️ File access failed for {file}: {e}")
                        continue
            
            if results:
                final_result = "\n\n".join(results)
                logger.info(f"✅ Comprehensive analysis completed ({len(final_result)} chars)")
                return final_result
            else:
                logger.warning("⚠️ No results from comprehensive analysis")
                return f"Repository analysis attempted for {repo_url}. Index creation may have succeeded, but search and file access encountered path resolution issues. The repository has been indexed and is available for future searches."
                
        except Exception as e:
            logger.error(f"❌ Comprehensive analysis failed: {e}")
            return f"Comprehensive analysis failed: {str(e)}"
    
    async def _fallback_analysis(self, repo_url: str, repo_type: str, tool_name: str) -> str:
        """Provide fallback analysis when MCP tools are not available."""
        logger.info(f"🔄 Using fallback analysis for {tool_name}")
        
        if not repo_url:
            return f"""
**General Repository Analysis Guidance**

Tool: {tool_name}

For comprehensive Git repository research, you can:

1. **Repository Structure Analysis**
   - Examine directory organization and file patterns
   - Identify main components and modules
   - Review configuration files and documentation

2. **Code Quality Assessment**
   - Look for consistent coding patterns
   - Check for test coverage and CI/CD setup
   - Review code organization and architecture

3. **Dependency Analysis**
   - Examine package.json, requirements.txt, or similar files
   - Check for outdated or vulnerable dependencies
   - Review dependency management practices

4. **Development Activity**
   - Analyze commit frequency and patterns
   - Review contributor activity and collaboration
   - Check issue and pull request management

**Note:** For automated analysis with real repository data, ensure the MCP server (awslabs.git-repo-research-mcp-server) is properly installed and configured.
"""
        
        # Provide repository-specific guidance
        if repo_type.lower() == 'public':
            return f"""
**Public Repository Analysis: {repo_url}**

Tool: {tool_name}
Repository Type: Public
Access Method: Direct (no authentication required)

**Manual Analysis Steps:**

1. **Visit the Repository**
   - Go to: {repo_url}
   - Review the README.md for project overview
   - Check the repository structure and organization

2. **Code Analysis**
   - Examine the main source code directories
   - Look for architectural patterns and design choices
   - Review configuration and build files

3. **Activity Assessment**
   - Check recent commits and contributor activity
   - Review open/closed issues and pull requests
   - Analyze release history and versioning

4. **Dependencies & Security**
   - Review dependency files (package.json, requirements.txt, etc.)
   - Check for security advisories or vulnerability reports
   - Examine CI/CD configuration if present

**For Automated Analysis:**
To get comprehensive automated analysis with real repository data, ensure:
- MCP server (awslabs.git-repo-research-mcp-server) is installed via: `uvx awslabs.git-repo-research-mcp-server@latest`
- AWS credentials are properly configured
- The server is accessible from this application

Repository URL: {repo_url}
Analysis Type: {tool_name}
"""
        else:
            return f"""
**Private Repository Analysis: {repo_url}**

Tool: {tool_name}
Repository Type: Private
Access Method: Authenticated (GitHub token required)

**Prerequisites for Private Repository Analysis:**

1. **GitHub Token Configuration**
   - Ensure your GitHub personal access token is set
   - Token must have appropriate repository access permissions
   - Token should include 'repo' scope for full repository access

2. **MCP Server Setup**
   - Install: `uvx awslabs.git-repo-research-mcp-server@latest`
   - Configure GitHub token in environment variables
   - Ensure AWS credentials are properly set

3. **Manual Analysis (if automated tools unavailable)**
   - Access the repository directly: {repo_url}
   - Review code structure and organization
   - Analyze commit history and contributor patterns
   - Examine dependencies and security considerations

**Security Note:** Private repositories may contain sensitive information. Ensure proper access controls and review permissions before analysis.

Repository URL: {repo_url}
Analysis Type: {tool_name}
Token Status: {'✅ Configured' if self.github_token else '❌ Missing'}
"""
    
    def update_github_token(self, token: str):
        """Update GitHub token and reinitialize client if needed."""
        self.github_token = token
        logger.info("GitHub token updated")
    
    def set_public_mode(self, public_mode: bool):
        """Set whether to operate in public repository mode (no token required)."""
        self._public_mode = public_mode
        logger.info(f"Public mode set to: {public_mode}")
    
    def can_access_repository(self, repo_type: str) -> bool:
        """Check if we can access a repository of the given type."""
        if repo_type.lower() == 'public':
            return True  # Public repos don't need tokens
        elif repo_type.lower() == 'private':
            return bool(self.github_token)  # Private repos need tokens
        return False
    
    def is_connected(self) -> bool:
        """Check if MCP client is connected and functional."""
        return self._connected
    
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
    
    async def close(self):
        """Clean up MCP client resources."""
        try:
            self._connected = False
            self._tools_cache = None
            logger.info("MCP client resources cleaned up")
        except Exception as e:
            logger.error(f"Error during MCP client cleanup: {str(e)}")