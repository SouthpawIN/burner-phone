# 🔥 Burner Phone - Universal Phone Agent

![Burner Phone](burner-phone-pfp.webp)

**Universal Android Device Control Framework** - Works on physical phones (Termux or ADB), emulators, and even integrates with AI agents as a self-aware phone companion.

## Use Cases

### 1. Burner Phone Automation
Control temporary/test devices for automation tasks, testing, or privacy-focused workflows.

### 2. Spare Phone AI Companion
Turn an old phone into an always-listening AI device with camera, mic, and speaker access.

### 3. Emulator Testing
Test Android apps or automate workflows without needing physical hardware.

### 4. Multi-Device Management
Manage multiple phones (physical + emulators) from one configuration.

### 5. AI Agent Integration
Integrate with AI agents like Hermes for self-aware phone companionship.

## What's New in v2.0

✨ **Universal Device Support**
- Termux Android (best performance)
- Standard Android via ADB only
- Emulators (Android Studio, Genymotion, Waydroid)
- Auto-detection of device type

🤖 **AI Agent Integration**
- Can run as standalone skill OR integrate with AI agents like Hermes
- Vision feedback loop preserved from v1
- Configuration-driven setup

📱 **Multi-Device Management**
- Configure multiple devices in one place
- Hot-swap between physical phones and emulators
- Works across Tailscale networks

## Quick Start

### Option 1: As a Skill (Backward Compatible)

```bash
# Clone the skill
git clone https://github.com/SouthpawIN/burner-phone.git ~/.opencode/skills/burner-phone
cd ~/.opencode/skills/burner-phone

# Install dependencies
pip install -r requirements.txt

# Configure your device
cp config.example.yaml ~/.hermes-phone-agent/config.yaml
nano ~/.hermes-phone-agent/config.yaml  # Edit for your device

# Test connection
python3 scripts/test_device.py
```

### Option 2: As Universal Phone Agent

```bash
# Clone anywhere you want
git clone https://github.com/SouthpawIN/burner-phone.git
cd burner-phone

# Install
pip install -r requirements.txt

# Configure (see below)
cp config.example.yaml config.yaml
nano config.yaml

# Use in Python
from phone_agent import PhoneAgent

agent = PhoneAgent()
agent.capture_camera()  # Take photo
agent.record_audio(5)   # Record 5 seconds
agent.play_audio("output.wav")
```

## Configuration

Create `~/.hermes-phone-agent/config.yaml`:

### For Termux Phone (Best Performance)

```yaml
name: "Samsung Galaxy S10"
device_type: "termux"
ip_address: "100.93.96.90"  # Tailscale IP
ssh_port: 8022
ssh_key: "~/.ssh/phone_access"
screen_pin: "4658"
```

### For Standard Android (No Termux)

```yaml
name: "My Android Phone"
device_type: "adb"
ip_address: "100.x.x.x"  # Your phone's IP
adb_port: 5555
screen_pin: "your_pin"
```

### For Emulator (No Spare Phone?)

```yaml
name: "Android Emulator"
device_type: "emulator"
ip_address: "localhost"
adb_port: 5555
screen_pin: null  # Usually no PIN on emulators
```

## Features

### Vision Feedback Loop (v1 Compatible)

```bash
# Take screenshot
adb exec-out screencap -p > ./assets/screen.png

# Analyze with AI
python3 scripts/vision_helper.py ./assets/screen.png "Find the Settings icon"

# Tap at coordinates returned by vision
adb shell input tap 540 1200
```

### New Audio Controls

```python
from phone_agent import PhoneAgent

agent = PhoneAgent()

# Record audio
agent.record_audio(duration=5, output_path="recording.wav")

# Play audio
agent.play_audio("response.wav")

# Capture camera (front-facing on supported devices)
agent.capture_camera()
```

### Screen Control

```python
# Wake screen
agent.wake_screen()

# Unlock with PIN
agent.unlock_screen(pin="4658")

# Type text
agent.type_text("Hello world")
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                 Phone Agent Framework                │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │
│  │   Termux     │  │    ADB       │  │Emulator  │  │
│  │   Backend    │  │   Backend    │  │ Backend  │  │
│  └──────┬───────┘  └──────┬───────┘  └────┬─────┘  │
│         │                 │                │        │
│         └─────────────────┼────────────────┘        │
│                           ▼                         │
│              ┌─────────────────────┐                │
│              │  Device Abstraction │                │
│              │       Layer         │                │
│              └──────────┬──────────┘                │
│                         │                           │
│         ┌───────────────┼───────────────┐          │
│         ▼               ▼               ▼          │
│  ┌────────────┐  ┌────────────┐  ┌──────────┐     │
│  │   Camera   │  │   Audio    │  │  Screen  │     │
│  │  Control   │  │  Control   │  │  Control │     │
│  └────────────┘  └────────────┘  └──────────┘     │
└─────────────────────────────────────────────────────┘
```

## Directory Structure

```
burner-phone/
├── SKILL.md                    # Openskills manifest (v1 compatible)
├── README.md                   # This file
├── config.example.yaml         # Configuration template
├── requirements.txt            # Python dependencies
├── phone_agent.py              # Main agent interface (NEW)
├── backends/                   # Device backends (NEW)
│   ├── device_base.py          # Abstract base class
│   ├── termux_backend.py       # Termux support
│   ├── adb_backend.py          # Standard ADB support
│   └── emulator_backend.py     # Emulator support
├── config/                     # Configuration system (NEW)
│   └── device_config.py        # YAML config loader
├── scripts/                    # Utility scripts
│   ├── vision_helper.py        # Vision analysis (v1 preserved)
│   ├── test_device.py          # Test device connection (NEW)
│   └── setup.sh                # Installation script
└── assets/                     # Screenshots and media
    └── screen.png
```

## Requirements

- Python 3.8+
- ADB (Android Debug Bridge)
- For Termux: SSH access to device
- For vision: Senter Server or compatible vision API

### Install Dependencies

```bash
# System dependencies
sudo apt install adb ffmpeg  # Debian/Ubuntu
brew install android-platform-tools ffmpeg  # macOS

# Python dependencies
pip install -r requirements.txt
```

## Testing

```bash
# Test device connection
python3 scripts/test_device.py

# Test camera capture
python3 -c "from phone_agent import PhoneAgent; PhoneAgent().capture_camera()"

# Test audio recording
python3 -c "from phone_agent import PhoneAgent; PhoneAgent().record_audio(2, 'test.wav')"
```

## Migration from v1

v1 users: The vision feedback loop is **fully preserved**. Your existing workflows using `vision_helper.py` and ADB commands continue to work exactly as before. The new framework adds capabilities without breaking compatibility.

### What Changed

- ✅ Vision helper script unchanged
- ✅ ADB commands work the same way
- ✅ SKILL.md format preserved for openskills
- 🆕 Device abstraction layer
- 🆕 Multiple backend support
- 🆕 Configuration-driven setup
- 🆕 Python API for integration

## Related Projects

- [Senter](https://github.com/SouthpawIN/Senter) - AI phone companion framework
- [Senter-Server](https://github.com/SouthpawIN/Senter-Server) - Model proxy server
- [Hermes Agent](https://github.com/nous-research/hermes) - AI agent framework

## License

MIT
