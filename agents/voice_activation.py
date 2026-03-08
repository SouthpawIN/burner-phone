#!/usr/bin/env python3
"""
Voice Activation System - Multiple activation methods for phone assistant
Supports: Gaze + Voice, Wake Word, Double-Tap Side Button
"""

import subprocess
import time
import threading
import queue
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import re

class ActivationMethod(Enum):
    GAZE_VOICE = "gaze_voice"      # Looking at phone + speaking
    WAKE_WORD = "wake_word"        # Saying wake word (e.g., "Hey Phone")
    DOUBLE_TAP = "double_tap"      # Double-tap side button
    BUTTON_HOLD = "button_hold"    # Hold side button (like Siri)

@dataclass
class ActivationEvent:
    """Represents a voice activation event"""
    method: ActivationMethod
    confidence: float
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)

class VoiceActivationSystem:
    """
    Multi-method voice activation system for phone assistant.
    Runs as background service with auto-recovery.
    """
    
    def __init__(self, device_ip: str = "100.79.15.54", ssh_port: int = 8022,
                 wake_words: list = None, callback: Callable = None):
        self.device_ip = device_ip
        self.ssh_port = ssh_port
        self.ssh_key = "/home/sovthpaw/.ssh/phone_access"
        self.ssh_user = "droid"
        self.wake_words = wake_words or ["hey phone", "hello assistant", "ok phone"]
        self.callback = callback  # Callback function when activated
        
        # State
        self._running = False
        self._activation_queue: queue.Queue = queue.Queue()
        self._last_activation_time = 0
        self._cooldown_period = 2.0  # Seconds between activations
        
        # Gaze detection state
        self._front_camera_active = False
        self._gaze_threshold = 0.7  # Confidence threshold for gaze
        
        # Double-tap detection state
        self._last_button_press_time = 0
        self._double_tap_window = 0.5  # Seconds between taps
        
        print(f"[VoiceActivation] Initialized with methods: gaze+voice, wake_word, double_tap")
    
    def start(self):
        """Start the voice activation system"""
        if self._running:
            print("[VoiceActivation] Already running")
            return
        
        self._running = True
        print("[VoiceActivation] Starting activation threads...")
        
        # Start gaze + voice monitoring thread
        self._gaze_thread = threading.Thread(target=self._gaze_voice_loop, daemon=True)
        self._gaze_thread.start()
        
        # Start wake word monitoring thread  
        self._wake_thread = threading.Thread(target=self._wake_word_loop, daemon=True)
        self._wake_thread.start()
        
        # Start button monitoring thread
        self._button_thread = threading.Thread(target=self._button_loop, daemon=True)
        self._button_thread.start()
        
        # Start event processing thread
        self._process_thread = threading.Thread(target=self._event_processor, daemon=True)
        self._process_thread.start()
        
        print("[VoiceActivation] All threads started")
    
    def stop(self):
        """Stop the voice activation system"""
        self._running = False
        print("[VoiceActivation] Stopping...")
    
    def _gaze_voice_loop(self):
        """Monitor for gaze + voice activation"""
        while self._running:
            try:
                # Check if user is looking at phone (using front camera)
                looking = self._detect_gaze()
                
                if looking:
                    # User is looking - listen for voice
                    voice_detected = self._detect_voice()
                    if voice_detected:
                        self._trigger_activation(ActivationMethod.GAZE_VOICE, 0.9,
                                                {"gaze_confidence": 0.8})
                
                time.sleep(0.5)  # Check every 500ms
                
            except Exception as e:
                print(f"[VoiceActivation] Gaze loop error: {e}")
                time.sleep(1)
    
    def _wake_word_loop(self):
        """Monitor for wake word activation"""
        while self._running:
            try:
                # Use Whisper or similar for wake word detection
                # For now, use a simple keyword spotting approach
                audio_chunk = self._capture_audio_chunk(duration=1.0)
                
                if audio_chunk:
                    text = self._transcribe_short(audio_chunk)
                    if text:
                        for wake_word in self.wake_words:
                            if wake_word in text.lower():
                                self._trigger_activation(ActivationMethod.WAKE_WORD, 0.85,
                                                        {"detected_text": text})
                                break
                
                time.sleep(1.0)  # Check every second
                
            except Exception as e:
                print(f"[VoiceActivation] Wake word loop error: {e}")
                time.sleep(1)
    
    def _button_loop(self):
        """Monitor for double-tap side button activation"""
        last_press = 0
        
        while self._running:
            try:
                # Check if power button was pressed
                # Using dumpsys to monitor key events
                result = self._ssh("dumpsys input | grep -i 'power\|keyevent' | tail -5", timeout=2)
                
                current_time = time.time()
                
                # Simple double-tap detection (would need more sophisticated approach in production)
                if "KEYCODE_POWER" in str(result):
                    time_since_last = current_time - last_press
                    
                    if 0 < time_since_last < self._double_tap_window:
                        # Double-tap detected!
                        self._trigger_activation(ActivationMethod.DOUBLE_TAP, 0.95,
                                                {"tap_interval": time_since_last})
                    
                    last_press = current_time
                
                time.sleep(0.1)  # Check every 100ms
                
            except Exception as e:
                # Silent fail - button detection is best-effort
                time.sleep(0.1)
    
    def _detect_gaze(self) -> bool:
        """Detect if user is looking at the phone using front camera"""
        # This would ideally use face/gaze detection library
        # For now, simple check: capture front camera and detect if face present
        try:
            # Capture front camera image
            result = self._ssh("timeout 2 termux-camera-photo -c 1 /sdcard/gaze_check.jpg 2>/dev/null", timeout=3)
            if not result:
                return False
            
            # TODO: Add actual gaze detection using OpenCV or similar
            # For now, assume if camera works, user might be looking
            return True
            
        except Exception as e:
            return False
    
    def _detect_voice(self) -> bool:
        """Detect if voice is present (above noise floor)"""
        try:
            # Record short audio chunk and check amplitude
            result = self._ssh("termux-microphone-record -f /sdcard/.voice_check.wav -l 0.5 2>/dev/null", timeout=2)
            if result:
                # Check file size as proxy for voice presence
                size_result = self._ssh("stat -c%s /sdcard/.voice_check.wav 2>/dev/null")
                if size_result:
                    size = int(str(size_result).strip())
                    return size > 1000  # More than ~10ms of audio
            return False
        except:
            return False
    
    def _capture_audio_chunk(self, duration: float) -> Optional[bytes]:
        """Capture a short audio chunk for processing"""
        try:
            # Record to temp file
            self._ssh(f"termux-microphone-record -f /sdcard/.chunk.wav -l {int(duration)} 2>/dev/null")
            
            # Download the file
            result = subprocess.run([
                "scp", "-i", self.ssh_key,
                "-P", str(self.ssh_port),
                "-o", "StrictHostKeyChecking=no",
                f"{self.ssh_user}@{self.device_ip}:/sdcard/.chunk.wav",
                "/tmp/chunk.wav"
            ], capture_output=True, timeout=5)
            
            if result.returncode == 0:
                with open("/tmp/chunk.wav", "rb") as f:
                    return f.read()
            return None
        except:
            return None
    
    def _transcribe_short(self, audio_data: bytes) -> str:
        """Transcribe short audio chunk (for wake word detection)"""
        # Use Whisper or similar - for now, placeholder
        # In production, use a lightweight model like whisper-tiny
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_data)
                temp_path = f.name
            
            # Use faster-whisper or similar for quick transcription
            # This is a placeholder - would integrate actual STT
            return ""  # Placeholder
            
        except Exception as e:
            print(f"[VoiceActivation] Transcription error: {e}")
            return ""
    
    def _trigger_activation(self, method: ActivationMethod, confidence: float, metadata: dict):
        """Trigger an activation event"""
        # Check cooldown
        if time.time() - self._last_activation_time < self._cooldown_period:
            return
        
        self._last_activation_time = time.time()
        event = ActivationEvent(method=method, confidence=confidence, 
                               timestamp=time.time(), metadata=metadata)
        self._activation_queue.put(event)
        
        print(f"[VoiceActivation] ACTIVATED via {method.value} (confidence: {confidence:.2f})")
        
        # Trigger callback if set
        if self.callback:
            try:
                self.callback(event)
            except Exception as e:
                print(f"[VoiceActivation] Callback error: {e}")
    
    def _event_processor(self):
        """Process activation events in background"""
        while self._running:
            try:
                event = self._activation_queue.get(timeout=1.0)
                
                # Start voice recording for command
                print(f"[VoiceActivation] Processing {event.method.value} activation...")
                
                # TODO: Integrate with main assistant loop
                # This would trigger the speech-to-text -> LLM -> TTS pipeline
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[VoiceActivation] Event processor error: {e}")
    
    def _ssh(self, command: str, timeout: int = 10) -> bool:
        """Execute a command via SSH"""
        try:
            result = subprocess.run([
                "ssh", "-i", self.ssh_key,
                "-p", str(self.ssh_port),
                "-o", "StrictHostKeyChecking=no",
                "-o", "ConnectTimeout=5",
                f"{self.ssh_user}@{self.device_ip}",
                command
            ], capture_output=True, timeout=timeout)
            return result.returncode == 0
        except:
            return False
    
    def get_pending_activations(self) -> list:
        """Get pending activation events"""
        events = []
        try:
            while True:
                events.append(self._activation_queue.get_nowait())
        except queue.Empty:
            pass
        return events
