---
name: burner-phone-control
description: "Complete Android phone control via ADB/SSH - camera, audio, screen, apps"
trigger_conditions:
  - "Full phone automation needed"
  - "Controlling Android device remotely"
tools_required:
  - "terminal"
  - "browser_navigate"
  - "vision_analyze"
---

# Burner-Phone Control Skill

## Overview

Complete remote control of Android phones via ADB (USB/wireless) or SSH (Termux). Enables camera capture, audio recording/playback, screen control, app launching, and vision-guided UI interaction.

### Supported Devices:
- **S10** - 100.93.96.90:8022 (SSH/Termux) + ADB RF8M221SXHZ
- **Duo** - 100.79.15.54:8022 (SSH/Termux)
- Any Android with ADB wireless debugging enabled

## Phone Agent Interface

### 1. Camera Control

```python
def capture_front_camera():
    """Capture front-facing camera image."""
    # Via ADB (works on any Android)
    subprocess.run([
        "adb", "-s", "RF8M221SXHZ",
        "shell", "am", "start", "-a", "android.media.action.IMAGE_CAPTURE",
        "--et", "android.intent.extra.CAMERA_FACING", "1"  # Front camera
    ])
    
    # Pull latest photo
    subprocess.run([
        "adb", "-s", "RF8M221SXHZ",
        "pull", "/sdcard/DCIM/Camera/IMG_*.jpg", "/tmp/front-camera.jpg"
    ])

def capture_screenshot():
    """Capture screen screenshot."""
    # Via ADB
    subprocess.run([
        "adb", "-s", "RF8M221SXHZ",
        "exec-out", "screencap", "-p"
    ], stdout=open("/tmp/screenshot.png", "wb"))
    
    # Or via SSH (Termux)
    subprocess.run([
        "ssh", "-p", "8022", "droid@100.93.96.90",
        "screencap -p /sdcard/screen.png"
    ])
```

### 2. Audio Control

```python
def record_audio(duration=5):
    """Record audio for specified duration."""
    # Via ADB + arecord (if available) or screen recording with audio
    subprocess.run([
        "adb", "-s", "RF8M221SXHZ",
        "shell", "screenrecord",
        "--time-limit", str(duration),
        "/sdcard/recording.mp4"
    ])
    
    # Extract audio
    subprocess.run([
        "adb", "-s", "RF8M221SXHZ",
        "pull", "/sdcard/recording.mp4", "/tmp/"
    ])

def play_audio(audio_path):
    """Play audio file through phone speaker."""
    # Push audio to phone
    subprocess.run([
        "adb", "-s", "RF8M221SXHZ",
        "push", audio_path, "/sdcard/playback.mp3"
    ])
    
    # Play via Intent
    subprocess.run([
        "adb", "-s", "RF8M221SXHZ",
        "shell", "am", "startactivity",
        "-a", "android.intent.action.VIEW",
        "-t", "audio/mp3",
        f"file:///sdcard/playback.mp3"
    ])
```

### 3. Screen Control

```python
def wake_screen():
    """Wake device if screen is off."""
    subprocess.run([
        "adb", "-s", "RF8M221SXHZ",
        "shell", "input", "keyevent", "26"  # POWER key
    ])

def unlock_screen(pin="4658"):
    """Enter PIN to unlock screen."""
    wake_screen()
    time.sleep(1)  # Wait for lock screen
    
    # Type PIN digits
    for digit in pin:
        subprocess.run([
            "adb", "-s", "RF8M221SXHZ",
            "shell", "input", "text", digit
        ])
    time.sleep(0.5)
    
    # Swipe up to unlock (if pattern/gesture)
    subprocess.run([
        "adb", "-s", "RF8M221SXHZ",
        "shell", "input", "swipe", "540", "1000", "540", "500", "200"
    ])

def tap(x, y):
    """Tap at coordinates."""
    subprocess.run([
        "adb", "-s", "RF8M221SXHZ",
        "shell", "input", "tap", str(x), str(y)
    ])

def swipe(x1, y1, x2, y2, duration=200):
    """Swipe from (x1,y1) to (x2,y2)."""
    subprocess.run([
        "adb", "-s", "RF8M221SXHZ",
        "shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration)
    ])
```

### 4. App Control

```python
def launch_app(package_name):
    """Launch app by package name."""
    subprocess.run([
        "adb", "-s", "RF8M221SXHZ",
        "shell", "monkey", "-p", package_name, "1"
    ])

def open_url(url):
    """Open URL in default browser."""
    subprocess.run([
        "adb", "-s", "RF8M221SXHZ",
        "shell", "am", "start",
        "-a", "android.intent.action.VIEW",
        f"{url}"
    ])

def kill_app(package_name):
    """Force stop app."""
    subprocess.run([
        "adb", "-s", "RF8M221SXHZ",
        "shell", "am", "force-stop", package_name
    ])
```

### 5. Vision-Guided UI Interaction

```python
def find_and_tap_element(description):
    """Use vision to find element and tap it."""
    from hermes_tools import browser_navigate, vision_analyze
    
    # Capture screenshot
    capture_screenshot()
    
    # Analyze with vision
    result = vision_analyze(
        image_url="/tmp/screenshot.png",
        question=f"""Find the element: {description}
        Return exact center coordinates (x, y) as JSON:
        {{"found": true/false, "x": number, "y": number, "confidence": 0-1}}"""
    )
    
    # Parse result and tap
    import json
    match = re.search(r'\{[^}]+\}', result)
    if match:
        coords = json.loads(match.group())
        if coords.get("found") and coords.get("confidence", 0) > 0.7:
            tap(coords["x"], coords["y"])
            return True
    return False
```

## Complete Phone Control Example

```python
def check_weather_on_phone():
    """Open weather app and read current temperature."""
    # Wake and unlock
    wake_screen()
    unlock_screen("4658")
    
    # Launch weather app
    launch_app("com.google.android.apps.weather")
    time.sleep(2)
    
    # Capture screen
    capture_screenshot()
    
    # Read temperature with vision
    temp = vision_analyze(
        image_url="/tmp/screenshot.png",
        question="What is the current temperature shown? Return as number." 
    )
    
    return temp
```

## Device Configuration

```yaml
# ~/.hermes-phone-agent/config.yaml
name: "Samsung Galaxy S10"
device_type: "termux"

ip_address: "100.93.96.90"
ssh_port: 8022
adb_device_id: "RF8M221SXHZ"

ssh_key: "~/.ssh/phone_access"
ssh_user: "droid"

screen_pin: "4658"
```

## Verification Steps

```bash
# Verify ADB connection
adb -s RF8M221SXHZ shell getprop ro.build.model
# Should return: SM-G973U or similar

# Verify SSH (if Termux with openssh installed)
ssh -p 8022 droid@100.93.96.90 'echo connected'

# Test screenshot
cd /tmp && adb -s RF8M221SXHZ exec-out screencap -p > test.png
ls -la test.png  # Should exist with size > 0
```

## Integration with Other Skills

- **card-scanner-vision** - Uses camera capture for MTG card scanning
- **senter-attention** - Uses front camera + mic for gaze detection
- **speak** - Routes TTS audio to phone speaker
- **pocket-shop-loop** - Phone as portable card scanner