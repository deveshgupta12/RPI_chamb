# Quick Start Guide - RPi Zero W

Fast setup guide for Raspberry Pi Zero W deployment.

## One-Command Setup

```bash
# Download and setup in one go
cd ~ && git clone <your-repo> device-app && \
cd device-app && \
python3 -m venv venv && \
source venv/bin/activate && \
pip install --upgrade pip setuptools wheel && \
pip install -r requirements.txt
```

## Hardware Wiring (5 Pins Needed)

```
RPi Zero W GPIO Pins:
- GPIO 2  → Button (LED1) → GND
- GPIO 3  → Button (LED2) → GND  
- GPIO 4  → Button (Capture) → GND
- GPIO 17 → Button (Power) → GND
- GPIO 18 → LED (UV-A, 470Ω) → GND
- GPIO 23 → LED (UV-B, 470Ω) → GND
- GPIO 15 → LED (Capture, 470Ω) → GND
- GPIO 24 → LED (Status, 470Ω) → GND
- GPIO 27 → LED (Power, 470Ω) → GND
- Camera: Ribbon cable to CSI port
```

## Enable Camera & Start

```bash
# 1. Enable camera interface
sudo raspi-config
# → Interface Options → Camera → Enable → Reboot

# 2. Test camera
libcamera-hello -t 5

# 3. Run application
cd ~/device-app
source venv/bin/activate
python3 "final (1).py"

# 4. Access web interface
# Open browser: http://<device-ip>:5000/video_feed
```

## Auto-Start on Boot (Systemd Service)

```bash
# Create service file
sudo nano /etc/systemd/system/device-app.service
```

Paste this:
```ini
[Unit]
Description=Device IoT App
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/device-app
Environment="PATH=/home/pi/device-app/venv/bin"
ExecStart=/home/pi/device-app/venv/bin/python3 "final (1).py"
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable device-app
sudo systemctl start device-app
sudo systemctl status device-app
```

## Monitor & Troubleshoot

```bash
# View logs
sudo journalctl -u device-app -f

# Check resource usage
top -b -n 1 | head -20

# Check temperature (should be < 80°C)
vcgencmd measure_temp

# Check camera
libcamera-still -o test.jpg

# Test stream
curl http://localhost:5000/video_feed > stream.mjpeg
```

## API Quick Reference

```bash
# Power status
curl http://<ip>:5000/power_status

# Capture image
curl -X POST http://<ip>:5000/capture

# List images
curl http://<ip>:5000/list_files

# Download image
curl http://<ip>:5000/images/RF_pic_2024-01-01T12_00_00.jpeg > image.jpg

# Toggle LED1
curl http://<ip>:5000/led1_toggle

# Toggle LED2
curl http://<ip>:5000/led2_toggle

# Video stream
# Open in browser: http://<ip>:5000/video_feed
```

## Configuration Tweaks

Edit `final (1).py` to adjust:

**For better battery life:**
```python
INACTIVITY_IDLE_TIMEOUT = 120        # 2 minutes to idle
INACTIVITY_SHUTDOWN_TIMEOUT = 300    # 5 minutes to shutdown
```

**For slower WiFi:**
```python
STREAM_RESOLUTION = (240, 360)       # Ultra-low resolution
STREAM_FRAMERATE = 5                 # Very smooth BUT less responsive
STREAM_JPEG_QUALITY = 40             # Heavy compression
```

**For better image quality (fast network):**
```python
STREAM_RESOLUTION = (480, 640)       # Higher resolution
STREAM_FRAMERATE = 15                # Faster
STREAM_JPEG_QUALITY = 60             # Better quality
```

## Power Button Usage

- **Tap (< 3 sec)**: No action (accidental press protection)
- **Hold (3+ sec)**: Toggle power ON/OFF
- **LED Feedback**: Flash on press

Default timeout:
- **Idle after 5 min**: Camera off, minimal power (~200 mA)
- **Shutdown after 15 min**: Full device poweroff

## Expected Performance (Zero W)

- **Video Stream**: 320×480 @ 10 FPS (~1.4 Mbps)
- **Startup Time**: 15-20 seconds
- **CPU Usage Idle**: 5-10%
- **CPU Usage Streaming**: 30-40%
- **Memory Usage**: 80-120 MB
- **Power Draw Streaming**: 350-400 mA
- **Capture Time**: 3-6 seconds
- **Image Quality**: 2592×1944 pixels (5MP)

## WiFi Connection

```bash
# Connect to WiFi
sudo raspi-config
# → System Options → Wireless LAN

# Or manually edit:
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
# Add your network details
```

## Tips for Smooth Operation

1. ✅ Use Class 10 SD card (fast write speeds)
2. ✅ Keep device cool (use heatsink if available)
3. ✅ Use 5V/2.5A power supply (proper current capacity)
4. ✅ Mount camera lens carefully (avoid dust)
5. ✅ Test WiFi signal strength: `iwconfig`
6. ✅ Monitor temperature: `vcgencmd measure_temp`
7. ✅ Keep system updated: `sudo apt upgrade`

## Troubleshooting

### "No cameras available"
```bash
# Check camera connection
vcgencmd get_camera
# Should show: supported=1 detected=1

# If not:
# 1. Reseat ribbon cable firmly
# 2. Try different port
# 3. Enable camera in raspi-config
```

### "ModuleNotFoundError: picamera2"
```bash
pip install picamera2
# Or update all packages:
pip install -r requirements.txt --upgrade
```

### "Port 5000 already in use"
```bash
# Kill existing process
sudo lsof -i :5000
sudo kill -9 <PID>

# Or use different port (edit line in code):
# app.run(host='0.0.0.0', port=5001, ...)
```

### High CPU / Laggy Stream
1. Reduce frame rate: `STREAM_FRAMERATE = 5`
2. Reduce resolution: `STREAM_RESOLUTION = (240, 360)`
3. Reduce quality: `STREAM_JPEG_QUALITY = 30`
4. Close browser tabs
5. Disconnect other WiFi devices

### Button Not Working
```bash
# Test GPIO
python3 << 'EOF'
from gpiozero import Button
btn = Button(2)  # Test GPIO 2
btn.wait_for_press()
print("Button works!")
EOF
```

## Production Deployment

For 24/7 operation:

```bash
# 1. Enable systemd service (see above)

# 2. Disable screen blanking
sudo nano /etc/lightdm/lightdm.conf
# Change: xserver-command=X -s 0 -dpms

# 3. Monitor via SSH
ssh pi@<device-ip>
systemctl status device-app

# 4. Check logs remotely
ssh pi@<device-ip> journalctl -u device-app -f

# 5. Automatic restart on crash
# (Already configured in systemd service)

# 6. Monitor power consumption
ssh pi@<device-ip> watch -n 1 'vcgencmd pmic_read_adc EXT5V_V'
```

## Remote Management

```bash
# SSH into device
ssh pi@<device-ip>

# Restart service
sudo systemctl restart device-app

# View real-time logs
sudo journalctl -u device-app -f

# Get device info
uname -a
free -h
df -h
vcgencmd measure_temp
vcgencmd get_config frequency_cap

# Get IP address
hostname -I
```

## Files Included

- `final (1).py` - Main application
- `README.md` - Full documentation
- `BATTERY_OPTIMIZATION_GUIDE.md` - Battery optimization details
- `RPI_ZERO_W_OPTIMIZATION.md` - Zero W specific optimizations
- `requirements.txt` - Python dependencies
- `img/` - Directory for captured images

## Support & Documentation

For detailed information:
- Battery optimization: See `BATTERY_OPTIMIZATION_GUIDE.md`
- RPi Zero W specifics: See `RPI_ZERO_W_OPTIMIZATION.md`
- Full API: See `README.md`
- Power states: See Power Management in `README.md`

## Quick Test After Setup

```bash
# 1. Start application
python3 "final (1).py"

# 2. In another terminal, test API
curl http://localhost:5000/device_status

# 3. View video stream
# Open browser: http://<device-ip>:5000/video_feed

# 4. Capture image
curl -X POST http://localhost:5000/capture

# 5. Check captured image  
ls -lh img/
```

That's it! Your device is ready to use. 🚀
