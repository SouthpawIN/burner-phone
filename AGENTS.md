# Burner Phone - 24/7 Always-Aware Assistant

## CRITICAL: Voice Conversation Protocol

**This is a VOICE CONVERSATION, not text chat. You MUST speak through the user's Duo device for ALL output.**

### Speak Skill - MANDATORY USAGE

```bash
# ALWAYS use this for voice output (async, doesn't block):
python3 /home/sovthpaw/Senter/skills/speak/speak.py "YOUR MESSAGE HERE" --if-on

# For testing or when you need to wait for playback:
python3 /home/sovthpaw/Senter/skills/speak/speak.py "YOUR MESSAGE HERE" --device duo --sync
```

### Speak Skill Configuration

- **Location**: `/home/sovthpaw/Senter/skills/speak/speak.py`
- **TTS Engine**: Soprano 80M (port 8102)
- **Routing**: Via TailScale SSH to devices
- **Devices**: 
  - Duo: `100.79.15.54` (default, most commonly used)
  - S10: `100.93.96.90`
  - Local: `localhost` (when no remote devices available)

### Speaking Rules

1. **Speak BEFORE actions** - "Starting to work on X..."
2. **Speak DURING thinking** - "Analyzing the problem...", "I wonder if..."
3. **Speak AFTER results** - "Done. Found Y files..."
4. **Every paragraph typed = corresponding speech**
5. **Use --if-on flag** for async background speaking (doesn't slow down work)

### Queue Management

If audio gets stuck or queued:
```bash
rm -f /tmp/speak_playing && echo "[]" > /tmp/speak_queue
```

### Device Auto-Selection

The speak skill uses `--device auto` by default, which:
1. Checks TailScale for most recently active device
2. Falls back to SSH connectivity check
3. Defaults to Duo if both available
4. Uses local playback if no remote devices online

---

## Project Overview

This is the **burner-phone** project - a universal Android device control framework being developed as a 24/7 always-aware assistant add-on for Hermes Agent (hackathon submission).

### Key Components

- **PhoneAgent**: Unified interface for Termux/ADB/emulator devices
- **Phone Daemon**: 24/7 background service with attention detection
- **Auto-SSH Daemon**: Automatic SSH startup and recovery
- **Speak Skill Integration**: TTS routing through Soprano to devices
- **Senter-Aware**: Gaze-based attention detection

### Project Files

```
/home/sovthpaw/burner-phone/
├── phone_agent.py          # Main interface (251 lines)
├── phone_daemon.py         # 24/7 daemon (657 lines)
├── backends/
│   ├── device_base.py      # Base class
│   ├── termux_backend.py   # SSH-based control (FIXED: added Optional import)
│   ├── adb_backend.py      # ADB-based control (FIXED: added Optional import)
│   └── emulator_backend.py # Emulator support (FIXED: added Optional import)
├── scripts/
│   ├── auto_ssh_daemon.py  # Auto-recovery service
│   ├── notification_reader.py
│   ├── vision_helper.py
│   └── test_device.py
├── config/
│   └── device_config.py    # Config loader
├── PROJECT-PLAN.md         # Comprehensive project plan (SEE THIS FIRST!)
├── AGENTS.md               # This file
└── config.example.yaml     # Template configuration
```

### Configuration Files

- **Duo**: `~/.hermes-phone-agent/config-duo.yaml`
- **S10**: `~/.hermes-phone-agent/config.yaml`
- **Daemon**: `~/.hermes-phone-agent/daemon.yaml`

---

## Integration with Hermes Agent

This project is an **add-on for Hermes Agent** (`/home/sovthpaw/hermes-agent/`). See PROJECT-PLAN.md for detailed integration points:

1. **Skill Registration**: Will be in `/home/sovthpaw/hermes-agent/skills/phone-assistant/`
2. **Tool Calling**: Phone tools registered with Hermes tool registry
3. **Gateway Support**: Optional Telegram/Discord/Slack integration
4. **Cron Tasks**: Scheduled battery checks, notification polling

---

## Quick Start Commands

### Test Device Connectivity
```bash
cd /home/sovthpaw/burner-phone
python3 -c "
from phone_agent import PhoneAgent
agent = PhoneAgent(config_path='/home/sovthpaw/.hermes-phone-agent/config-duo.yaml')
print(agent.get_device_info())
"
```

### Test Camera Capture
```bash
python3 scripts/test_device.py  # Interactive test suite
```

### Start Auto-SSH Daemon
```bash
python3 scripts/auto_ssh_daemon.py --daemon
```

### Start Phone Daemon
```bash
python3 phone_daemon.py --daemon  # Full 24/7 mode
python3 phone_daemon.py --test    # Single attention check
```

### Test Speak Skill
```bash
python3 /home/sovthpaw/Senter/skills/speak/speak.py "Hello from burner phone" --device duo --sync
```

---

## Common Issues & Solutions

### ImportErrors in Backends
**Problem**: `NameError: name 'Optional' is not defined`
**Solution**: Already fixed - all backends have `from typing import Optional` on line 7

### Audio Playback Timeout
**Problem**: Speak skill times out waiting for device playback
**Solution**: Check Termux permissions on device, or use async mode (`--if-on`)

### SSH Offline
**Problem**: Device not reachable via SSH
**Solution**: Run auto-SSH daemon: `python3 scripts/auto_ssh_daemon.py --once`

### Queue Stuck
**Problem**: Speech messages queuing up and not playing
**Solution**: `rm -f /tmp/speak_playing && echo "[]" > /tmp/speak_queue`

---

## Session Checklist

When starting a new session on this project:

1. ✅ **Read PROJECT-PLAN.md** - Understand current status and priorities
2. ✅ **Enable speak skill** - Use it for ALL voice output
3. ✅ **Check device status** - Verify SSH/ADB connectivity
4. ✅ **Review todo list** - See what tasks are in progress
5. ✅ **Speak throughout** - Continuous voice updates while working

---

*Remember: This is a VOICE conversation. Speak as much as you type. Every paragraph should have corresponding speech through the Duo.*