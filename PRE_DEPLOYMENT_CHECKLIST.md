# Pre-Deployment Checklist

Complete this checklist before deploying to production.

## 📋 Code & Environment

- [ ] Python code has no syntax errors: `python3 -m py_compile "final (1).py"`
- [ ] All dependencies installed: `pip install -r requirements.txt`
- [ ] Virtual environment activated: `source venv/bin/activate`
- [ ] Flask can start: `python3 "final (1).py"` (Ctrl+C to stop)
- [ ] No errors in startup log

## 🎥 Hardware

### Camera
- [ ] Camera ribbon cable fully inserted
- [ ] Camera enabled in raspi-config
- [ ] Camera test passes: `libcamera-hello -t 5`
- [ ] Capture test succeeds: `libcamera-still -o test.jpg`
- [ ] Lens is clean (no dust or fingerprints)
- [ ] Camera mounted securely

### GPIO & Buttons
- [ ] All 9 GPIO pins wired correctly (see [README.md](README.md))
- [ ] Buttons respond: Each button produces "button pressed" feeling
- [ ] LEDs light up when connected to power
- [ ] No loose wires or cold solder joints
- [ ] Pull-up resistors properly installed (if not using GPIO pull-ups)

### Power
- [ ] 5V power supply is 2.5A minimum
- [ ] Micro USB connection secure
- [ ] Battery (if used) fully charged
- [ ] No power fluctuations during idle/capture

## 🌐 Network

- [ ] WiFi connection stable: `iwconfig`
- [ ] SSH access works: `ssh pi@<device-ip>`
- [ ] WiFi auto-reconnect enabled
- [ ] Signal strength adequate: `iwconfig | grep Signal`
- [ ] Default gateway set: `route -n`

## 🧪 Software Tests

### API Endpoints
```bash
# Test each endpoint status
curl http://localhost:5000/ping
curl http://localhost:5000/device_status
curl http://localhost:5000/power_status
curl -X POST http://localhost:5000/capture
curl http://localhost:5000/list_files
curl http://localhost:5000/led1_toggle
curl http://localhost:5000/led2_toggle
```

- [ ] /ping responds with "pong"
- [ ] /device_status returns online=true
- [ ] /power_status shows current state
- [ ] /capture triggers capture (check img/ directory)
- [ ] /list_files returns JSON with files
- [ ] /led1_toggle works (LED physical change expected)
- [ ] /led2_toggle works (LED physical change expected)

### Video Streaming
- [ ] Browser can open `http://<device-ip>:5000/video_feed`
- [ ] Video shows in browser (not just loading)
- [ ] Video is smooth (no major stuttering)
- [ ] Can view for 60+ seconds without disconnection

### Capture Quality
- [ ] Captured image appears in browser/files
- [ ] Image resolution is 2592×1944 (check with: `identify img/RF_pic_*.jpeg`)
- [ ] Image quality is good (sharp, correct colors)
- [ ] Capture time is 3-6 seconds

### Power Management
- [ ] Device enters IDLE after 5 minutes (status LED slow blink)
- [ ] Camera turns off in IDLE (stream shows frozen frame)
- [ ] Device shutdown possible (manual power off or 15 min timer)
- [ ] Device can be powered back on (power button)

## 🔌 System Resources

### During Idle
- [ ] CPU usage < 10%: `top`
- [ ] Memory usage < 120 MB: `free -h`
- [ ] Temperature < 60°C: `vcgencmd measure_temp`
- [ ] Power ~120 mA (if measured)

### During Streaming
- [ ] CPU usage < 50% (should be 30-40%): `top`
- [ ] Memory usage < 150 MB: `free -h`
- [ ] Temperature < 70°C: `vcgencmd measure_temp`
- [ ] Power ~350-400 mA (if measured)

### During Capture
- [ ] CPU briefly spikes to ~100% (normal during encode)
- [ ] Memory stays < 150 MB: `free -h`
- [ ] Temperature < 80°C: `vcgencmd measure_temp`
- [ ] Capture completes (doesn't hang)

## 📁 File System

- [ ] `img/` directory exists and is writable
- [ ] Enough space on SD card: `df -h` (>500 MB free)
- [ ] SD card speed adequate: `dd if=/dev/urandom of=/tmp/test bs=1M count=100 && rm /tmp/test` (~10+ MB/s write)
- [ ] No permission errors in logs

## 🔒 Security (If Exposing Online)

- [ ] Change default SSH password: `passwd`
- [ ] SSH key authentication enabled (optional but recommended)
- [ ] Firewall rules configured (if needed)
- [ ] HTTPS considered (use reverse proxy like nginx)
- [ ] Access controls in place

## 📊 Logging & Monitoring

- [ ] Systemd service created: `sudo systemctl status device-app`
- [ ] Logs accessible: `sudo journalctl -u device-app -n 50`
- [ ] No error messages in logs
- [ ] Service auto-restarts on failure (configured)
- [ ] Can monitor from remote SSH

## 🎯 Configuration

### For RPi Zero W
- [ ] `RPI_ZERO_MODE = True` in code
- [ ] `STREAM_RESOLUTION = (320, 480)`
- [ ] `STREAM_FRAMERATE = 10`
- [ ] `STREAM_JPEG_QUALITY = 50`

### For RPi 4B/5
- [ ] `RPI_ZERO_MODE = False` (or True if optimized version)
- [ ] Adjust STREAM_* settings to higher values

### Battery Optimizations
- [ ] `INACTIVITY_IDLE_TIMEOUT = 300` (5 min)
- [ ] `INACTIVITY_SHUTDOWN_TIMEOUT = 900` (15 min)
- [ ] Power button tested (3+ second hold)

## 🎨 Visual Indicators

### LEDs During Normal Operation
- [ ] Status LED: Steady green
- [ ] Power LED: Steady green
- [ ] Other LEDs: Off (until toggled)
- [ ] Capture LED: Brief flash on capture

### LEDs During Idle
- [ ] Status LED: Slow blinking (normal)
- [ ] Power LED: Slow blinking (normal)

### LEDs During Boot
- [ ] Status LED: Rapid blinking
- [ ] Power LED: Steady (normal)

### LEDs During Shutdown
- [ ] Status LED: Fast blinking
- [ ] Power LED: Fast blinking
- [ ] System shuts down cleanly

## 📱 Client Access

### From Browser
- [ ] Desktop browser streams smoothly: `http://<device-ip>:5000/video_feed`
- [ ] Mobile browser works
- [ ] Can capture from browser
- [ ] Can toggle LEDs from browser

### From Command Line
- [ ] curl can access all endpoints
- [ ] ffmpeg can stream from device (optional): `ffmpeg -i http://<device-ip>:5000/video_feed -t 10 out.mp4`

## 🔄 Reliability Tests

### Continuous Operation (30 min)
- [ ] Stream continuously for 30 minutes
- [ ] No crashes or disconnections
- [ ] Temperature stable
- [ ] No unexpected shutdowns

### Capture Stress Test
- [ ] Capture 10 images in succession
- [ ] All images saved correctly
- [ ] No file corruption
- [ ] All images have correct metadata

### Network Interruption Recovery
- [ ] Disconnect WiFi
- [ ] Stream drops (expected)
- [ ] Reconnect WiFi
- [ ] Stream resumes (should reconnect within 10 sec)

### Button Stress Test
- [ ] Press each button 10 times rapidly
- [ ] No button missed
- [ ] No system lock-up
- [ ] Responsive action each time

## 💾 Backup & Recovery

- [ ] Config backed up: `cp final\ \(1\).py final\ \(1\).py.bak`
- [ ] Image files backed up (if valuable)
- [ ] Can restore from backup if needed
- [ ] Recovery procedure documented

## 🚀 Pre-Flight Checklist

Before final deployment:

- [ ] All above items checked ✓
- [ ] No known issues remaining
- [ ] Performance acceptable
- [ ] Reliability confirmed
- [ ] Documentation read and understood
- [ ] Contact info/support available
- [ ] Monitoring plan in place
- [ ] Backup plan in place

## ⚠️ Known Limitations (RPi Zero W)

Accept these trade-offs:

- ✓ Maximum 10 FPS streaming (vs 20 on RPi 4B)
- ✓ 30-40% CPU usage during stream (vs 15-25%)
- ✓ Single concurrent stream maximum
- ✓ Stream lag 300-400 ms (normal)
- ✓ 3-6 second capture time (vs 1-2 sec)
- ✓ Limited to 2.4 GHz WiFi only

These are expected and acceptable on Zero W.

## 🎉 Deployment Ready

If all checkboxes are ✓, your device is ready for deployment!

### Next Steps
1. Set up auto-start: [QUICKSTART_ZERO_W.md](QUICKSTART_ZERO_W.md)
2. Document access (IP, port, credentials)
3. Test remote access
4. Monitor first 24 hours
5. Archive this checklist with date & status

## 📝 Sign-Off

- **Device IP**: _______________
- **Deployment Date**: _______________
- **Tested By**: _______________
- **Status**: [ ] Ready [ ] Not Ready
- **Notes**: _________________________________

---

For issues, refer to:
- RPI_ZERO_W_OPTIMIZATION.md (Technical)
- QUICKSTART_ZERO_W.md (Setup)
- README.md (Complete Reference)
