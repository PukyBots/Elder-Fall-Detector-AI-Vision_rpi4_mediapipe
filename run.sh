#!/bin/bash
# ==========================================
# Fall Detector Runner for Raspberry Pi 5
# ==========================================

# Portability: Adjust this if your hailo-rpi5-examples folder is elsewhere
HAILO_EXAMPLES_DIR="$HOME/tce/hailo-rpi5-examples"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Initializing Hailo AI Environment..."

# 1. Check if the Hailo examples directory exists
if [ ! -d "$HAILO_EXAMPLES_DIR" ]; then
    echo "ERROR: Hailo examples directory not found at $HAILO_EXAMPLES_DIR"
    echo "Please update the HAILO_EXAMPLES_DIR variable in this script."
    exit 1
fi

# 2. Check for device conflicts
if lsof /dev/hailo0 > /dev/null 2>&1; then
    echo "WARNING: /dev/hailo0 is currently in use by another process."
    echo "Attempting to stop background service..."
    sudo systemctl stop fall-detector.service 2>/dev/null || echo "Could not stop service automatically. You may need to kill the process manually."
fi

# 3. Source the Hailo Virtual Environment
source "$HAILO_EXAMPLES_DIR/venv_hailo_rpi_examples/bin/activate"

# 4. Export required environment variables
export DISPLAY=:0
export QT_QPA_PLATFORM=xcb
export GST_PLUGIN_FEATURE_RANK="vaapidecodebin:NONE"
export PYTHONPATH="$HAILO_EXAMPLES_DIR/hailo-apps:$PYTHONPATH"
export HAILO_ENV_FILE="$HAILO_EXAMPLES_DIR/.env"
export TAPPAS_POST_PROC_DIR="/usr/lib/aarch64-linux-gnu/hailo/tappas/post_processes"
export XAUTHORITY="$HOME/.Xauthority"

# 5. Navigate to hailo-apps so local paths work correctly
cd "$HAILO_EXAMPLES_DIR/hailo-apps"

echo "Starting Fall Detector Pipeline on USB Camera..."

# 6. Run the fall detector script
python "$SCRIPT_DIR/room.py" --input usb --width 640 --height 480
