"""
FocusGuard AI - Vercel Serverless Entry Point
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from focus_guard.server import app

# Export for Vercel
handler = app
