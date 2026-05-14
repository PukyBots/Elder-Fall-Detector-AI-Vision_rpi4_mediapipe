# AI Fall Detector for Raspberry Pi 5 (Hailo-8L AI HAT)

This repository contains a real-time Fall Detection system built for the Raspberry Pi 5. It leverages the Hailo-8L AI HAT for hardware-accelerated pose estimation (`yolov8s_pose`), utilizing an connected USB camera and speaker for alerts.

## 📦 Hardware Requirements
*   **Raspberry Pi 5** (4GB or 8GB recommended)
*   **Raspberry Pi AI HAT** (Hailo-8L)
*   **USB Web Camera**
*   **Speaker / Audio Output** (3.5mm jack, USB, or HDMI)

## 🖥️ Software & System Requirements
*   **OS:** Raspberry Pi OS (64-bit, Bookworm based)
*   **Python:** Python 3.11 (Default on Bookworm)
*   **Frameworks:** HailoRT, Tappas, and GStreamer

---

## 🛠️ Step-by-Step Installation Guide

Follow these steps exactly to set up a brand new Raspberry Pi 5 for this project.

### Step 1: Update System & Install Core Hailo Drivers
First, ensure the system is up-to-date and install the core Hailo software stack. Open a terminal and run:

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install hailo-all -y
```
**Reboot your Raspberry Pi** after the installation finishes:
```bash
sudo reboot
```

### Step 2: Setup the Hailo Environment
The script relies on the Hailo-Apps API and GStreamer wrappers provided by the official Raspberry Pi examples.

```bash
cd ~
git clone https://github.com/hailo-ai/hailo-rpi5-examples.git
cd hailo-rpi5-examples
source setup_env.sh
```
*(Note: `setup_env.sh` will automatically download the necessary AI models like YOLOv8 and compile the Python virtual environment located at `~/hailo-rpi5-examples/venv_hailo_rpi_examples`)*

### Step 3: Clone This Repository
Clone this exact project repository into your home directory:

```bash
cd ~
git clone https://github.com/Melroy-Sahyadri-ECE/fall-exterm.git
cd fall-exterm
```

### Step 4: Install Extra Dependencies (if any)
Activate the Hailo virtual environment and install any standard Python packages your `room.py` might import (like `requests` for webhooks, or `pygame` for speakers):

```bash
source ~/hailo-rpi5-examples/venv_hailo_rpi_examples/bin/activate
pip install requests
```

---

## 🚀 How to Run the Fall Detector

Because the pipeline relies on the Hailo AI hardware and GStreamer, it **requires** specific environment variables to be set before execution. 

To run the detector, execute the following commands in your terminal:

```bash
# 1. Export required hardware and software environment variables
export DISPLAY=:0
export QT_QPA_PLATFORM=xcb
export GST_PLUGIN_FEATURE_RANK="vaapidecodebin:NONE"
export PYTHONPATH="$HOME/hailo-rpi5-examples/hailo-apps:$PYTHONPATH"
export HAILO_ENV_FILE="$HOME/hailo-rpi5-examples/.env"
export TAPPAS_POST_PROC_DIR="/usr/lib/aarch64-linux-gnu/hailo/tappas/post_processes"
export XAUTHORITY="$HOME/.Xauthority"

# 2. Navigate to the hailo-apps directory (crucial for local Hailo library paths)
cd ~/hailo-rpi5-examples/hailo-apps

# 3. Execute the fall detector script using the Hailo Virtual Environment's Python
~/hailo-rpi5-examples/venv_hailo_rpi_examples/bin/python ~/fall-exterm/room.py --input usb --width 640 --height 480
```

### Troubleshooting
*   **`HAILO_OUT_OF_PHYSICAL_DEVICES` Error:** This means another process is already using the AI HAT. Kill the other process (or background services) before running the script.
*   **No Camera Feed:** Ensure your USB camera is plugged in and recognized on `/dev/video0`.
