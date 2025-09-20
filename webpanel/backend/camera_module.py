"""
This module provides functions to interact with video cameras using OpenCV.

Functions:
- get_available_cameras(): 
  Detects and returns all available video devices in the system. Returns a dictionary 
  where the key is the device index (int) and the value is the device name (str).

- generate_frames(device_id, resolution): 
  A Python generator function. It opens the specified video device, sets the resolution, 
  and continuously captures video frames. Each frame is encoded into JPEG format 
  and returned via the `yield` keyword. This is suitable for a Flask streaming response.
"""

import cv2
import time
import platform

def get_available_cameras():
    """
    Scans for and returns a dictionary of available video capture devices.
    """
    available_cameras = {}
    # Device indices are usually between 0 and 9, so we can check this range
    for i in range(10):
        # On Windows, using CAP_DSHOW is more stable and avoids some console errors.
        if platform.system() == "Windows":
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        else:
            cap = cv2.VideoCapture(i)

        if cap.isOpened():
            # isOpened() checks if the device can actually be opened
            available_cameras[i] = f"Device {i}"
            cap.release() # Release the capture immediately after checking
    return available_cameras

def generate_frames(device_id, resolution):
    """
    A generator function that captures frames from a specified device,
    encodes them as JPEG, and yields them for streaming.
    """
    print(f"Attempting to open device {device_id} with resolution {resolution[0]}x{resolution[1]}...")
    
    try:
        device_id_int = int(device_id)
    except (ValueError, TypeError):
        print(f"Error: Invalid device ID '{device_id}'. It must be an integer.")
        return

    # Initialize video capture with the given parameters, using CAP_DSHOW on Windows
    if platform.system() == "Windows":
        cap = cv2.VideoCapture(device_id_int, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(device_id_int)
    
    # Check if the device was opened successfully
    if not cap.isOpened():
        print(f"Error: Could not open video device {device_id}.")
        return

    # Set the desired resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
    
    # A short delay to ensure camera settings are applied
    time.sleep(1)

    # Check if the resolution was set successfully
    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Actual resolution for device {device_id}: {actual_width}x{actual_height}")


    try:
        while True:
            # Read one frame
            success, frame = cap.read()
            if not success:
                print(f"Cannot read frame from device {device_id}. It might be disconnected.")
                break
            else:
                # Encode the frame into JPEG format
                ret, buffer = cv2.imencode('.jpg', frame)
                if not ret:
                    print("Failed to encode frame.")
                    continue
                
                frame_bytes = buffer.tobytes()
                # Use the yield keyword to send the frame as part of the HTTP response
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    finally:
        # Ensure the camera resource is released when the generator ends
        print(f"Releasing device {device_id}...")
        cap.release()