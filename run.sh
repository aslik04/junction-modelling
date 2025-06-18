#!/bin/bash

# Start FastAPI server in background
cd backend || exit
nohup uvicorn server:app --host 0.0.0.0 --port 8000 > ../fastapi.log 2>&1 &
cd ..

# Start Flask app in foreground
python app.py
