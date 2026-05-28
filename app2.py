from flask import Flask, render_template, request, Response
import subprocess
import cv2
import time
import threading
import fall_detect

app = Flask(__name__)

# ==========================
# WIFI FUNCTIONS
# ==========================

def scan_wifi():

    try:

        result = subprocess.check_output(
            [
                'nmcli',
                '-t',
                '-f',
                'SSID,SIGNAL',
                'device',
                'wifi',
                'list'
            ]
        ).decode()

        networks = []

        for line in result.split('\n'):

            if ':' in line:

                parts = line.split(':')

                if len(parts) >= 2:

                    ssid = parts[0]
                    signal = parts[1]

                    if ssid.strip() != "":
                        networks.append((ssid, signal))

        return networks

    except Exception as e:

        print("WiFi Scan Error:", e)
        return []


def connect_wifi(ssid, password):

    try:

        print(f"Connecting to WiFi: {ssid}")

        # STOP hotspot completely
        subprocess.run(
            ['nmcli', 'connection', 'down', 'Hotspot'],
            capture_output=True
        )

        subprocess.run(
            ['nmcli', 'connection', 'delete', 'Hotspot'],
            capture_output=True
        )

        time.sleep(3)

        # enable normal wifi mode
        subprocess.run(
            ['nmcli', 'radio', 'wifi', 'on'],
            capture_output=True
        )

        time.sleep(2)

        # connect to wifi
        result = subprocess.run(
            [
                'nmcli',
                'device',
                'wifi',
                'connect',
                ssid,
                'password',
                password
            ],
            capture_output=True,
            text=True
        )

        print(result.stdout)
        print(result.stderr)

        return result.returncode == 0

    except Exception as e:

        print("WiFi Connect Error:", e)

        return False
        

def get_current_wifi():

    try:

        result = subprocess.check_output(
            [
                'nmcli',
                '-t',
                '-f',
                'ACTIVE,SSID',
                'device',
                'wifi'
            ]
        ).decode()

        for line in result.split('\n'):

            if line.startswith("yes:"):

                return line.split(":")[1]

        return "Not Connected"

    except Exception as e:

        print(e)
        return "Unknown"


# ==========================
# CAMERA STREAM
# ==========================

def generate_frames():

    while True:

        try:

            # get frame from fall detector
            if fall_detect.output_frame is None:

                time.sleep(0.03)
                continue

            frame = fall_detect.output_frame.copy()

            ret, buffer = cv2.imencode('.jpg', frame)

            if not ret:
                continue

            frame_bytes = buffer.tobytes()

            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' +
                frame_bytes +
                b'\r\n'
            )

        except Exception as e:

            print("Video Stream Error:", e)
            time.sleep(1)


# ==========================
# ROUTES
# ==========================

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

    ssid = request.form['ssid']
    password = request.form['password']

    # immediate response page
    connecting_page = f"""
    <!DOCTYPE html>
    <html>

    <head>

        <title>Connecting...</title>

        <meta http-equiv="refresh" content="10;url=/" />

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

            <p>Please wait 10 seconds...</p>

            <p>
            Raspberry Pi is trying to connect.
            Your phone may disconnect from hotspot temporarily.
            </p>

            <p>
            After connection:
            </p>

            <h3>
            http://raspberrypi.local:5000
            </h3>

        </div>

    </body>

    </html>
    """

    # start connection in background
    def do_connect():

        time.sleep(2)

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


# ==========================
# MAIN
# ==========================

if __name__ == '__main__':

    # start fall detector thread
    detector_thread = threading.Thread(
        target=fall_detect.run_detector,
        daemon=True
    )

    detector_thread.start()

    # start flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        threaded=True
    )