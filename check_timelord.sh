#!/bin/sh

ps aux | grep 'timelord.py' | grep -v 'grep' && exit
cd /root/projects/timelord
/usr/bin/python timelord.py &
