import cv2
import numpy as np
import time
import math
import threading
import urllib.request
import subprocess
import speech_recognition as sr

from collections import deque
from tflite_runtime.interpreter import Interpreter

import shared_state
shared_state.latest_alert = "⚠ FALL DETECTED!"

# ==========================
# KEYPOINTS
# ==========================

NOSE = 0
L_EYE = 1
R_EYE = 2
L_EAR = 3
R_EAR = 4
L_SHOULDER = 5
R_SHOULDER = 6
L_ELBOW = 7
R_ELBOW = 8
L_WRIST = 9
R_WRIST = 10
L_HIP = 11
R_HIP = 12
L_KNEE = 13
R_KNEE = 14
L_ANKLE = 15
R_ANKLE = 16


SKELETON_EDGES = [
    (NOSE, L_EYE),
    (NOSE, R_EYE),
    (L_EYE, L_EAR),
    (R_EYE, R_EAR),
    (L_SHOULDER, R_SHOULDER),
    (L_SHOULDER, L_HIP),
    (R_SHOULDER, R_HIP),
    (L_HIP, R_HIP),
    (L_SHOULDER, L_ELBOW),
    (L_ELBOW, L_WRIST),
    (R_SHOULDER, R_ELBOW),
    (R_ELBOW, R_WRIST),
    (L_HIP, L_KNEE),
    (L_KNEE, L_ANKLE),
    (R_HIP, R_KNEE),
    (R_KNEE, R_ANKLE)
]


ACTIVITY_COLORS = {
    "Standing": (0, 255, 0),
    "Lying": (0, 165, 255),
    "FALL DETECTED": (0, 0, 255),
}


# ==========================
# ALERTS
# ==========================

topics = [
    "id_1",
    "id_2"
]

ALARM_WAV = "alarm.wav"

_last_alert = 0
voice_triggered = False
voice_trigger_time = 0

output_frame = None


# ==========================
# ALERT FUNCTION
# ==========================

def send_alert(reason="Emergency"):

    global _last_alert

    if time.time() - _last_alert < 10:
        return

    _last_alert = time.time()

    print(f"[ALERT] {reason}")

    # ntfy notification
    def _send():

        for topic in topics:

            try:

                url = f"https://ntfy.sh/{topic}"

                req = urllib.request.Request(
                    url,
                    data=reason.encode(),
                    headers={
                        "Title": "Room Emergency Alert",
                        "Priority": "max",
                        "Tags": "warning",
                    },
                )

                urllib.request.urlopen(req, timeout=5)

                print(f"[NTFY] Alert sent to {topic}")

            except Exception as e:

                print(f"[NTFY ERROR] {topic}:", e)

    threading.Thread(target=_send, daemon=True).start()


    # play alarm using VLC
    try:

        subprocess.Popen(
            [
                "cvlc",
                "--play-and-exit",
                ALARM_WAV
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        print("[ALARM] Playing alarm.wav")

    except Exception as e:
        print("[ALARM ERROR]", e)



def voice_listener():

    global voice_triggered, voice_trigger_time

    recognizer = sr.Recognizer()

    with sr.Microphone() as source:

        print("[VOICE] Adjusting noise...")

        recognizer.adjust_for_ambient_noise(
            source,
            duration=2
        )

        print("[VOICE] Listening for help keywords...")

        while True:

            try:
                audio = recognizer.listen(
                    source,
                    timeout=2,
                    phrase_time_limit=3
                )

                text = recognizer.recognize_google(audio)
                text = text.lower()

                print("[VOICE] Heard:", text)

                keywords = [
                    "help",
                    "help me",
                    "save me",
                    "emergency",
                    "please help"
                ]


                for word in keywords:

                    if word in text:

                        print("[VOICE] HELP DETECTED")

                        voice_triggered = True
                        voice_trigger_time = time.time()

                        send_alert(
                            "VOICE HELP DETECTED"
                        )

                        break

            except sr.WaitTimeoutError:
                pass

            except sr.UnknownValueError:
                pass

            except Exception as e:
                print("[VOICE ERROR]", e)

# ==========================
# MOVENET MODEL
# ==========================

class MoveNet:

    def __init__(self, model_path):

        self.interpreter = Interpreter(model_path=model_path)

        self.interpreter.allocate_tensors()

        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        self.height = self.input_details[0]['shape'][1]
        self.width = self.input_details[0]['shape'][2]

        print(f"[MODEL] Input size: {self.width}x{self.height}")

    def detect(self, frame):

        h, w, _ = frame.shape

        image = cv2.resize(frame, (self.width, self.height))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        input_tensor = np.expand_dims(image, axis=0)
        input_tensor = input_tensor.astype(np.uint8)

        self.interpreter.set_tensor(
            self.input_details[0]['index'],
            input_tensor
        )

        self.interpreter.invoke()

        keypoints = self.interpreter.get_tensor(
            self.output_details[0]['index']
        )

        keypoints = keypoints[0][0]

        points = []
        confs = []

        for kp in keypoints:
            y, x, conf = kp

            points.append([x * w, y * h])
            confs.append(conf)

        return np.array(points), np.array(confs)


# ==========================
# FALL DETECTOR
# ==========================

class FallDetector:

    def __init__(self):

        self.history = deque(maxlen=10)
        self.fall_frames = 0
        self.is_fallen = False
        self.fall_time = 0

    def classify(self, keypoints, confs, frame_h):

        if np.sum(confs > 0.3) < 6:
            return "Standing", False

        ls = keypoints[L_SHOULDER]
        rs = keypoints[R_SHOULDER]
        lh = keypoints[L_HIP]
        rh = keypoints[R_HIP]

        shoulder_center = (ls + rs) / 2
        hip_center = (lh + rh) / 2

        dx = shoulder_center[0] - hip_center[0]
        dy = shoulder_center[1] - hip_center[1]

        angle = abs(math.degrees(math.atan2(dx, dy)))

        visible_y = keypoints[confs > 0.3][:, 1]
        visible_x = keypoints[confs > 0.3][:, 0]

        body_height = visible_y.max() - visible_y.min()
        body_width = visible_x.max() - visible_x.min()

        aspect = 0

        if body_height > 1:
            aspect = body_width / body_height

        pose = "Standing"

        if angle > 45 or aspect > 1.2:
            pose = "Lying"

        self.history.append((pose, angle))

        fall_detected = False

        if len(self.history) >= 5:

            recent = list(self.history)

            upright_before = any(
                p[0] == "Standing"
                for p in recent[:-2]
            )

            now_lying = recent[-1][0] == "Lying"

            sudden_change = (
                abs(recent[-1][1] - recent[0][1]) > 20
            )

            if now_lying and sudden_change:
                self.fall_frames += 1
            else:
                self.fall_frames = 0

        if self.fall_frames >= 2 and not self.is_fallen:
            self.is_fallen = True
            self.fall_time = time.time()
            fall_detected = True


        if self.is_fallen:
            if time.time() - self.fall_time > 5:

                self.is_fallen = False
                self.fall_frames = 0

            else:
                pose = "FALL DETECTED"

        return pose, fall_detected


# ==========================
# DRAWING
# ==========================


def draw_skeleton(frame, keypoints, confs, color):

    pts = {}

    for i in range(17):

        if confs[i] > 0.3:

            x, y = int(keypoints[i][0]), int(keypoints[i][1])

            pts[i] = (x, y)

    for s, e in SKELETON_EDGES:

        if s in pts and e in pts:
            cv2.line(frame, pts[s], pts[e], color, 2)

    for p in pts.values():
        cv2.circle(frame, p, 4, color, -1)


# ==========================
# MAIN
# ==========================

def run_detector():

    global output_frame
    global voice_triggered, voice_trigger_time

    print("Loading MoveNet...")

    model = MoveNet("movenet_lightning.tflite")

    detector = FallDetector()

    # camera
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        cap = cv2.VideoCapture(1)

    if not cap.isOpened():
        print("Camera not found")
        return

    # resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # voice thread
    voice_thread = threading.Thread(
        target=voice_listener,
        daemon=True
    )

    voice_thread.start()

    print("Starting fall detector...")

    while True:

        ret, frame = cap.read()

        if not ret:
            continue

        # pose detection
        keypoints, confs = model.detect(frame)

        # classify pose
        pose, fallen = detector.classify(
            keypoints,
            confs,
            frame.shape[0]
        )

        color = ACTIVITY_COLORS.get(
            pose,
            (255, 255, 255)
        )

        # draw skeleton
        draw_skeleton(frame, keypoints, confs, color)

        # show pose
        cv2.putText(
            frame,
            pose,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            color,
            2
        )

        # fall alert
        if fallen:
            send_alert("FALL DETECTED")

        # voice warning
        if voice_triggered:

            if time.time() - voice_trigger_time < 5:

                cv2.putText(
                    frame,
                    "VOICE HELP DETECTED!",
                    (20, 90),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    3
                )

            else:
                voice_triggered = False

        # IMPORTANT
        output_frame = frame.copy()

    cap.release()
    cv2.destroyAllWindows()
