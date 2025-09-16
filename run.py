#!/usr/bin/env python3
"""
Simple runner script for the IT Help Desk Voice Bot
"""

import sys
import subprocess

def main():
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode in ['dev', 'start', 'console']:
            # Run voice bot in specified mode
            subprocess.run([sys.executable, 'voice_bot.py', mode])
        elif mode == 'web':
            # Run web interface only
            subprocess.run([sys.executable, '-c', 
                          "from web_interface import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000)"])
        else:
            print(f"Unknown mode: {mode}")
            print("Available modes: dev, start, console, web")
    else:
        # Run main application with menu
        subprocess.run([sys.executable, 'main.py'])

if __name__ == "__main__":
    main()
