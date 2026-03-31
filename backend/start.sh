#!/bin/bash
cd /Users/yashwithreddy/MiniProject/EstateX/backend
export DEBUG=true
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
