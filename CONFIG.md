# Device Configuration File
# Edit this file to customize your device behavior

[Hardware]
# Set to True for RPi Zero W, False for RPi 4B/5
RPI_ZERO_MODE = True

[Streaming]
# Video stream settings (balance between quality and performance)
# Lower values = smoother but lower quality
# Can be adjusted based on network speed

# Resolution: (width, height)
# RPi Zero W: (320, 480) or lower
# RPi 4B/5:   (480, 640) or higher
STREAM_RESOLUTION = (320, 480)

# Frames per second (affects smoothness)
# RPi Zero W: 8-10 FPS (smooth on single-core)
# RPi 4B/5:   15-20 FPS
STREAM_FRAMERATE = 10

# JPEG compression quality (0-100)
# Lower = faster encoding, less bandwidth
# 50 = good balance for streaming
STREAM_JPEG_QUALITY = 50

# Frame buffer size (affects memory usage)
# Lower = less memory but potential buffering
STREAM_BUFFER_SIZE = 8

# Timeout for stream operations (seconds)
STREAM_TIMEOUT = 30

[Image_Capture]
# High-quality image capture (separate from streaming)
# These settings don't affect stream performance

# Capture resolution (full sensor is best)
CAPTURE_RESOLUTION = (2592, 1944)

# JPEG quality for captures (usually high)
CAPTURE_JPEG_QUALITY = 85

# Autofocus timeout (seconds)
AUTOFOCUS_TIMEOUT = 5

[Power_Management]
# Automatic idle and shutdown timeouts

# Time to idle mode (camera powers down)
# Units: seconds
# 300 = 5 minutes (default)
# Values: 60-1800 (1 min to 30 min)
INACTIVITY_IDLE_TIMEOUT = 300

# Time to full shutdown
# Units: seconds
# 900 = 15 minutes (default)
# Values: 300-3600 (5 min to 1 hour)
INACTIVITY_SHUTDOWN_TIMEOUT = 900

# Client timeout (no ping detected)
# Units: seconds
CLIENT_TIMEOUT = 60

# Monitor check interval (how often to check timers)
# Higher = less CPU polling, less responsive
# Lower = more responsive, more CPU usage
# RPi Zero W: 10-20 seconds recommended
MONITOR_CHECK_INTERVAL = 10

[Threading]
# Threading configuration (affects responsiveness vs CPU load)

# Number of Flask worker processes
# RPi Zero W: 1 (single core)
# RPi 4B/5:   2-4
FLASK_WORKERS = 1

# Number of worker threads
# RPi Zero W: 2 (limited)
# RPi 4B/5:   4-8
FLASK_THREADS = 2

[Server]
# Web server settings

# IP to bind to (0.0.0.0 = all interfaces)
HOST = 0.0.0.0

# Port number
PORT = 5000

# Debug mode (False for production)
DEBUG = False

# Use reloader (True slows down Zero W)
USE_RELOADER = False

[Logging]
# Logging configuration

# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = INFO

# Log format
LOG_FORMAT = %(asctime)s - %(levelname)s - %(message)s

[GPIO]
# GPIO pin assignments (don't change unless you rewired)

# Buttons
GPIO_BUTTON_LED1 = 2
GPIO_BUTTON_LED2 = 3
GPIO_BUTTON_CAPTURE = 4
GPIO_BUTTON_POWER = 17

# LEDs
GPIO_LED_UV_A = 18
GPIO_LED_UV_B = 23
GPIO_LED_CAPTURE = 15
GPIO_LED_STATUS = 24
GPIO_LED_POWER = 27

[Files]
# File configuration

# Directory for captured images
IMAGE_DIRECTORY = img/

# Max image lifetime (0 = no limit)
# Example: 86400 = delete after 1 day
MAX_IMAGE_AGE_SECONDS = 0

# Max images to keep (0 = no limit)
MAX_IMAGES = 0

# File names pattern
IMAGE_FILENAME_PATTERN = RF_pic_{timestamp}.jpeg

[Expert_Tuning]
# Advanced settings - only change if you know what you're doing!

# Enable deep sleep (experimental)
DEEP_SLEEP_ENABLED = True

# Camera warmup time (ms)
CAMERA_WARMUP_TIME = 500

# Max consecutive frame errors before stopping stream
MAX_FRAME_ERRORS = 10

# MJPEG boundary marker
MJPEG_BOUNDARY = frame

# Enable power button
POWER_BUTTON_ENABLED = True

# Power button hold time (seconds)
POWER_BUTTON_HOLD_TIME = 3

---

## Quick Presets

### Preset 1: Maximum Battery Life
```
INACTIVITY_IDLE_TIMEOUT = 120
INACTIVITY_SHUTDOWN_TIMEOUT = 300
STREAM_RESOLUTION = (240, 360)
STREAM_FRAMERATE = 5
STREAM_JPEG_QUALITY = 40
MONITOR_CHECK_INTERVAL = 20
```

### Preset 2: Balanced (Default)
```
# Use values from [Streaming] and [Power_Management] as-is
```

### Preset 3: Best Stream Quality
```
STREAM_RESOLUTION = (480, 640)
STREAM_FRAMERATE = 15
STREAM_JPEG_QUALITY = 60
RPI_ZERO_MODE = False
```

### Preset 4: Slow WiFi (<2 Mbps)
```
STREAM_RESOLUTION = (240, 360)
STREAM_FRAMERATE = 8
STREAM_JPEG_QUALITY = 35
STREAM_BUFFER_SIZE = 4
```

### Preset 5: Fast WiFi (>10 Mbps)
```
STREAM_RESOLUTION = (640, 800)
STREAM_FRAMERATE = 20
STREAM_JPEG_QUALITY = 70
STREAM_BUFFER_SIZE = 16
RPI_ZERO_MODE = False
```

---

## Tips for Configuration

1. **Test one change at a time**
   - Change only one value
   - Restart application
   - Observe results

2. **Monitor while testing**
   - Open SSH: `ssh pi@<device-ip>`
   - Watch resources: `watch -n 1 'top -b -n 1'`
   - Check temp: `vcgencmd measure_temp`

3. **Battery testing**
   - Enable idle mode
   - Set low timeouts
   - Monitor voltage: `ssh pi@<device-ip> watch vcgencmd pmic_read_adc`

4. **Streaming quality**
   - Start with default values
   - If stuttering: reduce framerate or quality
   - If too blurry: increase quality or resolution

5. **Reset to defaults**
   - Edit values in top of `final (1).py`
   - Or delete this file and use defaults

---

## Configuration Limits

| Setting | Min | Max | Recommended |
|---------|-----|-----|-------------|
| Stream FPS | 1 | 30 | 8-20 |
| Stream Quality | 10 | 100 | 40-70 |
| Idle Timeout | 60 | 3600 | 300 |
| Shutdown Timeout | 300 | 7200 | 900 |
| Monitor Interval | 5 | 60 | 10 |
| Autofocus Timeout | 1 | 10 | 5 |

---

## Advanced: Adaptive Streaming

For manual adaptive quality based on network:

```
# If network slow: reduce STREAM_JPEG_QUALITY
# If network fast: increase STREAM_RESOLUTION
# If CPU high: reduce STREAM_FRAMERATE
# If memory high: reduce STREAM_BUFFER_SIZE
```

Monitor in real-time:
```bash
ssh pi@<device> watch -n 1 'echo "CPU:"; top -bn1 | head -3; echo "Memory:"; free -h | head -2'
```

---

## Troubleshooting via Configuration

**High CPU (>70%)**
- Reduce STREAM_FRAMERATE
- Reduce STREAM_RESOLUTION
- Increase MONITOR_CHECK_INTERVAL

**Stuttering video**
- Increase STREAM_BUFFER_SIZE (to 16)
- Reduce STREAM_RESOLUTION
- Increase MONITOR_CHECK_INTERVAL

**Out of memory**
- Reduce STREAM_BUFFER_SIZE
- Reduce max concurrent streams in nginx
- Reduce STREAM_RESOLUTION

**Slow captures**
- Check SD card speed: `dd if=/dev/urandom of=/tmp/test bs=1M count=100`
- Reduce CAPTURE_RESOLUTION (not recommended)
- Increase lighting for faster autofocus

---

For full documentation, see README.md and RPI_ZERO_W_OPTIMIZATION.md
