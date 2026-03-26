# Hermes Documentation for Burner-Phone

*Generated: March 25, 2026*
*Purpose: Reference documentation for Android device control and voice assistant*

---

## 🔊 Voice Mode (Primary Feature)

### Voice Mode Overview
**Docs:** https://hermes-agent.nousresearch.com/docs/user-guide/features/voice-mode

Real-time voice interaction in:
- CLI interface
- Telegram
- Discord
- Discord Voice Channels

### Use Voice Mode with Hermes
**Guide:** https://hermes-agent.nousresearch.com/docs/guides/use-voice-mode-with-hermes

Hands-on setup and usage patterns for voice workflows.

---

## 📱 Phone Control Tools

### Terminal & File Operations
**Docs:** https://hermes-agent.nousresearch.com/docs/user-guide/features/tools

Tools:
- `terminal` - Execute ADB commands, SSH to device
- `read_file` / `write_file` - Read/write config files
- `patch` - Edit configuration
- `execute_code` - Run Python scripts for phone control

**Use Cases:**
- Running ADB commands (`adb devices`, `adb shell ...`)
- SSH connections to Termux-enabled devices
- Managing device configuration files
- Running phone agent scripts

---

### Browser Tools (for scrcpy-web)
Tools:
- `browser_navigate` - Open scrcpy-web interface
- `browser_vision` - Analyze phone screen visually
- `browser_snapshot` - Get page elements

**Use Cases:**
- Controlling phone via web interface
- Screen analysis for automation
- Vision-guided app navigation

---

## 🎙️ Audio/TTS Integration

### Text-to-Speech Tool
Tool: `text_to_speech`

**Use Cases:**
- Speaking responses through phone speakers
- Voice feedback for user interactions
- Multi-device audio routing

---

## 🔄 Automation Features

### Skills System
**Docs:** https://hermes-agent.nousresearch.com/docs/user-guide/features/skills

Procedural memory the agent creates and reuses.

**Existing Burner-Phone Skills:**
- `senter-attention` - Gaze + wake word detection
- `speak-integration` - Multi-device TTS routing
- Phone control skills (camera, audio, screen)

---

### Persistent Memory
**Docs:** https://hermes-agent.nousresearch.com/docs/user-guide/features/memory

**Use Cases:**
- Remembering device configurations
- Tracking conversation context
- Storing user preferences

---

## 🛠️ Implementation Patterns

### Voice Conversation Pattern
```python
# Speak before actions
"Connecting to S10 device..."
terminal("adb connect 100.93.96.90")

# Speak after results
"Connected! Device is online."
```

### Phone Control Pattern
```python
# Via terminal/ADB
terminal("adb -s RF8M221SXHZ shell input keyevent KEYCODE_HOME")

# Via SSH (Termux devices)
terminal("ssh -i ~/.ssh/phone_access -p 8022 droid@100.93.96.90 'termux-camera-photo'")
```

---

## 🔗 Key Documentation Pages

1. **Voice Mode** - https://hermes-agent.nousresearch.com/docs/user-guide/features/voice-mode
2. **Use Voice Mode Guide** - https://hermes-agent.nousresearch.com/docs/guides/use-voice-mode-with-hermes
3. **Tools & Toolsets** - https://hermes-agent.nousresearch.com/docs/user-guide/features/tools
4. **Skills System** - https://hermes-agent.nousresearch.com/docs/user-guide/features/skills
5. **Messaging Gateway** - For Telegram/Discord voice integration

---

## 📝 Related Projects

- **Pocket-Shop** - Uses vision for card scanning (can use phone camera)
- **Senter-Server** - Model endpoints for attention detection
