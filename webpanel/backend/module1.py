"""
This module provides a class to manage and interact with video cameras using OpenCV.

Classes:
- CameraManager: 
  A class to detect available cameras and generate streaming video frames.
  It is designed for easy integration into web applications (e.g., Flask).
"""

import cv2
import time
import platform
from typing import Dict, Any, Generator, Tuple

class CameraManager:
    """
    Manages camera detection and frame generation.

    This class encapsulates camera functionalities, making it easier to integrate
    into a larger application. It supports specifying a video capture backend
    for broader hardware compatibility.
    """

    def __init__(self, backend: Any = None):
        """
        Initializes the CameraManager.

        Args:
            backend (Any, optional): The OpenCV video capture backend to use
                                     (e.g., cv2.CAP_DSHOW, cv2.CAP_MSMF).
                                     If None, a suitable default is chosen based on the OS.
        """
        if backend is None:
            # On Windows, CAP_DSHOW is often more stable and provides better device info.
            self.backend = cv2.CAP_DSHOW if platform.system() == "Windows" else cv2.CAP_ANY
        else:
            self.backend = backend
        print(f"CameraManager initialized using backend: {self.backend}")

    def get_available_cameras(self) -> Dict[int, str]:
        """
        Scans for and returns a dictionary of available video capture devices.
        
        This method checks device indices 0 through 9, which is standard for most systems.

        Returns:
            Dict[int, str]: A dictionary where the key is the device index (int) and
                            the value is a descriptive name (e.g., "Device 0").
        """
        available_cameras = {}
        for i in range(10):
            cap = cv2.VideoCapture(i, self.backend)
            if cap.isOpened():
                available_cameras[i] = f"Device {i}"
                cap.release()
        return available_cameras

    def generate_frames(self, device_id: int, resolution: Tuple[int, int]) -> Generator[bytes, None, None]:
        """
        A generator function that captures frames from a specified device,
        encodes them as JPEG, and yields them for streaming.

        Args:
            device_id (int): The index of the video device to use.
            resolution (Tuple[int, int]): The desired resolution (width, height).

        Yields:
            bytes: A byte string for a single JPEG frame, formatted for HTTP streaming.
        """
        print(f"Attempting to open device {device_id} with resolution {resolution[0]}x{resolution[1]}...")
        
        cap = cv2.VideoCapture(device_id, self.backend)
        
        if not cap.isOpened():
            print(f"Error: Could not open video device {device_id}.")
            return

        # Set the desired resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
        
        # --- SPEED OPTIMIZATION ---
        # The original time.sleep(1) was removed to significantly speed up camera initialization.
        # A very short delay can sometimes be useful, but 1 second is often excessive.
        # time.sleep(0.1) # Optional: uncomment if your camera needs a moment to apply settings.

        actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"Actual resolution for device {device_id}: {actual_width}x{actual_height}")

        if actual_width != resolution[0] or actual_height != resolution[1]:
            print("Warning: The camera does not support the requested resolution. Using default.")

        try:
            while True:
                success, frame = cap.read()
                if not success:
                    print(f"Cannot read frame from device {device_id}. It might be disconnected.")
                    break
                
                # Encode the frame into JPEG format
                ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                if not ret:
                    print("Failed to encode frame.")
                    continue
                
                frame_bytes = buffer.tobytes()
                
                # Yield the frame in a format suitable for multipart streaming
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        finally:
            print(f"Releasing device {device_id}...")
            cap.release()


# Example of how to use the CameraManager class
if __name__ == '__main__':
    # You can specify a backend, for example cv2.CAP_MSMF on Windows
    # camera_manager = CameraManager(backend=cv2.CAP_MSMF)
    camera_manager = CameraManager()

    print("Searching for available cameras...")
    cameras = camera_manager.get_available_cameras()

    if not cameras:
        print("No cameras found.")
    else:
        print("Available cameras:", cameras)
        
        # Example: stream from the first available camera
        first_camera_id = list(cameras.keys())[0]
        resolution = (640, 480)
        
        print(f"\n--- Starting stream from camera {first_camera_id} ---")
        print("--- (This is a generator, in a real app you would use it in a streaming response) ---")
        
        frame_generator = camera_manager.generate_frames(device_id=first_camera_id, resolution=resolution)
        
        # Demonstrate getting a few frames from the generator
        try:
            for i in range(5):
                frame = next(frame_generator)
                print(f"Generated frame {i+1}, length: {len(frame)} bytes")
            
            print("\nSuccessfully generated a few frames. The generator is ready for integration.")
        except StopIteration:
            print("Could not generate frames. The camera may have been disconnected or an error occurred.")
