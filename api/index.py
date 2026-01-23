"""
Vercel Serverless Function Entry Point
Note: WebSocket is not fully supported on Vercel serverless.
For full functionality, deploy to Railway, Render, or a VPS.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from mangum import Mangum

# Import the main app
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.backend.app import app

# Wrap for Vercel
handler = Mangum(app, lifespan="off")
