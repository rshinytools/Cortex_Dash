#!/bin/bash
# ABOUTME: Simple startup script for frontend to avoid nohup issues
# ABOUTME: Runs Next.js dev server in background

# Kill any existing Next.js processes
pkill -f "next dev" 2>/dev/null || true

# Start the dev server
exec npm run dev