"""
FocusGuard AI - FastAPI Server
Handles HTTP routes and WebSocket connections for real-time focus monitoring.
"""

import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

from focus_guard.engine.groq_agent import GroqAgent

load_dotenv()

# =============================================================================
# App Configuration
# =============================================================================

app = FastAPI(title="FocusGuard AI")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# Initialize AI agent (graceful fallback if no API key)
try:
    groq_agent = GroqAgent()
except Exception as e:
    print(f"Warning: Could not initialize GroqAgent: {e}")
    groq_agent = None


# =============================================================================
# Health Check (for Railway/Render)
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint for deployment platforms."""
    return {"status": "healthy", "service": "FocusGuard AI"}


# =============================================================================
# Middleware
# =============================================================================

@app.middleware("http")
async def add_no_cache_header(request, call_next):
    """Disable caching for development."""
    response = await call_next(request)
    
    if response.status_code == 304:
        response.status_code = 200
        
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    return response


# =============================================================================
# Static Files
# =============================================================================

class NoCacheStaticFiles(StaticFiles):
    """Static file handler with cache disabled."""
    
    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response


if os.path.exists(STATIC_DIR):
    app.mount("/static", NoCacheStaticFiles(directory=STATIC_DIR), name="static")


# =============================================================================
# Page Routes
# =============================================================================

def serve_page(filename: str) -> FileResponse:
    """Helper to serve HTML pages with no-cache headers."""
    path = os.path.join(STATIC_DIR, filename)
    response = FileResponse(path)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


@app.get("/")
async def landing():
    """Landing page."""
    return serve_page("landing.html")


@app.get("/app")
async def demo_app():
    """Main focus application."""
    return serve_page("app.html")


@app.get("/dashboard")
async def dashboard():
    """Session history dashboard."""
    return serve_page("dashboard.html")


@app.get("/settings")
async def settings():
    """User settings page."""
    return serve_page("settings.html")


# =============================================================================
# WebSocket Endpoint
# =============================================================================

@app.websocket("/ws/focus")
async def websocket_focus(websocket: WebSocket):
    """Real-time focus monitoring via WebSocket."""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            image_data = data.get("image")
            reason = data.get("reason")
            
            result = {}
            
            if image_data:
                # Remove data URL prefix if present
                if "," in image_data:
                    image_data = image_data.split(",")[1]
                result = groq_agent.process_distraction(image_data)
            elif reason:
                # Text-only trigger (e.g., tab switch)
                roast = groq_agent.generate_roast(reason)
                result = {"is_focused": False, "activity": reason, "tease": roast}
            
            if result:
                await websocket.send_json(result)
                
    except WebSocketDisconnect:
        pass
