#!/bin/bash

PORT=8000
URL="http://localhost:$PORT"

# Start python server in background
python -m http.server $PORT &

SERVER_PID=$!

# Small delay to make sure the server starts
sleep 1

# Open browser
xdg-open "$URL" >/dev/null 2>&1

# Stop server cleanly on Ctrl+C
trap "kill $SERVER_PID" INT

wait $SERVER_PID