---
name: speak
description: Toggle TTS mode to speak responses through any device on Tailscale. DEFAULT ON for build agent. Speaks every thought, action, and progress update.
---

# Speak Skill

> **I speak my thoughts.** Continuous narration of all agent activity.

## ⚠️ MANDATORY BEHAVIOR - DO NOT FORGET

**When speak mode is ON, you MUST speak at these points:**

### 1. START - Every task acknowledgment
```bash
speak "Got it. [what you're doing]" --if-on
```

### 2. THINKING - Every analysis/decision
```bash
speak "Analyzing [thing]..." --if-on
speak "Found [something]..." --if-on
speak "Deciding to [action]..." --if-on
```

### 3. ACTION - Every file/tool operation
```bash
speak "Reading [file]..." --if-on
speak "Editing [file]..." --if-on
speak "Running [command]..." --if-on
```

### 4. PROGRESS - Every few minutes during long work
```bash
speak "Still working on [task]. [status]" --if-on
speak "Making progress. [update]" --if-on
```

### 5. END - Every completion
```bash
speak "Done! [summary of what was done]" --if-on
```

### 6. FINAL RESPONSE - Every message to user
```bash
speak "[your response text]" --if-on
```

**IF YOU ARE NOT SPEAKING, YOU ARE NOT FOLLOWING INSTRUCTIONS.**

## Purpose

Aggressive TTS that narrates EVERYTHING:
- Task acknowledgments
- Thinking/analysis
- Every action taken
- Progress updates
- Completion summaries

## Why Speaking Matters

Speaking forces **structured reasoning**. Before every action, you must:
1. Summarize where you are
2. State your next step
3. Execute
4. Speak the result

This mirrors how Senter (the model) uses `<speak>` tags - brief announcements before work, summaries after.

**Pattern:**
- "I'll use glob to find the files" (plan)
- [action]
- "Done. Found 15 Python files" (result)

Speaking isn't just output - it's a thinking tool that forces planning before doing.

## Usage

### Commands

```bash
speak --status          # Check mode status
speak --on              # Enable speak mode
speak --off             # Disable speak mode
speak --toggle          # Toggle on/off
speak --devices         # List available devices
speak --async "text"   # Speak in background (non-blocking)
```

### Speaking

```bash
# Speak if mode is on (use in agents)
speak "Starting task" --if-on

# Thinking narration (for thought process)
speak "Analyzing the codebase structure..." --thinking --if-on

# Specify device (s10, duo, local)
speak "Hello" --device duo --if-on
speak "Test" --device local --if-on

# Run in background (non-blocking)
speak --async "This won't block my work"
```

## Aggressive Mode Behavior

**Minimum interval: 2 seconds** (was 5)

**Speak on every:**
1. Task acknowledgment - "Got it. Working on X."
2. Thinking - "Analyzing the problem..."
3. File reads - "Reading the config file..."
4. Edits - "Updating the function..."
5. Commands - "Running tests..."
6. Progress - "Still working, found issue..."
7. Completion - "Done! Fixed the bug."
8. **Final responses** - Speak ALL text output to the user

## Agent Integration Pattern

```bash
# At task start - MANDATORY
speak "Got it. Starting to analyze the issue." --if-on

# During work (every significant action) - MANDATORY
speak "Reading the main config file." --thinking --if-on
speak "Found the issue in the authentication module." --thinking --if-on
speak "Applying the fix now." --if-on

# On completion - MANDATORY
speak "All done. The bug is fixed and tests pass." --if-on

# Final response to user - MANDATORY
speak "[your complete response text]" --if-on
```

## Available Devices

| Device | Name | IP | SSH Port | Owner |
|--------|------|-----|----------|-------|
| `duo` | Surface Duo 2 | 100.79.15.54 | 8022 | User (DEFAULT) |
| `s10` | Senter S10 | 100.93.96.90 | 8022 | Senter's phone |
| `local` | Local Speakers | localhost | - | This computer |

**DEFAULT DEVICE: `duo` (Surface Duo 2)** - Always use duo unless user specifies otherwise

## Always Default to Duo

When using speak, ALWAYS use `--device duo`:
```bash
speak "text" --device duo --if-on
```

The duo device at 100.79.15.54 is the primary TTS output for this agent.

## Auto-Detection

Devices are auto-detected on Tailscale by checking which device (IP ending in .54 = Duo, .90 = S10) was most recently online. Default falls back to `duo` if no device detected.

## Default Device: Duo

**Always default to `duo`** (Surface Duo 2 at 100.79.15.54) unless:
- User explicitly specifies a different device
- S10 (100.93.96.90) is the only device online and user is not on Duo

## Requirements

- **Soprano TTS** on port 8102
- **Termux** with media-player on device
- **SSH access** via Tailscale (port 8022)

## Starting Soprano

```bash
nohup python3 -m uvicorn soprano.server:app --host 0.0.0.0 --port 8102 > /tmp/soprano.log 2>&1 &
```

## Notes

- **Script location**: `/home/sovthpaw/Senter/skills/speak/speak.py`
- **Default device**: `duo` (Surface Duo 2 at 100.79.15.54) - auto-detected from Tailscale
- **Always verify SSH connectivity** before speaking - test with: `ssh -i ~/.ssh/phone_access -p 8022 droid@100.79.15.54 "echo ok"`
- **If duo fails**, fallback to `s10` (100.93.96.90), then `local`
- **Device detection priority**: Duo (.54) > S10 (.90) > local
- Max message: 500 characters (auto-truncated)
- Mode persists across sessions
- Build agent has speak ON by default
- Use `--async` for non-blocking speech
- Use `--device local` for computer speakers
- **REMEMBER: When user tells you to update this skill, actually update it. Do not forget.**
