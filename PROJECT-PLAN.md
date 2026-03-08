# 24/7 Always-Aware Phone Assistant - Hermes Hackathon Submission

## Project Vision

Build a **24/7 always-aware phone assistant** that integrates with Hermes Agent as a powerful add-on for the Hermes Agent hackathon. The system continuously monitors user attention via gaze detection, responds to voice commands, proactively notifies about important events (messages, battery, calls), and can automate device actions through vision-based feedback loops.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    HERMES AGENT                             │
│  (Core AI with tool calling, CLI, messaging integrations)   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              PHONE ASSISTANT SKILL                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Phone Daemon (phone_daemon.py - 657 lines)           │  │
│  │  • Attention detection loop (gaze + wake word)        │  │
│  │  • Conversation memory persistence                    │  │
│  │  • Event queue for async operations                   │  │
│  │  • TTS routing via speak skill                        │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Burner Phone (Device Control Framework)              │  │
│  │  • Universal backend (Termux/ADB/Emulator)            │  │
│  │  • Camera, audio, screen control                      │  │
│  │  • Vision feedback loop via vision_helper.py          │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Auto-Recovery System (auto_ssh_daemon.py)            │  │
│  │  • USB device detection via ADB                       │  │
│  │  • Automatic SSH daemon startup                       │  │
│  │  • Continuous connectivity monitoring                 │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Speak Skill Integration (soprano 80M TTS)            │  │
│  │  • Routes audio via TailScale to Duo/S10 devices      │  │
│  │  • Async background speaking (--if-on flag)           │  │
│  │  • Queue management for overlapping speech            │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Senter-Aware (Gaze Detection)                        │  │
│  │  • Continuous camera monitoring                       │  │
│  │  • Detects when user is looking at + speaking to phone│  │
│  │  • Natural attention-based activation                 │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Current Status (as of March 6, 2026)

### ✅ Completed Components

1. **Burner Phone Framework** (`/home/sovthpaw/burner-phone/`)
   - Universal PhoneAgent interface (251 lines)
   - TermuxBackend for SSH-based control (183 lines)
   - ADBBackend for standard Android devices (210 lines)
   - EmulatorBackend for emulators (170 lines)
   - Vision helper for screen analysis and app automation
   - Device configuration system (YAML-based)

2. **Phone Daemon** (`phone_daemon.py` - 657 lines)
   - Attention detection via senter-aware gaze integration
   - Conversation memory with persistent storage
   - Event queue for async operations
   - TTS routing through speak skill
   - Auto-recovery on device startup

3. **Auto-SSH Daemon** (`scripts/auto_ssh_daemon.py` - 400+ lines)
   - Automatic USB device detection via ADB
   - SSH daemon auto-start on Termux devices
   - Continuous connectivity monitoring (30s intervals)
   - Multi-device support (Duo, S10, etc.)

4. **Speak Skill Integration** (`/home/sovthpaw/Senter/skills/speak/speak.py`)
   - Soprano 80M TTS with queue management
   - TailScale routing to devices (duo: 100.79.15.54, s10: 100.93.96.90)
   - Async background speaking (`--if-on` flag)
   - Auto-recovery for offline devices

5. **Device Configuration**
   - Duo config: `~/.hermes-phone-agent/config-duo.yaml` (Termux, SSH online)
   - S10 config: `~/.hermes-phone-agent/config.yaml` (Termux, ADB connected)

### 🔧 Bugs Fixed During Session

- **Import bugs in all backends**: Added `from typing import Optional` to:
  - `backends/termux_backend.py` (line 7)
  - `backends/adb_backend.py` (line 7)
  - `backends/emulator_backend.py` (line 7)

### 📋 Verified Working

- ✅ SSH connectivity to Duo via Tailscale
- ✅ Camera capture on Duo through Termux backend
- ✅ Auto-SSH daemon detecting and starting SSH on devices
- ✅ Speak skill routing audio to Duo speakers
- ✅ Phone agent initialization with device configs

---

## Integration Points with Hermes Agent

### 1. Skill Registration

The phone assistant will be registered as a skill in `/home/sovthpaw/hermes-agent/skills/phone-assistant/` with:
- `SKILL.md` - Documentation and usage instructions
- `scripts/phone_daemon.py` - Daemon entry point (symlink to burner-phone)
- `scripts/auto_ssh_daemon.py` - Auto-recovery service
- Integration hooks for Hermes tool calling

### 2. Tool Calling Framework

Hermes agent's tool registry (`tools/registry.py`) can register phone-specific tools:
- `phone_capture_camera()` - Take photo from device camera
- `phone_record_audio(duration)` - Record audio for N seconds
- `phone_play_audio(path)` - Play audio file on device
- `phone_send_text(message)` - Send notification/text
- `phone_check_battery()` - Get battery level
- `phone_read_notifications()` - Fetch recent notifications

### 3. Gateway Integration (Optional)

The phone assistant can leverage Hermes gateway (`gateway/platforms/`) for:
- Receiving commands via Telegram/Discord/Slack
- Sending status updates to messaging platforms
- Multi-device coordination across platforms

### 4. Cron/Scheduled Tasks

Use Hermes cron system (`cron/`) for:
- Periodic battery checks (every 30 minutes)
- Notification polling (every 1 minute)
- Health checks and auto-recovery (every 5 minutes)

---

## Remaining Implementation Tasks

### Phase 1: Core Functionality (Week 1)

- [ ] **Fix audio playback on Duo** - Termux permissions or alternative playback method
- [ ] **Enable wireless ADB on Duo** - For screen wake/unlock features
- [ ] **Test notification reader** (`scripts/notification_reader.py`) on actual device
- [ ] **Integrate senter-aware gaze detection** - Continuous monitoring loop
- [ ] **Build battery monitoring** - Simple script to check and alert on low battery

### Phase 2: Hermes Integration (Week 2)

- [ ] **Create skill directory structure** in `/home/sovthpaw/hermes-agent/skills/phone-assistant/`
- [ ] **Register phone tools** with Hermes tool registry
- [ ] **Add slash commands** for manual phone control (`/phone capture`, `/phone speak`, etc.)
- [ ] **Test tool calling** from Hermes CLI and gateway platforms

### Phase 3: Proactive Features (Week 2-3)

- [ ] **Notification monitoring daemon** - Continuous background polling
- [ ] **Battery warning system** - Alert when below threshold (20%, 10%)
- [ ] **Call/text forwarding** - Read incoming calls/messages aloud
- [ ] **Smart wake detection** - Combine gaze + voice activity detection

### Phase 4: Vision & Automation (Week 3)

- [ ] **Screen analysis pipeline** - Use vision_helper.py for app detection
- [ ] **App automation** - Tap, swipe, type via ADB based on screen content
- [ ] **Context-aware actions** - "Open WhatsApp and message X" with vision feedback

### Phase 5: Demo & Documentation (Week 4)

- [ ] **End-to-end demo script** - Showcase all features for hackathon
- [ ] **Video recording** - Record demo session
- [ ] **README documentation** - Installation, configuration, usage
- [ ] **GitHub repo cleanup** - Clean commits, proper structure
- [ ] **Hackathon submission** - Final package and presentation

---

## Speak Skill Configuration (CRITICAL)

### Default Behavior

**The speak skill MUST be used for ALL voice output during phone assistant work.** This is non-negotiable and should be documented in AGENTS.md.

```bash
# Correct usage (async, doesn't block):
python3 /home/sovthpaw/Senter/skills/speak/speak.py "Your message here" --if-on

# For synchronous playback (waits for completion):
python3 /home/sovthpaw/Senter/skills/speak/speak.py "Your message here" --device duo --sync

# Device auto-selection based on TailScale connection:
python3 /home/sovthpaw/Senter/skills/speak/speak.py "Message" --device auto --if-on
```

### Device Selection Logic

The speak skill automatically selects device based on:
1. **TailScale status** - Most recently active device (duo or s10)
2. **SSH connectivity** - Falls back to devices with working SSH
3. **Local playback** - If no remote devices available, plays locally

### Queue Management

- Queue file: `/tmp/speak_queue`
- Playing lock: `/tmp/speak_playing`
- State file: `/tmp/senter_speak_mode` (on/off)

**Clear queue if stuck**: `echo "[]" > /tmp/speak_queue && rm -f /tmp/speak_playing`

---

## Configuration Files

### Main Phone Config (`~/.hermes-phone-agent/config.yaml`)

```yaml
name: "Samsung Galaxy S10"
device_type: "termux"
ip_address: "100.93.96.90"
ssh_port: 8022
adb_port: 5555
ssh_key: "~/.ssh/phone_access"
ssh_user: "droid"
screen_pin: "4658"
camera_path: "/sdcard/senter_gaze.jpg"
audio_input_path: "/sdcard/senter_in.wav"
audio_output_path: "/sdcard/senter_out.wav"
```

### Duo Config (`~/.hermes-phone-agent/config-duo.yaml`)

```yaml
name: "Surface Duo 2"
device_type: "termux"
ip_address: "100.79.15.54"
ssh_port: 8022
adb_port: 5555
ssh_key: "~/.ssh/phone_access"
ssh_user: "droid"
screen_pin: null
auto_ssh_recovery: true
usb_connected: true
```

### Daemon Config (`~/.hermes-phone-agent/daemon.yaml`)

```yaml
config_dir: "~/.hermes-phone-agent"
log_file: "/tmp/phone_daemon.log"
pid_file: "/tmp/phone_daemon.pid"
memory_file: "~/.hermes-phone-agent/memory.json"
gaze_detection_enabled: true
gaze_check_interval: 2.0
gaze_skill_path: "/home/sovthpaw/Senter/skills/senter-aware/aware.py"
wake_word_enabled: true
speak_skill_path: "/home/sovthpaw/Senter/skills/speak/speak.py"
speak_device: "auto"
memory_enabled: true
max_memory_size: 10000
conversation_timeout: 300.0
senter_url: "http://100.84.195.22:8081"
vision_model: "qwen2.5-omni:3b"
```

---

## Testing Checklist

### Basic Connectivity

- [ ] SSH to device: `ssh -i ~/.ssh/phone_access -p 8022 droid@100.79.15.54`
- [ ] ADB devices: `adb devices -l`
- [ ] Phone agent init: `python3 phone_agent.py --list`
- [ ] Camera capture: `python3 scripts/test_device.py` (option 1)

### Audio Pipeline

- [ ] Soprano server running: `curl http://localhost:8102/docs`
- [ ] Speak skill test: `python3 speak.py "test" --device duo --sync`
- [ ] Audio recording: `python3 phone_agent.py --record 2`
- [ ] Audio playback: Verify audio plays on device speakers

### Daemon & Auto-Recovery

- [ ] Auto-SSH daemon: `python3 scripts/auto_ssh_daemon.py --daemon`
- [ ] Phone daemon test: `python3 phone_daemon.py --test`
- [ ] Device watchdog: Check `/tmp/device_watchdog.log`
- [ ] Notification reader: `python3 scripts/notification_reader.py --test`

### Integration Tests

- [ ] Hermes CLI can call phone tools
- [ ] Gateway commands trigger phone actions
- [ ] Cron jobs execute scheduled tasks
- [ ] Memory persists across daemon restarts

---

## Demo Script for Hackathon

```bash
#!/bin/bash
# demo.sh - 24/7 Phone Assistant Demo

echo "=== 24/7 Always-Aware Phone Assistant Demo ==="
echo ""

# 1. Start auto-SSH daemon
echo "Starting auto-recovery service..."
python3 scripts/auto_ssh_daemon.py --daemon &
AUTO_SSH_PID=$!

# 2. Initialize phone agent
echo "Initializing phone agent on Duo..."
python3 -c "
from phone_agent import PhoneAgent
agent = PhoneAgent(config_path='/home/sovthpaw/.hermes-phone-agent/config-duo.yaml')
print(f'Connected to: {agent.get_device_info()[\"name\"]}')
"

# 3. Test camera capture
echo "Testing camera capture..."
python3 -c "
from phone_agent import PhoneAgent
agent = PhoneAgent(config_path='/home/sovthpaw/.hermes-phone-agent/config-duo.yaml')
agent.capture_camera()
print('✓ Camera captured image')
"

# 4. Speak greeting
echo "Speaking demo greeting..."
python3 /home/sovthpaw/Senter/skills/speak/speak.py \
  "Welcome to the twenty-four-seven always-aware phone assistant! I can hear you, see your attention, and help you with anything on your phone." \
  --device duo --if-on

# 5. Start notification monitoring (background)
echo "Starting notification monitor..."
python3 scripts/notification_reader.py --daemon &

# 6. Run phone daemon in interactive mode
echo "Starting phone daemon..."
python3 phone_daemon.py --verbose

# Cleanup on exit
trap "kill $AUTO_SSH_PID 2>/dev/null" EXIT
```

---

## Success Metrics

- ✅ All models serving on correct ports (Soprano: 8102, Senter: 8081)
- ✅ Speech pipeline working end-to-end (STT→Process→TTS)
- ✅ Phone agent responding to voice commands
- ✅ Seamless Hermes integration (tool calling + gateway optional)
- ✅ Standalone operation fully functional
- ✅ Auto-recovery keeping SSH alive 24/7
- ✅ Gaze detection activating conversations naturally
- ✅ Documentation complete and clear

---

## Notes for Future Sessions

**CRITICAL**: Always use the speak skill (`/home/sovthpaw/Senter/skills/speak/speak.py`) for voice output. This is configured in AGENTS.md and must be followed to avoid repetition.

- Device selection: `--device auto` (uses most recently active via TailScale)
- Async mode: `--if-on` flag (doesn't block execution)
- Sync mode: `--sync` flag (waits for playback completion - use for testing)
- Clear queue if stuck: `echo "[]" > /tmp/speak_queue && rm -f /tmp/speak_playing`

**Project Location**: `/home/sovthpaw/burner-phone/`
**Hermes Agent**: `/home/sovthpaw/hermes-agent/`
**Speak Skill**: `/home/sovthpaw/Senter/skills/speak/speak.py`

---

*Last updated: March 6, 2026*
*Status: Phase 1 in progress - Core functionality being tested*