import sys
from pathlib import Path
import uvicorn
import asyncio
import signal

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

async def run_server():
    """Start the FocusGuard AI web server with graceful shutdown."""
    config = uvicorn.Config(
        "focus_guard.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        ws_ping_interval=None,
        ws_ping_timeout=None
    )
    server = uvicorn.Server(config)
    await server.serve()

def main():
    """Entry point."""
    
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("\n🛑 FocusGuard AI Stopped.")

if __name__ == "__main__":
    main()
