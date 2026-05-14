#!/bin/bash
# ==========================================
# Fall Detector Runner for Raspberry Pi 5
# ==========================================

echo "Initializing Hailo AI Environment..."

# 1. Source the Hailo Virtual Environment
source ~/hailo-rpi5-examples/venv_hailo_rpi_examples/bin/activate

# 2. Export all required environment variables for the Hailo AI HAT and GStreamer
export DISPLAY=:0
export QT_QPA_PLATFORM=xcb
export GST_PLUGIN_FEATURE_RANK="vaapidecodebin:NONE"
export PYTHONPATH="$HOME/hailo-rpi5-examples/hailo-apps:$PYTHONPATH"
export HAILO_ENV_FILE="$HOME/hailo-rpi5-examples/.env"
export TAPPAS_POST_PROC_DIR="/usr/lib/aarch64-linux-gnu/hailo/tappas/post_processes"
export XAUTHORITY="$HOME/.Xauthority"

# 3. Navigate to hailo-apps so local paths in the Hailo libraries work correctly
cd ~/hailo-rpi5-examples/hailo-apps

echo "Starting Fall Detector Pipeline on USB Camera..."

# 4. Run the fall detector script
python ~/fall-exterm/room.py --input usb --width 640 --height 480
