#!/usr/bin/env python3
"""ADB Backend - For standard Android devices via ADB only"""

import subprocess
import time
import tempfile
from pathlib import Path
from typing import Optional
from .device_base import DeviceBackend, DeviceConfig


class ADBBackend(DeviceBackend):
    """Backend for standard Android devices using ADB only"""
    
    def __init__(self, config: DeviceConfig):
        super().__init__(config)
        self.connected = False
    
    def _ensure_connected(self) -> bool:
        """Ensure ADB connection is established"""
        if self.connected:
            return True
        
        try:
            result = subprocess.run([
                "adb", "connect", f"{self.config.ip_address}:5555"
            ], capture_output=True, timeout=15, text=True)
            
            if b"connected" in result.stdout.lower() or b"already" in result.stdout.lower():
                self.connected = True
                return True
            else:
                print(f"ADB connect failed: {result.stdout}")
                return False
        except Exception as e:
            print(f"ADB connection error: {e}")
            return False
    
    def _adb_shell(self, command: str, timeout: int = 30) -> bool:
        """Execute a shell command via ADB"""
        if not self._ensure_connected():
            return False
        
        try:
            result = subprocess.run([
                "adb", "shell"
            ] + command.split(), capture_output=True, timeout=timeout)
            return result.returncode == 0
        except Exception as e:
            print(f"ADB shell error: {e}")
            return False
    
    def _adb_push(self, local_path: str, remote_path: str) -> bool:
        """Push a file via ADB"""
        if not self._ensure_connected():
            return False
        
        try:
            result = subprocess.run([
                "adb", "push", local_path, remote_path
            ], capture_output=True, timeout=30)
            return result.returncode == 0
        except Exception as e:
            print(f"ADB push error: {e}")
            return False
    
    def _adb_pull(self, remote_path: str, local_path: str) -> bool:
        """Pull a file via ADB"""
        if not self._ensure_connected():
            return False
        
        try:
            result = subprocess.run([
                "adb", "pull", remote_path, local_path
            ], capture_output=True, timeout=30)
            return result.returncode == 0
        except Exception as e:
            print(f"ADB pull error: {e}")
            return False
    
    def capture_camera(self) -> bool:
        """Capture screen using adb screencap (front camera not directly accessible via ADB)"""
        # Note: Direct front camera access requires an app or Termux
        # Using screencap as fallback - user should have camera feed on screen
        if not self._ensure_connected():
            return False
        
        try:
            # Capture screen
            result = subprocess.run([
                "adb", "shell", "screencap", "-p", "/sdcard/senter_gaze.jpg"
            ], capture_output=True, timeout=10)
            
            if result.returncode != 0:
                return False
            
            # Pull the image
            return self._adb_pull(
                "/sdcard/senter_gaze.jpg",
                self.config.camera_path
            )
        except Exception as e:
            print(f"Camera capture error: {e}")
            return False
    
    def record_audio(self, duration: int, output_path: str) -> bool:
        """Record audio - requires screen recording with audio"""
        # ADB screenrecord can capture audio on Android 10+
        if not self._ensure_connected():
            return False
        
        remote_path = f"/sdcard/{Path(output_path).name.replace('.wav', '.mp4')}"
        
        try:
            result = subprocess.run([
                "adb", "shell", "screenrecord",
                "--audio",
                f"--time-limit={duration}",
                remote_path
            ], capture_output=True, timeout=duration + 10)
            
            if result.returncode != 0:
                return False
            
            # Pull the recording
            success = self._adb_pull(remote_path, output_path.replace('.wav', '.mp4'))
            
            # Convert to WAV if needed
            if success and output_path.endswith('.wav'):
                import subprocess
                convert_result = subprocess.run([
                    "ffmpeg", "-i", output_path.replace('.wav', '.mp4'),
                    "-ar", "16000", "-ac", "1", output_path
                ], capture_output=True, timeout=30)
                
                # Clean up MP4
                Path(output_path.replace('.wav', '.mp4')).unlink(missing_ok=True)
                
                return convert_result.returncode == 0
            
            return success
        except Exception as e:
            print(f"Audio recording error: {e}")
            return False
    
    def play_audio(self, audio_path: str) -> bool:
        """Play audio - push file and use media scanner"""
        if not self._ensure_connected():
            return False
        
        remote_path = f"/sdcard/{Path(audio_path).name}"
        
        # Push the audio file
        if not self._adb_push(audio_path, remote_path):
            return False
        
        # Try to play using media player
        # This may require user interaction depending on Android version
        success = self._adb_shell(
            f"am start -a android.intent.action.VIEW "
            f"-t audio/* -d file://{remote_path}"
        )
        
        return success
    
    def wake_screen(self) -> bool:
        """Wake screen using ADB"""
        if not self._ensure_connected():
            return False
        
        return self._adb_shell("input keyevent KEYCODE_WAKEUP")
    
    def unlock_screen(self, pin: Optional[str] = None) -> bool:
        """Unlock screen with PIN using ADB"""
        pin = pin or self.config.screen_pin
        if not pin:
            return True
        
        if not self._ensure_connected():
            return False
        
        # Check lock state
        result = subprocess.run([
            "adb", "shell", "dumpsys", "power"
        ], capture_output=True, timeout=5, text=True)
        
        if "mUserActivityTimeoutOverrideSeconds=null" in result.stdout:
            return True  # Already unlocked
        
        # Swipe up
        self._adb_shell("input swipe 500 1500 500 500")
        time.sleep(0.5)
        
        # Enter PIN
        success = self._adb_shell(f"input text {pin}")
        if not success:
            return False
        
        # Press enter
        return self._adb_shell("input keyevent KEYCODE_ENTER")
    
    def is_online(self) -> bool:
        """Check if device is reachable via ADB"""
        try:
            result = subprocess.run([
                "adb", "connect", f"{self.config.ip_address}:5555"
            ], capture_output=True, timeout=10, text=True)
            
            return b"connected" in result.stdout.lower() or b"already" in result.stdout.lower()
        except:
            return False
    
    def type_text(self, text: str) -> bool:
        """Type text using ADB input"""
        if not self._ensure_connected():
            return False
        
        try:
            escaped = text.replace("\\", "\\\\").replace("\n", "\\n")
            return self._adb_shell(f"input text {escaped}")
        except Exception as e:
            print(f"Type text error: {e}")
            return False