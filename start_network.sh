#!/bin/bash

echo "=================================="
echo "Starting ElderCare Network Manager"
echo "=================================="

sleep 10

echo "Waiting for NetworkManager..."
sleep 5

CONNECTED=0

echo "Checking for saved WiFi..."

for i in {1..5}
do
    ACTIVE_WIFI=$(nmcli -t -f DEVICE,STATE device | grep "^wlan0:connected")

    if [ ! -z "$ACTIVE_WIFI" ]
    then
        SSID=$(iwgetid -r)
        echo "Connected to saved WiFi: $SSID"
        CONNECTED=1
        break
    fi

    echo "Attempt $i/5"
    sleep 1
done

if [ $CONNECTED -eq 0 ]
then

    echo "No WiFi connection found"
    echo "Starting ElderCare AP"

    sudo nmcli connection up ElderCare_AP

    RET=$?

    echo "Hotspot return code: $RET"

    if [ $RET -eq 0 ]
    then
        echo "Hotspot started successfully"
        mpg123 /home/raspberry/elder_care/connect_ap.mp3 &

    else
        echo "Hotspot failed"
    fi
fi

echo "Starting Flask Application"

cd /home/raspberry/elder_care

exec /home/raspberry/elder_care/venv/bin/python app.py