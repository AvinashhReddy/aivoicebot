# IT Help Desk Voice Bot

A professional voice-powered AI assistant for IT help desk operations using LiveKit Agents framework.

## Features

- **Natural Voice Conversations**: Real-time voice interaction with customers
- **Intelligent Issue Detection**: Automatically identifies and prices IT issues
- **Ticket Management**: Creates and manages support tickets
- **Multi-modal Interface**: Voice bot + web interface for testing
- **Professional Workflow**: Guided conversation flow for information collection

## Supported IT Issues

- Wi-Fi not working: $20
- Email login issues - password reset: $15  
- Slow laptop performance - CPU change: $25
- Printer problems - power plug change: $10

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd aivoicebot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Setup

```bash
# Copy environment template
cp env_example.txt .env

# Edit .env file and add your API keys:
# OPENAI_API_KEY=your_openai_api_key_here
# LIVEKIT_URL=your_livekit_url
# LIVEKIT_API_KEY=your_livekit_api_key
# LIVEKIT_API_SECRET=your_livekit_secret
```

### 3. Running the Application

```bash
# Option 1: Run main application with menu
python main.py

# Option 2: Run voice bot directly
python voice_bot.py dev

# Option 3: Run web interface only
python -c "from web_interface import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000)"
```

## Project Structure

```
aivoicebot/
├── agent.py              # Voice assistant agent class
├── config.py             # Configuration and system prompts
├── database.py           # SQLite database operations
├── main.py               # Main application entry point
├── tools.py              # Function tools for ticket operations
├── voice_bot.py          # LiveKit voice bot entrypoint
├── web_interface.py      # FastAPI web interface
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Architecture

### Core Components

1. **Voice Bot (`voice_bot.py`)**: LiveKit entrypoint that sets up the agent session
2. **Agent (`agent.py`)**: Main voice assistant that handles conversations
3. **Tools (`tools.py`)**: Function tools for creating and updating tickets
4. **Database (`database.py`)**: SQLite-based ticket storage
5. **Web Interface (`web_interface.py`)**: FastAPI-based testing interface

### Voice Pipeline

```
User Speech → STT (Whisper) → LLM (GPT-4) → TTS (OpenAI) → Agent Response
```

## Configuration

The bot behavior is configured in `config.py`:

- **System prompts**: Define conversation flow and behavior
- **Issue detection**: Maps user descriptions to supported IT issues
- **Pricing**: Automatic price quotes for different services

## Usage

### Voice Bot Modes

1. **Development Mode**: `python voice_bot.py dev`
   - Connects to LiveKit for testing
   - Available in Agents playground

2. **Production Mode**: `python voice_bot.py start`
   - Production deployment mode

3. **Console Mode**: `python voice_bot.py console`
   - Terminal-based testing (Python only)

### Conversation Flow

1. **Greeting**: Bot welcomes user and asks for name/email
2. **Details Collection**: Collects phone number and address
3. **Issue Understanding**: Identifies the IT problem
4. **Price Quote**: Provides service fee estimate
5. **Confirmation**: Creates ticket with confirmation number

## Development

### Adding New IT Issues

1. Update `ISSUE_DETECTION` in `config.py`
2. Add pricing to `get_issue_type_and_price()` function
3. Update system prompt with new issue description

### Adding New Tools

1. Create async function in `tools.py` with `@llm.function_tool` decorator
2. Add to `ALL_TOOLS` list
3. Update system prompt to describe the new tool

## Requirements

- Python 3.9+
- OpenAI API key
- LiveKit Cloud account (or self-hosted server)
- Required packages (see `requirements.txt`)

## License

[Add your license information here]

## Support

For issues and questions, please refer to the LiveKit Agents documentation:
- [LiveKit Agents Docs](https://docs.livekit.io/agents/)
- [Voice AI Quickstart](https://docs.livekit.io/agents/start/voice-ai/)