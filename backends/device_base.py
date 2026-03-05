#!/usr/bin/env python3
"""
Universal Device Backend Abstraction
Provides a common interface for different device types:
- Termux Android (physical phones with Termux)
- Standard Android (via ADB only)
- Emulators (Android Studio, Genymotion, Waydroid)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import subprocess
import time


@dataclass
class DeviceConfig:
    """Configuration for a phone device"""
    name: str
    device_type: str  # 'termux', 'adb', 'emulator'
    ip_address: Optional[str] = None
    ssh_port: int = 8022
    adb_port: int = 5555
    ssh_key: Optional[str] = None
    ssh_user: str = "droid"
    screen_pin: Optional[str] = None
    camera_path: str = "/sdcard/senter_gaze.jpg"
    audio_input_path: str = "/sdcard/senter_in.wav"
    audio_output_path: str = "/sdcard/senter_out.wav"


class DeviceBackend(ABC):
    """Abstract base class for device backends"""
    
    def __init__(self, config: DeviceConfig):
        self.config = config
    
    @abstractmethod
    def capture_camera(self) -> bool:
        """Capture a photo from the front camera"""
        pass
    
    @abstractmethod
    def record_audio(self, duration: int, output_path: str) -> bool:
        """Record audio for specified duration in seconds"""
        pass
    
    @abstractmethod
    def play_audio(self, audio_path: str) -> bool:
        """Play an audio file through the device speaker"""
        pass
    
    @abstractmethod
    def wake_screen(self) -> bool:
        """Wake up the device screen if sleeping"""
        pass
    
    @abstractmethod
    def unlock_screen(self, pin: Optional[str] = None) -> bool:
        """Unlock the device screen with PIN if needed"""
        pass
    
    @abstractmethod
    def is_online(self) -> bool:
        """Check if device is reachable"""
        pass
    
    @abstractmethod
    def type_text(self, text: str) -> bool:
        """Type text on the device"""
        pass


def create_backend(config: DeviceConfig) -> DeviceBackend:
    """Factory function to create appropriate backend based on device type"""
    if config.device_type == "termux":
        from .termux_backend import TermuxBackend
        return TermuxBackend(config)
    elif config.device_type == "adb":
        from .adb_backend import ADBBackend
        return ADBBackend(config)
    elif config.device_type == "emulator":
        from .emulator_backend import EmulatorBackend
        return EmulatorBackend(config)
    else:
        raise ValueError(f"Unknown device type: {config.device_type}")


def detect_device_type(ip_address: str, ssh_port: int = 8022) -> Optional[str]:
    """Auto-detect device type by testing connectivity and capabilities"""
    # Try SSH first (Termux)
    try:
        result = subprocess.run([
            "ssh", "-i", f"~/.ssh/phone_access",
            "-p", str(ssh_port),
            "-o", "ConnectTimeout=2",
            "-o", "BatchMode=yes",
            f"droid@{ip_address}",
            "which termux-camera-photo"
        ], capture_output=True, timeout=5)
        
        if result.returncode == 0:
            return "termux"
    except:
        pass
    
    # Try ADB
    try:
        result = subprocess.run([
            "adb", "connect", f"{ip_address}:5555"
        ], capture_output=True, timeout=10)
        
        if b"connected" in result.stdout.lower() or b"already" in result.stdout.lower():
            return "adb"
    except:
        pass
    
    return None