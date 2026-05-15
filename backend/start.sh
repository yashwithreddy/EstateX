#!/bin/bash
cd "$(dirname "$0")"
export DEBUG=true
exec .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
