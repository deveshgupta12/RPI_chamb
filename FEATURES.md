# Features Overview

This document outlines all the features of the Raspberry Pi Battery-Optimized IoT Device.

## Core Features

### Battery Optimization
- Lazy camera initialization (starts only when needed)
- Intelligent idle mode with automatic power-down
- Reduced polling frequency to minimize CPU wake-ups
- Efficient LED blinking patterns
- Single autofocus mode (not continuous)
- Automatic shutdown after configurable inactivity period
- Hardware sleep modes for reduced power consumption
- CPU frequency scaling when in idle mode

### Hardware Control
- Manual power button for device on/off
- LED toggle buttons with state feedback
- Capture button with long-press support
- Status indication LEDs
- GPIO-based button inputs with debouncing
- Hardware interrupts for responsive button handling

### Camera & Video
- Video streaming via MJPEG
- High-resolution image capture with autofocus
- Configurable resolution and quality
- Automatic camera shutdown in idle mode
- Frame rate limiting for smoother playback
- Optimized JPEG encoding quality settings
- Frame skipping on Pi Zero W for performance

### Web Interface
- RESTful API for all device functions
- Real-time device status
- File listing with pagination
- Power state monitoring
- Video streaming endpoint (/video_feed)
- Image capture endpoint
- System health monitoring

### Power Management
- Automatic shutdown after inactivity
- Idle mode with reduced power consumption
- Manual power control via button
- Graceful device state transitions
- Device wake-on-client-activity
- Inactivity timer with reset functionality
- System state tracking (POWERED_OFF, BOOTING, RUNNING, IDLE, SHUTTING_DOWN)

## Platform-Specific Optimizations

### Raspberry Pi Zero W Optimizations
- Reduced frame rates for smoother performance
- Frame skipping to reduce CPU load
- Lower JPEG quality settings to reduce processing
- Disabled Flask reloader to save CPU cycles
- Specific threading configurations for single-core CPU
- Memory usage optimizations
- Network interface management

### Raspberry Pi 4B/5 Optimizations
- Higher resolution streaming options
- Increased frame rates
- Better multi-threading support
- Enhanced performance capabilities

## Network Features
- Wi-Fi hotspot creation capability
- Client monitoring to detect when devices connect/disconnect
- mDNS broadcasting for service discovery
- Remote access via web interface
- Automatic IP address detection

## Security Features
- Protected endpoints with authentication (where applicable)
- Secure GPIO access patterns
- Proper error handling to prevent crashes
- Input validation on API endpoints
- Safe shutdown procedures

## Monitoring & Logging
- Comprehensive logging system
- Activity timestamp tracking
- Error reporting and handling
- System state change logging
- Performance metrics collection