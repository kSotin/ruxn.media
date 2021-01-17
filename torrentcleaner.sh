#!/bin/bash
set -e

# Exit if running
if [[ "`pidof -x $(basename $0) -o %PPID`" ]]
then
    echo "[Skipping] Currently clearing, skipping..."
    exit
fi

THRESHOLD=85
TARGET=75
DRIVE=/dev/md3

# Get disk usage
USED=$(df -h | grep ${DRIVE} | awk '{print $5}' | sed 's/%//')
if [ ${USED} -lt ${THRESHOLD} ]
then
    echo "[Skipping] Disk usage: ${USED}%, skipping..."
    exit
else
    while [ ${USED} -ge ${TARGET} ]
    do
        echo "[Working] Disk usage: ${USED}%."
        /usr/bin/python3 "$(cd `dirname $0`; pwd)/torrentcleaner.py"
        # Wait for apps to refresh
        sleep 70
        # Get disk usage
        USED=$(df -h | grep ${DRIVE} | awk '{print $5}' | sed 's/%//')
    done
fi
