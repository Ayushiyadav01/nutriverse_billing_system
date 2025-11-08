#!/bin/bash

# Change to the server directory
cd "$(dirname "$0")/.."

# Run the FastAPI server with uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

