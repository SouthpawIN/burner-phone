# Three-Agent System Quick Start

## Overview

This repository contains the edge intelligence layer for the distributed three-agent system:
- **Frontend Agent**: Quick tasks (<2s latency)
- **Planner Agent**: Task orchestration (<5s latency)  
- **Hermes Agent**: Heavy reasoning on server (via qwopus)

## Installation

```bash
# Clone the repository
git clone https://github.com/SouthpawIN/burner-phone
cd burner-phone

# Install dependencies
pip install -r requirements.txt

# Configure
cat > ~/.hermes-phone-agent/config.yaml << EOF
server:
  address: "100.84.195.22"  # Your senter-server TailScale IP
  port: 8080

frontend:
  model: "qwen-omni"
  max_context: 8192

planner:
  model: "qwen-7b"
  escalation_threshold: 0.7
devicetype: "termux"  # or "adb", "emulator"
EOF
```

## Running the Agents

### Demo Mode (No Server Required)

```bash
# Run the orchestrator in demo mode
python3 -m agents.orchestrator --demo
```

### Interactive Mode

```bash
# Start interactive session
python3 -m agents.orchestrator

# Enter queries:
#   "What's the weather?" -> Frontend handles
#   "Debug this code..."  -> Planner escalates to Hermes
```

### As a Library

```python
from agents.orchestrator import ThreeAgentOrchestrator

orchestrator = ThreeAgentOrchestrator()

result = orchestrator.process("Help me debug this Python script...")
print(result["final_response"])
```

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for full system documentation.

## API Reference

### Frontend Agent

```python
from agents.frontend import FrontendAgent

config = {"model": "qwen-omni", "max_context": 8192}
frontend = FrontendAgent(config)

result = frontend.process("What's the weather?")
# Returns: {"task_type": "web_search", "response": "...", "latency_ms": 150}
```

### Planner Agent

```python
from agents.planner import PlannerAgent

config = {"model": "qwen-7b", "escalation_threshold": 0.7}
planner = PlannerAgent(config)

result = planner.process("Debug this complex async code...")
# Returns: {"complexity": 0.85, "escalate": True, "response": "..."}
```

## Server Setup

The Hermes API runs on your senter-server:

```bash
# On senter-server (100.84.195.22)
./bin/senter-server hermes-api

# Verify
curl http://localhost:8080/health
```

## Testing

```bash
# Test frontend agent
python3 -c "from agents.frontend import FrontendAgent; a = FrontendAgent({}); print(a.process('test'))"

# Test planner agent  
python3 -c "from agents.planner import PlannerAgent; a = PlannerAgent({}); print(a.process('test'))"

# Run orchestrator demo
python3 -m agents.orchestrator --demo
```
