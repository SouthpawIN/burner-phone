# Three-Agent Distributed AI System

## Overview

A distributed intelligence system that splits work between edge (phone) and server hardware, enabling responsive local interaction while leveraging powerful server-side reasoning.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                           │
│                    (Voice/Text Chat)                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┴────────────────────┐
        │                                         │
        ▼                                         ▼
┌───────────────────┐                    ┌─────────────────────┐
│  FRONTEND AGENT   │                    │   PLANNER AGENT     │
│  (on Phone)       │◄──────────────────►│   (on Phone)        │
│                   │                    │                     │
│ • Quick tasks     │                    │ • Task breakdown    │
│ • Web searches    │                    │ • Prompt building   │
│ • Smart home      │                    │ • Workflow mgmt     │
│ • App control     │                    │ • State tracking    │
│                   │                    │                     │
│ Model: Omni 3B    │                    │ Model: Qwen2.5-7B   │
└───────────────────┘                    └───────────┬─────────┘
                                                    │
                                                    │ Complex tasks
                                                    │ requiring reasoning
                                                    ▼
                    ┌────────────────────────────────────────────────┐
                    │              SENTER SERVER                     │
                    │           (100.84.195.22)                    │
                    │                                              │
                    │  ┌───────────────────────────────────┐       │
                    │  │            HERMES AGENT           │       │
                    │  │            (qwopus)              │       │
                    │  │                                   │       │
                    │  │  • Deep reasoning                │       │
                    │  │  • Complex problem solving       │       │
                    │  │  • Code generation & analysis    │       │
                    │  │  • Multi-step planning          │       │
                    │  │                                   │       │
                    │  └───────────────────┬───────────────┘       │
                    │                      │                       │
                    │  ┌───────────────────▼───────────────────┐   │
                    │  │         MODEL SERVICES              │   │
                    │  │                                      │   │
                    │  │  • qwen35       - Qwen3.5-35B-A3B  │   │
                    │  │  • qwen27        - Qwen3.5-27B     │   │
                    │  │  • qwopus        - Qwen+Opus dist   │   │
                    │  │  • qwen-omni     - Multimodal 3B    │   │
                    │  │  • soprano       - TTS 80M          │   │
                    │  │  • qwen-image    - Image gen        │   │
                    │  │  • ltx           - Video gen        │   │
                    │  │  • acestep       - Music gen        │   │
                    │  │                                      │   │
                    │  └──────────────────────────────────────┘   │
                    │                                              │
                    │  ┌───────────────────────────────────┐      │
                    │  │        PHONE AGENT API            │      │
                    │  │                                   │      │
                    │  │  • Camera control                │      │
                    │  │  • Screen interaction            │      │
                    │  │  • Audio recording/playback      │      │
                    │  │  • Vision feedback loop          │      │
                    │  │                                   │      │
                    │  └───────────────────────────────────┘      │
                    └──────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. Frontend Agent (Edge - Phone)

**Purpose:** Immediate, responsive interaction for simple tasks

**Responsibilities:**
- Handle quick queries without breaking conversation flow
- Web searches via MCP tools
- Smart home device control
- Opening apps, browser navigation
- Simple Q&A from context

**Model:** Qwen2.5-Omni 3B (multimodal, fast)

**Latency Target:** < 2 seconds

---

### 2. Planner Agent (Edge - Phone)

**Purpose:** Orchestrate complex tasks, build prompts for Hermes

**Responsibilities:**
- Break down complex user requests into steps
- Build optimized prompts for Hermes reasoning
- Track conversation state and context
- Decide when to escalate to Hermes vs handle locally
- Manage tool selection and sequencing

**Model:** Senter Omni 3B (fine-tuned for function calling)

**Latency Target:** < 5 seconds for planning

**Note:** Uses the same model as Frontend Agent - both are continuously fine-tuned for improved function calling and task orchestration.

---

### 3. Hermes Agent (Server - qwopus)

**Purpose:** Heavy reasoning, complex problem solving

**Responsibilities:**
- Deep analytical reasoning
- Multi-step problem decomposition
- Code generation and debugging
- Complex workflow orchestration
- Learning and adaptation

**Model:** Qwen3.5-27B + Opus 4.6 Distillation (qwopus)

**Latency Target:** < 30 seconds for complex reasoning

---

### 4. Phone Agent API (Server)

**Purpose:** Remote device control interface

**Responsibilities:**
- Camera capture and streaming
- Screen interaction (tap, swipe, text input)
- Audio recording and playback
- Vision analysis via Qwen Omni
- Screenshot capture

**Interface:** REST API + WebSocket for real-time feedback

---

## Data Flow Examples

### Example 1: Simple Query (Frontend Only)

```
User: "What's the weather today?"
    ↓
Frontend Agent:
  • Detects simple query pattern
  • Calls web search tool
  • Returns formatted answer
    ↓
Response: "It's 72°F and sunny with a high of 78°F"
```

**Total Latency:** ~1-2 seconds

---

### Example 2: Medium Complexity (Frontend + Planner)

```
User: "Set up a morning routine reminder"
    ↓
Frontend Agent:
  • Detects multi-step task
  • Escalates to Planner
    ↓
Planner Agent:
  • Breaks into steps:
    1. Determine user's typical wake time
    2. Create reminder structure
    3. Set up notification preferences
  • Executes via device APIs
    ↓
Response: "Morning routine set for 7 AM with alarm and notification"
```

**Total Latency:** ~5-10 seconds

---

### Example 3: Complex Reasoning (Full Stack)

```
User: "Help me debug this Python script that's failing"
    ↓
Frontend Agent:
  • Detects code debugging request
  • Escalates to Planner
    ↓
Planner Agent:
  • Analyzes complexity
  • Builds detailed prompt with context
  • Sends to Hermes
    ↓
Hermes (qwopus):
  • Analyzes code structure
  • Identifies bug pattern
  • Generates fix with explanation
  • Provides testing suggestions
    ↓
Planner Agent:
  • Formats response
  • May execute test via Phone Agent
    ↓
Frontend Agent:
  • Presents solution to user
```

**Total Latency:** ~15-30 seconds

---

## Communication Protocols

### Frontend ↔ Planner (Local IPC)

```python
# Simple message queue or shared state
{
    "type": "escalate|resolve|status",
    "task_id": "uuid",
    "data": {...},
    "priority": "high|normal|low"
}
```

### Planner ↔ Hermes (HTTP/REST)

```python
POST /api/hermes/reason
{
    "prompt": "Detailed reasoning request...",
    "context": {...},
    "task_type": "debugging|planning|analysis",
    "timeout": 60
}
```

### Hermes ↔ Phone Agent (HTTP/REST + WebSocket)

```python
# Camera capture
POST /api/phone/camera/capture
{
    "camera": "front|back",
    "resolution": "high|medium|low"
}

# Screen interaction
POST /api/phone/screen/tap
{
    "x": 100,
    "y": 200
}

# Vision analysis
POST /api/phone/vision/analyze
{
    "image": "base64...",
    "query": "What do you see?"
}
```

---

## Hardware Requirements

### Phone (Edge)
- **RAM:** 6GB minimum, 8GB recommended
- **Storage:** 2GB free for models
- **Models hosted:** Omni 3B (~2GB), optionally 7B (~4GB)
- **Network:** Wi-Fi or 5G for server connectivity

### Server (Backend)
- **GPU:** Dual RTX 3090 (48GB VRAM) or equivalent
- **RAM:** 64GB minimum
- **Storage:** 100GB+ for model storage
- **Network:** Stable internet connection

---

## Repository Structure

```
southpawin/
├── senter-server/          # Backend infrastructure
│   ├── bin/
│   │   ├── senter-server   # Model management
│   │   └── hermes-api      # Hermes REST interface
│   ├── scripts/
│   │   ├── install.sh
│   │   ├── detect-hardware.sh
│   │   └── download-models.sh
│   └── config/
│
├── burner-phone/           # Edge agents + phone control
│   ├── agents/
│   │   ├── frontend.py     # Frontend agent
│   │   ├── planner.py      # Planner agent  
│   │   └── orchestrator.py # Agent coordination
│   ├── phone/
│   │   ├── phone_agent.py  # Device control
│   │   └── vision_helper.py # Vision feedback
│   └── skills/
│       └── speak/          # TTS skill
│
└── hermes-agent-pr/       # Pull requests to NousResearch
    └── (feature branches)
```

---

## Installation & Setup

### Server Setup

```bash
# Clone and install Senter-Server
git clone https://github.com/SouthpawIN/Senter-Server
cd Senter-Server
./scripts/install.sh

# Verify all services
./bin/senter-server status
```

### Phone Setup

```bash
# Clone burner-phone on phone or sync from server
git clone https://github.com/SouthpawIN/burner-phone
cd burner-phone
pip install -r requirements.txt

# Configure
nano ~/.hermes-phone-agent/config.yaml

# Start agents
python3 -m agents.orchestrator
```

---

## Configuration

### Server Config (~/.hermes-server/config.yaml)

```yaml
server:
  host: "0.0.0.0"
  port: 8080
  
hermes:
  model: "qwopus"
  max_tokens: 4096
  temperature: 0.7
  
phone_agent:
  enabled: true
  vision_model: "qwen-omni"
```

### Phone Config (~/.hermes-phone-agent/config.yaml)

```yaml
server:
  address: "100.84.195.22"  # TailScale IP
  port: 8080
  
frontend:
  model: "qwen-omni"
  max_context: 8192
  
planner:
  model: "qwen-7b"
  escalation_threshold: 0.7
  
device:
  type: "termux"  # or "adb", "emulator"
```

---

## Performance Targets

| Operation | Target Latency | Notes |
|-----------|---------------|-------|
| Frontend query | < 2s | Local only |
| Planner task | < 5s | Local + simple tools |
| Hermes reasoning | < 30s | Server roundtrip |
| Camera capture | < 1s | Via Phone Agent |
| Vision analysis | < 3s | Omni on server |

---

## Future Enhancements

- [ ] Model caching on phone for offline capability
- [ ] Incremental reasoning updates via WebSocket
- [ ] Multi-phone support with load balancing
- [ ] Federated learning across devices
- [ ] Edge model fine-tuning from server interactions
