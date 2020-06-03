#!/bin/bash
set -e

# Exit if running
if [[ "`pidof -x $(basename $0) -o %PPID`" ]]; then exit; fi

RCLONE_POLL_INTERVAL=15
THRESHOLD=60
DRIVE=/dev/sda3
LOCAL_MOVIES_DIR="/home/ruxn/local/Movies"
LOCAL_TVSHOWS_DIR="/home/ruxn/local/TV Shows"
CLOUD_MOVIES_DIR="gcrypt:Movies"
CLOUD_TVSHOWS_DIR="gcrypt:TV Shows"

# Check app statuses
# IS_PLEX_ACTIVE=$(systemctl is-active plexmediaserver) || :
# IS_RADARR_ACTIVE=$(systemctl is-active radarr) || :
# IS_SONARR_ACTIVE=$(systemctl is-active sonarr) || :

# Get disk usage
USED=$(df -h | grep ${DRIVE} | awk '{print $5}' | sed 's/%//')
if [ ${USED} -lt ${THRESHOLD} ]
then
    echo "Disk usage: ${USED}%, skipping..."
    echo
    exit
fi
while [ ${USED} -ge ${THRESHOLD} ]
do
    echo "Disk usage has reached ${USED}%."
    echo
    # echo "Checking if Plex is running..."
    # echo ${IS_PLEX_ACTIVE}
    # echo "Checking if Radarr is running..."
    # echo ${IS_RADARR_ACTIVE}
    # echo "Checking if Sonarr is running..."
    # echo ${IS_SONARR_ACTIVE}
    # echo
    # if [ ${IS_PLEX_ACTIVE} = "active" ]
    # then
    #     echo "Stopping Plex Media Server..."
    #     sudo systemctl stop plexmediaserver
    #     echo "Plex Media Server stopped."
    # fi
    # if [ ${IS_RADARR_ACTIVE} = "active" ]
    # then
    #     echo "Stopping Radarr..."
    #     sudo systemctl stop radarr
    #     echo "Radarr stopped."
    # fi
    # if [ ${IS_SONARR_ACTIVE} = "active" ]
    # then
    #     echo "Stopping Sonarr..."
    #     sudo systemctl stop sonarr
    #     echo "Sonarr stopped."
    # fi
    # echo
    # Get the oldest entry
    OLDEST=$(find "${LOCAL_MOVIES_DIR}"/* "${LOCAL_TVSHOWS_DIR}"/* -maxdepth 0 -printf '%T+ %p\n' | sort | head -n 1 | awk '{$1="";print $0}' | sed 's/^ //')
    OLDEST_MTIME=$(find "${LOCAL_MOVIES_DIR}"/* "${LOCAL_TVSHOWS_DIR}"/* -maxdepth 0 -printf '%T+ %p\n' | sort | head -n 1 | awk '{print $1}')
    OLDEST_NAME=$(basename "${OLDEST}")
    if [ -d "${OLDEST}" ]
    then
        echo "${OLDEST} is chosen, which was last modified at ${OLDEST_MTIME}."
        if [[ "${OLDEST}" =~ "${LOCAL_MOVIES_DIR}" ]]
        then
            echo "${OLDEST} is a Movie. Moving it to cloud..."
            echo
            /usr/bin/rclone mkdir "${CLOUD_MOVIES_DIR}/${OLDEST_NAME}" --log-level NOTICE
            /usr/bin/rclone move "${OLDEST}" "${CLOUD_MOVIES_DIR}/${OLDEST_NAME}" --log-level NOTICE --delete-empty-src-dirs
            rmdir "${OLDEST}"
            echo "${OLDEST} is moved to cloud at $(date)"
	    echo
        elif [[ "${OLDEST}" =~ "${LOCAL_TVSHOWS_DIR}" ]]
        then
            echo "${OLDEST} is a TV series. Moving it to cloud..."
            echo
            /usr/bin/rclone mkdir "${CLOUD_TVSHOWS_DIR}/${OLDEST_NAME}" --log-level NOTICE
            /usr/bin/rclone move "${OLDEST}" "${CLOUD_TVSHOWS_DIR}/${OLDEST_NAME}" --log-level NOTICE --delete-empty-src-dirs
            rmdir "${OLDEST}"
            echo "${OLDEST} is moved to cloud at $(date)"
            echo
        fi
    else
        echo "${OLDEST} is not a directory, exiting..."
        echo
        exit 1
    fi
    # Get disk usage
    USED=$(df -h | grep ${DRIVE} | awk '{print $5}' | sed 's/%//')
done

# Wait until rclone polls for change
# sleep ${RCLONE_POLL_INTERVAL}
# if [ ${IS_PLEX_ACTIVE} = "active" ]
# then
#     echo "Starting Plex Media Server..."
#     sudo systemctl start plexmediaserver
#     echo "Plex Media Server started."
# fi
# if [ ${IS_RADARR_ACTIVE} = "active" ]
# then
#     echo "Starting Radarr..."
#     sudo systemctl start radarr
#     echo "Radarr started."
# fi
# if [ ${IS_SONARR_ACTIVE} = "active" ]
# then
#     echo "Starting Sonarr..."
#     sudo systemctl start sonarr
#     echo "Sonarr started."
# fi
echo
echo "============================================================================"
echo
