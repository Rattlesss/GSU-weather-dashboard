#!/usr/bin/env bash
set -e

source venv/bin/activate

echo "=== Running data pipeline ==="
python src/run_pipeline.py

echo "Configuring..."
sleep 2

echo "=== Launching dashboard ==="
streamlit run dashboard/app.py
