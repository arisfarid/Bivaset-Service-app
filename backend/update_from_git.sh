#!/bin/bash
echo "Updating from GitHub..."
git fetch origin
git reset --hard origin/main
echo "Restarting bot..."
pkill -f "python3 bot.py"
nohup python3 bot.py &
echo "Bot updated and restarted."