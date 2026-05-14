# AI Fall Detector for Raspberry Pi 5 (Hailo-8L AI HAT)

This repository contains a real-time Fall Detection system built for the Raspberry Pi 5. It leverages the Hailo-8L AI HAT for hardware-accelerated pose estimation (`yolov8s_pose`), utilizing a connected USB camera and speaker for alerts.

## 📦 Hardware Requirements
*   **Raspberry Pi 5** (4GB or 8GB recommended)
*   **Raspberry Pi AI HAT** (Hailo-8L)
*   **USB Web Camera**
*   **Speaker / Audio Output** (3.5mm jack, USB, or HDMI)

## 🖥️ Software & System Requirements
*   **OS:** Raspberry Pi OS (64-bit, Bookworm based)
*   **Python:** Python 3.11 (Default on Bookworm)

---

## 🛠️ Step-by-Step Installation Guide

Follow these exact commands on a brand new Raspberry Pi 5. **Do not skip any steps.**

### Step 1: Update System & Install Core Hailo Drivers
Open a terminal (`Ctrl+Alt+T`) and run:

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install hailo-all -y
```
**Reboot your Raspberry Pi** after the installation finishes:
```bash
sudo reboot
```

### Step 2: Setup the Hailo Python Environment
Once rebooted, open a new terminal. The script relies on the official Hailo examples which provide necessary GStreamer wrappers.

```bash
cd ~
git clone https://github.com/hailo-ai/hailo-rpi5-examples.git
cd hailo-rpi5-examples
source setup_env.sh
```
*(Wait for this script to finish. It will automatically download the YOLOv8 AI models and compile the Python virtual environment located at `~/hailo-rpi5-examples/venv_hailo_rpi_examples`)*

### Step 3: Clone This Repository
Clone this project repository into your home directory:

```bash
cd ~
git clone https://github.com/Melroy-Sahyadri-ECE/fall-exterm.git
cd fall-exterm
```

---

## 🚀 How to Run the Fall Detector

Because the pipeline relies on the Hailo AI hardware and GStreamer, it **requires** specific environment variables to be set before execution. 

We have provided an automated `run.sh` script to make this 100% foolproof!

Simply run these commands in your terminal:

```bash
cd ~/fall-exterm
chmod +x run.sh
./run.sh
```

### Troubleshooting
*   **`HAILO_OUT_OF_PHYSICAL_DEVICES` Error:** This means another AI process or background service is already using the AI HAT. You can forcefully kill other processes using it by running: `kill -9 $(fuser /dev/hailo0 2>/dev/null)`
*   **No Camera Feed:** Ensure your USB camera is plugged into a blue USB 3.0 port and recognized by the Pi.
*   **Permissions Error on `./run.sh`:** Ensure you ran `chmod +x run.sh` first to make the script executable.
