#!/bin/bash

echo "Waiting for WiFi startup..."

sleep 20

# --------------------------------
# TRY CONNECTING TO SAVED WIFI
# --------------------------------
echo "Checking saved WiFi connection..."

CONNECTED=0

for i in {1..15}
do

    WIFI=$(nmcli -t -f DEVICE,STATE dev status | grep '^wlan0:connected')

    if [ ! -z "$WIFI" ]; then

        CONNECTED=1

        echo "Saved WiFi connected"

        break
    fi

    echo "Waiting for WiFi... ($i)"

    sleep 2

done


# --------------------------------
# START HOTSPOT ONLY IF NO WIFI
# --------------------------------
if [ $CONNECTED -eq 0 ]; then

    echo "No saved WiFi found"

    echo "Starting hotspot..."

    nmcli radio wifi on
    sleep 3


    # disconnect wlan
    nmcli dev disconnect wlan0 2>/dev/null

    sleep 2

    # delete old hotspot
    nmcli connection delete Hotspot 2>/dev/null

    sleep 1

    # start hotspot
    nmcli dev wifi hotspot \
        ifname wlan0 \
        ssid ElderCare \
        password 12345678

    if [ $? -eq 0 ]; then

        echo "Hotspot started"

    else

        echo "Hotspot failed"
    fi

else

    echo "Using saved WiFi"

fi


# --------------------------------
# START FLASK APP
# --------------------------------
cd /home/raspberry/elder_care

/home/raspberry/elder_care/venv/bin/python app.py
