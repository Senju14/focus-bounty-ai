#!/usr/bin/env python3
"""
FocusBounty - Entry Point
Run: python main.py
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

if __name__ == "__main__":
    import uvicorn
    
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║                                                            ║
    ║   🎯 FocusBounty - Vigilante Focus Agent                   ║
    ║                                                            ║
    ║   AI-powered real-time focus enforcement                   ║
    ║   Built with Gemini + Opik for Comet Resolution Hackathon  ║
    ║                                                            ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    print("  Open: http://localhost:8000")
    print()
    
    uvicorn.run(
        "backend.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
