#!/usr/bin/env python3
"""
Always-On Phone Agent Daemon
============================
24/7 background service that listens for user attention via:
1. PRIMARY: Gaze detection (senter-aware - looking at phone + speaking)
2. BACKUP: Wake word detection

Features:
- Continuous low-power monitoring loop
- Multimodal attention detection (camera + audio)
- Conversational memory persistence
- Integration with burner-phone device control
- Speak skill TTS routing
- Extensible architecture for future features

Usage:
    python3 phone_daemon.py --daemon     # Run as background daemon
    python3 phone_daemon.py --test       # Test attention detection once
    python3 phone_daemon.py              # Interactive mode
"""

import os
import sys
import time
import json
import signal
import threading
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from queue import Queue, Empty
import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# ============ CONFIGURATION ============

@dataclass
class DaemonConfig:
    """Configuration for the phone agent daemon"""
    # Paths
    config_dir: str = "~/.hermes-phone-agent"
    log_file: str = "/tmp/phone_daemon.log"
    pid_file: str = "/tmp/phone_daemon.pid"
    state_file: str = "/tmp/phone_daemon.state"
    memory_file: str = "~/.hermes-phone-agent/memory.json"
    
    # Attention detection (senter-aware integration)
    gaze_detection_enabled: bool = True
    gaze_check_interval: float = 2.0  # seconds between gaze checks
    gaze_skill_path: str = "/home/sovthpaw/Senter/skills/senter-aware/aware.py"
    
    # Wake word fallback
    wake_word_enabled: bool = True
    wake_words: list = None
    
    # Device control (burner-phone integration)
    device_config_path: str = None  # Uses default if None
    
    # TTS (speak skill integration)
    speak_skill_path: str = "/home/sovthpaw/Senter/skills/speak/speak.py"
    speak_device: str = "auto"  # auto, duo, s10, local
    
    # Memory & context
    memory_enabled: bool = True
    max_memory_size: int = 10000  # characters
    conversation_timeout: float = 300.0  # 5 minutes of silence = new session
    
    # Logging
    log_level: str = "INFO"
    verbose: bool = False
    
    # Model endpoints
    senter_url: str = "http://100.84.195.22:8081"
    vision_model: str = "qwen2.5-omni:3b"


def load_config(config_path: Optional[str] = None) -> DaemonConfig:
    """Load configuration from YAML file or use defaults"""
    if config_path is None:
        # Default locations
        possible_paths = [
            Path("~/.hermes-phone-agent/daemon.yaml").expanduser(),
            Path("./daemon.yaml"),
            Path("/etc/hermes-phone-agent/daemon.yaml")
        ]
        
        for path in possible_paths:
            if path.exists():
                config_path = str(path)
                break
    
    config = DaemonConfig()
    
    if config_path and Path(config_path).exists():
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f) or {}
        
        # Update config from YAML
        for field in data:
            if hasattr(config, field):
                setattr(config, field, data[field])
    
    # Set defaults for lists
    if config.wake_words is None:
        config.wake_words = ["senter", "hey senter", "phone", "hey phone"]
    
    return config


# ============ LOGGING ============

class DaemonLogger:
    """Simple file and console logger"""
    
    def __init__(self, log_file: str, verbose: bool = False):
        self.log_file = Path(log_file)
        self.verbose = verbose
        self._ensure_log_dir()
    
    def _ensure_log_dir(self):
        """Ensure log directory exists"""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _write(self, level: str, message: str):
        """Write to log file"""
        line = f"[{self._timestamp()}] [{level}] {message}\n"
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(line)
        except Exception as e:
            print(f"Failed to write to log: {e}", file=sys.stderr)
    
    def log(self, level: str, message: str):
        """Log a message"""
        self._write(level, message)
        
        if self.verbose or level in ("ERROR", "WARN"):
            print(f"[{level}] {message}", file=sys.stderr)
    
    def debug(self, msg: str):
        self.log("DEBUG", msg)
    
    def info(self, msg: str):
        self.log("INFO", msg)
    
    def warn(self, msg: str):
        self.log("WARN", msg)
    
    def error(self, msg: str):
        self.log("ERROR", msg)


# ============ MEMORY SYSTEM ============

class ConversationMemory:
    """Persistent conversational memory"""
    
    def __init__(self, config: DaemonConfig):
        self.config = config
        self.memory_file = Path(config.memory_file).expanduser()
        self.memory_dir = self.memory_file.parent
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        self._memory: Dict[str, Any] = {
            "sessions": [],
            "current_session": None,
            "facts": {},
            "preferences": {}
        }
        
        self._load()
    
    def _load(self):
        """Load memory from disk"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r') as f:
                    self._memory = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load memory: {e}")
    
    def _save(self):
        """Save memory to disk"""
        try:
            # Enforce size limit
            memory_str = json.dumps(self._memory)
            if len(memory_str) > self.config.max_memory_size:
                # Trim old sessions
                if len(self._memory["sessions"]) > 10:
                    self._memory["sessions"] = self._memory["sessions"][-10:]
            
            with open(self.memory_file, 'w') as f:
                json.dump(self._memory, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save memory: {e}")
    
    def start_session(self) -> str:
        """Start a new conversation session"""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self._memory["current_session"] = session_id
        self._memory["sessions"].append({
            "id": session_id,
            "started": datetime.now().isoformat(),
            "messages": []
        })
        self._save()
        return session_id
    
    def add_message(self, role: str, content: str):
        """Add a message to the current session"""
        if not self._memory["current_session"]:
            self.start_session()
        
        current = None
        for session in self._memory["sessions"]:
            if session["id"] == self._memory["current_session"]:
                current = session
                break
        
        if current:
            current["messages"].append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            })
            self._save()
    
    def get_context(self, max_messages: int = 10) -> list:
        """Get recent conversation context"""
        if not self._memory["current_session"]:
            return []
        
        for session in self._memory["sessions"]:
            if session["id"] == self._memory["current_session"]:
                return session["messages"][-max_messages:]
        
        return []
    
    def store_fact(self, key: str, value: Any):
        """Store a persistent fact"""
        self._memory["facts"][key] = value
        self._save()
    
    def get_fact(self, key: str, default: Any = None) -> Any:
        """Retrieve a stored fact"""
        return self._memory["facts"].get(key, default)


# ============ ATTENTION DETECTION ============

class AttentionDetector:
    """
    Multimodal attention detection using senter-aware (gaze) + wake word fallback
    
    States:
    - IDLE: No activity
    - PASSIVE: User looking at phone but not speaking
    - LISTENING: User speaking but not looking at phone
    - ADDRESSING: User looking at AND speaking to phone (ACTIVATION!)
    """
    
    def __init__(self, config: DaemonConfig, logger: DaemonLogger):
        self.config = config
        self.logger = logger
        self._last_check = 0
        self._current_state = "idle"
    
    def detect_via_gaze(self) -> Dict[str, Any]:
        """
        PRIMARY detection method: Use senter-aware skill
        
        Returns dict with:
        - addressing: bool (is user addressing the phone?)
        - looking: bool
        - speaking: bool
        - reason: str
        """
        if not self.config.gaze_detection_enabled:
            return {"addressing": False, "error": "Gaze detection disabled"}
        
        try:
            # Import and use senter-aware
            sys.path.insert(0, str(Path(self.config.gaze_skill_path).parent))
            
            # Check if module exists
            if not Path(self.config.gaze_skill_path).exists():
                self.logger.error(f"Senter-aware skill not found at {self.config.gaze_skill_path}")
                return {"addressing": False, "error": "Skill not found"}
            
            # Run the awareness check
            result = subprocess.run(
                ["python3", self.config.gaze_skill_path],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                # User is addressing
                return {
                    "addressing": True,
                    "looking": True,
                    "speaking": True,
                    "reason": "Gaze detection activated"
                }
            else:
                # Not addressing
                return {
                    "addressing": False,
                    "looking": False,
                    "speaking": False,
                    "reason": "No gaze+speech combination detected"
                }
                
        except subprocess.TimeoutExpired:
            self.logger.warn("Gaze detection timeout")
            return {"addressing": False, "error": "Timeout"}
        except Exception as e:
            self.logger.error(f"Gaze detection error: {e}")
            return {"addressing": False, "error": str(e)}
    
    def detect_via_wake_word(self, audio_chunk: bytes = None) -> bool:
        """
        BACKUP detection method: Simple wake word detection
        
        This is a placeholder - in production you'd use:
        - Porcupine (Picovoice)
        - Snowboy
        - Vosk offline keyword spotting
        - Or integrate with STT and check for wake words in transcript
        """
        if not self.config.wake_word_enabled:
            return False
        
        # For now, this is a placeholder
        # In the full implementation, you'd analyze audio_chunk
        # or check STT output for wake words
        
        self.logger.debug("Wake word detection called (placeholder)")
        return False
    
    def check_attention(self) -> Dict[str, Any]:
        """
        Main attention check - combines gaze (primary) + wake word (backup)
        
        Returns:
            Dict with addressing status and metadata
        """
        current_time = time.time()
        
        # Rate limit checks
        if current_time - self._last_check < self.config.gaze_check_interval:
            return {"addressing": False, "reason": "Rate limited"}
        
        self._last_check = current_time
        
        # PRIMARY: Gaze detection
        gaze_result = self.detect_via_gaze()
        
        if gaze_result.get("addressing"):
            self._current_state = "addressing"
            self.logger.info(f"ATTENTION DETECTED (gaze): {gaze_result.get('reason')}")
            return gaze_result
        
        # BACKUP: Wake word (if gaze didn't trigger)
        if self.config.wake_word_enabled:
            # In full implementation, you'd capture audio here
            # and check for wake words
            pass
        
        self._current_state = "idle"
        return {"addressing": False, "reason": "No attention detected"}


# ============ DAEMON MAIN CLASS ============

class PhoneAgentDaemon:
    """
    Main daemon class - orchestrates all components
    
    Architecture:
    ┌─────────────────────────────────────────┐
    │         Phone Agent Daemon              │
    ├─────────────────────────────────────────┤
    │  Attention Detector (gaze + wake word)  │
    │  Conversation Memory                    │
    │  Device Controller (burner-phone)       │
    │  TTS Router (speak skill)               │
    │  Main Event Loop                        │
    └─────────────────────────────────────────┘
    """
    
    def __init__(self, config: DaemonConfig = None):
        self.config = config or load_config()
        self.logger = DaemonLogger(self.config.log_file, self.config.verbose)
        
        # Initialize components
        self.attention = AttentionDetector(self.config, self.logger)
        self.memory = ConversationMemory(self.config) if self.config.memory_enabled else None
        
        # State
        self._running = False
        self._activated = False
        self._conversation_active = False
        self._last_user_activity = 0
        
        # Event queue for async operations
        self.event_queue: Queue = Queue()
        
        # Threads
        self._monitor_thread: Optional[threading.Thread] = None
        self._conversation_thread: Optional[threading.Thread] = None
    
    def log(self, level: str, message: str):
        """Convenience logging"""
        self.logger.log(level, f"[Daemon] {message}")
    
    def start_daemon(self):
        """Start the daemon in background"""
        self.log("INFO", "Starting phone agent daemon...")
        
        # Write PID file
        try:
            with open(self.config.pid_file, 'w') as f:
                f.write(str(os.getpid()))
        except Exception as e:
            self.log("ERROR", f"Failed to write PID file: {e}")
        
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Start monitoring thread
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        self.log("INFO", f"Daemon started (PID: {os.getpid()})")
        
        # Main loop - process events
        while self._running:
            try:
                event = self.event_queue.get(timeout=1.0)
                self._process_event(event)
            except Empty:
                continue
    
    def _monitor_loop(self):
        """Background thread that monitors for attention"""
        self.log("INFO", "Attention monitoring thread started")
        
        while self._running:
            if not self._conversation_active:
                # Check for attention
                result = self.attention.check_attention()
                
                if result.get("addressing"):
                    self._activate()
            
            time.sleep(0.5)  # Don't spam the attention check
    
    def _activate(self):
        """Activate the agent - user is addressing us"""
        if self._activated:
            return
        
        self._activated = True
        self._conversation_active = True
        self._last_user_activity = time.time()
        
        self.log("INFO", ">>> ACTIVATING AGENT <<<")
        
        # Start new conversation session
        if self.memory:
            session_id = self.memory.start_session()
            self.log("INFO", f"New conversation session: {session_id}")
        
        # Speak activation confirmation
        self._speak("I'm here. How can I help?")
    
    def _deactivate(self):
        """Deactivate after timeout"""
        if time.time() - self._last_user_activity > self.config.conversation_timeout:
            self._activated = False
            self._conversation_active = False
            self.log("INFO", ">>> DEACTIVATING (timeout) <<<")
    
    def _speak(self, text: str):
        """Speak text using the speak skill"""
        try:
            # Use async speaking (--if-on flag)
            cmd = [
                "python3", self.config.speak_skill_path,
                text,
                "--if-on",
                "--device", self.config.speak_device,
                "--async"
            ]
            
            subprocess.run(cmd, capture_output=True, timeout=5)
            
            if self.memory:
                self.memory.add_message("assistant", text)
                
        except Exception as e:
            self.log("ERROR", f"Speak error: {e}")
    
    def _process_event(self, event: Dict[str, Any]):
        """Process events from the queue"""
        event_type = event.get("type")
        
        if event_type == "user_speech":
            transcript = event.get("transcript", "")
            self.log("INFO", f"User said: {transcript}")
            
            if self.memory:
                self.memory.add_message("user", transcript)
            
            self._last_user_activity = time.time()
            
            # Process the command (placeholder - would integrate with LLM here)
            self._process_command(transcript)
        
        elif event_type == "heartbeat":
            self._deactivate()
    
    def _process_command(self, command: str):
        """Process a user command - placeholder for LLM integration"""
        # This is where you'd integrate with an LLM to understand intent
        # and take actions via burner-phone
        
        self.log("DEBUG", f"Processing command: {command}")
        
        # Simple keyword-based responses for now
        command_lower = command.lower()
        
        if "hello" in command_lower or "hey" in command_lower:
            self._speak("Hello! What would you like to do?")
        
        elif "battery" in command_lower:
            # Would check battery level via burner-phone
            self._speak("Checking battery level...")
        
        elif "time" in command_lower:
            current_time = datetime.now().strftime("%I:%M %p")
            self._speak(f"It's {current_time}")
        
        else:
            self._speak("I'm still learning. Try asking me something simple.")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.log("INFO", f"Received signal {signum}, shutting down...")
        self._running = False
        
        # Clean up PID file
        try:
            Path(self.config.pid_file).unlink(missing_ok=True)
        except:
            pass
        
        self.log("INFO", "Daemon stopped")
        sys.exit(0)
    
    def test_attention(self):
        """Run a single attention check (for testing)"""
        self.log("INFO", "Testing attention detection...")
        result = self.attention.check_attention()
        print(f"\nAttention Result: {json.dumps(result, indent=2)}")
        return result


# ============ MAIN ENTRY POINT ============

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Always-On Phone Agent Daemon")
    parser.add_argument("--daemon", action="store_true", help="Run as background daemon")
    parser.add_argument("--test", action="store_true", help="Test attention detection once")
    parser.add_argument("--config", "-c", help="Config file path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Load config
    config = load_config(args.config)
    config.verbose = args.verbose
    
    # Create daemon
    daemon = PhoneAgentDaemon(config)
    
    if args.test:
        # Test mode
        result = daemon.test_attention()
        sys.exit(0 if result.get("addressing") else 1)
    
    elif args.daemon:
        # Daemon mode
        daemon.start_daemon()
    
    else:
        # Interactive mode (foreground monitoring)
        print("Phone Agent Daemon - Interactive Mode")
        print("Press Ctrl+C to exit\n")
        
        try:
            while True:
                result = daemon.attention.check_attention()
                
                if result.get("addressing"):
                    print(f"\n>>> ATTENTION DETECTED! <<<")
                    print(f"Reason: {result.get('reason')}")
                    # Would activate conversation here
                
                time.sleep(config.gaze_check_interval)
                
        except KeyboardInterrupt:
            print("\n\nShutting down...")


if __name__ == "__main__":
    main()