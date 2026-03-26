#!/usr/bin/env python3
"""
Assistant Daemon - Complete speech-to-speech phone assistant
Runs as background service with all capabilities integrated
"""

import subprocess
import time
import threading
import queue
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass
import json
import signal
import sys

# Import our components
sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.phone_control import PhoneControlAgent
from agents.voice_activation import VoiceActivationSystem, ActivationMethod, ActivationEvent
from skills.speak import speak as tts_speak

@dataclass
class ConversationState:
    """Tracks conversation state"""
    active: bool = False
    waiting_for_response: bool = False
    context: dict = None

class AssistantDaemon:
    """
    Complete speech-to-speech assistant daemon.
    
    Features:
    - Multiple activation methods (gaze+voice, wake word, double-tap)
    - Speech-to-text transcription
    - Natural language understanding
    - Phone control execution
    - Text-to-speech response
    - Continuous conversation loop
    """
    
    def __init__(self, device_ip: str = "100.79.15.54", ssh_port: int = 8022,
                 wake_words: list = None):
        self.device_ip = device_ip
        self.ssh_port = ssh_port
        
        # Initialize components
        self.phone_control = PhoneControlAgent(device_ip, ssh_port)
        self.voice_activation = VoiceActivationSystem(
            device_ip, ssh_port, wake_words or ["hey phone", "hello assistant"],
            callback=self._on_activation
        )
        
        # Conversation state
        self.state = ConversationState()
        self._running = False
        self._response_queue: queue.Queue = queue.Queue()
        
        # STT/TTS configuration
        self.stt_model = "whisper-tiny"  # Lightweight model for phone
        self.tts_device = "duo"  # Default TTS device
        
        print("[AssistantDaemon] Initialized")
        print(f"  - Device: {device_ip}")
        print(f"  - Wake words: {wake_words or ['hey phone', 'hello assistant']}")
        print(f"  - STT: {self.stt_model}")
        print(f"  - TTS: Soprano via {self.tts_device}")
    
    def start(self):
        """Start the assistant daemon"""
        if self._running:
            print("[AssistantDaemon] Already running")
            return
        
        self._running = True
        print("\n" + "="*60)
        print("ASSISTANT DAEMON STARTING")
        print("="*60)
        
        # Start voice activation system
        self.voice_activation.start()
        
        # Start response processor
        self._response_thread = threading.Thread(target=self._response_loop, daemon=True)
        self._response_thread.start()
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        print("[AssistantDaemon] RUNNING - Waiting for activation...")
        print("  Activate by: looking at phone + speaking, saying 'Hey Phone', or double-tapping side button")
        print("="*60 + "\n")
        
        # Main loop - keep daemon alive
        try:
            while self._running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the assistant daemon"""
        print("\n[AssistantDaemon] Stopping...")
        self._running = False
        self.voice_activation.stop()
        print("[AssistantDaemon] Stopped")
    
    def _on_activation(self, event: ActivationEvent):
        """Called when voice activation is detected"""
        print(f"\n[AssistantDaemon] ACTIVATED via {event.method.value}")
        
        # Start listening for command
        self.state.active = True
        self._listen_for_command()
    
    def _listen_for_command(self):
        """Listen for user's voice command"""
        print("[AssistantDaemon] Listening...")
        
        # Record audio until silence detected (VAD)
        audio_data = self._record_until_silence(max_duration=15)
        
        if not audio_data:
            print("[AssistantDaemon] No audio captured")
            self.state.active = False
            return
        
        # Transcribe audio
        command_text = self._transcribe(audio_data)
        if not command_text:
            print("[AssistantDaemon] Could not transcribe audio")
            self.state.active = False
            return
        
        print(f"[AssistantDaemon] Command: '{command_text}'")
        
        # Process command and generate response
        self._process_command(command_text)
    
    def _record_until_silence(self, max_duration: int = 15) -> Optional[bytes]:
        """Record audio until silence is detected (simple VAD)"""
        # This is a simplified version - production would use proper VAD
        record_duration = min(3, max_duration)  # Default 3 seconds
        
        try:
            # Record on device
            self._ssh(f"termux-microphone-record -f /sdcard/.cmd.wav -l {record_duration} 2>/dev/null")
            
            # Download audio
            result = subprocess.run([
                "scp", "-i", "/home/sovthpaw/.ssh/phone_access",
                "-P", str(self.ssh_port),
                "-o", "StrictHostKeyChecking=no",
                f"droid@{self.device_ip}:/sdcard/.cmd.wav",
                "/tmp/cmd.wav"
            ], capture_output=True, timeout=5)
            
            if result.returncode == 0:
                with open("/tmp/cmd.wav", "rb") as f:
                    return f.read()
        except Exception as e:
            print(f"[AssistantDaemon] Recording error: {e}")
        
        return None
    
    def _transcribe(self, audio_data: bytes) -> str:
        """Transcribe audio to text using Whisper"""
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_data)
                temp_path = f.name
            
            # Use faster-whisper or openai-whisper
            # For production, use a pre-loaded model
            from faster_whisper import WhisperModel
            
            model = WhisperModel(self.stt_model, device="cpu", compute_type="int8")
            segments, info = model.transcribe(temp_path, beam_size=3)
            
            text = " ".join([segment.text for segment in segments])
            return text.strip()
            
        except ImportError:
            # Fallback - would need to install faster-whisper
            print("[AssistantDaemon] STT not available, using placeholder")
            return ""
        except Exception as e:
            print(f"[AssistantDaemon] Transcription error: {e}")
            return ""
    
    def _process_command(self, command: str):
        """Process the user's command and generate response"""
        print(f"[AssistantDaemon] Processing: '{command}'")
        
        # Route to phone control agent
        response = self.phone_control.execute_command(command)
        
        print(f"[AssistantDaemon] Response: {response}")
        
        # Speak the response
        self._speak_response(response)
        
        # Check if user wants to continue conversation
        self._check_for_followup()
    
    def _speak_response(self, text: str):
        """Speak response using TTS"""
        print(f"[AssistantDaemon] Speaking: {text[:50]}...")
        
        # Use the fixed speak skill
        try:
            subprocess.run([
                "python3", "/home/sovthpaw/Senter/skills/speak/speak.py",
                text, "--device", self.tts_device, "--sync"
            ], timeout=10)
        except Exception as e:
            print(f"[AssistantDaemon] TTS error: {e}")
    
    def _check_for_followup(self):
        """Check if user has a follow-up question"""
        print("[AssistantDaemon] Listening for follow-up (3 seconds)...")
        
        # Brief listening window for follow-up
        audio_data = self._record_until_silence(max_duration=3)
        
        if audio_data:
            followup = self._transcribe(audio_data)
            if followup and len(followup) > 2:  # Minimum length check
                print(f"[AssistantDaemon] Follow-up: '{followup}'")
                self._process_command(followup)
        
        self.state.active = False
    
    def _response_loop(self):
        """Background loop for processing responses"""
        while self._running:
            try:
                response = self._response_queue.get(timeout=1.0)
                self._speak_response(response)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[AssistantDaemon] Response loop error: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.stop()
        sys.exit(0)
    
    def _ssh(self, command: str, timeout: int = 10) -> bool:
        """Execute a command via SSH"""
        try:
            result = subprocess.run([
                "ssh", "-i", "/home/sovthpaw/.ssh/phone_access",
                "-p", str(self.ssh_port),
                "-o", "StrictHostKeyChecking=no",
                "-o", "ConnectTimeout=5",
                f"droid@{self.device_ip}", command
            ], capture_output=True, timeout=timeout)
            return result.returncode == 0
        except:
            return False


def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("PHONE ASSISTANT DAEMON")
    print("="*60)
    
    daemon = AssistantDaemon(
        device_ip="100.79.15.54",
        ssh_port=8022,
        wake_words=["hey phone", "hello assistant", "ok phone"]
    )
    
    daemon.start()


if __name__ == "__main__":
    main()
