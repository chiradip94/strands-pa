#!/bin/bash
# start.sh

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

echo "Starting Strands Chat Frontend..."
echo "Serving files from: $DIR"

# Try to use python's http.server (usually available)
if command -v python3 &>/dev/null; then
    echo "Access your app at http://localhost:8080"
    cd "$DIR" && python3 -m http.server 8080
elif command -v python &>/dev/null; then
    echo "Access your app at http://localhost:8080"
    cd "$DIR" && python -m SimpleHTTPServer 8080
else
    echo "Error: Python is not installed. Please open index.html manually in your browser."
fi
