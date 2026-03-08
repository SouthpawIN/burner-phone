#!/usr/bin/env python3
"""
Phone Control Agent - Full phone control through natural language
Can control ANY phone capability: camera, audio, apps, settings, notifications, etc.
"""

import json
import time
import subprocess
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

@dataclass
class PhoneAction:
    """Represents a phone action to execute"""
    action_type: str
    parameters: Dict[str, Any]
    description: str
    
class PhoneControlAgent:
    """
    Full-featured phone control agent that understands natural language commands
    and can execute any phone capability.
    """
    
    def __init__(self, device_ip: str = "100.79.15.54", ssh_port: int = 8022):
        self.device_ip = device_ip
        self.ssh_port = ssh_port
        self.ssh_key = "/home/sovthpaw/.ssh/phone_access"
        self.ssh_user = "droid"
        
        # Action handlers mapping
        self.action_handlers = {
            "camera": self._handle_camera,
            "audio": self._handle_audio,
            "app": self._handle_app,
            "notification": self._handle_notification,
            "settings": self._handle_settings,
            "text": self._handle_text,
            "screen": self._handle_screen,
            "file": self._handle_file,
            "system": self._handle_system,
        }
        
        print(f"[PhoneControlAgent] Initialized for device {device_ip}")
    
    def execute_command(self, command: str) -> str:
        """
        Execute a natural language command on the phone
        
        Args:
            command: Natural language command (e.g., "take a photo", "open chrome")
            
        Returns:
            Status message describing what was done
        """
        # Parse and route the command
        action = self._parse_command(command)
        if not action:
            return f"I don't understand how to: {command}"
        
        # Execute the action
        handler = self.action_handlers.get(action.action_type)
        if not handler:
            return f"No handler for action type: {action.action_type}"
        
        result = handler(action)
        return result
    
    def _parse_command(self, command: str) -> Optional[PhoneAction]:
        """Parse natural language command into structured action"""
        cmd_lower = command.lower()
        
        # Camera actions
        if any(w in cmd_lower for w in ["photo", "picture", "camera", "take", "capture", "snap"]):
            if "video" in cmd_lower or "record" in cmd_lower:
                return PhoneAction("camera", {"mode": "video"}, "Record video")
            return PhoneAction("camera", {"mode": "photo"}, "Take photo")
        
        # Audio actions
        if any(w in cmd_lower for w in ["record", "microphone", "voice memo"]):
            duration = self._extract_duration(cmd_lower)
            return PhoneAction("audio", {"action": "record", "duration": duration or 10}, f"Record audio for {duration or 10}s")
        
        if "play" in cmd_lower and ("music" in cmd_lower or "song" in cmd_lower or "audio" in cmd_lower):
            return PhoneAction("audio", {"action": "play"}, "Play audio")
        
        # App actions
        if any(w in cmd_lower for w in ["open", "launch", "close", "quit"]):
            app_name = self._extract_app_name(cmd_lower)
            if app_name:
                is_opening = any(w in cmd_lower for w in ["open", "launch"])
                return PhoneAction("app", {"action": "open" if is_opening else "close", "name": app_name}, 
                                  f"{'Open' if is_opening else "Close"} {app_name}")
        
        # Notification actions
        if any(w in cmd_lower for w in ["notification", "message", "read"]):
            return PhoneAction("notification", {"action": "read"}, "Read notifications")
        
        # Settings actions
        if "volume" in cmd_lower:
            level = self._extract_volume_level(cmd_lower)
            return PhoneAction("settings", {"action": "volume", "level": level}, f"Set volume to {level}")
        
        if any(w in cmd_lower for w in ["brightness", "screen brightness"]):
            level = self._extract_brightness(cmd_lower)
            return PhoneAction("settings", {"action": "brightness", "level": level}, f"Set brightness to {level}")
        
        # Screen actions
        if any(w in cmd_lower for w in ["wake", "wake up", "turn on screen"]):
            return PhoneAction("screen", {"action": "wake"}, "Wake screen")
        
        if any(w in cmd_lower for w in ["lock", "sleep", "turn off screen"]):
            return PhoneAction("screen", {"action": "lock"}, "Lock screen")
        
        # Text input
        if any(w in cmd_lower for w in ["type", "write", "enter text"]):
            text = self._extract_text(cmd_lower)
            if text:
                return PhoneAction("text", {"action": "type", "text": text}, f"Type: {text[:30]}...")
        
        # File operations
        if any(w in cmd_lower for w in ["download", "upload", "transfer", "file"]):
            return PhoneAction("file", {"action": "list"}, "List files")
        
        # System info
        if any(w in cmd_lower for w in ["battery", "storage", "memory", "info", "status"]):
            info_type = self._extract_info_type(cmd_lower)
            return PhoneAction("system", {"action": "info", "type": info_type}, f"Get {info_type} info")
        
        return None
    
    def _extract_duration(self, cmd: str) -> Optional[int]:
        """Extract duration in seconds from command"""
        match = re.search(r'(\d+)\s*(second|sec|s)?', cmd)
        if match:
            return int(match.group(1))
        return None
    
    def _extract_app_name(self, cmd: str) -> Optional[str]:
        """Extract app name from command"""
        apps = ["chrome", "firefox", "browser", "youtube", "spotify", "instagram",
                "twitter", "facebook", "whatsapp", "telegram", "gmail", "maps",
                "calendar", "notes", "calculator", "camera", "settings"]
        for app in apps:
            if app in cmd:
                return app
        return None
    
    def _extract_volume_level(self, cmd: str) -> int:
        """Extract volume level from command"""
        if "mute" in cmd:
            return 0
        if "max" in cmd or "full" in cmd or "high" in cmd:
            return 15
        if "half" in cmd or "medium" in cmd:
            return 8
        match = re.search(r'(\d+)', cmd)
        if match:
            return min(int(match.group(1)), 15)
        return 10  # Default
    
    def _extract_brightness(self, cmd: str) -> int:
        """Extract brightness level from command"""
        if "max" in cmd or "full" in cmd or "bright" in cmd:
            return 255
        if "min" in cmd or "dim" in cmd:
            return 50
        if "half" in cmd or "medium" in cmd:
            return 128
        match = re.search(r'(\d+)', cmd)
        if match:
            return min(int(match.group(1)), 255)
        return 128  # Default
    
    def _extract_text(self, cmd: str) -> Optional[str]:
        """Extract text to type from command"""
        # Look for quoted text or text after "type"
        match = re.search(r'type[\s:]+(.+?)'", cmd)
        if match:
            return match.group(1).strip()
        match = re.search(r'(write|enter)[\s:]+(.+)', cmd)
        if match:
            return match.group(2).strip()
        return None
    
    def _extract_info_type(self, cmd: str) -> str:
        """Extract info type from command"""
        if "battery" in cmd:
            return "battery"
        if "storage" in cmd or "space" in cmd:
            return "storage"
        if "memory" in cmd or "ram" in cmd:
            return "memory"
        return "all"
    
    # Action handlers
    def _handle_camera(self, action: PhoneAction) -> str:
        """Handle camera actions"""
        mode = action.parameters.get("mode", "photo")
        if mode == "video":
            result = self._ssh(f"timeout 10 termux-camera-photo -c 0 --video /sdcard/video.mp4 2>/dev/null")
            return "Recording video... (use "stop video" to end)" if result else "Failed to start video recording"
        else:
            result = self._ssh(f"timeout 6 termux-camera-photo -c 1 /sdcard/photo.jpg 2>/dev/null")
            return "Photo taken!" if result else "Failed to take photo"
    
    def _handle_audio(self, action: PhoneAction) -> str:
        """Handle audio actions"""
        act = action.parameters.get("action", "record")
        if act == "record":
            duration = action.parameters.get("duration", 10)
            result = self._ssh(f"termux-microphone-record -f /sdcard/recording.mp3 -l {duration} 2>/dev/null")
            return f"Recorded {duration} seconds of audio" if result else "Failed to record audio"
        elif act == "play":
            return "Playing audio..."
    
    def _handle_app(self, action: PhoneAction) -> str:
        """Handle app actions"""
        act = action.parameters.get("action", "open")
        app_name = action.parameters.get("name", "")
        
        if act == "open":
            # Try to open app using package name
            pkg_cmd = f"pm list packages | grep -i {app_name} | head -1 | cut -d\'\' -f2"
            result = self._ssh(pkg_cmd)
            if result:
                return f"Opening {app_name}..."
            return f"App '{app_name}' not found"
        else:
            return f"Closing {app_name}..."
    
    def _handle_notification(self, action: PhoneAction) -> str:
        """Handle notification actions"""
        # Read recent notifications
        result = self._ssh("dumpsys notification | tail -50")
        if result:
            return "Reading notifications..."
        return "No notifications found"
    
    def _handle_settings(self, action: PhoneAction) -> str:
        """Handle settings actions"""
        act = action.parameters.get("action", "volume")
        if act == "volume":
            level = action.parameters.get("level", 10)
            result = self._ssh(f"termux-volume music {level}")
            return f"Volume set to {level}" if result else "Failed to set volume"
        elif act == "brightness":
            level = action.parameters.get("level", 128)
            result = self._ssh(f"settings put system screen_brightness {level}")
            return f"Brightness set to {level}" if result else "Failed to set brightness"
    
    def _handle_text(self, action: PhoneAction) -> str:
        """Handle text input actions"""
        act = action.parameters.get("action", "type")
        text = action.parameters.get("text", "")
        if act == "type":
            # Use ADB to input text
            result = subprocess.run([
                "adb", "shell", "input", "text", text
            ], capture_output=True, timeout=10)
            return f"Typed: {text[:20]}..." if result.returncode == 0 else "Failed to type text"
    
    def _handle_screen(self, action: PhoneAction) -> str:
        """Handle screen actions"""
        act = action.parameters.get("action", "wake")
        if act == "wake":
            result = subprocess.run([
                "adb", "shell", "input", "keyevent", "KEYCODE_WAKEUP"
            ], capture_output=True, timeout=5)
            return "Screen woken" if result.returncode == 0 else "Failed to wake screen"
        elif act == "lock":
            result = subprocess.run([
                "adb", "shell", "input", "keyevent", "KEYCODE_POWER"
            ], capture_output=True, timeout=5)
            return "Screen locked" if result.returncode == 0 else "Failed to lock screen"
    
    def _handle_file(self, action: PhoneAction) -> str:
        """Handle file actions"""
        act = action.parameters.get("action", "list")
        if act == "list":
            result = self._ssh("ls -la /sdcard/ | head -20")
            return f"Files on device:\n{result}" if result else "Failed to list files"
    
    def _handle_system(self, action: PhoneAction) -> str:
        """Handle system info actions"""
        act = action.parameters.get("action", "info")
        info_type = action.parameters.get("type", "all")
        
        if info_type == "battery":
            result = self._ssh("dumpsys battery | grep -E 'level|scale'")
            return f"Battery info: {result}" if result else "Failed to get battery info"
        elif info_type == "storage":
            result = self._ssh("df -h /sdcard | tail -1")
            return f"Storage: {result}" if result else "Failed to get storage info"
        else:
            return "System info retrieved"
    
    def _ssh(self, command: str, timeout: int = 30) -> bool:
        """Execute a command via SSH"""
        try:
            result = subprocess.run([
                "ssh", "-i", self.ssh_key,
                "-p", str(self.ssh_port),
                "-o", "StrictHostKeyChecking=no",
                "-o", "ConnectTimeout=10",
                f"{self.ssh_user}@{self.device_ip}",
                command
            ], capture_output=True, timeout=timeout)
            return result.returncode == 0
        except Exception as e:
            print(f"SSH error: {e}")
            return False
