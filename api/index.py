"""
FocusGuard AI - Vercel Serverless Entry Point
"""
import sys
import os
from pathlib import Path

# Add src to path
root = Path(__file__).parent.parent
sys.path.insert(0, str(root / "src"))

from focus_guard.server import app

# Vercel expects 'app' variable
app = app
