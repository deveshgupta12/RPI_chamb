#!/bin/bash

# Device App Uninstall Script for Raspberry Pi
# Safely removes the application and cleans up

echo "=========================================="
echo "Device App Uninstall Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Confirm before proceeding
read -p "Are you sure you want to uninstall the Device App? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstall cancelled."
    exit 0
fi

echo ""
echo "[1/5] Stopping systemd service (if running)..."
if systemctl is-active --quiet device-app; then
    echo "Stopping device-app service..."
    sudo systemctl stop device-app
    echo "✓ Service stopped"
fi

if [ -f /etc/systemd/system/device-app.service ]; then
    echo "Disabling and removing systemd service..."
    sudo systemctl disable device-app
    sudo rm /etc/systemd/system/device-app.service
    sudo systemctl daemon-reload
    echo -e "${GREEN}✓ Service removed${NC}"
else
    echo "No systemd service found (skipped)"
fi

echo ""
echo "[2/5] Removing virtual environment..."
if [ -d "venv" ]; then
    echo "Deleting Python virtual environment..."
    rm -rf venv
    echo -e "${GREEN}✓ Virtual environment removed${NC}"
else
    echo "No virtual environment found (skipped)"
fi

echo ""
echo "[3/5] Handling image files..."
read -p "Do you want to keep the captured images in 'img/' directory? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    if [ -d "img" ]; then
        echo "Deleting image directory..."
        rm -rf img
        echo -e "${GREEN}✓ Image directory removed${NC}"
    fi
else
    echo "Keeping image directory"
fi

echo ""
echo "[4/5] Cleaning up Python cache..."
if [ -d "__pycache__" ]; then
    rm -rf __pycache__
    echo -e "${GREEN}✓ Python cache cleaned${NC}"
else
    echo "No cache found (skipped)"
fi

# Find and remove all __pycache__ directories
if find . -type d -name "__pycache__" -delete 2>/dev/null; then
    echo -e "${GREEN}✓ All Python caches removed${NC}"
fi

echo ""
echo "[5/5] Removing GPIO group permissions..."
# Restore GPIO group permissions (optional - user remains in gpio group)
echo "Note: User 'pi' will retain membership in 'gpio' and 'video' groups"
echo "      To fully remove these, run:"
echo "      sudo deluser pi gpio"
echo "      sudo deluser pi video"

echo ""
echo -e "${GREEN}=========================================="
echo "Uninstallation Complete!"
echo "==========================================${NC}"
echo ""
echo "What remains:"
echo "  ✓ Source code (final new.py, README.md, etc.)"
echo "  ✓ Documentation files"
echo "  ○ Virtual environment: REMOVED"
echo "  ○ Systemd service: REMOVED"
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "  ○ Image directory (img/): REMOVED"
else
    echo "  ✓ Image directory (img/): KEPT"
fi
echo ""
echo "To reinstall:"
echo "  bash setup.sh"
echo ""
