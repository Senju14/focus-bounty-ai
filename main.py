"""
FocusGuard AI - Entry Point
Run locally: python main.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def main():
    import uvicorn
    
    print("Starting FocusGuard AI...")
    print("Open http://localhost:8000 in your browser")
    
    uvicorn.run(
        "focus_guard.server:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
