#!/bin/bash

# Change to the frontend directory
cd "$(dirname "$0")/.."

# Run the Streamlit app
streamlit run streamlit_app.py --server.port 8501

