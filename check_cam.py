# camera_view.py
# Raspberry Pi 4 Camera Live View

import cv2

# Open camera
cap = cv2.VideoCapture(0)

# Check camera
if not cap.isOpened():
    print("Camera not detected")
    exit()

while True:

    ret, frame = cap.read()

    if not ret:
        print("Failed to capture frame")
        break

    # Show camera feed
    cv2.imshow("Raspberry Pi Camera", frame)

    # Press q to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()