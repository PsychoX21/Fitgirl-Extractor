#!/bin/bash
# Start Xvfb virtual frame buffer on Linux containers so Chrome has a full real display
if [ -z "$DISPLAY" ]; then
    export DISPLAY=:99
    Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
    sleep 1
fi

# Start the FastAPI server
exec uvicorn app:app --host 0.0.0.0 --port "${PORT:-8000}"
