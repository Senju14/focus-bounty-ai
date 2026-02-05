"""
FocusGuard AI - Entry Point
Run: python run_local.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def main():
    import uvicorn
    from focus_guard.server import app
    
    # Use PORT env var for Replit, default 5000
    port = int(os.environ.get("PORT", 5000))
    
    print("🚀 Starting FocusGuard AI...")
    print(f"🌐 Open http://localhost:{port} in your browser")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
