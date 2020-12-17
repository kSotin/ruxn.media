#!/bin/bash
set -e

THRESHOLD=95
DRIVE=/dev/sda3

# Get disk usage
USED=$(df -h | grep ${DRIVE} | awk '{print $5}' | sed 's/%//')
if [ ${USED} -lt ${THRESHOLD} ]
then
    echo "[Skipping] Disk usage: ${USED}%, skipping..."
    exit
else
    echo "[Working] Disk usage: ${USED}%, pausing all downloads..."
    /usr/bin/python3 "$(cd `dirname $0`; pwd)/emergencystop.py"
fi
