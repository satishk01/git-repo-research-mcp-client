#!/usr/bin/env python

import logging
import asyncio
import json
from typing import Optional, List, Dict
from datetime import datetime

import boto3
from botocore.config import Config as BotoConfig

from config import Config
from mcp_integration import MCPIntegration

logger = logging.getLogger(__name__)

class AgentManager:
    """Manages AI agent lifecycle and configuration for Git Repository Research."""
    
    def __init__(self, github_token: Optional[str] = None):
        """Initialize agent manager with optional GitHub token."""
        self.github_token = github_token
        self.bedrock_client = None
        self.mcp_integration = None
        self._initialized = False
        
    async def initialize_agent(self):
        """Initialize the AI agent with Bedrock model and MCP tools."""
        try:
            # For EC2 instance role, use default credentials without specifying profile
            # This should automatically use the EC2 instance role
            self.bedrock_client = boto3.client(
                'bedrock-runtime',
                region_name=Config.BEDROCK_REGION,
                config=BotoConfig(
                    read_timeout=Config.READ_TIMEOUT,
                    connect_timeout=Config.CONNECT_TIMEOUT,
                    retries=dict(max_attempts=Config.MAX_RETRIES, mode="adaptive"),
                )
            )
            
            logger.info(f"Initializing Bedrock client with EC2 role, region: {Config.BEDROCK_REGION}")
            
            # Try to find the correct Nova Pro model ID
            await self._find_and_test_nova_model()
            
            # Initialize MCP integration
            self.mcp_integration = MCPIntegration(self.github_token)
            await self.mcp_integration.setup_client()
            
            self._initialized = True
            logger.info("AI Agent initialized successfully with Bedrock and MCP tools")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent: {str(e)}")
            raise
    
    async def _find_and_test_nova_model(self):
        """Find and test the correct Nova Pro model ID."""
        # Different possible Nova Pro model IDs to try
        possible_model_ids = [
            "us.amazon.nova-pro-v1:0",
            "amazon.nova-pro-v1:0", 
            "nova-pro-v1:0",
            "us.amazon.nova-lite-v1:0",  # Fallback to Nova Lite
            "amazon.nova-lite-v1:0"
        ]
        
        # First, try to list available models to see what's actually available
        try:
            bedrock_client = boto3.client('bedrock', region_name=Config.BEDROCK_REGION)
            response = bedrock_client.list_foundation_models()
            available_models = [model['modelId'] for model in response.get('modelSummaries', [])]
            logger.info(f"Available models: {available_models}")
            
            # Filter for Nova models
            nova_models = [model for model in available_models if 'nova' in model.lower()]
            logger.info(f"Available Nova models: {nova_models}")
            
            if nova_models:
                # Use the first available Nova model
                Config.BEDROCK_MODEL_ID = nova_models[0]
                logger.info(f"Using Nova model: {Config.BEDROCK_MODEL_ID}")
            
        except Exception as e:
            logger.warning(f"Could not list available models: {str(e)}")
        
        # Test each possible model ID
        for model_id in possible_model_ids:
            try:
                logger.info(f"Testing model: {model_id}")
                
                test_body = {
                    "messages": [
                        {
                            "role": "user",
                            "content": [{"text": "Hello, this is a test."}]
                        }
                    ],
                    "max_tokens": 10,
                    "temperature": 0.1
                }
                
                response = self.bedrock_client.invoke_model(
                    modelId=model_id,
                    body=json.dumps(test_body),
                    contentType="application/json"
                )
                
                # If successful, update the config and break
                Config.BEDROCK_MODEL_ID = model_id
                logger.info(f"✅ Successfully connected to model: {model_id}")
                return
                
            except Exception as e:
                logger.warning(f"❌ Model {model_id} failed: {str(e)}")
                continue
        
        # If we get here, none of the models worked
        raise Exception(f"Could not access any Nova models. Please check your IAM permissions for Bedrock models in region {Config.BEDROCK_REGION}")
    
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
    
    async def process_query(self, query: str) -> str:
        """Process a user query using Bedrock and MCP tools."""
        if not self._initialized:
            raise RuntimeError("Agent not initialized. Call initialize_agent() first.")
        
        try:
            logger.info(f"Processing query: {query[:100]}...")
            
            # Get available tools
            tools = await self.mcp_integration.list_tools()
            
            # Create a comprehensive prompt for Git repository analysis
            system_prompt = self._create_system_prompt()
            tools_info = "\n".join([f"- {tool['name']}: {tool['description']}" for tool in tools])
            
            full_prompt = f"""{system_prompt}

Available Git Repository Research Tools:
{tools_info}

User Query: {query}

As a Git Repository Research assistant, please provide a comprehensive analysis for this query. 

If the query involves a specific repository URL:
1. Analyze the repository structure and organization
2. Examine the codebase for patterns, architecture, and quality
3. Review dependencies and potential security concerns
4. Assess development activity and contributor patterns
5. Provide actionable insights and recommendations

If the query is general:
1. Provide expert guidance on Git repository analysis
2. Explain best practices and methodologies
3. Suggest specific approaches for repository research

Please provide detailed, actionable insights based on your expertise in repository analysis."""
            
            # Call Bedrock
            response = await self._call_bedrock(full_prompt)
            logger.info("Query processed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Failed to process query: {str(e)}")
            raise
    
    async def _call_bedrock(self, prompt: str) -> str:
        """Call Amazon Nova Pro via Bedrock."""
        try:
            body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}]
                    }
                ],
                "max_tokens": Config.MAX_TOKENS,
                "temperature": Config.TEMPERATURE
            }
            
            response = self.bedrock_client.invoke_model(
                modelId=Config.BEDROCK_MODEL_ID,
                body=json.dumps(body),
                contentType="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['output']['message']['content'][0]['text']
            
        except Exception as e:
            logger.error(f"Bedrock API call failed: {str(e)}")
            raise
    
    async def get_available_tools(self) -> List[Dict]:
        """Get list of available MCP tools."""
        if not self.mcp_integration:
            return []
        
        try:
            return await self.mcp_integration.list_tools()
        except Exception as e:
            logger.error(f"Failed to get available tools: {str(e)}")
            return []
    
    def update_github_token(self, token: str):
        """Update GitHub token and reinitialize agent if needed."""
        self.github_token = token
        
        if self.mcp_integration:
            try:
                self.mcp_integration.update_github_token(token)
                logger.info("GitHub token updated successfully")
            except Exception as e:
                logger.error(f"Failed to update GitHub token: {str(e)}")
                raise
    
    def is_initialized(self) -> bool:
        """Check if agent is properly initialized."""
        return self._initialized and self.bedrock_client is not None
    
    def get_connection_status(self) -> Dict[str, bool]:
        """Get status of various connections."""
        status = {
            "agent_initialized": self.is_initialized(),
            "bedrock_model": self.bedrock_client is not None,
            "mcp_connected": False,
            "github_token_set": bool(self.github_token)
        }
        
        if self.mcp_integration:
            status["mcp_connected"] = self.mcp_integration.is_connected()
        
        return status
    
    async def get_tool_descriptions(self) -> Dict[str, str]:
        """Get descriptions of available tools."""
        if not self.mcp_integration:
            return {}
        
        return await self.mcp_integration.get_tool_descriptions()
    
    async def cleanup(self):
        """Clean up agent resources."""
        try:
            if self.mcp_integration:
                await self.mcp_integration.close()
            
            self.bedrock_client = None
            self.mcp_integration = None
            self._initialized = False
            
            logger.info("Agent manager resources cleaned up")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    async def create_query_record(self, query: str, response: str, success: bool = True) -> Dict:
        """Create a record of a query and response for history tracking."""
        tools_count = 0
        if self.mcp_integration:
            try:
                tools = await self.get_available_tools()
                tools_count = len(tools)
            except:
                tools_count = 0
        
        return {
            "query": query,
            "response": response,
            "timestamp": datetime.now(),
            "success": success,
            "tools_available": tools_count
        }