---
name: burner-phone-wireless-scanner
description: "Wireless S10 camera capture for card scanning over TailScale"
trigger_conditions:
  - "Using S10 as wireless card scanner"
  - "Capturing card images over network"
tools_required:
  - "terminal"
  - "vision_analyze"
---

# Burner-Phone Wireless Scanner Skill

## Overview

Enables the S10 phone to function as a **wireless card scanner** connected via TailScale (no USB required). Uses SSH and wireless ADB over the network for camera capture.

### Connection Details:
- **S10 IP:** 100.93.96.90 (via TailScale)
- **SSH Port:** 8022
- **Wireless ADB Port:** 5555

## Setup for Wireless Operation

### 1. Enable Wireless ADB on S10 (One-Time Setup)

```bash
# Connect S10 via USB temporarily
cd /home/sovthpaw/burner-phone/

# Start wireless ADB on port 5555
adb -s RF8M221SXHZ tcpip 5555

# Now disconnect USB - ADB stays active over network
```

### 2. Connect Wirelessly Over TailScale

```bash
# Connect to S10 via wireless ADB over TailScale
adb connect 100.93.96.90:5555

# Verify connection
adb devices
# Should show: 100.93.96.90:5555  device
```

### 3. Alternative: SSH-Based Screen Capture

If wireless ADB isn't available, use SSH to trigger camera:

```bash
# Via SSH, take screenshot
curl -X POST http://127.0.0.1:8080/screenshot
# Or use termux:widget for camera capture
```

## Card Scanning Workflow

### Step 1: Open Camera App on S10

```bash
# Via SSH to S10
curl -X POST http://127.0.0.1:8080/app/com.google.android.camera

# Or via ADB
adb -s 100.93.96.90:5555 shell am start -n com.google.android.camera/view.photo
```

### Step 2: User Points Camera at Card

User physically positions S10 camera over the card to scan.

### Step 3: Capture Image

**Option A: Screenshot (if card shown on screen)**
```bash
# Via SSH over TailScale
ssh -p 8022 termux@100.93.96.90 'termux-touch-notification "Capture" && screencap -p /sdcard/card-scan.png'

# Pull image to host
scp -P 8022 termux@100.93.96.90:/sdcard/card-scan.png:/tmp/card-scan.png
```

**Option B: Camera Capture via ADB**
```bash
# Take screenshot via wireless ADB
adb -s 100.93.96.90:5555 exec-out screencap -p > /tmp/card-scan.png
```

### Step 4: Analyze with Vision Tool

```python
from hermes_tools import vision_analyze

def scan_card(image_path):
    """Identify card from captured image."""
    result = vision_analyze(
        image_url=image_path,
        question="""Identify this Magic: The Gathering trading card. Provide:
1. Card name (exact name as printed)
2. Set name and set code (e.g., "Fourth Edition [4ED]")
3. Card number if visible
4. Condition assessment: Mint, Near Mint, Excellent, Good, Lightly Played, Heavily Played, or Damaged
5. Whether it's foil, stamped, or has any variants
6. Confidence level (0-1)

Format as JSON with keys: name, set_name, set_code, card_number, condition, is_foil, has_stamp, confidence"""
    )
    return parse_result(result)
```

## Quick Card Scan Command

```bash
# One-liner to capture and scan a card
ssh -p 8022 termux@100.93.96.90 'screencap -p /sdcard/card.png' && \
scp -P 8022 termux@100.93.96.90:/sdcard/card.png:/tmp/ && \
echo "Card image captured to /tmp/card.png - ready for vision analysis"
```

## Verification Steps

```bash
# Verify TailScale connection to S10
ping 100.93.96.90

# Verify SSH works
ssh -p 8022 termux@100.93.96.90 'echo connected'

# Verify wireless ADB (if enabled)
adb connect 100.93.96.90:5555
adb -s 100.93.96.90:5555 shell getprop ro.build.model
# Should return: RF8M221SXHZ or similar S10 identifier
```

## Integration with Pocket-Shop Loop

```python
def wireless_card_scan():
    """Capture card image from S10 and identify it."""
    import subprocess
    
    # Capture screenshot from S10 via SSH
    subprocess.run([
        "ssh", "-p", "8022", "termux@100.93.96.90",
        "screencap -p /sdcard/card-scan.png"
    ])
    
    # Pull image to host
    subprocess.run([
        "scp", "-P", "8022",
        "termux@100.93.96.90:/sdcard/card-scan.png",
        "/tmp/card-scan.png"
    ])
    
    # Analyze with vision
    from hermes_tools import vision_analyze
    card_data = vision_analyze(
        image_url="/tmp/card-scan.png",
        question="Identify this Magic: The Gathering card..."
    )
    
    return card_data
```

## Troubleshooting

**Wireless ADB not connecting:**
```bash
# Re-enable wireless ADB (requires USB temporarily)
adb -s RF8M221SXHZ tcpip 5555
```

**SSH connection failed:**
```bash
# Verify TailScale is running on both ends
sudo tailscale status

# Check S10 is reachable
ping 100.93.96.90
```

**Camera app not opening:**
```bash
# Try alternative camera app package name
adb -s 100.93.96.90:5555 shell pm list packages | grep camera
```

## Notes

- S10 must remain connected to TailScale network
- Wireless ADB may need re-enabling after S10 reboot
- SSH method works without wireless ADB setup
- Camera quality depends on lighting and steadiness