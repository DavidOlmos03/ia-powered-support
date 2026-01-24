#!/bin/sh
# Startup script for Railway deployment

# Use Railway's PORT variable, default to 8000 if not set
PORT=${PORT:-8000}

# Start uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
