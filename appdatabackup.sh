#!/bin/bash
set -e

PLEX_ARCHIVE=/home/ruxn/plexbackup.tar
RADARR_ARCHIVE=/home/ruxn/radarrbackup.tar
SONARR_ARCHIVE=/home/ruxn/sonarrbackup.tar

echo "Checking if Plex is running..."
IS_PLEX_ACTIVE=$(systemctl is-active plexmediaserver) || :
echo ${IS_PLEX_ACTIVE}
echo "Checking if Radarr is running..."
IS_RADARR_ACTIVE=$(systemctl is-active radarr) || :
echo ${IS_RADARR_ACTIVE}
echo "Checking if Sonarr is running..."
IS_SONARR_ACTIVE=$(systemctl is-active sonarr) || :
echo ${IS_SONARR_ACTIVE}
echo
if [ ${IS_PLEX_ACTIVE} = "active" ]
then
    echo "Stopping Plex Media Server..."
    sudo systemctl stop plexmediaserver
    echo "Plex Media Server stopped."
fi
if [ ${IS_RADARR_ACTIVE} = "active" ]
then
    echo "Stopping Radarr..."
    sudo systemctl stop radarr
    echo "Radarr stopped."
fi
if [ ${IS_SONARR_ACTIVE} = "active" ]
then
    echo "Stopping Sonarr..."
    sudo systemctl stop sonarr
    echo "Sonarr stopped."
fi
echo

echo "Creating Plex's archive..."
sudo tar -cf ${PLEX_ARCHIVE} -C "/var/lib/plexmediaserver/Library/Application Support" --exclude="Plex Media Server/Cache" "Plex Media Server"
echo "Creating Radarr's archive..."
sudo tar -cf ${RADARR_ARCHIVE} -C "/home/ruxn/.config" "Radarr"
echo "Creating Sonarr's archive..."
sudo tar -cf ${SONARR_ARCHIVE} -C "/home/ruxn/.config" "NzbDrone"
echo

echo "Starting rclone move..."
/usr/bin/rclone move ${PLEX_ARCHIVE} gdrive_crypt:backups --log-level NOTICE
/usr/bin/rclone move ${RADARR_ARCHIVE} gdrive_crypt:backups --log-level NOTICE
/usr/bin/rclone move ${SONARR_ARCHIVE} gdrive_crypt:backups --log-level NOTICE
echo "Backup completed at $(date)"
echo

if [ ${IS_PLEX_ACTIVE} = "active" ]
then
    echo "Starting Plex Media Server..."
    sudo systemctl start plexmediaserver
    echo "Plex Media Server started."
fi
if [ ${IS_RADARR_ACTIVE} = "active" ]
then
    echo "Starting Radarr..."
    sudo systemctl start radarr
    echo "Radarr started."
fi
if [ ${IS_SONARR_ACTIVE} = "active" ]
then
    echo "Starting Sonarr..."
    sudo systemctl start sonarr
    echo "Sonarr started."
fi
echo
echo "============================================================================"
echo
