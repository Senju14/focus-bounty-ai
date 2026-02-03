import os
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from dotenv import load_dotenv

from focus_guard.engine.groq_agent import GroqAgent

load_dotenv()

app = FastAPI(title="FocusGuard AI - Toxic Coach")

@app.middleware("http")
async def add_no_cache_header(request, call_next):
    response = await call_next(request)
    
    # Force 200 OK for all static assets to avoid 304 frustration in dev
    if response.status_code == 304:
        response.status_code = 200
        
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    # Remove all headers that trigger 304
    keys_to_del = ["ETag", "Last-Modified", "If-None-Match", "If-Modified-Since"]
    for key in keys_to_del:
        if key in response.headers:
            del response.headers[key]
            
    return response

# Initialize Groq Agent
groq_agent = GroqAgent()

# Custom Static Files to Disable Caching (Dev Mode)
class NoCacheStaticFiles(StaticFiles):
    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

# Serve static files with no cache
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", NoCacheStaticFiles(directory=str(static_path)), name="static")

@app.get("/")
async def landing():
    """Serve the Product Landing Page."""
    response = FileResponse(static_path / "landing.html")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

@app.get("/app")
async def demo_app():
    """Serve the Main Focus Application."""
    response = FileResponse(static_path / "app.html")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

@app.websocket("/ws/focus")
async def websocket_focus(websocket: WebSocket):
    """WebSocket endpoint for receiving distraction triggers."""
    await websocket.accept()
    
    try:
        while True:
            # Receive image from frontend
            data = await websocket.receive_json()
            image_data = data.get("image")
            
            # Allow fallback to text-only reason for legacy/testing
            reason = data.get("reason")
            
            result = {}
            if image_data:
                # Strip header if present (data:image/jpeg;base64,...)
                if "," in image_data:
                    image_data = image_data.split(",")[1]
                
                # Run full pipeline
                result = groq_agent.process_distraction(image_data)
            elif reason:
                # Legacy text-only path
                roast = groq_agent.generate_roast(reason)
                result = {"is_focused": False, "activity": reason, "tease": roast}
            
            if result:
                # Send result back
                await websocket.send_json(result)
                
    except WebSocketDisconnect:
        print("Client disconnected")
