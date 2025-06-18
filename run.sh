#!/bin/bash

# Start FastAPI (server.py) in background
uvicorn backend.server:app --host 0.0.0.0 --port 8001 &

# Start Flask (app.py) on main Render port (5000)
gunicorn app:app -b 0.0.0.0:5000
