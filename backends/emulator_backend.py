#!/usr/bin/env python3
"""Emulator Backend - For Android emulators (Android Studio, Genymotion, Waydroid)"""

import subprocess
import time
from pathlib import Path
from .device_base import DeviceBackend, DeviceConfig


class EmulatorBackend(DeviceBackend):
    """Backend for Android emulators"""
    
    def __init__(self, config: DeviceConfig):
        super().__init__(config)
        # Emulators typically run on localhost
        self.emulator_addr = f"{config.ip_address or 'localhost'}:{config.adb_port or 5555}"
    
    def _adb_emu(self, command: str, timeout: int = 30) -> bool:
        """Execute ADB command targeting emulator"""
        try:
            result = subprocess.run([
                "adb", "-s", self.emulator_addr, "shell"
            ] + command.split(), capture_output=True, timeout=timeout)
            return result.returncode == 0
        except Exception as e:
            print(f"ADB emulator error: {e}")
            return False
    
    def _adb_push(self, local_path: str, remote_path: str) -> bool:
        """Push file to emulator"""
        try:
            result = subprocess.run([
                "adb", "-s", self.emulator_addr, "push", local_path, remote_path
            ], capture_output=True, timeout=30)
            return result.returncode == 0
        except Exception as e:
            print(f"Emulator push error: {e}")
            return False
    
    def _adb_pull(self, remote_path: str, local_path: str) -> bool:
        """Pull file from emulator"""
        try:
            result = subprocess.run([
                "adb", "-s", self.emulator_addr, "pull", remote_path, local_path
            ], capture_output=True, timeout=30)
            return result.returncode == 0
        except Exception as e:
            print(f"Emulator pull error: {e}")
            return False
    
    def capture_camera(self) -> bool:
        """Capture emulator camera or screen"""
        # Emulators have virtual cameras - try to access front camera
        try:
            # Try screencap first (most reliable)
            result = subprocess.run([
                "adb", "-s", self.emulator_addr,
                "shell", "screencap", "-p", "/sdcard/senter_gaze.jpg"
            ], capture_output=True, timeout=10)
            
            if result.returncode != 0:
                return False
            
            return self._adb_pull("/sdcard/senter_gaze.jpg", self.config.camera_path)
        except Exception as e:
            print(f"Emulator camera error: {e}")
            return False
    
    def record_audio(self, duration: int, output_path: str) -> bool:
        """Record audio from emulator"""
        try:
            remote_path = f"/sdcard/{Path(output_path).name.replace('.wav', '.mp4')}"
            
            result = subprocess.run([
                "adb", "-s", self.emulator_addr,
                "shell", "screenrecord",
                "--audio",
                f"--time-limit={duration}",
                remote_path
            ], capture_output=True, timeout=duration + 10)
            
            if result.returncode != 0:
                return False
            
            success = self._adb_pull(remote_path, output_path.replace('.wav', '.mp4'))
            
            # Convert to WAV
            if success and output_path.endswith('.wav'):
                convert_result = subprocess.run([
                    "ffmpeg", "-i", output_path.replace('.wav', '.mp4'),
                    "-ar", "16000", "-ac", "1", output_path,
                    "-y"  # Overwrite
                ], capture_output=True, timeout=30)
                
                Path(output_path.replace('.wav', '.mp4')).unlink(missing_ok=True)
                return convert_result.returncode == 0
            
            return success
        except Exception as e:
            print(f"Emulator audio error: {e}")
            return False
    
    def play_audio(self, audio_path: str) -> bool:
        """Play audio on emulator - outputs to host speakers"""
        remote_path = f"/sdcard/{Path(audio_path).name}"
        
        if not self._adb_push(audio_path, remote_path):
            return False
        
        # Play using media player
        success = self._adb_emu(
            f"am start -a android.intent.action.VIEW "
            f"-t audio/* -d file://{remote_path}"
        )
        
        return success
    
    def wake_screen(self) -> bool:
        """Wake emulator screen"""
        return self._adb_emu("input keyevent KEYCODE_WAKEUP")
    
    def unlock_screen(self, pin: Optional[str] = None) -> bool:
        """Unlock emulator - often no lock on emulators"""
        pin = pin or self.config.screen_pin
        if not pin:
            return True
        
        # Check if locked
        result = subprocess.run([
            "adb", "-s", self.emulator_addr, "shell", "dumpsys", "power"
        ], capture_output=True, timeout=5, text=True)
        
        if "mUserActivityTimeoutOverrideSeconds=null" in result.stdout:
            return True
        
        # Enter PIN directly (emulators often skip swipe)
        success = self._adb_emu(f"input text {pin}")
        if not success:
            return False
        
        return self._adb_emu("input keyevent KEYCODE_ENTER")
    
    def is_online(self) -> bool:
        """Check if emulator is running"""
        try:
            result = subprocess.run([
                "adb", "devices"
            ], capture_output=True, timeout=5, text=True)
            
            return self.emulator_addr in result.stdout
        except:
            return False
    
    def type_text(self, text: str) -> bool:
        """Type text on emulator"""
        try:
            escaped = text.replace("\\", "\\\\").replace("\n", "\\n")
            return self._adb_emu(f"input text {escaped}")
        except Exception as e:
            print(f"Emulator type error: {e}")
            return False
    
    def get_emulator_info(self) -> dict:
        """Get emulator-specific information"""
        info = {}
        
        # Get model
        result = subprocess.run([
            "adb", "-s", self.emulator_addr,
            "shell", "getprop", "ro.product.model"
        ], capture_output=True, timeout=5, text=True)
        info['model'] = result.stdout.strip() if result.returncode == 0 else "Unknown"
        
        # Get Android version
        result = subprocess.run([
            "adb", "-s", self.emulator_addr,
            "shell", "getprop", "ro.build.version.release"
        ], capture_output=True, timeout=5, text=True)
        info['android_version'] = result.stdout.strip() if result.returncode == 0 else "Unknown"
        
        return info