#!/usr/bin/env python3
"""Termux Backend - For Android phones with Termux installed"""

import subprocess
import time
from pathlib import Path
from .device_base import DeviceBackend, DeviceConfig


class TermuxBackend(DeviceBackend):
    """Backend for Termux-enabled Android devices"""
    
    def __init__(self, config: DeviceConfig):
        super().__init__(config)
        self.ssh_options = [
            "-i", str(Path(config.ssh_key).expanduser()),
            "-p", str(config.ssh_port),
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=10"
        ]
    
    def _ssh(self, command: str, timeout: int = 30) -> bool:
        """Execute a command via SSH"""
        try:
            result = subprocess.run([
                "ssh"
            ] + self.ssh_options + [
                f"{self.config.ssh_user}@{self.config.ip_address}",
                command
            ], capture_output=True, timeout=timeout)
            return result.returncode == 0
        except Exception as e:
            print(f"SSH error: {e}")
            return False
    
    def _scp_upload(self, local_path: str, remote_path: str) -> bool:
        """Upload a file via SCP"""
        try:
            result = subprocess.run([
                "scp", "-i", str(Path(self.config.ssh_key).expanduser()),
                "-P", str(self.config.ssh_port),
                "-o", "StrictHostKeyChecking=no",
                local_path,
                f"{self.config.ssh_user}@{self.config.ip_address}:{remote_path}"
            ], capture_output=True, timeout=30)
            return result.returncode == 0
        except Exception as e:
            print(f"SCP error: {e}")
            return False
    
    def _scp_download(self, remote_path: str, local_path: str) -> bool:
        """Download a file via SCP"""
        try:
            result = subprocess.run([
                "scp", "-i", str(Path(self.config.ssh_key).expanduser()),
                "-P", str(self.config.ssh_port),
                "-o", "StrictHostKeyChecking=no",
                f"{self.config.ssh_user}@{self.config.ip_address}:{remote_path}",
                local_path
            ], capture_output=True, timeout=30)
            return result.returncode == 0
        except Exception as e:
            print(f"SCP download error: {e}")
            return False
    
    def capture_camera(self) -> bool:
        """Capture photo using termux-camera-photo"""
        # Try to capture with timeout
        success = self._ssh(
            f"timeout 6 termux-camera-photo -c 1 {self.config.camera_path} 2>/dev/null",
            timeout=10
        )
        return success
    
    def record_audio(self, duration: int, output_path: str) -> bool:
        """Record audio using termux-microphone-record"""
        remote_path = f"/sdcard/{Path(output_path).name}"
        success = self._ssh(
            f"termux-microphone-record -f {remote_path} -l {duration} 2>/dev/null",
            timeout=duration + 5
        )
        if success:
            return self._scp_download(remote_path, output_path)
        return False
    
    def play_audio(self, audio_path: str) -> bool:
        """Play audio using termux-media-player"""
        # Upload the audio file
        remote_path = f"/sdcard/{Path(audio_path).name}"
        if not self._scp_upload(audio_path, remote_path):
            return False
        
        # Set volume and play
        success = self._ssh(
            f"termux-volume music 15 && termux-media-player play {remote_path}",
            timeout=30
        )
        return success
    
    def wake_screen(self) -> bool:
        """Wake screen using ADB"""
        try:
            result = subprocess.run([
                "adb", "connect", f"{self.config.ip_address}:5555"
            ], capture_output=True, timeout=10)
            
            if b"connected" not in result.stdout.lower():
                return False
            
            # Wake the device
            result = subprocess.run([
                "adb", "shell", "input", "keyevent", "KEYCODE_WAKEUP"
            ], capture_output=True, timeout=5)
            
            return result.returncode == 0
        except Exception as e:
            print(f"ADB wake error: {e}")
            return False
    
    def unlock_screen(self, pin: Optional[str] = None) -> bool:
        """Unlock screen with PIN using ADB"""
        pin = pin or self.config.screen_pin
        if not pin:
            return True  # No PIN required
        
        try:
            # Check if locked
            result = subprocess.run([
                "adb", "shell", "dumpsys", "power"
            ], capture_output=True, timeout=5, text=True)
            
            if "mUserActivityTimeoutOverrideSeconds=null" in result.stdout:
                # Already unlocked
                return True
            
            # Swipe up to unlock screen
            subprocess.run([
                "adb", "shell", "input", "swipe", "500", "1500", "500", "500"
            ], capture_output=True, timeout=5)
            time.sleep(0.5)
            
            # Enter PIN
            result = subprocess.run([
                "adb", "shell", "input", "text", pin
            ], capture_output=True, timeout=5)
            
            if result.returncode != 0:
                return False
            
            # Press enter
            subprocess.run([
                "adb", "shell", "input", "keyevent", "KEYCODE_ENTER"
            ], capture_output=True, timeout=5)
            
            return True
        except Exception as e:
            print(f"Unlock error: {e}")
            return False
    
    def is_online(self) -> bool:
        """Check if device is reachable via SSH"""
        try:
            result = subprocess.run([
                "ssh"
            ] + self.ssh_options + [
                f"{self.config.ssh_user}@{self.config.ip_address}",
                "echo ok"
            ], capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def type_text(self, text: str) -> bool:
        """Type text using ADB input"""
        try:
            # Escape special characters
            escaped = text.replace("\\", "\\\\").replace("\n", "\\n")
            result = subprocess.run([
                "adb", "shell", "input", "text", escaped
            ], capture_output=True, timeout=10)
            return result.returncode == 0
        except Exception as e:
            print(f"Type text error: {e}")
            return False