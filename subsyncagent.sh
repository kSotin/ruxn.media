#!/bin/bash

cd `dirname $0`
while :
do
    while [ $(cat tosync | wc -l) -ge 2 ]
    do
        VIDEO=$(sed -n 1p tosync)
        SUBTITLES=$(sed -n 2p tosync)
        /home/ruxn/.local/bin/ffsubsync "${VIDEO}" -i "${SUBTITLES}" --overwrite-input
        flock tosync sed -i '1,2d' tosync
    done
    sleep 5
done
