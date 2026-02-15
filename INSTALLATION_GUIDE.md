# Installation Guide

This guide provides step-by-step instructions for installing and setting up your Raspberry Pi Battery-Optimized IoT Device.

## Prerequisites

- Raspberry Pi (Zero W, 4B, or 5)
- PiCamera module
- MicroSD card (8GB+ recommended)
- Power supply
- Buttons and LEDs as per GPIO mapping

## Setup Instructions

### 1. Operating System Installation

1. Download Raspberry Pi OS Lite from the official website
2. Flash the OS to your microSD card using Raspberry Pi Imager
3. Enable SSH by creating an empty `ssh` file in the boot partition
4. Configure Wi-Fi by creating a `wpa_supplicant.conf` file in the boot partition

### 2. Initial Configuration

```bash
sudo raspi-config
```

Enable the following interfaces:
- Camera
- SSH
- I2C (if needed for additional sensors)

### 3. Software Installation

Run the setup script:

```bash
chmod +x setup.sh
./setup.sh
```

This script will:
- Update the system packages
- Install Python dependencies
- Install required system packages
- Set up the virtual environment
- Configure GPIO permissions
- Create necessary directories

### 4. Configuration

Edit the configuration file to match your setup:

```bash
nano config.ini
```

Key settings to configure:
- RPI_ZERO_MODE (True for Pi Zero W, False for Pi 4B/5)
- Stream resolution and quality settings
- Power management timeouts
- GPIO pin mappings

### 5. Service Setup

To run the application as a service:

```bash
sudo systemctl enable rpi-camera.service
sudo systemctl start rpi-camera.service
```

### 6. Accessing the Device

Once installed, you can access the device through:
- Web interface: `http://[device-ip]:5000`
- SSH connection for administration
- Physical buttons for basic controls

## Troubleshooting

If you encounter issues during installation:

1. Check that all dependencies are installed:
   ```bash
   pip list | grep -E "(flask|picamera|gpio)"
   ```

2. Verify GPIO permissions:
   ```bash
   groups pi
   ```
   (Should include gpio, video, and i2c groups)

3. Check the logs:
   ```bash
   journalctl -u rpi-camera.service
   ```

## Updating the Software

To update to the latest version:

```bash
git pull origin master
sudo systemctl restart rpi-camera.service
```