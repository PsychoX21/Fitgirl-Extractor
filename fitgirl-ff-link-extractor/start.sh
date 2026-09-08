#!/bin/bash
set -e

# Start Xvfb virtual display if not already running
if [ -z "$DISPLAY" ] || [ "$DISPLAY" = ":99" ]; then
    export DISPLAY=:99
    # Clean up old lock files if any
    rm -f /tmp/.X99-lock
    Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
    sleep 2
fi

# Launch FastAPI web server with uvicorn
exec uvicorn app:app --host 0.0.0.0 --port "${PORT:-8000}"
