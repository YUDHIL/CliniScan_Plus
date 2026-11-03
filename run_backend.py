"""
Launcher for CliniScan+ FastAPI REST API Server
Binds to 0.0.0.0 for cloud deployment (Render, Docker) & local development.
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
    raw_port = os.getenv("PORT", "8000").strip()
    port = int(raw_port) if raw_port.isdigit() else 8000
    host = os.getenv("HOST", "0.0.0.0").strip() or "0.0.0.0"

    print("=" * 65, flush=True)
    print("Starting CliniScan+ Hospital-Grade FastAPI REST API Server...", flush=True)
    print(f"Base API URL: http://{host}:{port}", flush=True)
    print(f"Interactive API Docs: http://{host}:{port}/docs", flush=True)
    print(f"Listening Interface: {host} (Bound to 0.0.0.0 for Cloud Container Port Scans)", flush=True)
    print("=" * 65, flush=True)
    uvicorn.run("src.api_server:app", host=host, port=port, reload=False)
