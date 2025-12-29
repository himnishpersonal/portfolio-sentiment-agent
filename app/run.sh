#!/bin/bash
# Run the Streamlit app

cd "$(dirname "$0")/.."
streamlit run app/streamlit_app.py --server.port 8501 --server.address 0.0.0.0

