#!/bin/bash

PLEX_LOCAL="/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Plug-in Support/Databases"
RADARR_LOCAL=/home/ruxn/.config/Radarr/Backups/scheduled
SONARR_LOCAL=/var/lib/sonarr/Backups/scheduled
PLEX_CLOUD=gdrive:backups/plexbackups
RADARR_CLOUD=gdrive:backups/radarrbackups
SONARR_CLOUD=gdrive:backups/sonarrbackups

if [ -d "${PLEX_LOCAL}" -a "$(ls "${PLEX_LOCAL}")" ]
then
    echo "Syncing PLEX backups..."
    /usr/bin/rclone sync "${PLEX_LOCAL}" "${PLEX_CLOUD}" --log-level INFO
else
    echo "No archives found in local PLEX backup directory, skipping..."
    echo
fi
if [ -d "${RADARR_LOCAL}" -a "$(ls "${RADARR_LOCAL}")" ]
then
    echo "Syncing RADARR backups..."
    /usr/bin/rclone sync "${RADARR_LOCAL}" "${RADARR_CLOUD}" --log-level INFO
else
    echo "No archives found in local RADARR backup directory, skipping..."
    echo
fi
if [ -d "${SONARR_LOCAL}" -a "$(ls "${SONARR_LOCAL}")" ]
then
    echo "Syncing SONARR backups..."
    /usr/bin/rclone sync "${SONARR_LOCAL}" "${SONARR_CLOUD}" --log-level INFO
else
    echo "No archives found in local SONARR backup directory, skipping..."
    echo
fi
