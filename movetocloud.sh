#!/bin/bash
set -e

# Exit if running
if [[ "`pidof -x $(basename $0) -o %PPID`" ]]
then
    echo "[Skipping] Currently moving, skipping..."
    exit
fi

THRESHOLD=75
DRIVE=/dev/md3
LOCAL_MOVIES_DIR="/home/ruxn/local/Movies"
LOCAL_TVSHOWS_DIR="/home/ruxn/local/TV Shows"
CLOUD_MOVIES_DIR="gcrypt:Movies"
CLOUD_TVSHOWS_DIR="gcrypt:TV Shows"

# Get disk usage
USED=$(df -h | grep ${DRIVE} | awk '{print $5}' | sed 's/%//')
if [ ${USED} -lt ${THRESHOLD} ]
then
    echo "[Skipping] Disk usage: ${USED}%, skipping..."
    exit
fi
while [ ${USED} -ge ${THRESHOLD} ]
do
    echo "[Working] Disk usage: ${USED}%."
    # Get the oldest entry
    OLDEST=$(find "${LOCAL_MOVIES_DIR}"/* "${LOCAL_TVSHOWS_DIR}"/* -maxdepth 0 -printf '%T+ %p\n' | sort | head -n 1 | awk '{$1="";print $0}' | sed 's/^ //')
    OLDEST_MTIME=$(find "${LOCAL_MOVIES_DIR}"/* "${LOCAL_TVSHOWS_DIR}"/* -maxdepth 0 -printf '%T+ %p\n' | sort | head -n 1 | awk '{print $1}')
    OLDEST_NAME=$(basename "${OLDEST}")
    if [ -d "${OLDEST}" ]
    then
        if [[ "${OLDEST}" =~ "${LOCAL_MOVIES_DIR}" ]]
        then
            echo "[Working] Selecting ${OLDEST_NAME}..."
            /usr/bin/rclone mkdir "${CLOUD_MOVIES_DIR}/${OLDEST_NAME}"
            /usr/bin/rclone move "${OLDEST}" "${CLOUD_MOVIES_DIR}/${OLDEST_NAME}" --log-level INFO --delete-empty-src-dirs
            echo "[Working] Cleaning up..."
            rmdir "${OLDEST}"
            echo "[Working] ${OLDEST_NAME} moved to cloud."
        elif [[ "${OLDEST}" =~ "${LOCAL_TVSHOWS_DIR}" ]]
        then
            echo "[Working] Selecting ${OLDEST_NAME}..."
            /usr/bin/rclone mkdir "${CLOUD_TVSHOWS_DIR}/${OLDEST_NAME}"
            /usr/bin/rclone move "${OLDEST}" "${CLOUD_TVSHOWS_DIR}/${OLDEST_NAME}" --log-level INFO --delete-empty-src-dirs
            echo "[Working] Cleaning up..."
            rmdir "${OLDEST}"
            echo "[Working] ${OLDEST_NAME} moved to cloud."
        fi
    else
        echo "[Exception] ${OLDEST} is not a directory, exiting..."
        exit 1
    fi
    # Get disk usage
    USED=$(df -h | grep ${DRIVE} | awk '{print $5}' | sed 's/%//')
done
