from libcamera import controls, Transform
from gpiozero import Button, LED
import time
from datetime import datetime, timedelta
from signal import pause
from flask import Flask, Response, send_from_directory, request, jsonify
from picamera2 import Picamera2
import cv2
import threading
from subprocess import check_call
import os
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Flask app
app = Flask(__name__)
IMAGE_DIRECTORY = "img/"

# Ensure image directory exists
os.makedirs(IMAGE_DIRECTORY, exist_ok=True)

# --- Global State & Locks ---
state_lock = threading.Lock()
camera_lock = threading.Lock()
blink_lock = threading.Lock()

timer = time.time()
client_status = {'last_ping': None, 'status': False}

# --- RPi Zero W Optimization Settings ---
RPI_ZERO_MODE = True  # Optimize for Raspberry Pi Zero W (512MB RAM, single-core)

# --- Battery Optimization Settings ---
INACTIVITY_IDLE_TIMEOUT = 300  # 5 minutes to idle mode
INACTIVITY_SHUTDOWN_TIMEOUT = 0  # DISABLED - No automatic shutdown
CLIENT_TIMEOUT = 60  # Client idle timeout
MONITOR_CHECK_INTERVAL = 10  # Reduce polling frequency (from 5s to 10s)
VIDEO_STREAM_ACTIVE = False  # Track if video stream is being watched
DEEP_SLEEP_ENABLED = False  # DISABLED - Aggressive power saving off

# --- Camera Streaming Optimization (RPi Zero W) ---
STREAM_RESOLUTION = (320, 480)  # Reduced for RPi Zero W (was 480x640)
STREAM_FRAMERATE = 10  # 10 FPS for smoothness on Zero (was 20 FPS)
STREAM_JPEG_QUALITY = 50  # Reduced quality for faster encoding (was 60)
STREAM_BUFFER_SIZE = 8  # Reduced buffer to save RAM on Zero
STREAM_TIMEOUT = 30  # Timeout for stream operations

# --- Image Capture Optimization ---
CAPTURE_RESOLUTION = (2592, 1944)  # High quality capture (full camera sensor)
CAPTURE_JPEG_QUALITY = 85  # High quality for captures
AUTOFOCUS_TIMEOUT = 5  # Max time for autofocus

# --- Threading Optimization ---
FLASK_WORKERS = 1 if RPI_ZERO_MODE else 4  # Single worker for Zero W
FLASK_THREADS = 2 if RPI_ZERO_MODE else 4  # Limited threads for Zero W

# --- Hardware Setup ---
# Configure camera but DON'T start it immediately - only start on demand
camera = None
camera_initialized = False

def initialize_camera():
    """Lazy initialization of camera with optimized settings for RPi Zero W."""
    global camera, camera_initialized
    if camera_initialized and camera:
        # Check if camera is still functional
        try:
            # Try a simple operation to verify camera is responsive
            camera.capture_buffer("main")
            return
        except Exception as e:
            logging.warning(f"Camera appears to be initialized but not responsive: {e}")
            # Try to restart camera
            try:
                camera.stop()
            except:
                pass
            camera_initialized = False
    
    # Clean up any existing camera instance
    if camera:
        try:
            camera.stop()
        except:
            pass
        camera = None
    
    try:
        camera = Picamera2()
        transform = Transform(rotation=90)
        
        # Optimize camera configuration for RPi Zero W
        # Use proper format for streaming
        main_config = {
            "format": 'XBGR8888',  # Using XBGR for better OpenCV compatibility
            "size": STREAM_RESOLUTION
        }
        
        camera.configure(camera.create_preview_configuration(
            main=main_config,
            transform=transform,
            buffer_count=STREAM_BUFFER_SIZE
        ))
        
        # Set controls before starting camera
        # Using automatic exposure for better adaptation to lighting conditions
        camera.set_controls({
            "AfMode": controls.AfModeEnum.Continuous,  # Continuous autofocus
            "AeEnable": True,  # Enable automatic exposure
            "AeExposureMode": controls.AeExposureModeEnum.Normal,
            "Brightness": 0.0,
            "Contrast": 1.0,
            "Saturation": 1.0
        })
        
        camera.start()
        
        # Small delay to let camera settle
        time.sleep(0.5)
        
        camera_initialized = True
        logging.info(f"Camera initialized (RPi Zero W mode: {RPI_ZERO_MODE})")
    except Exception as e:
        logging.error(f"Failed to initialize camera: {e}")
        camera_initialized = False
        if camera:
            try:
                camera.stop()
            except:
                pass
            camera = None

def shutdown_camera():
    """Gracefully shutdown camera to save power."""
    global camera, camera_initialized
    if camera_initialized and camera:
        try:
            camera.stop()
            camera.close()  # Properly close the camera
            camera_initialized = False
            logging.info("Camera shutdown.")
        except Exception as e:
            logging.error(f"Failed to shutdown camera: {e}")
        finally:
            camera = None

# Define the buttons and LEDs
led1_button = Button(2)
led2_button = Button(3)
capture_button = Button(4, hold_time=2)
power_button = Button(17, hold_time=3)  # Long press (3s) to toggle power
led1 = LED(18, active_high=False)
led2 = LED(23, active_high=False)
ledc = LED(15)
status_led = LED(24)
power_indicator_led = LED(27)  # New LED to indicate device power state

# System state enumeration
class SystemState:
    POWERED_OFF = "powered_off"
    BOOTING = "booting"
    RUNNING = "running"
    IDLE = "idle"
    SHUTTING_DOWN = "shutting_down"

system_state = SystemState.BOOTING
device_power_on = True  # Track whether device is powered on

# Initial LED state - minimal power draw during boot
led1.off()  # Changed from .on() to save battery
led2.off()  # Changed from .on() to save battery
status_led.blink(on_time=0.5, off_time=0.5)  # Blink instead of solid for better battery
power_indicator_led.on()  # Device is powered on

# --- Helper Functions ---

def update_timer():
    """Safely update the global inactivity timer."""
    global timer
    with state_lock:
        timer = time.time()

def set_system_state(new_state):
    """Updates the system state and sets status LED pattern accordingly."""
    global system_state
    system_state = new_state
    update_status_led()

def update_status_led():
    """Updates status LED based on current system state."""
    if system_state == SystemState.POWERED_OFF:
        # Off when powered off
        status_led.off()
        power_indicator_led.off()
    
    elif system_state == SystemState.BOOTING:
        # Rapid blink during boot only
        status_led.blink(on_time=0.1, off_time=0.1)
        power_indicator_led.on()
    
    elif system_state == SystemState.RUNNING:
        # Solid on during normal operation
        status_led.on()
        power_indicator_led.on()
    
    elif system_state == SystemState.IDLE:
        # Slow blink in idle to minimize power draw while showing device is alive
        status_led.blink(on_time=0.5, off_time=1.5)
        power_indicator_led.blink(on_time=1, off_time=1)  # Alternating slow blink for idle
    
    elif system_state == SystemState.SHUTTING_DOWN:
        # Fast blink during shutdown as warning
        status_led.blink(on_time=0.2, off_time=0.2)
        power_indicator_led.blink(on_time=0.2, off_time=0.2)

def blink():
    """Blinks the capture LED without overlapping threads - optimized for battery."""
    def blink_led():
        # Try to acquire lock; if we can't, it means it's already blinking.
        if not blink_lock.acquire(blocking=False):
            return

        try:
            # Reduced blink count from 6 to 3 for faster feedback
            for _ in range(3):
                ledc.on()
                time.sleep(0.1)  # Reduced from 0.2
                ledc.off()
                time.sleep(0.1)  # Reduced from 0.2
        finally:
            blink_lock.release()

    threading.Thread(target=blink_led, daemon=True).start()

def power_on_device():
    """Powers on the device and initializes all systems."""
    global device_power_on, system_state
    
    with state_lock:
        device_power_on = True
        system_state = SystemState.BOOTING
    
    logging.info("Device powered ON - Booting system")
    update_status_led()
    initialize_camera()
    
    # Boot sequence complete after a short delay
    time.sleep(2)
    with state_lock:
        system_state = SystemState.RUNNING
    logging.info("System boot complete - RUNNING")
    update_status_led()

def power_off_device():
    """Powers off the device gracefully."""
    global device_power_on, system_state
    
    with state_lock:
        device_power_on = False
        system_state = SystemState.SHUTTING_DOWN
    
    logging.info("Device powered OFF - Shutting down")
    update_status_led()
    
    # Flash warning indication
    for _ in range(3):
        power_indicator_led.toggle()
        time.sleep(0.15)
    
    time.sleep(1)
    shutdown_camera()
    
    # Final shutdown
    with state_lock:
        system_state = SystemState.POWERED_OFF
    
    logging.warning("Device is now in powered off state")
    update_status_led()
    
    # Note: Device doesn't actually power off - stays in low-power state
    # This allows power button to wake it up

def monitor_client():
    """Periodically checks if the client has timed out - reduced polling frequency."""
    timeout_duration = timedelta(seconds=CLIENT_TIMEOUT)
    while True:
        time.sleep(MONITOR_CHECK_INTERVAL)
        
        # Skip if device is powered off
        if not device_power_on or system_state == SystemState.POWERED_OFF:
            continue
        
        with state_lock:
            if client_status['last_ping']:
                if datetime.now() - client_status['last_ping'] > timeout_duration:
                    client_status['status'] = False
                    logging.info("Client timeout detected.")

def shutdown_monitor():
    """Handles automatic power-off and idle LED states - optimized for battery."""
    global timer, system_state
    idle_mode_active = False

    while True:
        # Increased sleep interval to reduce CPU polling
        time.sleep(MONITOR_CHECK_INTERVAL)
        
        # Skip all auto-shutdown logic since it's disabled
        if INACTIVITY_SHUTDOWN_TIMEOUT == 0:
            time.sleep(10)  # Just sleep and continue
            continue
            
        with state_lock:
            current_time = time.time()
            duration = current_time - timer
            is_client_active = client_status["status"]

        # Power off after INACTIVITY_SHUTDOWN_TIMEOUT of inactivity and no active client
        if duration > INACTIVITY_SHUTDOWN_TIMEOUT and not is_client_active:
            logging.warning("Inactivity shutdown triggered.")
            set_system_state(SystemState.SHUTTING_DOWN)
            # Brief warning blinks before shutdown
            for _ in range(3):
                led1.toggle()
                led2.toggle()
                time.sleep(0.15)
            time.sleep(1)  # Allow status LED to blink
            shutdown_camera()  # Ensure camera is off before shutdown
            check_call(['sudo', 'poweroff'])

        # Enter idle mode after INACTIVITY_IDLE_TIMEOUT seconds
        if duration > INACTIVITY_IDLE_TIMEOUT and not is_client_active:
            if not idle_mode_active:
                logging.info("Entering idle mode: Shutting down power-hungry components.")
                if led1.is_active: 
                    led1.off()
                if led2.is_active: 
                    led2.off()
                shutdown_camera()  # Power down camera in idle
                idle_mode_active = True
                set_system_state(SystemState.IDLE)
        else:
            # Exit idle mode if activity occurred
            if idle_mode_active:
                idle_mode_active = False
                logging.info("Exiting idle mode: Initializing camera.")
                initialize_camera()
                set_system_state(SystemState.RUNNING)

def capture_image():
    """Captures a still image in high quality - optimized for RPi Zero W."""
    global system_state
    
    with state_lock:
        client_status['last_ping'] = datetime.now()
    
    update_timer()
    ledc.on()
    
    timestamp = datetime.now().strftime("%Y-%m-%dT%H_%M_%S")
    filename = f"RF_pic_{timestamp}.jpeg"
    path = os.path.join(IMAGE_DIRECTORY, filename)
    
    try:
        # Ensure camera is initialized
        if not camera_initialized:
            initialize_camera()
        
        # Lock camera to prevent conflict with video stream
        with camera_lock:
            logging.info("Starting autofocus for high-quality capture...")
            
            # Set high-quality parameters before capture
            camera.set_controls({
                "AfMode": controls.AfModeEnum.Auto,
                "AfTrigger": controls.AfTriggerEnum.Start,
                "ExposureTime": 30000,  # Slightly longer exposure for better quality
                "AnalogueGain": 1.0
            })
            
            # Wait for autofocus to complete
            time.sleep(AUTOFOCUS_TIMEOUT)
            
            # Capture at full resolution for high quality
            capture_config = camera.create_still_configuration(
                main={"format": "RGB888", "size": CAPTURE_RESOLUTION}
            )
            camera.switch_mode_and_capture_file(capture_config, path)
            
            logging.info(f"High-quality capture complete: {path}")
            
    except Exception as e:
        logging.error(f"Capture failed: {e}")
        # Fallback: use basic capture
        try:
            with camera_lock:
                camera.capture_file(path)
                logging.info(f"Captured (fallback): {path}")
        except Exception as e2:
            logging.error(f"Fallback capture also failed: {e2}")
    
    finally:
        time.sleep(0.3)  # Short feedback time
        ledc.off()

# --- Flask Routes ---

@app.route('/ping')
def ping():
    """Ping endpoint - should reset idle timer and wake device."""
    global system_state
    
    with state_lock:
        client_status['last_ping'] = datetime.now()
        client_status['status'] = True
    
    update_timer()
    
    # Wake up from idle if needed
    if system_state == SystemState.IDLE:
        initialize_camera()
        set_system_state(SystemState.RUNNING)
        logging.info("Device awakened from idle by client ping")
    
    blink()
    return jsonify(status="pong", code=200)

@app.route('/device_status')
def device_status():
    return jsonify(online=True)

@app.route('/system_status')
def system_status():
    return jsonify(state=system_state, power_on=device_power_on)

@app.route('/power_status')
def power_status():
    """Returns device power state."""
    return jsonify(powered_on=device_power_on, state=system_state)

@app.route('/capture', methods=['GET', 'POST'])
def trigger_capture():
    # Run capture in a separate thread so we don't block the HTTP response immediately
    threading.Thread(target=capture_image, daemon=True).start()
    return jsonify(status="capture_started")

@app.route('/list_files', methods=['GET'])
def list_files():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        # Use scandir for better performance, get stats for sorting
        files_with_stats = []
        with os.scandir(IMAGE_DIRECTORY) as entries:
            for entry in entries:
                if entry.is_file() and entry.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    files_with_stats.append((entry.name, entry.stat().st_mtime))

        # Sort by modification time, newest first
        files_with_stats.sort(key=lambda x: x[1], reverse=True)
        sorted_filenames = [f[0] for f in files_with_stats]

        total_files = len(sorted_filenames)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_files = sorted_filenames[start:end]

        return jsonify({
            "page": page,
            "per_page": per_page,
            "total": total_files,
            "files": paginated_files
        })
    except Exception as e:
        logging.error(f"Error listing files: {e}")
        return jsonify(error=str(e)), 500

@app.route('/images/<path:filename>')
def get_file(filename):
    return send_from_directory(IMAGE_DIRECTORY, filename)

@app.route('/led1_status')
def led1_status_route():
    return jsonify(active=led1.is_active)

@app.route('/led2_status')
def led2_status_route():
    return jsonify(active=led2.is_active)

@app.route('/uv_status')
def uv_status_route():
    return jsonify(UV_A=led1.is_active, UV_B=led2.is_active)

@app.route('/led1_toggle')
def toggle_led1_route():
    update_timer()
    led1.toggle()
    return jsonify(active=led1.is_active)

@app.route('/led2_toggle')
def toggle_led2_route():
    update_timer()
    led2.toggle()
    return jsonify(active=led2.is_active)

@app.route('/poweroff')
def poweroff_route():
    # Set system state to shutting down
    set_system_state(SystemState.SHUTTING_DOWN)
    # Delay poweroff slightly to allow response to be sent and status LED to blink
    threading.Timer(2.0, lambda: check_call(['sudo', 'poweroff'])).start()
    return jsonify(status="powering_off")

# --- Video Streaming ---

def generate_frames():
    """Generate video frames optimized for RPi Zero W - lower res, adaptive quality."""
    global VIDEO_STREAM_ACTIVE, client_status
    
    frames_without_data = 0
    max_frames_without_data = 30  # Increased to allow more retries
    frame_skip_counter = 0
    skip_rate = 1 if RPI_ZERO_MODE else 0
    last_frame_time = time.time()
    frame_interval = 1.0 / STREAM_FRAMERATE
    jpeg_quality = STREAM_JPEG_QUALITY
    
    # Retry counter for initialization
    init_retry_count = 0
    max_init_retries = 5
    
    # Ping interval to prevent client timeout (every 30 seconds)
    last_ping_time = time.time()
    ping_interval = 30
    
    try:
        # First ensure camera is initialized
        while not camera_initialized and init_retry_count < max_init_retries:
            logging.info(f"Initializing camera for streaming (attempt {init_retry_count + 1})")
            initialize_camera()
            init_retry_count += 1
            if not camera_initialized:
                time.sleep(0.5)  # Give camera time to initialize
        
        if not camera_initialized:
            logging.error("Max camera initialization retries exceeded")
            return
            
        logging.info("Camera successfully initialized for streaming")
        
        while VIDEO_STREAM_ACTIVE:
            # Periodically update client status to prevent timeout
            current_time = time.time()
            if current_time - last_ping_time > ping_interval:
                with state_lock:
                    client_status['last_ping'] = datetime.now()
                    client_status['status'] = True
                last_ping_time = current_time
            
            try:
                # Frame rate limiting for smoother playback
                current_time = time.time()
                time_since_last = current_time - last_frame_time
                if time_since_last < frame_interval:
                    time.sleep(frame_interval - time_since_last)
                    continue
                
                last_frame_time = time.time()
                
                # Use lock with timeout to prevent hanging on Zero W
                if not camera_lock.acquire(timeout=2.0):  # Increased timeout
                    logging.warning("Camera lock timeout")
                    continue
                
                try:
                    # Use capture_buffer instead of capture_array for better compatibility
                    frame_buffer = camera.capture_buffer("main")
                    if frame_buffer is None:
                        frames_without_data += 1
                        logging.warning(f"Empty frame captured ({frames_without_data}/{max_frames_without_data})")
                        if frames_without_data > max_frames_without_data:
                            logging.error("Too many empty frames, stopping stream")
                            break
                        time.sleep(0.1)
                        continue
                    
                    # Convert buffer to numpy array for OpenCV processing
                    import numpy as np
                    frame_array = np.frombuffer(frame_buffer, dtype=np.uint8)
                    
                    # Reshape based on stream resolution (assuming RGB format)
                    frame = frame_array.reshape((STREAM_RESOLUTION[1], STREAM_RESOLUTION[0], 3))
                    
                    frames_without_data = 0  # Reset counter on successful frame
                    
                except Exception as capture_error:
                    camera_lock.release()
                    frames_without_data += 1
                    logging.warning(f"Frame capture error: {capture_error} ({frames_without_data}/{max_frames_without_data})")
                    if frames_without_data > max_frames_without_data:
                        logging.error("Too many frame capture errors, stopping stream")
                        break
                    time.sleep(0.2)
                    continue
                finally:
                    camera_lock.release()
                
                # Skip frames on Zero W for smoother playback
                if RPI_ZERO_MODE:
                    frame_skip_counter += 1
                    if frame_skip_counter % (skip_rate + 1) != 0:
                        continue
                
                # Encode frame to JPEG with optimized quality
                ret, buffer = cv2.imencode('.jpg', frame, 
                                          [cv2.IMWRITE_JPEG_QUALITY, int(jpeg_quality)])
                
                if not ret:
                    logging.warning("JPEG encoding failed")
                    continue
                    
                frame_bytes = buffer.tobytes()
                # Yield frame and catch client disconnection
                try:
                    frame_data = (b'--frame\r\n'
                                  b'Content-Type: image/jpeg\r\n'
                                  b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n'
                                  b'\r\n' + frame_bytes + b'\r\n')
                    yield frame_data
                except GeneratorExit:
                    # Client disconnected, stop the stream
                    logging.info("Client disconnected, stopping video stream")
                    break
                except Exception as e:
                    # Other error during yield
                    logging.error(f"Error during frame yield: {e}")
                    break
                
            except Exception as e:
                logging.error(f"Frame generation error: {e}")
                # Don't break immediately, try to recover
                time.sleep(0.5)
                continue
                
    except Exception as e:
        logging.error(f"Fatal error in frame generation: {e}")
    finally:
        VIDEO_STREAM_ACTIVE = False
        logging.info("Frame generation loop ended") 

@app.route('/')
def index():
    """Root route to serve a simple page with links to all endpoints."""
    return """
    <h1>Raspberry Pi Camera Controller</h1>
    <ul>
        <li><a href="/video_feed">Live Video Feed</a></li>
        <li><a href="/capture">Capture Image</a></li>
        <li><a href="/device_status">Device Status</a></li>
        <li><a href="/system_status">System Status</a></li>
        <li><a href="/power_status">Power Status</a></li>
        <li><a href="/led1_status">LED1 Status</a></li>
        <li><a href="/led2_status">LED2 Status</a></li>
        <li><a href="/uv_status">UV Status</a></li>
        <li><a href="/led1_toggle">Toggle LED1</a></li>
        <li><a href="/led2_toggle">Toggle LED2</a></li>
        <li><a href="/list_files">List Captured Images</a></li>
        <li><a href="/ping">Ping Device</a></li>
        <li><a href="/poweroff">Power Off</a></li>
    </ul>
    """

@app.route('/video_feed')
def video_feed():
    """Video feed endpoint - enables lazy camera startup and shutdown."""

    global VIDEO_STREAM_ACTIVE, system_state, client_status
    
    update_timer()  # Reset activity timer
    
    # Update client status to prevent timeout
    with state_lock:
        client_status['last_ping'] = datetime.now()
        client_status['status'] = True
        initialize_camera()
        set_system_state(SystemState.RUNNING)
    
    # Add a small delay to ensure camera is ready
    time.sleep(0.1)
    
    # Only start streaming if camera is properly initialized
    if not camera_initialized:
        logging.error("Camera failed to initialize, cannot start video stream")
        return "Camera initialization failed", 500
    
    VIDEO_STREAM_ACTIVE = True
    logging.info("Video stream started")
    
    try:
        response = Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
        # Add headers to prevent caching
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        logging.error(f"Error in video feed response: {e}")
        VIDEO_STREAM_ACTIVE = False
        return "Video stream error", 500

# --- Main Entry Point ---

def hardware_button_listener():
    """Connects physical buttons to their actions - optimized for battery."""
    global system_state, device_power_on
    
    def handle_led1_press():
        # Skip if device is powered off
        if not device_power_on or system_state == SystemState.POWERED_OFF:
            return
        update_timer()
        if system_state == SystemState.IDLE:
            initialize_camera()
            set_system_state(SystemState.RUNNING)
        led1.toggle()
    
    def handle_led2_press():
        # Skip if device is powered off
        if not device_power_on or system_state == SystemState.POWERED_OFF:
            return
        update_timer()
        if system_state == SystemState.IDLE:
            initialize_camera()
            set_system_state(SystemState.RUNNING)
        led2.toggle()
    
    def handle_capture_press():
        # Skip if device is powered off
        if not device_power_on or system_state == SystemState.POWERED_OFF:
            return
        update_timer()
        if system_state == SystemState.IDLE:
            initialize_camera()
            set_system_state(SystemState.RUNNING)
    
    def handle_power_button_press():
        """Handle power button press - toggle power on/off."""
        blink()  # Quick feedback
        if device_power_on and system_state != SystemState.POWERED_OFF:
            # Currently on, turn off
            power_off_device()
        else:
            # Currently off, turn on
            threading.Thread(target=power_on_device, daemon=True).start()
    
    # Button handlers
    led1_button.when_pressed = handle_led1_press
    led2_button.when_pressed = handle_led2_press
    capture_button.when_pressed = handle_capture_press
    capture_button.when_held = capture_image
    
    # Power button - toggle on/off with long press (3 seconds)
    power_button.when_held = handle_power_button_press
    
    pause()

if __name__ == '__main__':
    # Start background threads as daemons so they die when main app dies
    threading.Thread(target=hardware_button_listener, daemon=True).start()
    threading.Thread(target=shutdown_monitor, daemon=True).start()
    threading.Thread(target=monitor_client, daemon=True).start()
    
    # Initialize camera immediately after app launch
    logging.info("Initializing camera...")
    initialize_camera()
    
    # System is now fully booted and running
    set_system_state(SystemState.RUNNING)
    logging.info(f"System boot complete. RPi Zero W mode: {RPI_ZERO_MODE}")
    if camera_initialized:
        logging.info("Camera successfully initialized")
    else:
        logging.warning("Camera initialization failed, continuing without camera")
    
    # Configure Flask for RPi Zero W
    # Use Gunicorn in production: 
    # gunicorn -w 1 -b 0.0.0.0:5000 --threads 2 --timeout 120 --worker-class sync "final_new:app"
    
    if RPI_ZERO_MODE:
        # Optimized for RPi Zero W with limited resources
        app.run(
            host='0.0.0.0',
            port=5000,
            threaded=True,
            debug=False,
            use_reloader=False  # Disable reloader to save CPU
        )
    else:
        # Standard configuration for RPi 4/5
        app.run(
            host='0.0.0.0',
            port=5000,
            threaded=True,
            debug=False
        )