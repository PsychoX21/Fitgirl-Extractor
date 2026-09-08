#!/bin/bash
set -e

# Start lightweight Xvfb virtual display with minimal memory footprint (1024x768x16 bit color = <5MB RAM)
if [ -z "$DISPLAY" ] || [ "$DISPLAY" = ":99" ]; then
    export DISPLAY=:99
    rm -f /tmp/.X99-lock
    Xvfb :99 -screen 0 1024x768x16 -ac -nolisten tcp -noreset &
    sleep 1
fi

# Launch FastAPI web server with single lightweight uvicorn worker
exec uvicorn app:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 1 --limit-concurrency 50
