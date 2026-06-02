from flask import Flask, render_template, request, Response, jsonify
import subprocess
import cv2
import time
import threading
import os

import fall_detect
import shared_state

app = Flask(__name__)

# ==================================================
# AUDIO
# ==================================================

def play_connected_sound_wifi():

    try:

        mp3 = os.path.join(
            os.path.dirname(__file__),
            "connect.mp3"
        )

        print("PLAYING WIFI CONNECT SOUND")
        print("FILE:", mp3)

        subprocess.Popen(
            ["mpg123", mp3],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    except Exception as e:

        print("Audio error:", e)


def play_connected_sound_ap():

    try:

        mp3 = os.path.join(
            os.path.dirname(__file__),
            "connect_ap.mp3"
        )

        print("PLAYING AP SOUND")
        print("FILE:", mp3)

        subprocess.Popen(
            ["mpg123", mp3],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    except Exception as e:

        print("Audio error:", e)


# ==================================================
# WIFI FUNCTIONS
# ==================================================

def scan_wifi():
    try:
        subprocess.run(
            ["nmcli", "device", "set", "wlan0", "managed", "yes"],
            capture_output=True
        )

        subprocess.run(
            ["nmcli", "device", "wifi", "rescan"],
            capture_output=True
        )

        time.sleep(3)

        result = subprocess.check_output([
            "nmcli",
            "-t",
            "-f",
            "SSID,SIGNAL",
            "device",
            "wifi",
            "list"
        ]).decode()

        networks = []
        seen = set()

        for line in result.splitlines():

            parts = line.rsplit(":", 1)

            if len(parts) != 2:
                continue

            ssid = parts[0].strip()
            signal = parts[1].strip()

            if (
                ssid
                and ssid not in seen
                and ssid != "ElderCare"
            ):
                seen.add(ssid)
                networks.append((ssid, signal))

        print("Scanned networks:", networks)

        return networks

    except Exception as e:
        print("WiFi Scan Error:", e)
        return []


def connect_wifi(ssid, password):

    try:

        print(f"Attempting connection to: {ssid}")

        r = subprocess.run(
            ["sudo", "nmcli", "connection", "down", "ElderCare_AP"],
            capture_output=True,
            text=True
        )

        print("DOWN STDOUT:", r.stdout)
        print("DOWN STDERR:", r.stderr)

        time.sleep(5)

        r = subprocess.run(
            [
                "sudo",
                "nmcli",
                "device",
                "wifi",
                "connect",
                ssid,
                "password",
                password
            ],
            capture_output=True,
            text=True
        )

        print("CONNECT STDOUT:", r.stdout)
        print("CONNECT STDERR:", r.stderr)
        print("RETURN CODE:", r.returncode)

        time.sleep(15)

        current_ssid = subprocess.getoutput(
            "iwgetid -r"
        ).strip()

        ip_addr = subprocess.getoutput(
            "hostname -I | awk '{print $1}'"
        ).strip()

        print("CURRENT SSID:", current_ssid)
        print("CURRENT IP:", ip_addr)

        if current_ssid == ssid and ip_addr:

            print("WiFi Connected Successfully")

            threading.Thread(
                target=play_connected_sound_wifi,
                daemon=True
            ).start()

            return True

        print("Connection verification failed")

        subprocess.run(
            ["sudo", "nmcli", "connection", "up", "ElderCare_AP"]
        )

        return False

    except Exception as e:

        print("WiFi Error:", e)

        subprocess.run(
            ["sudo", "nmcli", "connection", "up", "ElderCare_AP"]
        )

        return False

def get_current_wifi():

    try:

        ssid = subprocess.getoutput(
            "iwgetid -r"
        ).strip()

        if ssid:
            return ssid

        active = subprocess.getoutput(
            "nmcli -t -f NAME connection show --active"
        )

        if "ElderCare_AP" in active:
            return "Hotspot Mode (ElderCare)"

        return "Not Connected"

    except Exception as e:

        print(e)
        return "Unknown"


# ==================================================
# CAMERA STREAM
# ==================================================

def generate_frames():

    while True:

        try:

            if fall_detect.output_frame is None:
                time.sleep(0.03)
                continue

            frame = fall_detect.output_frame.copy()

            ret, buffer = cv2.imencode(
                '.jpg',
                frame
            )

            if not ret:
                continue

            frame_bytes = buffer.tobytes()

            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n'
                + frame_bytes +
                b'\r\n'
            )

        except Exception as e:

            print("Video Stream Error:", e)
            time.sleep(1)


# ==================================================
# ROUTES
# ==================================================

@app.route('/')
def index():

    wifi_list = scan_wifi()
    current_wifi = get_current_wifi()

    return render_template(
        'webpage.html',
        wifi_list=wifi_list,
        current_wifi=current_wifi
    )


@app.route('/connect', methods=['POST'])
def connect():

    ssid = request.form['ssid'].strip()
    password = request.form['password'].strip()

    connecting_page = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Connecting...</title>
        <meta http-equiv="refresh" content="20;url=/" />
        <style>
            body {{
                font-family: Arial;
                text-align: center;
                margin-top: 80px;
                background: #111;
                color: white;
            }}

            .box {{
                width: 80%;
                margin: auto;
                padding: 30px;
                border-radius: 15px;
                background: #222;
            }}

            h1 {{
                color: #00ff88;
            }}
        </style>
    </head>
    <body>

        <div class="box">

            <h1>Connecting to WiFi...</h1>

            <h2>{ssid}</h2>

            <p>Please wait 20 seconds...</p>

            <p>
            Your device will disconnect
            from "ElderCare" temporarily.
            </p>

            <p>
            If successful, connect your laptop
            to <b>{ssid}</b> and refresh.
            </p>

            <p>
            If unsuccessful, reconnect to
            <b>ElderCare</b> hotspot.
            </p>

        </div>

    </body>
    </html>
    """

    def do_connect():
        time.sleep(1)
        connect_wifi(ssid, password)

    threading.Thread(
        target=do_connect,
        daemon=True
    ).start()

    return connecting_page


@app.route('/video_feed')
def video_feed():

    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@app.route('/push_alert')
def push_alert():

    msg = shared_state.latest_alert
    shared_state.latest_alert = ""

    return jsonify({
        "alert": msg
    })


# ==================================================
# MAIN
# ==================================================

if __name__ == '__main__':

    detector_thread = threading.Thread(
        target=fall_detect.run_detector,
        daemon=True
    )

    detector_thread.start()

    app.run(
        host='0.0.0.0',
        port=5000,
        threaded=True
    )