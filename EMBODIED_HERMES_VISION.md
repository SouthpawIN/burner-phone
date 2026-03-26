# Hermes Embodied - The Phone as Physical Presence

## Core Philosophy

**The phone IS Hermes embodied in the physical world.** This transforms the phone from a simple tool into Hermes' dedicated presence that can see, hear, interact with devices, and serve as both an automation platform AND a personal companion.

---

## Dual Purpose Device

### 1. As a Tool (Hermes' Hands in the World)
- **Independent terminal access** - Phone runs its own shell sessions
- **Separate browser** - Can browse web independently of Hermes' main browser
- **Sensor access** - GPS, camera, microphone, accelerometer, battery monitoring
- **Device control** - Apps, notifications, system settings via ADB/Termux
- **Network presence** - Always-on connection via TailScale

### 2. As a Companion (User's Personal Assistant)
- **Always-aware** - Continuously monitors for user attention
- **Contextual understanding** - Knows when user is addressing Hermes vs background noise
- **Natural interaction** - Gaze + speech activation, no wake words needed
- **Proactive assistance** - Anticipates needs based on patterns and context

---

## Auto-Journal & Goal Extraction System

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  AUTO-JOURNAL DAEMON                        │
│  (Runs 24/7 in background, silent collection mode)          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐                      │
│  │ Conversation │    │  Context     │                      │
│  │  Capture     │───▶│  Awareness   │                      │
│  │  (Audio/Text)│    │  (Location,  │                      │
│  └──────────────┘    │   Time, App) │                      │
│         │            └──────────────┘                      │
│         ▼                                                   │
│  ┌─────────────────────────────────────┐                   │
│  │   Background Goal Extractor         │                   │
│  │   (Sub-agent running silently)      │                   │
│  │   • NLP on captured conversations   │                   │
│  │   • Intent recognition              │                   │
│  │   • Goal hypothesis generation      │                   │
│  └──────────────┬──────────────────────┘                   │
│                 │                                           │
│                 ▼                                           │
│  ┌─────────────────────────────────────┐                   │
│  │  Goal Confirmation Interface        │                   │
│  │  (Chat-based, non-intrusive)       │                   │
│  │  "I noticed you mentioned X -      │                   │
│  │   want me to help with that?"      │                   │
│  └──────────────┬──────────────────────┘                   │
│                 │                                           │
│                 ▼ (User confirms)                           │
│  ┌─────────────────────────────────────┐                   │
│  │  Task Automation Queue              │                   │
│  │  (Background execution)             │                   │
│  │  • Add to Hermes todo list          │                   │
│  │  • Schedule via cron jobs           │                   │
│  │  • Execute with Hermes tools        │                   │
│  └─────────────────────────────────────┘                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### User Experience Flow

#### Scenario 1: Casual Goal Mention

```
User (casually, while scrolling phone): 
  "I should probably call my mom this week, it's been a while"
  
[Background - Auto-journal]
  • Conversation captured with timestamp + context
  • Sub-agent analyzes: "call", "mom", "this week" → intent detected
  
[5 minutes later - when user is addressing phone]
Hermes (via chat): 
  "Hey, I noticed you mentioned calling your mom earlier. 
   Want me to help with that?"
   
User: "Yeah, maybe schedule it for Thursday afternoon"

[Background - Task automation]
  • Goal added to Hermes todo list
  • Calendar event created for Thursday 2pm
  • Reminder scheduled
  
[Thursday 2pm]
Hermes (proactive notification):
  "It's time to call your mom - want me to dial?"
```

#### Scenario 2: Multi-Step Project

```
User (during conversation):
  "I've been thinking about starting a blog, 
   need to figure out hosting and all that"
  
[Background]
  • Goal extracted: "Start a blog"
  • Sub-agent researches: hosting options, platforms, requirements
  
[Next interaction]
Hermes:
  "About the blog you mentioned - I looked into some options.
   We could use WordPress, Ghost, or something simpler like Medium.
   What were you thinking?"
   
User: "Let's go with WordPress, sounds good"

[Background automation]
  • Research hosting providers (Bluehost, SiteGround, etc.)
  • Compare pricing and features
  • Present options to user
  • Once confirmed, automate setup process
```

---

## Embodied AI Capabilities

### What Hermes Can Do Through the Phone

#### Perception
- **See:** Front/rear cameras for visual input
- **Hear:** Microphone array for audio capture
- **Sense:** GPS location, battery level, motion sensors
- **Monitor:** Notifications, incoming calls, messages

#### Action
- **Speak:** TTS through phone speakers (Soprano 80M)
- **Type:** Automated text input via ADB/Termux
- **Navigate:** App launching, screen tapping, swiping
- **Communicate:** Make calls, send texts, use messaging apps

#### Computation
- **Terminal:** Full shell access on phone (Termux)
- **Browser:** Web browsing with automation
- **Apps:** Control any installed Android app
- **Network:** HTTP requests, API calls, file transfers

---

## Background Automation Architecture

### Key Principle: Never Interrupt the Front Chat

```
┌─────────────────────────────────────────────────────────┐
│              FRONT-END CHAT (User-Facing)               │
│  • Direct conversation with Hermes                      │
│  • Immediate responses                                  │
│  • Natural, uninterrupted flow                          │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│           BACKGROUND AUTOMATION (Silent)                │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ Goal        │  │ Task        │  │ Cron Jobs   │    │
│  │ Extractor   │──▶│ Executor    │──▶│ Scheduler   │    │
│  │ (Sub-agent) │  │ (Tools)     │  │ (Periodic)  │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ Research    │  │ Monitoring  │  │ Notification│    │
│  │ Agents      │  │ Daemons     │  │ System      │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Implementation Strategy

1. **Separate Processes:**
   - Front chat runs in main Hermes session
   - Background automation uses sub-agents and cron jobs
   - Communication via shared todo lists, memory files, hooks

2. **Goal Extraction Pipeline:**
   ```python
   # Auto-journal daemon (background)
   class GoalExtractor:
       def process_conversation(self, text, context):
           # Use LLM to extract potential goals
           goals = llm.extract_goals(text, context)
           
           for goal in goals:
               if self.needs_confirmation(goal):
                   # Queue for chat confirmation
                   self.queue_for_confirmation(goal)
               else:
                   # Auto-execute simple tasks
                   self.execute_goal(goal)
   ```

3. **Task Execution:**
   - Simple tasks: Execute immediately (set reminder, send text)
   - Complex tasks: Break into subtasks, run in background
   - Long-running tasks: Use cron jobs with progress tracking

---

## Integration with Hermes Agent Core

### 1. Todo List Integration

```python
# Phone assistant adds to Hermes todo list
from hermes_tools import todo

def add_goal_to_todo(goal, priority="medium"):
    todos = todo()  # Get current list
    new_item = {
        "id": f"phone_{datetime.now().timestamp()}",
        "content": goal.description,
        "status": "pending",
        "priority": priority
    }
    todo(todos=[*todos, new_item], merge=True)
```

### 2. Cron Job Scheduling

```python
# Schedule recurring tasks via Hermes cron
from hermes_tools import schedule_cronjob

def schedule_recurring_task(prompt, schedule, name):
    schedule_cronjob(
        prompt=prompt,
        schedule=schedule,  # "every 1h", "0 9 * * *", etc.
        name=name,
        deliver="local"  # Don't interrupt user
    )
```

### 3. Sub-Agent Spawning

```python
# Spawn background research agent
from hermes_tools import delegate_task

def spawn_research_agent(topic):
    return delegate_task(
        goal=f"Research {topic} and provide actionable recommendations",
        context="User mentioned this casually - research silently",
        model="cheaper_model"  # Use efficient model for background work
    )
```

### 4. Hook Integration

```yaml
# ~/.hermes/hooks/phone-journal/HOOK.yaml
name: phone-journal
events:
  - session:start     # Start journaling daemon
  - todo:update       # Sync with Hermes todo list
  - cron:execute      # Handle scheduled tasks
```

---

## Technical Requirements

### Models & Services

| Component | Model/Service | Purpose | Endpoint |
|-----------|---------------|---------|----------|
| Goal Extraction | Hermes main model | NLP on conversations | Local |
| Research Agents | Smaller/faster model | Background research | Local |
| TTS | Soprano 80M | Voice output | Port 8102 |
| STT | Whisper/Silero | Speech-to-text | Local |
| Attention | Qwen2.5-Omni 3B | Gaze + speech detection | Port 8081 |

### Hardware

**Phone (Embodied Hermes):**
- Android device with Termux OR ADB wireless debugging
- Camera + microphone access
- TailScale for network presence
- Battery capacity for 24/7 operation (or wired charging)

**Server (Hermes Core):**
- GPU for model inference (RTX 3090+ recommended)
- RAM: 32GB+ for multiple models
- Storage: Fast SSD for conversation logs

### Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Goal extraction latency | < 5s | From speech to goal hypothesis |
| Background task startup | < 1s | Sub-agent spawn time |
| Battery drain (24/7) | < 15%/day | With periodic rest periods |
| Storage (journal logs) | ~100MB/day | Compressed conversation logs |

---

## Privacy & Ethics

### User Control

1. **Opt-in journaling:** User explicitly enables auto-journal feature
2. **Transparent logging:** User can view all captured conversations
3. **Easy deletion:** One-command to clear journal history
4. **Local-first option:** Process conversations on-device only

### Data Handling

- **Encryption:** All conversation logs encrypted at rest
- **Retention:** Auto-delete after 30 days unless user saves
- **Access:** Only Hermes and authorized sub-agents can access
- **Export:** User can export all data in standard formats

---

## Demo Scenarios for Hackathon

### 1. Casual Goal → Automated Task

```
[Presenter casually mentions]
"Man, I need to remember to buy groceries this weekend"

[5 minutes later]
Hermes: "You mentioned buying groceries - want me to help?"
User: "Yeah, maybe make a list"

[Hermes creates shopping list, suggests stores, 
 schedules reminder for Saturday morning]
```

### 2. Multi-Step Project from Conversation

```
[Presenter discusses idea]
"Thinking about learning guitar, heard it's good for stress"

[Background research happens silently]

[Next interaction]
Hermes: "About the guitar - I found some beginner options 
 under $200, and a free YouTube course. Interested?"
```

### 3. Proactive Assistance

```
[Hermes notices pattern: user always checks weather at 8am]

[Next morning at 7:55am]
Hermes (proactive): "Good morning! Weather's 72° and sunny 
 today - perfect for that hike you mentioned"
```

---

## Implementation Roadmap

### Phase 1: Core Embodiment (Week 1)
- [x] Phone daemon with 24/7 monitoring
- [x] Speak skill integration (Soprano TTS)
- [ ] Auto-journal conversation capture
- [ ] Basic goal extraction sub-agent

### Phase 2: Goal System (Week 2)
- [ ] Confirmation interface (chat-based)
- [ ] Integration with Hermes todo list
- [ ] Background task execution
- [ ] Simple automation (reminders, texts, etc.)

### Phase 3: Advanced Automation (Week 3)
- [ ] Complex multi-step task handling
- [ ] Research sub-agents
- [ ] Cron job integration
- [ ] Proactive notification system

### Phase 4: Polish & Demo (Week 4)
- [ ] End-to-end demo scenarios
- [ ] Privacy controls and settings
- [ ] Documentation and tutorials
- [ ] Hackathon submission package

---

*This vision transforms Hermes from a chatbot into an embodied AI presence - always available, always learning, always helping without being intrusive.*