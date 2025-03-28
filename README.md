# SiteCheck AI Assistant

A powerful AI-powered construction safety and management assistant built with FastAPI and modern AI models.

## Version Information

Current stable version: v1.0.0

### Branches
- `main`: Main branch containing the latest stable release
- `v1.0-stable`: Stable branch for version 1.0.x
- `develop`: Development branch for upcoming features

For production use, please use the latest tagged release or the stable branch.

## Features

- 🤖 Intelligent query routing and processing
- 👥 Specialized construction safety assistants
- 📊 Real-time streaming responses
- 🔄 Automatic task delegation
- 🛡️ Built-in safety compliance checks

## Prerequisites

- Python 3.11+ or Docker
- OpenAI API key
- Anthropic API key (optional)
- macOS/Linux (ARM64 compatible)

## Installation

### Option 1: Local Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/sitecheck-py.git
cd sitecheck-py
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your API keys:
```bash
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key  # Optional
```

### Option 2: Docker Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/sitecheck-py.git
cd sitecheck-py
```

2. Create a `.env` file with your API keys:
```bash
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key  # Optional
```

3. Build and run with Docker Compose:
```bash
docker-compose up --build
```

Or build and run with Docker:
```bash
docker build -t sitecheck .
docker run -p 8001:8001 --env-file .env sitecheck
```

## Cloud Deployment

### Azure Container Apps

1. Build and push to Azure Container Registry:
```bash
az acr build --registry <registry-name> --image sitecheck:v1.0.0 .
```

2. Deploy to Azure Container Apps:
```bash
az containerapp create \
  --name sitecheck \
  --resource-group <resource-group> \
  --image <registry-name>.azurecr.io/sitecheck:v1.0.0 \
  --target-port 8001 \
  --ingress external \
  --env-vars OPENAI_API_KEY=<your-key> ANTHROPIC_API_KEY=<your-key>
```

### AWS ECS

1. Build and push to Amazon ECR:
```bash
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <aws-account>.dkr.ecr.<region>.amazonaws.com
docker build -t sitecheck .
docker tag sitecheck:latest <aws-account>.dkr.ecr.<region>.amazonaws.com/sitecheck:v1.0.0
docker push <aws-account>.dkr.ecr.<region>.amazonaws.com/sitecheck:v1.0.0
```

2. Deploy using AWS ECS (Fargate):
- Create an ECS cluster
- Create a task definition using the ECR image
- Create a service with the task definition
- Configure environment variables in the task definition

## Usage

1. Start the server:
```bash
uvicorn agentforge.main:app --reload --port 8001
```

2. Send queries to the API:
```bash
# General query
curl -N -X POST http://127.0.0.1:8001/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello", "temperature": 0.7}'

# Construction safety query
curl -N -X POST http://127.0.0.1:8001/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Create a safety meeting for working at heights", "temperature": 0.7}'
```

3. Use with a specific agent:
```bash
curl -N -X POST http://127.0.0.1:8001/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Review our fall protection policy", "force_agent": "safetyauditor", "temperature": 0.7}'
```

## Available Agents

- **SiteCheck Manager**: Coordinates and delegates tasks
- **Safety Meeting Writer**: Creates toolbox meetings and safety documentation
- **Incident Investigator**: Handles incident analysis and investigations
- **Compliance Advisor**: Provides regulatory guidance
- **Safety Auditor**: Conducts safety audits and assessments
- **Product Support**: Assists with product usage and account management

## API Endpoints

### Query Parameters

Both the `/query` and `/stream_process` endpoints accept the following parameters in their request body:

```json
{
    "query": "Your query text here",
    "agent": "General Assistant",
    "temperature": 0.7,
    "preferred_model": "gpt-4o-mini",
    "model_type": "default",
    "model_category": "cost-optimized"
}
```

#### Required Parameters

- `query` (string)
  - The text query to be processed by the AI agent
  - Required for all requests

#### Optional Parameters

- `agent` (string)
  - Default: "General Assistant"
  - Available options:
    - "General Assistant": General purpose AI assistant
    - "Construction Meeting Assistant": Construction meeting specialist
    - "Safety Assistant": Safety and compliance specialist

- `temperature` (float)
  - Controls randomness in the response
  - Range: 0.0 to 1.0
  - Default: 0.7
  - Lower values: more focused and deterministic
  - Higher values: more creative and varied

- `preferred_model` (string)
  - Specific model to use for the response
  - Default: "gpt-4o-mini"
  - Examples:
    - "gpt-4o-mini": Default OpenAI model (cost-optimized)
    - "o3-mini": Claude 3 Opus (reasoning)
    - "gpt-4o": GPT-4 Turbo (flagship)

- `model_type` (string)
  - Type of model to use
  - Default: "default"
  - Options:
    - "default": Standard processing
    - "reasoning": Enhanced analytical capabilities

- `model_category` (string)
  - Category of model to use
  - Default: "cost-optimized"
  - Options:
    - "reasoning": Best for complex analysis
    - "flagship": Best quality but expensive
    - "cost-optimized": Good balance of quality and cost
    - "legacy": Older models
    - "claude": Anthropic models

### Example Requests

#### Minimal Request
```json
{
    "query": "Hello"
}
```

#### Full Request with All Parameters
```json
{
    "query": "Create a safety meeting agenda",
    "agent": "Safety Assistant",
    "temperature": 0.7,
    "preferred_model": "o3-mini",
    "model_type": "reasoning",
    "model_category": "flagship"
}
```

### Streaming Response Format

When using the `/stream_process` endpoint, responses are returned as Server-Sent Events (SSE) with the following format:

```
data: {"type": "thinking", "content": "Processing your request..."}\n\n
data: {"type": "response", "content": "First part of response..."}\n\n
data: {"type": "response", "content": "Next part of response..."}\n\n
data: [DONE]\n\n
```

#### Response Types
- `thinking`: Initial acknowledgment
- `response`: Actual content chunks
- `error`: Error messages if something goes wrong
- `[DONE]`: Stream completion marker

### Error Responses

If an error occurs, the API will return a JSON response with:
- HTTP status code (404 for not found, 500 for server errors)
- Error details including:
  - Error message
  - Available agents list
  - Suggestions for correction
  - Stack trace (in development mode)

## Development

The project follows a modular architecture:
- `agentforge/main.py`: FastAPI application entry point
- `agentforge/core/`: Core system components
- `agentforge/agents/`: Specialized AI agents
- `agentforge/utils/`: Utility functions and managers

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - See LICENSE file for details