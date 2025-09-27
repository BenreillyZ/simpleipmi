"""
This module is the main program for the Flask web application.
It is responsible for handling HTTP requests, rendering HTML pages, and providing a video streaming service.

Imported modules:
- flask: A lightweight web framework.
- camera_module: Our custom module for handling all camera-related operations.
  - CameraManager: A class that encapsulates camera detection and frame generation.
"""

# Import necessary libraries
from flask import Flask, render_template, Response, request
# Import the CameraManager class from our camera_module
from camera_module import CameraManager

# Initialize the Flask application
app = Flask(__name__)

# Create a single, shared instance of the CameraManager.
# This instance will handle all camera operations for the application.
camera_manager = CameraManager()

@app.route('/')
def index():
    """Main page route, renders the HTML page with control options."""
    # Get the user's current selections from the request's URL parameters
    selected_device_str = request.args.get('device')
    selected_res_str = request.args.get('resolution')

    try:
        selected_device_int = int(selected_device_str)
    except (ValueError, TypeError):
        selected_device_int = None

    # Use the camera_manager instance to get available cameras
    available_cameras = camera_manager.get_available_cameras()
    
    # Define a list of standard resolutions
    resolutions = {
        "640x480": (640, 480),
        "800x600": (800, 600),
        "1280x720": (1280, 720),  # 720p
        "1920x1080": (1920, 1080), # 1080p
    }
    
    # Render the template
    return render_template('index.html', 
                           cameras=available_cameras, 
                           resolutions=resolutions.keys(),
                           selected_device=selected_device_int,
                           selected_res=selected_res_str)

@app.route('/video_feed')
def video_feed():
    """Video feed route, returns a video stream."""
    # Get device ID and resolution from URL query parameters
    device_id_str = request.args.get('device', '0')
    res_str = request.args.get('resolution', '640x480')
    
    # Convert parameters to the correct types
    try:
        device_id = int(device_id_str)
        width, height = map(int, res_str.split('x'))
        resolution = (width, height)
    except (ValueError, AttributeError):
        print(f"Invalid parameters received. Using defaults.")
        device_id = 0
        resolution = (640, 480)

    # Use the camera_manager instance to generate frames
    return Response(camera_manager.generate_frames(device_id, resolution),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # Start the Flask development server
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)