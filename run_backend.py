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
    print("=" * 65)
    print("Starting CliniScan+ Hospital-Grade FastAPI REST API Server...")
    print("Base API URL: http://127.0.0.1:8000")
    print("Interactive API Docs: http://127.0.0.1:8000/docs")
    print("=" * 65)
    uvicorn.run("src.api_server:app", host="127.0.0.1", port=8000, reload=False)
