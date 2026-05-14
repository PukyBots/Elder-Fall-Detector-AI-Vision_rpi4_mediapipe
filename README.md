# AI Fall Detector for Raspberry Pi 5 (Hailo-8L AI HAT)

This repository contains a real-time Fall Detection system built for the Raspberry Pi 5. It leverages the Hailo-8L AI HAT for hardware-accelerated pose estimation (`yolov8s_pose`), utilizing a connected USB camera and speaker for alerts.

## 📦 Hardware Requirements
*   **Raspberry Pi 5** (4GB or 8GB recommended)
*   **Raspberry Pi AI HAT** (Hailo-8L)
*   **USB Web Camera**
*   **Speaker / Audio Output** (3.5mm jack, USB, or HDMI)

## 🖥️ Software & System Requirements
*   **OS:** Raspberry Pi OS (64-bit, Bookworm based)
*   **Python:** Python 3.11+ (Default on Bookworm)

---

## 🛠️ Step-by-Step Installation Guide

Follow these exact commands on a brand new Raspberry Pi 5. **Do not skip any steps.**

### Step 1: Update System & Install Core Hailo Drivers
Open a terminal (`Ctrl+Alt+T`) and run:

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install hailo-all -y
sudo reboot
```

### Step 2: Install System Dependencies
After reboot, open a new terminal and install the required system packages:

```bash
sudo apt install -y python3-gi python3-gi-cairo
```

### Step 3: Clone the Hailo Examples Repo
```bash
cd ~
git clone https://github.com/hailo-ai/hailo-rpi5-examples.git
cd hailo-rpi5-examples
```

### Step 4: Setup the Python Virtual Environment
Create the venv with system site-packages (this gives access to numpy, cv2, gi, hailo, etc. that are already installed system-wide):

```bash
cd ~/hailo-rpi5-examples
python3 -m venv --system-site-packages venv_hailo_rpi_examples
source venv_hailo_rpi_examples/bin/activate
```

Install the required Python packages inside the venv:

```bash
pip install --upgrade pip setuptools wheel
pip install setproctitle python-dotenv
pip install "git+https://github.com/hailo-ai/hailo-apps-infra.git@25.7.0#egg=hailo-apps"
```

> **Note:** The `hailo-apps-infra` version (`25.7.0`) matches the tag in `hailo-rpi5-examples/config.yaml`. If you are using a different version of `hailo-rpi5-examples`, check `config.yaml` for the correct `hailo_apps_infra_branch_tag` value.

Create the `.env` file (required by the framework, can be empty):

```bash
touch ~/hailo-rpi5-examples/.env
```

### Step 5: Verify the Environment
Confirm everything is installed correctly:

```bash
cd ~/hailo-rpi5-examples
source venv_hailo_rpi_examples/bin/activate
python3 -c "from hailo_apps.hailo_app_python.apps.pose_estimation.pose_estimation_pipeline import GStreamerPoseEstimationApp; print('✅ hailo-apps OK')"
python3 -c "import setproctitle; print('✅ setproctitle OK')"
python3 -c "import hailo; print('✅ hailo OK')"
python3 -c "import cv2; print('✅ OpenCV OK')"
```

All four lines should print ✅. If any fail, re-check the steps above.

### Step 6: Clone This Repository & Generate Alarm Sound
```bash
cd ~
git clone https://github.com/Melroy-Sahyadri-ECE/fall-exterm.git
cd fall-exterm
```

The alarm sound file is not included in the repo. Generate it:

```bash
python3 -c "
import struct, wave, math
sr = 44100; duration = 2.0; samples = int(sr * duration); data = []
for i in range(samples):
    t = i / sr
    freq = 880 if int(t * 4) % 2 == 0 else 1100
    phase = (t * 4) % 1.0
    envelope = min(1.0, phase * 20) * max(0.0, 1.0 - (phase - 0.8) * 5)
    sample = int(30000 * envelope * math.sin(2 * math.pi * freq * t))
    data.append(struct.pack('<h', max(-32768, min(32767, sample))))
with wave.open('alarm.wav', 'w') as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(b''.join(data))
print('✅ alarm.wav created')
"
```

Or place your own `alarm.wav` file in the `fall-exterm/` directory.

### Step 7: Configure Audio Output
Check which audio devices are available:

```bash
aplay -l
```

The code in `room.py` uses HDMI output (`plughw:1,0`) by default. If your setup is different, edit the `play_alarm()` function in `room.py` (around line 149):

| Audio Output | Device String |
|---|---|
| HDMI-0 (default) | `plughw:1,0` |
| HDMI-1 | `plughw:2,0` |
| USB Speaker | Check card number with `aplay -l`, then `plughw:<card>,0` |
| 3.5mm Jack | `plughw:0,0` (if available) |

Test that sound works:

```bash
aplay -D plughw:1,0 ~/fall-exterm/alarm.wav
```

---

## 🚀 How to Run the Fall Detector

```bash
cd ~/fall-exterm
chmod +x run.sh
./run.sh
```

A window titled **"Fall Detector"** will appear showing the camera feed with pose skeletons and fall detection status.

---

## 🔧 Troubleshooting

| Problem | Solution |
|---|---|
| `HAILO_OUT_OF_PHYSICAL_DEVICES` | Another process is using the AI HAT. Kill it: `kill -9 $(fuser /dev/hailo0 2>/dev/null)` |
| No camera feed | Ensure USB camera is plugged into a blue USB 3.0 port. Check: `ls /dev/video*` |
| Permission error on `run.sh` | Run `chmod +x run.sh` first |
| `No module named 'setproctitle'` | `source ~/hailo-rpi5-examples/venv_hailo_rpi_examples/bin/activate && pip install setproctitle` |
| `.env file not found` warning | `touch ~/hailo-rpi5-examples/.env` |
| `Failed opening file ... yolov8s_pose.hef` | Find the model: `find /usr -name "*yolov8*pose*.hef"` and update `--hef-path` in `run.sh` line 44 |
| `undefined symbol: filter_letterbox` | Your tappas `.so` only exports `filter`. Check: `nm -D /usr/lib/aarch64-linux-gnu/hailo/tappas/post_processes/libyolov8pose_post.so \| grep filter`. Update `post_process_function` in `room.py` `CustomPoseApp` accordingly |
| No alarm sound | 1) Check `alarm.wav` exists in `fall-exterm/`. 2) Check audio device with `aplay -l`. 3) Test: `aplay -D plughw:1,0 alarm.wav` |
| Bounding boxes misaligned | Ensure `use-letterbox` matches your postprocess function. If using `filter` (not `filter_letterbox`), the code should have `pipeline.replace("use-letterbox=true", "use-letterbox=false")` in `CustomPoseApp` |
