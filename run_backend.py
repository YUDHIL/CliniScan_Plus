"""
Launcher for CliniScan+ FastAPI REST API Server
Runs on http://127.0.0.1:8000
"""

import sys
import os

# Set UTF-8 encoding for standard output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0" if os.getenv("PORT") else "127.0.0.1")

    print("=" * 65)
    print("Starting CliniScan+ Hospital-Grade FastAPI REST API Server...")
    print(f"Base API URL: http://{host}:{port}")
    print(f"Interactive API Docs: http://{host}:{port}/docs")
    print("=" * 65)
    uvicorn.run("src.api_server:app", host=host, port=port, reload=False)
