from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import json
import asyncio
import logging
from typing import Dict, List
import uvicorn
import os
from datetime import datetime, timedelta
from database import db, Ticket
from config import LIVEKIT_CONFIG
import jwt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="IT Help Desk Voice Bot")

# Store active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove broken connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

async def dispatch_voice_bot_to_room(room_name: str, config: dict):
    """Ensure room exists - the running agent worker will handle room assignments"""
    try:
        from livekit import api
        
        # Create LiveKit API client
        livekit_api = api.LiveKitAPI(
            url=config['url'],
            api_key=config['api_key'],
            api_secret=config['api_secret']
        )
        
        # Create room if it doesn't exist
        try:
            await livekit_api.room.create_room(api.CreateRoomRequest(name=room_name))
            logger.info(f"Room {room_name} created successfully")
        except Exception as room_error:
            # Room might already exist - that's ok
            logger.info(f"Room {room_name} ready (might already exist)")
        finally:
            # Properly close the API client session
            await livekit_api.aclose()
        
        logger.info(f"Room {room_name} is ready for agent assignment")
        return True
        
    except Exception as e:
        logger.error(f"Error preparing room: {e}")
        return False

async def start_voice_bot_for_room(room_name: str, config: dict):
    """Start voice bot directly connected to the specific room"""
    try:
        import asyncio
        from livekit import rtc
        from livekit.agents import JobContext
        from datetime import datetime, timedelta
        
        # Create bot token for the same room
        bot_payload = {
            "iss": config["api_key"],
            "sub": "voice-bot",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1),
            "name": "voice-bot",
            "video": {
                "room": room_name,
                "roomJoin": True,
                "canPublish": True,
                "canSubscribe": True,
                "canPublishData": True
            }
        }
        
        bot_token = jwt.encode(bot_payload, config["api_secret"], algorithm="HS256")
        
        # Import the voice bot class
        import sys
        import os
        sys.path.append('/Users/avinashreddy/Documents/reps/aivoicebot')
        from voice_bot import ITHelpDeskBot, entrypoint
        
        # Create room connection
        room = rtc.Room()
        
        @room.on("participant_connected")
        def on_participant_connected(participant: rtc.RemoteParticipant):
            logger.info(f"Voice bot: Participant connected - {participant.identity}")
        
        # Connect to the room
        await room.connect(config["url"], bot_token)
        logger.info(f"Voice bot connected to room: {room_name}")
        
        # Create job context and start voice assistant
        class DirectJobContext:
            def __init__(self, room):
                self._room = room
            
            @property
            def room(self):
                return self._room
            
            async def wait_for_participant(self):
                # Wait for a participant to join
                import asyncio
                while len(self._room.remote_participants) == 0:
                    await asyncio.sleep(0.1)
            
            async def agent(self, assistant):
                # Keep the assistant running
                try:
                    while True:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    pass
        
        ctx = DirectJobContext(room)
        
        # Start the voice bot in background
        asyncio.create_task(entrypoint(ctx))
        logger.info(f"Voice bot assistant started for room: {room_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error starting voice bot for room {room_name}: {e}")
        return False

@app.get("/", response_class=HTMLResponse)
async def get_homepage():
    """Serve the main web interface with LiveKit integration"""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>IT Help Desk Voice Bot - Live Demo</title>
        <script src="https://unpkg.com/livekit-client@2.15.7/dist/livekit-client.umd.js" 
                onload="console.log('LiveKit script loaded successfully')"
                onerror="loadLiveKitFallback()"></script>
        <script>
            function loadLiveKitFallback() {{
                console.log('Primary CDN failed, trying fallback...');
                const script = document.createElement('script');
                script.src = 'https://cdn.jsdelivr.net/npm/livekit-client@2.15.7/dist/livekit-client.umd.js';
                script.onload = function() {{
                    console.log('Fallback LiveKit script loaded successfully');
                }};
                script.onerror = function() {{
                    console.error('Both CDNs failed to load LiveKit client');
                    document.getElementById('status').innerHTML = 'Error: Failed to load LiveKit client. Please check your internet connection.';
                    document.getElementById('status').className = 'status disconnected';
                }};
                document.head.appendChild(script);
            }}
            
            // Check multiple times for LiveKit availability
            let checkCount = 0;
            function checkLiveKit() {{
                checkCount++;
                const globals = Object.keys(window).filter(k => k.toLowerCase().includes('live'));
                console.log(`Check ${{checkCount}}: LiveKit globals found:`, globals);
                console.log(`Check ${{checkCount}}: window.LiveKit:`, typeof window.LiveKit);
                console.log(`Check ${{checkCount}}: window.LivekitClient:`, typeof window.LivekitClient);
                
                if (typeof window.LivekitClient !== 'undefined' || checkCount >= 5) {{
                    console.log('Final check - LiveKit available:', typeof window.LivekitClient !== 'undefined');
                    return;
                }}
                setTimeout(checkLiveKit, 500);
            }}
            
            window.addEventListener('load', function() {{
                setTimeout(checkLiveKit, 100);
            }});
        </script>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: white;
            }}
            .container {{
                max-width: 900px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 30px;
                box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            }}
            h1 {{
                text-align: center;
                margin-bottom: 30px;
                font-size: 2.5em;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }}
            .status {{
                text-align: center;
                margin: 20px 0;
                padding: 15px;
                border-radius: 10px;
                font-weight: bold;
            }}
            .connected {{
                background: rgba(76, 175, 80, 0.3);
                border: 2px solid #4CAF50;
            }}
            .disconnected {{
                background: rgba(244, 67, 54, 0.3);
                border: 2px solid #f44336;
            }}
            .connecting {{
                background: rgba(255, 193, 7, 0.3);
                border: 2px solid #ffc107;
            }}
            .controls {{
                text-align: center;
                margin: 30px 0;
            }}
            button {{
                background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
                border: none;
                color: white;
                padding: 15px 30px;
                font-size: 18px;
                border-radius: 50px;
                cursor: pointer;
                margin: 10px;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px 0 rgba(31, 38, 135, 0.2);
            }}
            button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px 0 rgba(31, 38, 135, 0.4);
            }}
            button:disabled {{
                background: #666;
                cursor: not-allowed;
                transform: none;
            }}
            .voice-controls {{
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 20px;
                margin: 20px 0;
            }}
            .mic-button {{
                width: 80px;
                height: 80px;
                border-radius: 50%;
                background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
                border: none;
                color: white;
                font-size: 24px;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px 0 rgba(31, 38, 135, 0.2);
            }}
            .mic-button:hover {{
                transform: scale(1.1);
            }}
            .mic-button.muted {{
                background: #666;
            }}
            .mic-button.speaking {{
                background: #4CAF50;
                animation: pulse 1s infinite;
            }}
            @keyframes pulse {{
                0% {{ transform: scale(1); }}
                50% {{ transform: scale(1.1); }}
                100% {{ transform: scale(1); }}
            }}
            .conversation-log {{
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                padding: 20px;
                margin: 20px 0;
                max-height: 300px;
                overflow-y: auto;
            }}
            .message {{
                margin: 10px 0;
                padding: 10px;
                border-radius: 10px;
            }}
            .user-message {{
                background: rgba(76, 175, 80, 0.3);
                text-align: right;
            }}
            .bot-message {{
                background: rgba(33, 150, 243, 0.3);
                text-align: left;
            }}
            .tickets-section {{
                margin-top: 40px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                padding: 20px;
            }}
            .ticket {{
                background: rgba(255, 255, 255, 0.2);
                margin: 10px 0;
                padding: 15px;
                border-radius: 10px;
                border-left: 4px solid #4ECDC4;
            }}
            .ticket-id {{
                font-weight: bold;
                color: #4ECDC4;
            }}
            .instructions {{
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 30px;
            }}
            .instructions h3 {{
                color: #4ECDC4;
                margin-top: 0;
            }}
            .instructions ul {{
                line-height: 1.6;
            }}
            .error {{
                background: rgba(244, 67, 54, 0.3);
                border: 2px solid #f44336;
                padding: 15px;
                border-radius: 10px;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎤 IT Help Desk Voice Bot - Live Demo</h1>
            
            <div class="instructions">
                <h3>How to Use the Voice Bot:</h3>
                <ul>
                    <li>Click "Connect to Voice Bot" to start a real voice conversation</li>
                    <li>Allow microphone access when prompted</li>
                    <li><strong>Speak clearly and loudly</strong> - the system needs to detect your voice</li>
                    <li>Try saying: "Hi, my laptop is running slowly"</li>
                    <li>The bot will collect your details and create a ticket</li>
                    <li>Click the microphone button to mute/unmute yourself</li>
                </ul>
                <div style="background: rgba(255, 193, 7, 0.2); border: 1px solid #ffc107; padding: 10px; border-radius: 5px; margin-top: 10px;">
                    <strong>🎤 Audio Troubleshooting:</strong><br>
                    • Check browser developer console (F12) for audio level messages<br>
                    • Ensure microphone is not muted in system settings<br>
                    • Try speaking louder or closer to the microphone<br>
                    • Make sure no other apps are using the microphone<br>
                    • Refresh page if connection issues persist
                </div>
            </div>
            
            <div id="status" class="status disconnected">
                Disconnected - Click "Connect to Voice Bot" to begin
            </div>
            
            <div class="controls">
                <button id="connectBtn" onclick="connectToVoiceBot()">Connect to Voice Bot</button>
                <button id="disconnectBtn" onclick="disconnectFromVoiceBot()" disabled>Disconnect</button>
                <button onclick="loadTickets()">Refresh Tickets</button>
            </div>
            
            <div id="voiceControls" class="voice-controls" style="display: none;">
                <button id="micButton" class="mic-button" onclick="toggleMicrophone()">🎤</button>
                <span>Click to mute/unmute microphone</span>
            </div>
            
            <div id="conversationLog" class="conversation-log" style="display: none;">
                <h3>Conversation Log</h3>
                <div id="messages"></div>
            </div>
            
            <div class="tickets-section">
                <h3>Recent Support Tickets</h3>
                <div id="tickets"></div>
            </div>
        </div>

        <script>
            let room = null;
            let localParticipant = null;
            let isConnected = false;
            let isMuted = false;
            let isSpeaking = false;

            const LIVEKIT_URL = '{os.getenv("LIVEKIT_URL", "ws://localhost:7880")}';
            const LIVEKIT_API_KEY = '{os.getenv("LIVEKIT_API_KEY", "devkey")}';
            const LIVEKIT_API_SECRET = '{os.getenv("LIVEKIT_API_SECRET", "secret")}';

            function updateStatus(message, status) {{
                const statusEl = document.getElementById('status');
                statusEl.textContent = message;
                statusEl.className = `status ${{status}}`;
            }}

            function updateButtons(connectEnabled, disconnectEnabled) {{
                document.getElementById('connectBtn').disabled = !connectEnabled;
                document.getElementById('disconnectBtn').disabled = !disconnectEnabled;
            }}

            function addMessage(speaker, message) {{
                const messagesDiv = document.getElementById('messages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${{speaker}}-message`;
                messageDiv.innerHTML = `<strong>${{speaker}}:</strong> ${{message}}`;
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }}

            async function connectToVoiceBot() {{
                try {{
                    updateStatus('Connecting to voice bot...', 'connecting');
                    updateButtons(false, false);

                    // Use LivekitClient which is available
                    if (typeof window.LivekitClient === 'undefined') {{
                        throw new Error('LiveKit client not loaded. Please refresh the page.');
                    }}
                    
                    const LiveKit = window.LivekitClient;
                    console.log('Using window.LivekitClient successfully');
                    
                    // Test microphone access first
                    try {{
                        const stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                        console.log('Microphone access granted');
                        
                        // Test audio levels
                        const audioContext = new AudioContext();
                        const source = audioContext.createMediaStreamSource(stream);
                        const analyzer = audioContext.createAnalyser();
                        source.connect(analyzer);
                        
                        const bufferLength = analyzer.frequencyBinCount;
                        const dataArray = new Uint8Array(bufferLength);
                        
                        function checkAudioLevel() {{
                            analyzer.getByteTimeDomainData(dataArray);
                            let sum = 0;
                            for (let i = 0; i < bufferLength; i++) {{
                                const sample = (dataArray[i] - 128) / 128;
                                sum += sample * sample;
                            }}
                            const rms = Math.sqrt(sum / bufferLength);
                            if (rms > 0.01) {{
                                console.log('Audio detected, RMS level:', rms);
                            }}
                        }}
                        
                        // Check for 3 seconds
                        const interval = setInterval(checkAudioLevel, 100);
                        setTimeout(() => {{
                            clearInterval(interval);
                            audioContext.close();
                            stream.getTracks().forEach(track => track.stop());
                        }}, 3000);
                        
                    }} catch (micError) {{
                        console.error('Microphone access denied:', micError);
                        throw new Error('Microphone access required. Please allow microphone access and try again.');
                    }}

                    // Use a fixed room name so voice bot can join
                    const roomName = `help-desk-room`;
                    
                    // Get access token from server
                    const tokenResponse = await fetch('/get-token', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ room: roomName }})
                    }});
                    
                    if (!tokenResponse.ok) {{
                        throw new Error('Failed to get access token');
                    }}
                    
                    const {{ token }} = await tokenResponse.json();

                    // Connect to LiveKit room with proper audio configuration
                    const roomOptions = {{
                        // Disable adaptive stream to prevent audio quality changes
                        adaptiveStream: false,
                        // Keep audio track always enabled
                        publishDefaults: {{
                            dtx: false,  // Disable discontinuous transmission
                            red: false,  // Disable redundancy encoding that might cause issues
                        }},
                        // Configure WebRTC for better audio handling
                        webAudioMix: false
                    }};
                    room = new LiveKit.Room(roomOptions);
                    
                    room.on('participantConnected', (participant) => {{
                        console.log('Participant connected:', participant.identity);
                        if (participant.identity === 'voice-bot') {{
                            addMessage('System', 'Voice bot connected! You can now speak.');
                        }}
                    }});
                    
                    room.on('participantDisconnected', (participant) => {{
                        console.log('Participant disconnected:', participant.identity);
                        if (participant.identity === 'voice-bot') {{
                            addMessage('System', 'Voice bot disconnected.');
                        }}
                    }});
                    
                    room.on('trackSubscribed', (track, publication, participant) => {{
                        console.log('Track subscribed:', track.kind, participant.identity);
                        if (track.kind === 'audio' && participant.identity === 'voice-bot') {{
                            // Play bot audio
                            const audioElement = track.attach();
                            audioElement.play();
                        }}
                    }});
                    
                    room.on('trackUnsubscribed', (track, publication, participant) => {{
                        track.detach();
                    }});
                    
                    room.on('dataReceived', (payload, participant) => {{
                        if (participant.identity === 'voice-bot') {{
                            const data = JSON.parse(new TextDecoder().decode(payload));
                            if (data.type === 'message') {{
                                addMessage('Bot', data.message);
                            }} else if (data.type === 'ticket_created') {{
                                addMessage('System', `Ticket created: #${{data.ticket_id}}`);
                                loadTickets();
                            }}
                        }}
                    }});

                    await room.connect(LIVEKIT_URL, token);
                    
                    // Configure audio with optimized settings for voice detection
                    const audioOptions = {{
                        autoGainControl: true,
                        echoCancellation: true,
                        noiseSuppression: true,
                    }};
                    
                    // Enable microphone with enhanced settings and force continuous publishing
                    await room.localParticipant.setMicrophoneEnabled(true, {{
                        ...audioOptions,
                        // Force continuous publishing - disable client-side silence detection
                        dtx: false,
                        // Ensure track stays enabled
                        degradationPreference: 'maintain-framerate'
                    }});
                    
                    // Add audio level monitoring and disable client-side silence detection
                    room.localParticipant.on('audioTrackPublished', (publication) => {{
                        console.log('Audio track published:', publication);
                        const track = publication.track;
                        if (track) {{
                            console.log('Configuring audio track to disable client-side VAD');
                            
                            // Try to disable client-side silence detection
                            if (track.mediaStreamTrack) {{
                                // Override the track's silence detection
                                track.mediaStreamTrack.enabled = true;
                            }}
                            
                            // Monitor audio levels
                            track.on('audioLevelChanged', (level) => {{
                                console.log('Audio level:', level);
                                if (level > 0.01) {{
                                    document.getElementById('micButton').classList.add('speaking');
                                }} else {{
                                    document.getElementById('micButton').classList.remove('speaking');
                                }}
                            }});
                        }}
                    }});
                    
                    localParticipant = room.localParticipant;
                    isConnected = true;
                    
                    updateStatus('Connected! Start speaking with the voice bot.', 'connected');
                    updateButtons(false, true);
                    document.getElementById('voiceControls').style.display = 'flex';
                    document.getElementById('conversationLog').style.display = 'block';
                    
                    addMessage('System', 'Connected to voice bot. The bot will start the conversation.');
                    
                }} catch (error) {{
                    console.error('Connection error:', error);
                    updateStatus(`Connection failed: ${{error.message}}`, 'disconnected');
                    updateButtons(true, false);
                    
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'error';
                    errorDiv.innerHTML = `
                        <strong>Connection Error:</strong> ${{error.message}}<br>
                        <small>Make sure the voice bot is running: <code>python voice_bot.py</code></small>
                    `;
                    document.querySelector('.container').insertBefore(errorDiv, document.querySelector('.tickets-section'));
                }}
            }}

            async function disconnectFromVoiceBot() {{
                if (room) {{
                    await room.disconnect();
                    room = null;
                }}
                
                isConnected = false;
                updateStatus('Disconnected', 'disconnected');
                updateButtons(true, false);
                document.getElementById('voiceControls').style.display = 'none';
                document.getElementById('conversationLog').style.display = 'none';
            }}

            function toggleMicrophone() {{
                if (!room || !localParticipant) return;
                
                isMuted = !isMuted;
                localParticipant.setMicrophoneEnabled(!isMuted);
                
                const micButton = document.getElementById('micButton');
                if (isMuted) {{
                    micButton.textContent = '🔇';
                    micButton.classList.add('muted');
                }} else {{
                    micButton.textContent = '🎤';
                    micButton.classList.remove('muted');
                }}
            }}

            async function loadTickets() {{
                try {{
                    const response = await fetch('/tickets');
                    const tickets = await response.json();
                    
                    const ticketsDiv = document.getElementById('tickets');
                    ticketsDiv.innerHTML = '';
                    
                    if (tickets.length === 0) {{
                        ticketsDiv.innerHTML = '<p>No tickets yet. Start a voice session to create one!</p>';
                        return;
                    }}
                    
                    tickets.forEach(ticket => {{
                        const ticketDiv = document.createElement('div');
                        ticketDiv.className = 'ticket';
                        ticketDiv.innerHTML = `
                            <div class="ticket-id">Ticket #${{ticket.id}}</div>
                            <div><strong>Name:</strong> ${{ticket.name}}</div>
                            <div><strong>Email:</strong> ${{ticket.email}}</div>
                            <div><strong>Phone:</strong> ${{ticket.phone}}</div>
                            <div><strong>Address:</strong> ${{ticket.address}}</div>
                            <div><strong>Issue:</strong> ${{ticket.issue}}</div>
                            <div><strong>Price:</strong> $${{ticket.price}}</div>
                            <div><strong>Created:</strong> ${{new Date(ticket.created_at).toLocaleString()}}</div>
                        `;
                        ticketsDiv.appendChild(ticketDiv);
                    }});
                }} catch (error) {{
                    console.error('Error loading tickets:', error);
                }}
            }}

            // Load tickets on page load
            window.onload = function() {{
                loadTickets();
            }};
        </script>
    </body>
    </html>
    """

@app.post("/get-token")
async def get_access_token(request: Request):
    """Generate LiveKit access token for voice bot connection"""
    try:
        data = await request.json()
        room_name = data.get("room", "voice-bot-demo")
        
        # Reload config to ensure we have latest env vars
        from config import LIVEKIT_CONFIG as fresh_config
        current_config = {
            "url": os.getenv("LIVEKIT_URL", "ws://localhost:7880"),
            "api_key": os.getenv("LIVEKIT_API_KEY", "devkey"),
            "api_secret": os.getenv("LIVEKIT_API_SECRET", "secret"),
        }
        
        logger.info(f"Generating token for room: {room_name}")
        logger.info(f"Fresh config from env: {current_config}")
        logger.info(f"Cached LIVEKIT_CONFIG: {LIVEKIT_CONFIG}")
        
        # Use current config instead of cached
        config_to_use = current_config
        
        # Create JWT token for LiveKit
        payload = {
            "iss": config_to_use["api_key"],
            "sub": "user-demo",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1),
            "name": "user-demo",
            "video": {
                "room": room_name,
                "roomJoin": True,
                "canPublish": True,
                "canSubscribe": True,
                "canPublishData": True
            }
        }
        
        access_token = jwt.encode(payload, config_to_use["api_secret"], algorithm="HS256")
        logger.info("JWT token generated successfully")
        
        # Create room and start voice bot for this specific room
        try:
            await dispatch_voice_bot_to_room(room_name, config_to_use)
            logger.info(f"Room {room_name} prepared for voice bot")
            
            # Start voice bot directly for this room
            await start_voice_bot_for_room(room_name, config_to_use)
            logger.info(f"Voice bot started for room {room_name}")
        except Exception as dispatch_error:
            logger.warning(f"Room preparation failed: {dispatch_error}")
        
        return {
            "token": access_token,
            "room": room_name
        }
        
    except Exception as e:
        logger.error(f"Error in get_access_token: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate access token: {str(e)}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time voice communication (legacy)"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "audio":
                # In a real implementation, you would process the audio here
                # For now, we'll simulate a bot response
                await asyncio.sleep(1)  # Simulate processing time
                
                # Send a simulated bot response
                response = {
                    "type": "bot_response",
                    "message": "Welcome to IT Help Desk. May I have your name and email?"
                }
                await manager.send_personal_message(json.dumps(response), websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/tickets")
async def get_tickets():
    """Get all support tickets"""
    try:
        tickets = db.get_all_tickets()
        return tickets
    except Exception as e:
        logger.error(f"Error fetching tickets: {e}")
        return []

@app.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: int):
    """Get a specific ticket by ID"""
    try:
        ticket = db.get_ticket(ticket_id)
        if ticket:
            return ticket
        else:
            return {"error": "Ticket not found"}
    except Exception as e:
        logger.error(f"Error fetching ticket {ticket_id}: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
