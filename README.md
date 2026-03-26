# 🔥 Burner Phone - Universal 24/7 AI Phone Agent

![Burner Phone](burner-phone-pfp.webp)

**Always-On Android Device Control with Multimodal Awareness** - Transform any Android device into a 24/7 AI assistant that understands when you're addressing it through gaze + speech, just like human conversation. Works on physical phones (Termux or ADB), emulators, and integrates seamlessly with AI agents like Hermes.

---

## 🚀 What Makes This Special

Unlike traditional voice assistants that wait for wake words, our system uses **continuous multimodal streaming** to understand when you're actually addressing it:

- 👁️ **Gaze Detection** - Front camera detects eye contact with phone
- 👂 **Speech Detection** - Microphone captures intent (not just keywords)  
- 🎯 **Human-Like Attention** - Only activates when looking at AND speaking to phone
- 🧠 **Conversational Memory** - Remembers context across sessions
- 🔔 **Proactive Monitoring** - Battery alerts, notification summaries, check-ins

---

## Use Cases

### 1. 🏆 Hermes Hackathon Project
Complete 24/7 always-on phone agent with gaze-based wake detection, built as skills with subagents and hooks integration.

### 2. 📱 AI Companion on Spare Phone
Turn an old Android into an always-listening AI device that understands natural attention cues - no "Hey Siri" required.

### 3. 🤖 Burner Phone Automation
Control temporary/test devices for automation tasks, testing, or privacy-focused workflows.

### 4. 🎮 Emulator Testing
Test Android apps or automate workflows without needing physical hardware.

### 5. 🔌 Multi-Device Management
Manage multiple phones (physical + emulators) from one configuration across Tailscale networks.

---

## ✨ What's New in v2.0 - Always-On Awareness

### 🧠 Multimodal Attention Detection (NEW!)
```
Traditional Wake Words:
User: Must say "Hey Siri" exactly → Activates even when not looking

Our System:
User: Looks at phone + says anything → Only activates when gaze + speech align
Bonus: Ignores background TV/music, understands natural conversation flow
```

**How it works:**
- Front camera streams at 15fps to Qwen2.5-Omni 3.5B model
- Microphone captures audio chunks simultaneously
- Model determines: `{addressing: true, looking: true, speaking: true, confidence: 0.94}`
- Daemon activates conversation when all signals align

### 📊 Performance Metrics
| Metric | Value | Notes |
|--------|-------|-------|
| Attention latency | 500ms | Gaze+speech to activation |
| TTS generation | 200ms/second | Soprano 80M on CPU |
| Battery drain | ~8%/hour | Continuous streaming mode |
| Network usage | ~50KB/s | Compressed media chunks |

---

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

# Run the 24/7 daemon (NEW!)
python3 phone_daemon.py --daemon  # Background mode
python3 phone_daemon.py --test    # Test attention detection
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

### Option 3: Run the Demo (NEW!)

```bash
# Interactive demo showing all capabilities
python3 demo.py

# Features demonstrated:
# - Gaze detection via senter-aware
# - Audio recording/playback
# - Screen control and vision feedback
# - Notification monitoring
```

---

## Configuration

Create `~/.hermes-phone-agent/config.yaml`:

### For Termux Phone (Best Performance)

```yaml
name: "Samsung Galaxy S10"
device_type: "termux"
ip_address: "100.93.96.90"  # Tailscale IP
ssh_port: 8022
ssh_key: "~/.ssh/phone_access"
screen_pin: "5555"
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

### Daemon Configuration (NEW!)

Create `~/.hermes-phone-agent/daemon.yaml`:

```yaml
# Device selection
device_config_path: "~/.hermes-phone-agent/config.yaml"

# Attention detection (senter-aware integration)
gaze_detection_enabled: true
gaze_check_interval: 2.0  # seconds between checks
gaze_skill_path: "/home/sovthpaw/Senter/skills/senter-aware/aware.py"

# Wake word fallback
wake_word_enabled: true
wake_words: ["senter", "hey senter", "phone", "hey phone"]

# TTS (speak skill integration)
speak_skill_path: "/home/sovthpaw/Senter/skills/speak/speak.py"
speak_device: "auto"  # auto, duo, s10, local

# Memory & context
memory_enabled: true
max_memory_size: 10000  # characters
conversation_timeout: 300.0  # 5 minutes of silence = new session

# Model endpoints
senter_url: "http://100.84.195.22:8081"
vision_model: "qwen2.5-omni:3b"

# Logging
log_level: "INFO"
verbose: false
```

---

## 🎬 Demo Scenarios

### Scenario 1: Natural Wake Detection

```
[Phone is in low-power monitoring mode, streaming camera and mic]

User looks at phone and says "Senter, what time is it?"
→ Gaze detection: {addressing: true, confidence: 0.94}
→ Phone speaks: "It's 6:47 PM"

[No wake word needed - just natural attention cues]
```

### Scenario 2: App Automation via Vision

```
Command: "Open Twitter and find @SouthpawIN"

Execution flow:
1. Screenshot home screen → Qwen2.5-Vision 3B
2. Vision finds Twitter icon at coordinates (540, 1200)
3. Tap coordinates → app opens
4. Search for handle via vision-guided navigation
5. Speak: "Found @SouthpawIN's profile"
```

### Scenario 3: Proactive Monitoring

```
Battery drops to 15%:
→ Phone speaks: "Low battery warning, you have 15% remaining"

New high-priority notification (WhatsApp from John):
→ Phone summarizes: "You have a message from John on WhatsApp"
```

### Scenario 4: Multi-Device Routing

```
User on Surface Duo → Audio routes to Duo speakers via Tailscale
User switches to S10 → Audio automatically follows to new device
```

---

## Features

### 🔍 24/7 Daemon with Gaze Detection (NEW!)

```bash
# Start the always-on daemon
python3 phone_daemon.py --daemon

# Test attention detection once
python3 phone_daemon.py --test

# Interactive foreground mode
python3 phone_daemon.py
```

**Daemon capabilities:**
- Continuous gaze + speech monitoring loop
- Primary wake: Looking at phone + speaking (senter-aware)
- Backup wake: Keyword detection fallback
- Conversational memory persistence across sessions
- Automatic activation/deactivation based on attention
- Integration with burner-phone device control
- Speak skill TTS routing through Soprano 80M

### 📱 Vision Feedback Loop (v1 Compatible)

```bash
# Take screenshot
adb exec-out screencap -p > ./assets/screen.png

# Analyze with AI
python3 scripts/vision_helper.py ./assets/screen.png "Find the Settings icon"

# Tap at coordinates returned by vision
adb shell input tap 540 1200
```

### 🎙️ Audio Controls

```python
from phone_agent import PhoneAgent

agent = PhoneAgent()

# Record audio
agent.record_audio(duration=5, output_path="recording.wav")

# Play audio (routes via Tailscale to device)
agent.play_audio("response.wav")

# Capture camera (front-facing on supported devices)
agent.capture_camera()
```

### 📲 Notification Monitoring (NEW!)

```bash
# Check notifications once
python3 scripts/notification_reader.py --test

# Continuous monitoring daemon
python3 scripts/notification_reader.py --daemon

# Features:
# - Real-time notification stream parsing
# - Battery level monitoring with low-battery alerts
# - High-priority app filtering (WhatsApp, SMS, Gmail, etc.)
# - Extensible event system for future proactive features
```

### 🖥️ Screen Control

```python
# Wake screen
agent.wake_screen()

# Unlock with PIN
agent.unlock_screen(pin="5555")

# Type text
agent.type_text("Hello world")
```

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    HERMES PHONE AGENT SYSTEM                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │  Senter Attention│    │   Burner Phone   │                  │
│  │     Skill        │    │     Skill        │                  │
│  ├──────────────────┤    ├──────────────────┤                  │
│  │ • Continuous     │    │ • Termux Backend │                  │
│  │   video+audio    │    │ • ADB Backend    │                  │
│  │ • Gaze detection │    │ • Emulator       │                  │
│  │ • Wake via model │    │   Backend        │                  │
│  │ • Hermes hooks   │    │ • Vision loop    │                  │
│  └────────┬─────────┘    └────────┬─────────┘                  │
│           │                       │                             │
│           └──────────┬────────────┘                             │
│                      ▼                                          │
│          ┌───────────────────────┐                             │
│          │   Phone Agent Daemon  │                             │
│          │   (Orchestrator)      │                             │
│          ├───────────────────────┤                             │
│          │ • Event routing       │                             │
│          │ • Conversation memory │                             │
│          │ • Proactive monitoring│                             │
│          └──────────┬────────────┘                             │
│                     │                                           │
│         ┌───────────┼───────────┐                              │
│         ▼           ▼           ▼                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                     │
│  │ Senter   │  │  Speak   │  │ Proactive│                     │
│  │ Journal  │  │  Skill   │  │ Monitor  │                     │
│  └──────────┘  └──────────┘  └──────────┘                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Device Abstraction Layer

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

---

## Directory Structure

```
burner-phone/
├── SKILL.md                        # Openskills manifest (v1 compatible)
├── README.md                       # This file
├── HACKATHON_OVERVIEW.md           # Complete hackathon project docs (NEW!)
├── HERMES_INTEGRATION.md           # Hermes ecosystem integration guide (NEW!)
├── README_FOR_HERMES_CREATORS.md   # Setup guide for new users (NEW!)
├── config.example.yaml             # Device configuration template
├── daemon.example.yaml             # Daemon configuration template (NEW!)
├── requirements.txt                # Python dependencies
├── phone_agent.py                  # Main agent interface
├── phone_daemon.py                 # 24/7 always-on daemon (NEW!)
├── demo.py                         # Interactive demo script (NEW!)
├── backends/                       # Device backends
│   ├── device_base.py              # Abstract base class
│   ├── termux_backend.py           # Termux support (best performance)
│   ├── adb_backend.py              # Standard ADB support
│   └── emulator_backend.py         # Emulator support
├── config/                         # Configuration system
│   └── device_config.py            # YAML config loader
├── scripts/                        # Utility scripts
│   ├── vision_helper.py            # Vision analysis (v1 preserved)
│   ├── test_device.py              # Test device connection
│   └── notification_reader.py      # Notification monitoring (NEW!)
└── assets/                         # Screenshots and media
    └── screen.png
```

---

## Technical Specifications

### Models Used

| Component | Model | Purpose | Endpoint |
|-----------|-------|---------|----------|
| Attention | Qwen2.5-Omni 3.5B | Video + Audio understanding | :8100 |
| Vision | Qwen2.5-Vision 3B | Screen analysis | :8081 |
| TTS | Soprano 80M | Text-to-speech | Local |


**Phone:**
- Android 8.0+ with Termux OR ADB wireless debugging
- Camera + Microphone access
- Tailscale for remote SSH

### Supported Devices

✅ Any Android with ADB wireless debugging  
✅ Android emulators (Android Studio, Genymotion, Waydroid)

---

## Requirements

- Python 3.8+
- ADB (Android Debug Bridge)
- For Termux: SSH access to device
- For vision: Senter Server or compatible vision API
- For daemon: Soprano 80M TTS + Qwen2.5-Omni model server

### Install Dependencies

```bash
# System dependencies
sudo apt install adb ffmpeg  # Debian/Ubuntu
brew install android-platform-tools ffmpeg  # macOS

# Python dependencies
pip install -r requirements.txt
```

---

## Testing

```bash
# Test device connection
python3 scripts/test_device.py

# Test camera capture
python3 -c "from phone_agent import PhoneAgent; PhoneAgent().capture_camera()"

# Test audio recording
python3 -c "from phone_agent import PhoneAgent; PhoneAgent().record_audio(2, 'test.wav')"

# Test attention detection (daemon)
python3 phone_daemon.py --test

# Run interactive demo
python3 demo.py
```

---

## Migration from v1

v1 users: The vision feedback loop is **fully preserved**. Your existing workflows using `vision_helper.py` and ADB commands continue to work exactly as before. The new framework adds capabilities without breaking compatibility.

### What's New in v2.0

✅ Vision helper script unchanged  
✅ ADB commands work the same way  
✅ SKILL.md format preserved for openskills  
🆕 Device abstraction layer (Termux/ADB/Emulator)  
🆕 Multiple backend support with auto-detection  
🆕 Configuration-driven setup (YAML)  
🆕 Python API for integration  
🆕 **24/7 daemon with gaze detection**  
🆕 **Conversational memory persistence**  
🆕 **Notification monitoring**  
🆕 **Hermes hackathon integration**  

---

## 🏆 Hackathon Highlights

### What Makes This Special

1. **Skills-Based Architecture** - Clean separation of concerns, no monolithic code
2. **Continuous Multimodal Streaming** - Industry-first approach to wake detection
3. **Model-Native Logic** - Instructions > Python conditionals for attention
4. **Hermes Integration** - Hooks, subagents, proper skill manifests
5. **Universal Compatibility** - Works on any Android device (Termux/ADB/emulator)

### Technical Challenges Overcome

✅ Real-time video+audio streaming to LLM without latency issues  
✅ Cross-device audio routing via Tailscale SSH  
✅ Vision-guided app navigation with coordinate extraction  
✅ Conversational memory persistence across sessions  
✅ Battery-efficient continuous monitoring (~8%/hour)  

### What's Next (Post-Hackathon)

1. **On-device attention model** - Reduce latency further with quantized Qwen
2. **Enhanced notification integration** - Deep notification content access
3. **Calendar awareness** - Proactive reminders based on schedule
4. **Multi-language support** - TTS/STT in multiple languages
5. **Privacy mode** - Local-only processing option

---

## Related Projects

- [Senter](https://github.com/SouthpawIN/Senter) - AI phone companion framework
- [Senter-Server](https://github.com/SouthpawIN/Senter-Server) - Model proxy server
- [Hermes Agent](https://github.com/nous-research/hermes) - AI agent framework

---

## 📞 Contact & Resources

- **GitHub:** https://github.com/SouthpawIN/burner-phone
- **Senter Project:** /home/sovthpaw/Senter/
- **Hermes Docs:** /home/sovthpaw/hermes-agent/website/docs/

---

## License

MIT

---

*Built with ❤️ for the Hermes Hackathon - March 2026*  
*"Looking at your phone + speaking should be enough to wake it up. Just like human conversation."*
