# 24/7 Phone Agent - IMPLEMENTATION PLAN
## Execute This NOW (March 6, 2026)

**STATUS:** ACTIVE IMPLEMENTATION  
**GOAL:** Build complete 24/7 phone assistant integrated with Hermes Agent  
**APPROACH:** Speak throughout, integrate existing components, update repos along the way

---

## PHASE 1: IMMEDIATE ACTIONS (Today - Next 2 Hours)

### Step 1.1: Update model-server Script for Safe Model Switching
**WHY:** Current script doesn't safely handle switching between models. Need clean start/stop/status with proper process management.

**LOCATION:** `/home/sovthpaw/bin/model-server`

**CHANGES NEEDED:**
- Add `switch` command that stops current model and starts new one atomically
- Add health checks before starting new model
- Add graceful shutdown with timeout
- Add logging for all state changes
- Support GLM-4.7-Flash model (from AGENTS.md config)

**FILE TO UPDATE:** `/home/sovthpaw/bin/model-server`

---

### Step 1.2: Integrate Speech-to-Text into Phone Agent
**WHY:** Phone agent needs to listen and understand voice commands, not just speak responses.

**EXISTING COMPONENTS TO FIND:**
- Search for whisper/faster-whisper installations
- Check if Senter has STT capabilities (Qwen Omni has audio input)
- Look for existing transcription scripts

**INTEGRATION POINT:** `/home/sovthpaw/burner-phone/phone_daemon.py`

**IMPLEMENTATION:**
1. Add STT module to phone_agent.py
2. Use Qwen Omni's native audio understanding OR whisper-faster
3. Feed transcribed text to Hermes for processing
4. Route response back through speak skill

---

### Step 1.3: Update burner-phone Repo with Latest Changes
**WHY:** Keep the main repo in sync with development.

**FILES TO UPDATE:**
- `README.md` - Add current status, demo instructions
- `SKILL.md` - Update with latest integration points  
- `HACKATHON_OVERVIEW.md` - Finalize submission details
- `HERMES_INTEGRATION.md` - Document tool registration

**GITHUB ACTION:** Commit and push after each major update

---

### Step 1.4: Prepare Hermes Agent PR Components
**WHY:** Get the phone assistant into hermes-agent as an official skill/tool.

**COMPONENTS TO EXTRACT:**
1. **Tool definitions** - Phone control tools for Hermes tool registry
2. **Skill documentation** - SKILL.md in proper format
3. **Example scripts** - Demo and test scripts
4. **Configuration templates** - Example configs for different devices

**TARGET REPO:** `/home/sovthpaw/hermes-agent/`

**PR STRATEGY:**
- Start with phone-assistant skill (already exists at `skills/phone-assistant/`)
- Add phone control tools to `tools/registry.py`
- Create example integration in `examples/` directory

---

## PHASE 2: CORE INTEGRATION (Hours 2-4)

### Step 2.1: Register Phone Tools with Hermes
**LOCATION:** `/home/sovthpaw/hermes-agent/tools/phone_tool.py`

**TOOLS TO REGISTER:**
```python
- phone_capture_camera(device="auto") → returns image path
- phone_record_audio(duration=5, device="auto") → returns audio path  
- phone_play_audio(audio_path, device="auto") → plays on device
- phone_send_text(message, contact=None, device="auto") → sends via SMS/app
- phone_check_battery(device="auto") → returns battery %
- phone_read_notifications(app_filter=None, device="auto") → returns list
- phone_open_app(app_name, device="auto") → opens app via ADB
- phone_speak(text, device="auto") → routes through speak skill
```

**REGISTRATION PATTERN:** Follow existing tools like `homeassistant_tool.py` or `browser_tool.py`

---

### Step 2.2: Add STT Pipeline to Phone Daemon
**LOCATION:** `/home/sovthpaw/burner-phone/phone_daemon.py`

**ARCHITECTURE:**
```
Microphone → Record WAV → STT (Whisper/Qwen Omni) → Text → Hermes Agent → Response Text → Soprano TTS → Device Speaker
```

**IMPLEMENTATION STEPS:**
1. Add `record_audio()` method to PhoneAgent class
2. Integrate faster-whisper or use Qwen Omni's native audio
3. Add transcription callback to daemon loop
4. Feed transcribed text to Hermes via API or CLI
5. Route response through speak skill

---

### Step 2.3: Implement Battery & Notification Monitoring
**LOCATION:** `/home/sovthpaw/burner-phone/scripts/`

**SCRIPTS TO CREATE/UPDATE:**
1. `battery_monitor.py` - Poll battery level, alert when < 20%
2. `notification_daemon.py` - Read notifications every 30s, speak important ones
3. `health_check.py` - Monitor SSH connectivity, trigger auto-recovery

**INTEGRATION:** Add to phone_daemon.py event queue

---

## PHASE 3: DEMO & POLISH (Hours 4-6)

### Step 3.1: Create End-to-End Demo Script
**LOCATION:** `/home/sovthpaw/burner-phone/scripts/demo_full.sh`

**DEMO SEQUENCE:**
1. Start all services (model-server, auto-ssh-daemon, phone-daemon)
2. Show gaze detection activation
3. Demonstrate voice command → action flow
4. Show notification reading
5. Display battery monitoring
6. Prove auto-recovery works (kill SSH, watch it restart)

---

### Step 3.2: Update All Documentation
**FILES TO UPDATE:**

**burner-phone repo:**
- `README.md` - Complete with installation, usage, demo
- `PROJECT-PLAN.md` - Mark phases complete
- `SKILL.md` - Final version for Hermes integration
- `HACKATHON_OVERVIEW.md` - Submission-ready

**hermes-agent repo (for PR):**
- `skills/phone-assistant/SKILL.md` - Update with latest
- `tools/phone_tool.py` - New file with tool definitions
- `README.md` - Add phone assistant to features list

---

### Step 3.3: Record Demo Video
**WHAT TO CAPTURE:**
1. Starting the system (all daemons)
2. Looking at phone + speaking → Hermes responds
3. Phone reads notification aloud
4. Battery warning when low
5. SSH crash and auto-recovery
6. Model switching via model-server

**TOOL:** Use OBS or `ffmpeg` to record terminal + audio

---

## PHASE 4: ANDROID ASSISTANT INTEGRATION (Advanced Goal)

### Step 4.1: Replace Google Assistant with Hermes on Android
**WHY:** Make this a true system-level assistant, not just an app. Deep integration with Android's notification system, voice trigger, and device controls.

**WHAT'S NEEDED:**
1. **Android App Wrapper** - Simple app that registers as default assistant
2. **Notification Listener Service** - System-level access to all notifications
3. **Accessibility Service** - Tap/click apps, read screen content
4. **Voice Trigger Integration** - "Hey Hermes" wake word at system level
5. **Intent Handling** - Respond to Android's ASSIST intent from power button/hot corner

**TERMUX ADVANTAGE:** Already has root-like access on many devices, can run full Python stack

**IMPLEMENTATION PATH:**
```bash
# 1. Create minimal Android app (Kotlin/Java)
- Registers as DEFAULT_ASSISTANT in IntentFilter
- Implements AssistantApp service
- Forwards voice/text to Hermes daemon via local socket

# 2. Notification Listener
- android.permission.BIND_NOTIFICATION_LISTENER_SERVICE
- Read all notifications, forward to phone_daemon.py
- Can respond: "You have 3 new messages from WhatsApp"

# 3. Accessibility Service  
- android.accessibilityservice.AccessibilityService
- Tap buttons, navigate apps programmatically
- Read screen content for vision-based actions

# 4. Wake Word Detection (always-on)
- Use Porcupine or Snowboy for low-power wake word
- "Hey Hermes" triggers recording → STT → processing
```

**FILES TO CREATE:**
- `/home/sovthpaw/burner-phone/android-assistant/` - Android app source
- `app/src/main/java/com/hermes/assistant/AssistantService.java`
- `app/src/main/java/com/hermes/assistant/NotificationListener.java`
- `app/src/main/res/xml/notification_listener.xml`
- `build.gradle` - Android build config

**TESTING:**
1. Build and install APK on Duo/S10
2. Set as default assistant in Settings → Apps → Default apps → Digital wellbeing & parental controls → Assistant app
3. Test wake word, notification reading, voice commands

**HACKATHON DEMO VALUE:** HUGE - shows this isn't just a script, it's a real Android assistant replacement

---

## PHASE 5: GITHUB & SUBMISSION (Hour 6+)

### Step 5.1: Push burner-phone Updates (with Android assistant if done)
```bash
cd /home/sovthpaw/burner-phone
git add .
git commit -m "feat: Complete 24/7 phone agent with Hermes integration"
# If Android assistant built:
# git commit -m "feat: Android system-level assistant integration"
git push origin main
```

---

### Step 5.2: Create Hermes Agent PR
```bash
cd /home/sovthpaw/hermes-agent
git checkout -b feature/phone-assistant
# Add phone_tool.py, update skills/phone-assistant/
git add .
git commit -m "Add phone assistant skill and tools"
git push origin feature/phone-assistant
# Create PR on GitHub
```

---

### Step 4.3: Prepare Hackathon Submission Package
**INCLUDE:**
- burner-phone repo link
- Demo video
- README with setup instructions
- Live demo if possible
- Architecture diagram
- Future roadmap

---

## SPEAK THROUGHOUT - CRITICAL

**EVERY ACTION REQUIRES SPEECH:**
```bash
# Before reading files
python3 /home/sovthpaw/Senter/skills/speak/speak.py "Reading model-server script..." --if-on

# During analysis  
python3 /home/sovthpaw/Senter/skills/speak/speak.py "Found the issue - need to add safe switching logic" --if-on

# After updates
python3 /home/sovthpaw/Senter/skills/speak/speak.py "Updated model-server with switch command and health checks" --if-on

# Progress updates every 5 minutes
python3 /home/sovthpaw/Senter/skills/speak/speak.py "Phase 1 step 2 complete - now starting STT integration" --if-on
```

---

## EXISTING COMPONENTS TO INTEGRATE

### Found on System:
- ✅ **Soprano TTS** (`/home/sovthpaw/Senter/skills/speak/speak.py`) - Already integrated
- ✅ **Qwen Omni 3B** (port 8100) - Can handle audio input natively
- ✅ **PhoneAgent framework** (`/home/sovthpaw/burner-phone/`) - Core complete
- ✅ **Auto-SSH daemon** (`scripts/auto_ssh_daemon.py`) - Working
- ✅ **Hermes tool registry** (`/home/sovthpaw/hermes-agent/tools/registry.py`) - Ready for phone tools

### Need to Find/Create:
- 🔍 **STT engine** - Check for whisper, or use Qwen Omni's native audio
- 📝 **Notification reader** - Exists but needs testing on actual device
- 🔋 **Battery monitor** - Simple script needed
- 📹 **Gaze detection integration** - senter-aware skill exists

---

## REPOS TO UPDATE ALONG THE WAY

### 1. burner-phone (Primary Dev Repo)
**PATH:** `/home/sovthpaw/burner-phone/`
**UPDATE AFTER:** Each major feature completion
**COMMIT MESSAGE PATTERN:** "feat: [what]", "fix: [what]", "docs: [what]"

### 2. hermes-agent (PR Target)
**PATH:** `/home/sovthpaw/hermes-agent/`
**BRANCH:** `feature/phone-assistant`
**UPDATE AFTER:** All phone tools ready, skill documentation complete
**GOAL:** Get merged into main hermes-agent repo

### 3. Personal AGENTS.md (Documentation)
**PATH:** `/home/sovthpaw/AGENTS.md`
**UPDATE:** Add model-server usage examples, phone agent quick start

---

## SUCCESS CRITERIA

✅ Model-server can safely switch between qwen35, glm-4.7-flash, qwen-omni  
✅ Phone agent records audio, transcribes, sends to Hermes, speaks response  
✅ Battery monitoring alerts when < 20%  
✅ Notifications read aloud every 30 seconds  
✅ Auto-recovery restarts SSH within 30 seconds of crash  
✅ All phone tools registered with Hermes and callable via CLI  
✅ Demo script runs end-to-end without errors  
✅ burner-phone repo pushed to GitHub  
✅ PR created for hermes-agent  

---

**STARTING NOW:** Phase 1, Step 1.1 - Update model-server script  
**TIME:** March 6, 2026, ~3:45 PM  
**STATUS:** READY TO EXECUTE