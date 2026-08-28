#!/bin/bash
echo "Starting AdapFit..."
echo ""
echo "1. Starting backend server on http://localhost:8000"
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"
echo ""
echo "2. Starting mobile app..."
cd mobile && npx expo start &
MOBILE_PID=$!
echo "   Mobile PID: $MOBILE_PID"
echo ""
echo "Backend: http://localhost:8000/docs"
echo "Mobile: Expo DevTools will open"
echo ""
echo "Press Ctrl+C to stop both"
wait $BACKEND_PID $MOBILE_PID
