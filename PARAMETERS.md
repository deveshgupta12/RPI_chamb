# Configurable Parameters

This document lists all the parameters that can be modified to customize and improve the functionality of the Raspberry Pi Battery-Optimized IoT Device.

## Configuration File Parameters

The main configuration is controlled through the `config.ini` file with the following sections and parameters:

### [Hardware]
- `RPI_ZERO_MODE` (Boolean): Set to True for RPi Zero W, False for RPi 4B/5
  - Affects optimizations and resource usage

### [Streaming]
- `STREAM_RESOLUTION` (Tuple): Video stream resolution as (width, height)
  - RPi Zero W recommended: (480, 640) for improved quality
  - RPi 4B/5 recommended: (480, 640) or higher
- `STREAM_FRAMERATE` (Integer): Frames per second (affects smoothness)
  - RPi Zero W recommended: 8-10 FPS
  - RPi 4B/5 recommended: 15-20 FPS
- `STREAM_JPEG_QUALITY` (Integer): JPEG compression quality (0-100)
  - Lower values = faster encoding, less bandwidth
  - Recommended: 50 for good balance
- `STREAM_BUFFER_SIZE` (Integer): Frame buffer size (affects memory usage)
  - Lower = less memory but potential buffering
- `STREAM_TIMEOUT` (Integer): Timeout for stream operations (seconds)

### [Image_Capture]
- `CAPTURE_RESOLUTION` (Tuple): High-quality image capture resolution
  - Full sensor resolution recommended: (3840, 2160)
- `CAPTURE_JPEG_QUALITY` (Integer): JPEG quality for captures (0-100)
  - Usually high quality recommended: 85+
- `AUTOFOCUS_TIMEOUT` (Integer): Autofocus timeout (seconds)
  - Time allowed for autofocus operation

### [Power_Management]
- `IDLE_DELAY` (Integer): Time to idle mode (camera powers down) in seconds
- `SHUTDOWN_DELAY` (Integer): Auto shutdown delay after inactivity in seconds
- `INACTIVITY_RESET_INTERVAL` (Integer): How often inactivity timer resets in seconds

### [System]
- `LOGGING_LEVEL` (String): Verbosity level (DEBUG, INFO, WARNING, ERROR)
- `ACTIVITY_LOG_FILE` (String): Path to activity log file
- `ERROR_LOG_FILE` (String): Path to error log file

## Hardware Configuration Parameters

### GPIO Pin Settings
These are typically defined in the Python code but can be modified:
- LED1_PIN: GPIO pin for first LED
- LED2_PIN: GPIO pin for second LED
- POWER_LED_PIN: GPIO pin for power LED
- LED1_BUTTON_PIN: GPIO pin for first button
- LED2_BUTTON_PIN: GPIO pin for second button
- CAPTURE_BUTTON_PIN: GPIO pin for capture button
- POWER_BUTTON_PIN: GPIO pin for power button

## Software Timing Parameters

These parameters are defined in the Python code and can be adjusted for fine-tuning:

- `BUTTON_HOLD_TIME`: Duration to detect a button hold (typically 3 seconds)
- `BLINK_DURATION`: Duration of LED blinks for feedback
- `CAMERA_INIT_TIMEOUT`: Maximum time to wait for camera initialization
- `MAX_FRAMES_WITHOUT_DATA`: Threshold for detecting camera issues
- `FRAME_SKIP_RATE`: Frame skipping rate for Pi Zero W optimization

## Network Parameters

- `FLASK_HOST`: Host IP for Flask server (typically '0.0.0.0')
- `FLASK_PORT`: Port for Flask server (typically 5000)
- `USE_RELOADER`: Whether to use Flask reloader (False recommended for production)
- `THREADED`: Whether to enable threading in Flask

## Performance Tuning Parameters

- `JPEG_QUALITY`: Quality setting for JPEG encoding
- `FRAME_INTERVAL`: Minimum time between frames for rate limiting
- `CAMERA_LOCK_TIMEOUT`: Timeout for camera access lock
- `SKIP_RATE`: Frame skip rate for Pi Zero W mode

## Customization Guidelines

### For Better Battery Life
1. Increase `SHUTDOWN_DELAY` for longer active periods
2. Decrease `STREAM_FRAMERATE` for lower CPU usage
3. Lower `STREAM_JPEG_QUALITY` for reduced processing
4. Increase `IDLE_DELAY` to stay active longer before sleeping

### For Better Performance
1. Decrease `SHUTDOWN_DELAY` for more responsive auto-shutdown
2. Increase `STREAM_FRAMERATE` for smoother video
3. Increase `STREAM_JPEG_QUALITY` for better image quality
4. Decrease `IDLE_DELAY` for quicker power savings

### For Different Hardware
1. Adjust `RPI_ZERO_MODE` based on your Pi model
2. Modify GPIO pin assignments for different board layouts
3. Change resolutions based on camera capabilities
4. Tune timing parameters for different CPU speeds