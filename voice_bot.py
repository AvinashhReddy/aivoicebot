"""
IT Help Desk Voice Bot - Main Entry Point

This is the main entry point for the LiveKit voice bot that handles
IT help desk conversations and ticket creation.
"""

import asyncio
import logging
import os
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import AgentSession
from livekit.plugins import openai, silero

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from agent import ITHelpDeskBot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def entrypoint(ctx: JobContext):
    """
    Main entrypoint for the voice bot
    
    This function is called by LiveKit when a new job is started.
    It sets up the agent session with voice components and starts
    the conversation with the customer.
    """
    logger.info(f"Voice bot assigned to room: {ctx.room.name}")
    
    try:
        # Create AgentSession with STT, LLM, TTS, and VAD configuration
        logger.info("Creating agent session with voice components...")
        session = AgentSession(
            stt=openai.STT(
                model="whisper-1",
                language="en",
            ),
            llm=openai.LLM(
                model="gpt-4",
                temperature=0.7,
            ),
            tts=openai.TTS(
                model="tts-1",
                voice="alloy",
            ),
            vad=silero.VAD.load(),
        )
        logger.info("✅ Agent session created")
        
        # Create the voice assistant
        logger.info("Creating voice assistant...")
        assistant = ITHelpDeskBot()
        logger.info("✅ Voice assistant created")
        
        # Start the session with room and agent
        logger.info("Starting agent session...")
        await session.start(
            room=ctx.room,
            agent=assistant,
        )
        logger.info("✅ Agent session started successfully")
        
        # Generate initial greeting
        logger.info("Generating initial greeting...")
        await session.generate_reply(
            instructions="Greet the user and offer your assistance."
        )
        logger.info("✅ Initial greeting generated")
        
    except Exception as e:
        logger.error(f"❌ Error in entrypoint: {e}")
        logger.exception("Full traceback:")
        raise


if __name__ == "__main__":
    # Run the LiveKit worker with our entrypoint function
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))