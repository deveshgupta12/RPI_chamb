#!/bin/bash

# Device App Setup Script for Raspberry Pi
# Supports RPi Zero W, RPi 3B+, RPi 4B, RPi 5

echo "=========================================="
echo "Device App Installation Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Raspberry Pi
if ! grep -qi "raspberry" /proc/cpuinfo; then
    echo -e "${YELLOW}Warning: This doesn't appear to be running on Raspberry Pi${NC}"
    echo "Continuing anyway..."
fi

echo "[1/6] Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

echo "[2/6] Installing dependencies..."
# Install core system packages
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    git \
    build-essential \
    libatlas-base-dev \
    libharfbuzz0b \
    libopenjp2-7

# Install libcap-dev for python-prctl (optional, skip on install failure)
echo "Installing optional system libraries..."
sudo apt-get install -y libcap-dev || echo "Note: libcap-dev not available, some features may be limited"

# Optional: Install image processing libraries if available
for pkg in libjasper-dev libwebp6 libtiff5; do
    if apt-cache search "^$pkg$" | grep -q .; then
        sudo apt-get install -y "$pkg" || true
    fi
done

echo "[3/6] Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "[4/6] Installing Python packages..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo "Handling optional dependencies..."
# These may fail on some systems - that's okay
pip install python-prctl || echo "Note: python-prctl install skipped (optional)"

echo "[5/6] Creating image directory..."
mkdir -p img
chmod 755 img

echo "[6/6] Setting up permissions..."
sudo usermod -a -G gpio pi
sudo usermod -a -G video pi

# Detect RPi model
echo ""
echo "Detecting Raspberry Pi model..."
if grep -q "Pi Zero W" /proc/device-tree/model; then
    echo -e "${GREEN}✓ Detected: Raspberry Pi Zero W${NC}"
    echo "  RPI_ZERO_MODE will be enabled"
elif grep -q "Pi Zero" /proc/device-tree/model; then
    echo -e "${GREEN}✓ Detected: Raspberry Pi Zero${NC}"
    echo "  RPI_ZERO_MODE will be enabled"
elif grep -q "Pi 4" /proc/device-tree/model; then
    echo -e "${GREEN}✓ Detected: Raspberry Pi 4${NC}"
    echo "  Standard optimizations will be used"
elif grep -q "Pi 5" /proc/device-tree/model; then
    echo -e "${GREEN}✓ Detected: Raspberry Pi 5${NC}"
    echo "  Standard optimizations will be used"
else
    echo -e "${YELLOW}⚠ Could not detect RPi model, using standard settings${NC}"
fi

# Offer to enable camera
echo ""
echo -e "${YELLOW}Important: Camera interface needs to be enabled${NC}"
read -p "Do you want to enable camera interface now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Opening raspi-config..."
    echo "Please navigate to: Interface Options → Camera → Enable"
    echo "Then exit and reboot when prompted."
    sudo raspi-config
fi

# Offer to create systemd service
echo ""
echo -e "${YELLOW}Optional: Create systemd service for auto-start?${NC}"
read -p "Create systemd service? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Creating systemd service file..."
    sudo tee /etc/systemd/system/device-app.service > /dev/null <<EOF
[Unit]
Description=Device IoT Application
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
ExecStart=$(pwd)/venv/bin/python3 "final (1).py"
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable device-app
    echo -e "${GREEN}✓ Service created and enabled${NC}"
    echo "  Start it with: sudo systemctl start device-app"
    echo "  Check status: sudo systemctl status device-app"
    echo "  View logs: sudo journalctl -u device-app -f"
fi

echo ""
echo -e "${GREEN}=========================================="
echo "Installation Complete!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Enable camera (if you skipped it): raspi-config"
echo "2. Reboot: sudo reboot"
echo "3. Start the app: python3 \"final (1).py\""
echo "4. View in browser: http://<device-ip>:5000/video_feed"
echo ""
echo "For help, see:"
echo "  - README.md (full documentation)"
echo "  - QUICKSTART_ZERO_W.md (quick start)"
echo "  - RPI_ZERO_W_OPTIMIZATION.md (Zero W details)"
echo ""
