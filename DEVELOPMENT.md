# Development Guide

## Quick Commands

```bash
# Run with menu selection
python run.py

# Run voice bot in development mode
python run.py dev

# Run voice bot in production mode  
python run.py start

# Run web interface only
python run.py web

# Run in console mode (terminal testing)
python run.py console
```

## Code Structure

### Modular Design

The codebase is organized into focused modules:

- **`voice_bot.py`**: Main entrypoint and LiveKit session setup
- **`agent.py`**: Voice assistant agent class and conversation logic
- **`tools.py`**: Function tools for ticket operations
- **`database.py`**: Data persistence layer
- **`config.py`**: Configuration and system prompts
- **`web_interface.py`**: FastAPI web interface
- **`main.py`**: Application launcher with options menu

### Adding New Features

#### New IT Issue Types
1. Add issue pattern to `ISSUE_DETECTION` in `config.py`
2. Update `get_issue_type_and_price()` function
3. Update system prompt with new issue description

#### New Function Tools
1. Create async function in `tools.py`:
```python
@llm.function_tool
async def new_tool(param: str) -> str:
    """Tool description"""
    # Implementation
    return "Response"
```
2. Add to `ALL_TOOLS` list
3. Update system prompt to describe new capability

#### Conversation Flow Changes
- Modify `on_user_turn_completed()` in `agent.py`
- Update conversation stages in `VoiceBotState`
- Adjust system prompt in `config.py`

## Testing

### Web Interface Testing
- Run: `python run.py web`
- Open: http://localhost:8000
- Test voice interactions in browser

### LiveKit Development Mode
- Run: `python run.py dev`
- Use LiveKit Agents playground
- Real-time voice testing

### Console Mode (Terminal)
- Run: `python run.py console`
- Text-based conversation testing
- Good for debugging conversation logic

## Configuration

### Environment Variables
Create `.env` file with:
```
OPENAI_API_KEY=your_key_here
LIVEKIT_URL=your_livekit_url
LIVEKIT_API_KEY=your_livekit_key
LIVEKIT_API_SECRET=your_livekit_secret
```

### Voice Components
Configured in `voice_bot.py` entrypoint:
- **STT**: OpenAI Whisper (`whisper-1`)
- **LLM**: OpenAI GPT-4 (`gpt-4`)
- **TTS**: OpenAI TTS (`tts-1`, voice: `alloy`)
- **VAD**: Silero Voice Activity Detection

### Conversation Behavior
Modify `SYSTEM_PROMPT` in `config.py` to change:
- Greeting style
- Information collection flow
- Response tone and length
- Tool usage instructions

## Debugging

### Logging
- Set log level in module imports
- Check console output for detailed flow
- Agent session logs show LiveKit events

### Common Issues
1. **Function schema errors**: Ensure tools use proper type hints
2. **Content parsing errors**: Handle both string/list message formats
3. **Connection issues**: Verify LiveKit credentials and network

## Deployment

### LiveKit Cloud
```bash
# Deploy to LiveKit Cloud
lk agent create

# Local development
python run.py dev
```

### Production Considerations
- Use environment variables for secrets
- Configure logging for production
- Set up monitoring and error tracking
- Consider horizontal scaling with multiple workers
