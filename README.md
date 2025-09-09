# Git Repository Research Streamlit Application

AI-powered Git repository analysis using Amazon Nova Pro and the Git Repository Research MCP Server.

## Overview

This Streamlit application provides an interactive web interface for researching and analyzing Git repositories using advanced AI capabilities. It leverages:

- **Amazon Nova Pro** via AWS Bedrock for AI processing
- **Git Repository Research MCP Server** for repository analysis tools
- **Strands SDK** for agent orchestration
- **Streamlit** for the web interface

## Features

- 🔍 **Repository Analysis**: Comprehensive analysis of Git repository structure, dependencies, and patterns
- 🤖 **AI-Powered Insights**: Natural language queries processed by Amazon Nova Pro
- 🔧 **Multiple Tools**: Access to all Git Repository Research MCP Server tools
- 🔑 **GitHub Integration**: Secure GitHub token input for repository access
- 📊 **Interactive UI**: Clean, functional Streamlit interface
- 📝 **Query History**: Track previous analyses and results

## Prerequisites

### AWS Setup
- EC2 instance with appropriate IAM role for Bedrock access
- IAM role must have permissions for:
  - `bedrock:InvokeModel` for Amazon Nova Pro
  - `bedrock:GetFoundationModel` for model access

### System Requirements
- Python 3.8 or higher
- Internet access for GitHub and AWS services
- `uvx` command available (for MCP server)

## Installation

### 1. Install System Dependencies (EC2 Amazon Linux)

```bash
# Install build tools and C++ compiler
sudo yum update -y
sudo yum groupinstall -y "Development Tools"
sudo yum install -y gcc-c++ cmake

# Or for Ubuntu/Debian:
# sudo apt update
# sudo apt install -y build-essential cmake g++
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install UV and UVX (if not already installed)

```bash
# Using pip
pip install uv

# Or using curl (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 4. Verify UVX Installation

```bash
uvx --version
```

## Required Packages

The application requires the following Python packages (see `requirements.txt`):

```
streamlit>=1.28.0
boto3>=1.34.0
botocore>=1.34.0
mcp>=1.0.0
python-dotenv>=1.0.0
```

## Configuration

### Environment Variables (Optional)

You can set these environment variables to customize the application:

```bash
export BEDROCK_REGION=us-west-2  # Default: us-west-2
export AWS_PROFILE=default       # Default: default
```

### IAM Role Requirements

Your EC2 instance must have an IAM role with the following policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:GetFoundationModel"
            ],
            "Resource": [
                "arn:aws:bedrock:*::foundation-model/us.amazon.nova-pro-v1:0"
            ]
        }
    ]
}
```

## Running the Application

### Start the Streamlit Application

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501` by default.

### For EC2 Deployment

To make the application accessible from outside the EC2 instance:

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

Make sure your EC2 security group allows inbound traffic on port 8501.

## Usage

### 1. Initialize the Application

1. Open the application in your web browser
2. (Optional) Enter your GitHub Personal Access Token in the sidebar for full repository access
3. Click "Initialize Agent" to connect to AWS Bedrock and the MCP server

### 2. Analyze Repositories

Enter natural language queries about Git repositories, such as:

- "Analyze the structure of repository https://github.com/microsoft/vscode"
- "What are the main dependencies in this project?"
- "Show me the recent commit activity and contributors"
- "What security issues might exist in this codebase?"
- "Compare the architecture of two similar repositories"

### 3. View Results

The AI agent will process your query using available MCP tools and display comprehensive analysis results.

## GitHub Token Setup

For full functionality, you'll need a GitHub Personal Access Token:

1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Generate a new token with appropriate permissions:
   - `repo` (for private repositories)
   - `public_repo` (for public repositories)
   - `read:org` (for organization repositories)
3. Enter the token in the sidebar of the application

**Note**: The token is stored only in your browser session and is not persisted.

## Troubleshooting

### Common Issues

#### 1. "Failed to initialize agent"
- **Cause**: AWS Bedrock access issues or missing IAM permissions
- **Solution**: Verify your EC2 IAM role has Bedrock permissions

#### 2. "Unable to connect to Git repository research service"
- **Cause**: MCP server connection issues or missing `uvx` command
- **Solution**: Ensure `uvx` is installed and accessible in PATH

#### 3. "GitHub token authentication failed"
- **Cause**: Invalid or expired GitHub token
- **Solution**: Generate a new GitHub Personal Access Token

#### 4. Import errors for Strands or MCP
- **Cause**: Missing Python packages
- **Solution**: Run `pip install -r requirements.txt`

### Logs and Debugging

The application logs important events to the console. When running with Streamlit, you can see logs in the terminal where you started the application.

For more detailed debugging, you can modify the logging level in `app.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Streamlit UI  │───▶│   Strands Agent  │───▶│  Amazon Nova Pro    │
│                 │    │                  │    │   (via Bedrock)     │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
         │                       │
         │                       ▼
         │              ┌──────────────────┐
         │              │   MCP Client     │
         │              │                  │
         ▼              └──────────────────┘
┌─────────────────┐              │
│ Session State   │              ▼
│ (GitHub Token)  │    ┌──────────────────┐
└─────────────────┘    │ Git Repo Research│
                       │   MCP Server     │
                       └──────────────────┘
```

## Security Considerations

- GitHub tokens are stored only in browser session memory
- No credentials are logged or persisted to disk
- AWS access uses EC2 IAM roles (no hardcoded credentials)
- All communications use HTTPS/TLS encryption

## Support

For issues related to:
- **Strands SDK**: Check the Strands documentation
- **MCP Server**: Refer to the awslabs.git-repo-research-mcp-server documentation
- **AWS Bedrock**: Check AWS Bedrock service documentation
- **This Application**: Check the logs and troubleshooting section above

## License

This application is provided as-is for demonstration purposes. Please ensure compliance with all relevant licenses for the underlying services and libraries.