#!/bin/bash

# Function to kill the existing process on port 5000
kill_process() {
    local port=5000
    local pid=$(lsof -t -i:$port)
    if [ -n "$pid" ]; then
        echo "Killing process on port $port (PID: $pid)"
        kill -9 $pid
    fi
}

# Delete the app2.log file (change the path to the actual file location)
rm /path/to/app2.log

# Kill the existing process on port 5000
kill_process

# Navigate to the directory where your app.py is located
cd /path/to/your/app/directory

# Start your app.py script
python3 app.py

