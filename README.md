# SiteCheck AI Assistant

A powerful AI-powered construction safety and management assistant built with FastAPI and modern AI models.

## Features

- 🤖 Intelligent query routing and processing
- 👥 Specialized construction safety assistants
- 📊 Real-time streaming responses
- 🔄 Automatic task delegation
- 🛡️ Built-in safety compliance checks

## Prerequisites

- Python 3.11+
- OpenAI API key
- Anthropic API key (optional)
- macOS/Linux (ARM64 compatible)

## Installation

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

### POST /query
Send a query to the AI assistant system.

**Request Body:**
```json
{
  "query": "string",
  "force_agent": "string (optional)",
  "temperature": "float (optional, default: 0.7)"
}
```

**Response:**
Streams JSON objects with the following structure:
```json
{
  "type": "string (thinking|response|error)",
  "content": "string",
  "agent": "string"
}
```

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