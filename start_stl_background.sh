#!/bin/bash
# Background STL Extraction Starter
# Runs the automated extraction in the background with nohup

echo "🚀 Starting C++ STL extraction in background..."
echo "📄 Processing pages 37-407 every 20 minutes"
echo "📁 Output: outputs/cpp_stl_containers/"
echo "📋 Logs: cpp_stl_extraction.log"

# Start in background with nohup
nohup python3 automated_stl_extraction.py > cpp_stl_background.log 2>&1 &

# Get the process ID
PID=$!
echo "✅ Started with PID: $PID"
echo "$PID" > cpp_stl_extraction.pid

echo ""
echo "🔧 Control commands:"
echo "  Check status: python3 stl_control.py status"
echo "  View logs:    python3 stl_control.py logs"
echo "  Stop:         kill $PID"
echo ""
echo "🎯 The process will run every 20 minutes until all 370 pages are processed"