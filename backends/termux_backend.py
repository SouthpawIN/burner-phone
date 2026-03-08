#!/usr/bin/env python3
"""Termux Backend - For Android phones with Termux installed (with SSH pooling)"""

import subprocess
import time
from pathlib import Path
from typing import Optional
import io

from .device_base import DeviceBackend, DeviceConfig
from .ssh_pool import SSHConnectionPool


class TermuxBackend(DeviceBackend):
    """Backend for Termux-enabled Android devices with connection pooling"""
    
    def __init__(self, config: DeviceConfig):
        super().__init__(config)
        
        # Initialize SSH connection pool (singleton per host/port)
        self._ssh_pool = SSHConnectionPool(
            host=config.ip_address,
            port=config.ssh_port,
            username=config.ssh_user,
            key_path=str(Path(config.ssh_key).expanduser()),
            max_connections=3,
            idle_timeout=60.0
        )
        
        # Legacy SSH options for ADB commands (can't pool these easily)
        self.ssh_options = [
            "-i", str(Path(config.ssh_key).expanduser()),
            "-p", str(config.ssh_port),
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=10"
        ]
    
    def _ssh(self, command: str, timeout: int = 30) -> bool:
        """Execute a command via SSH using connection pool"""
        try:
            with self._ssh_pool.connection() as client:
                if client is False:
                    return False
                    
                stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
                exit_status = stdout.channel.recv_exit_status()
                
                # Capture output for debugging if needed
                output = stdout.read().decode("utf-8")
                error = stderr.read().decode("utf-8")
                
                return exit_status == 0
                
        except Exception as e:
            print(f"SSH error: {e}")
            return False
    
    def _scp_upload(self, local_path: str, remote_path: str) -> bool:
        """Upload a file via SFTP using connection pool (faster than SCP)"""
        try:
            with self._ssh_pool.connection() as client:
                if client is False:
                    return False
                
                # Use SFTP which works over the existing SSH connection
                sftp = client.open_sftp()
                try:
                    sftp.put(local_path, remote_path)
                    return True
                finally:
                    sftp.close()
                    
        except Exception as e:
            print(f"SFTP upload error: {e}")
            # Fallback to scp if SFTP fails
            return self._scp_upload_fallback(local_path, remote_path)
    
    def _scp_upload_fallback(self, local_path: str, remote_path: str) -> bool:
        """Fallback to traditional SCP if SFTP fails"""
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
        """Download a file via SFTP using connection pool"""
        try:
            with self._ssh_pool.connection() as client:
                if client is False:
                    return False
                
                sftp = client.open_sftp()
                try:
                    sftp.get(remote_path, local_path)
                    return True
                finally:
                    sftp.close()
                    
        except Exception as e:
            print(f"SFTP download error: {e}")
            # Fallback to scp
            return self._scp_download_fallback(remote_path, local_path)
    
    def _scp_download_fallback(self, remote_path: str, local_path: str) -> bool:
        """Fallback to traditional SCP if SFTP fails"""
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
        """Play audio using termux-media-player (backgrounded for speed)"""
        # Upload the audio file
        remote_path = f"/sdcard/{Path(audio_path).name}"
        if not self._scp_upload(audio_path, remote_path):
            return False
        
        # Set volume and play in background (non-blocking)
        success = self._ssh(
            f"termux-volume music 15 && nohup termux-media-player play {remote_path} >/dev/null 2>&1 &",
            timeout=5  # Much shorter timeout since we're not waiting for playback
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
            return True
        
        try:
            result = subprocess.run([
                "adb", "shell", "dumpsys", "power"
            ], capture_output=True, timeout=5, text=True)
            
            if "mUserActivityTimeoutOverrideSeconds=null" in result.stdout:
                return True
            
            # Swipe up to unlock
            subprocess.run([
                "adb", "shell", "input", "swipe", "500", "1000", "500", "200", "100"
            ], capture_output=True, timeout=2)
            
            # Enter PIN
            for digit in str(pin):
                subprocess.run([
                    "adb", "shell", "input", "text", digit
                ], capture_output=True, timeout=1)
            
            return True
        except Exception as e:
            print(f"ADB unlock error: {e}")
            return False
    
    def type_text(self, text: str) -> bool:
        """Type text using ADB"""
        try:
            result = subprocess.run([
                "adb", "shell", "input", "text", text
            ], capture_output=True, timeout=10)
            return result.returncode == 0
        except Exception as e:
            print(f"ADB type error: {e}")
            return False
    
    def is_online(self) -> bool:
        """Check if device is online using connection pool"""
        try:
            with self._ssh_pool.connection() as client:
                if client is False:
                    return False
                stdin, stdout, stderr = client.exec_command("true")
                return stdout.channel.recv_exit_status() == 0
        except:
            return False
    
    def get_pool_stats(self) -> dict:
        """Get connection pool statistics"""
        return self._ssh_pool.stats()
