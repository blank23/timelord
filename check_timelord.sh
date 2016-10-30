#!/bin/sh

ps aux | grep 'python timelord.py' | grep -v 'grep' && echo "running"
