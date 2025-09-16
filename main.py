#!/usr/bin/env python3
"""
IT Help Desk Voice Bot - Main Application

This is the main entry point for the IT Help Desk Voice Bot application.
It provides both a web interface for testing and the LiveKit voice bot functionality.
"""

import asyncio
import logging
import os
import sys
from multiprocessing import Process
import uvicorn

from web_interface import app
from livekit.agents import cli, WorkerOptions
from voice_bot import entrypoint

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if required environment variables are set"""
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables before running the application.")
        return False
    
    return True

def run_web_interface():
    """Run the web interface server"""
    logger.info("Starting web interface on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

def run_voice_bot():
    """Run the LiveKit voice bot"""
    logger.info("Starting LiveKit voice bot...")
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))

def main():
    """Main application entry point"""
    print("🎤 IT Help Desk Voice Bot")
    print("=" * 40)
    
    if not check_environment():
        sys.exit(1)
    
    print("\nChoose how to run the application:")
    print("1. Web Interface Only (for testing)")
    print("2. Voice Bot Only (LiveKit)")
    print("3. Both (Web Interface + Voice Bot)")
    print("4. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == "1":
                print("\nStarting web interface...")
                print("Open http://localhost:8000 in your browser to test the voice bot")
                run_web_interface()
                break
                
            elif choice == "2":
                print("\nStarting voice bot...")
                print("Make sure LiveKit server is running")
                run_voice_bot()
                break
                
            elif choice == "3":
                print("\nStarting both web interface and voice bot...")
                print("Web interface: http://localhost:8000")
                print("Voice bot: Running on LiveKit")
                
                # Start web interface in a separate process
                web_process = Process(target=run_web_interface)
                web_process.start()
                
                # Start voice bot in the main process
                try:
                    run_voice_bot()
                except KeyboardInterrupt:
                    print("\nShutting down...")
                    web_process.terminate()
                    web_process.join()
                break
                
            elif choice == "4":
                print("Goodbye!")
                sys.exit(0)
                
            else:
                print("Invalid choice. Please enter 1, 2, 3, or 4.")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
