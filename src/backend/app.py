"""
FocusBounty - FastAPI Backend
Main server with REST API and WebSocket for real-time focus monitoring.
"""

import asyncio
import base64
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
import pathlib

import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel

from .perception import perception
from .agent import FocusAgent
from .actions import execute_action

FRONTEND_DIR = pathlib.Path(__file__).parent.parent / "frontend"


class SessionConfig(BaseModel):
    strictness: int = 5


class SessionResponse(BaseModel):
    session_id: str
    status: str
    message: str


class AppState:
    """Manages active focus sessions."""
    
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
        self.active_session_id: Optional[str] = None
        
    def create_session(self, config: SessionConfig) -> str:
        session_id = f"session_{int(time.time())}"
        self.sessions[session_id] = {
            "id": session_id,
            "agent": FocusAgent(strictness=config.strictness),
            "config": config,
            "started_at": datetime.now(),
            "running": False
        }
        self.active_session_id = session_id
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        return self.sessions.get(session_id)
    
    def end_session(self, session_id: str):
        if session_id in self.sessions:
            self.sessions[session_id]["running"] = False
            if self.active_session_id == session_id:
                self.active_session_id = None


state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    print("FocusBounty starting...")
    print("  API: http://localhost:8000")
    print("  Docs: http://localhost:8000/docs")
    yield
    print("FocusBounty stopped")


app = FastAPI(
    title="FocusBounty",
    description="Vigilante Focus Agent - AI-powered focus enforcement",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve frontend dashboard."""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return HTMLResponse("<h1>FocusBounty API</h1><p>Frontend not found. Go to /docs for API.</p>")


@app.get("/css/style.css")
async def get_css():
    """Serve CSS file."""
    return FileResponse(FRONTEND_DIR / "css" / "style.css")


@app.get("/js/script.js")
async def get_js():
    """Serve JavaScript file."""
    return FileResponse(FRONTEND_DIR / "js" / "script.js")


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {
        "name": "FocusBounty",
        "status": "running",
        "version": "1.0.0",
        "active_session": state.active_session_id
    }


@app.post("/api/session/start", response_model=SessionResponse)
async def start_session(config: SessionConfig = SessionConfig()):
    """Start a new focus session."""
    session_id = state.create_session(config)
    session = state.get_session(session_id)
    session["running"] = True
    
    return SessionResponse(
        session_id=session_id,
        status="active",
        message=f"Session started with strictness {config.strictness}/10"
    )


@app.post("/api/session/{session_id}/stop")
async def stop_session(session_id: str):
    """Stop a focus session and return statistics."""
    session = state.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    state.end_session(session_id)
    stats = session["agent"].get_stats()
    
    return {
        "status": "stopped",
        "session_id": session_id,
        "stats": stats
    }


@app.get("/api/session/{session_id}/stats")
async def get_stats(session_id: str):
    """Get session statistics."""
    session = state.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session["agent"].get_stats()


@app.post("/api/benchmark")
async def run_benchmark_endpoint():
    """Run benchmark evaluation and return results."""
    try:
        from .evaluation import run_benchmark
        results = run_benchmark()
        return JSONResponse(content=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/experiment")
async def run_experiment_endpoint(name: str = "focusbounty_eval"):
    """Run Opik experiment and return results."""
    try:
        from .evaluation import run_opik_experiment
        results = run_opik_experiment(name)
        return JSONResponse(content={"status": "completed", "experiment": name})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/focus")
async def websocket_focus(websocket: WebSocket):
    """Real-time focus monitoring via WebSocket."""
    await websocket.accept()
    print("WebSocket connected")
    
    session_id = None
    
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "start":
                config = SessionConfig(strictness=data.get("strictness", 5))
                session_id = state.create_session(config)
                state.get_session(session_id)["running"] = True
                
                await websocket.send_json({
                    "type": "session_started",
                    "session_id": session_id
                })
            
            elif msg_type == "stop":
                if session_id:
                    session = state.get_session(session_id)
                    if session:
                        stats = session["agent"].get_stats()
                        state.end_session(session_id)
                        await websocket.send_json({
                            "type": "session_stopped",
                            "stats": stats
                        })
                session_id = None

            elif msg_type == "frame":
                if session_id:
                    session = state.get_session(session_id)
                    if session and session["running"]:
                        image_data = data.get("image")
                        if image_data:
                            result = await process_frame(session, image_data)
                            if result:
                                await websocket.send_json(result)
            
    except WebSocketDisconnect:
        print("WebSocket disconnected")
        if session_id:
            state.end_session(session_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        if session_id:
            state.end_session(session_id)


async def process_frame(session: Dict, image_data: str) -> Optional[Dict]:
    """Process a single frame and return analysis results."""
    try:
        if "base64," in image_data:
            image_data = image_data.split("base64,")[1]
        
        img_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return None
        
        perception_data = perception.analyze(frame)
        decision = session["agent"].decide(perception_data)
        action_result = execute_action(decision)
        
        return {
            "type": "update",
            "perception": perception_data,
            "decision": decision,
            "action": action_result
        }
    except Exception as e:
        print(f"Frame processing error: {e}")
        return None
