#!/usr/bin/env python3
"""
Universal Phone Agent - Main Interface
Provides unified control over Android devices regardless of backend (Termux, ADB, Emulator)
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from backends.device_base import DeviceConfig, create_backend, detect_device_type
from config.device_config import load_config


class PhoneAgent:
    """
    Universal Phone Agent Interface
    
    Usage:
        agent = PhoneAgent()  # Uses default config
        agent.capture_camera()
        agent.record_audio(5)
        agent.play_audio("output.wav")
    """
    
    def __init__(self, config_path: str = None, device_config: DeviceConfig = None):
        """
        Initialize phone agent
        
        Args:
            config_path: Path to YAML config file (optional)
            device_config: DeviceConfig object (optional, overrides config_path)
        """
        # Load configuration
        if device_config:
            self.config = device_config
        else:
            self.config = load_config(config_path)
        
        # Create appropriate backend
        self.device = create_backend(self.config)
        
        print(f"📱 PhoneAgent initialized: {self.config.name} ({self.config.device_type})")
    
    def capture_camera(self, output_path: str = None) -> bool:
        """
        Capture photo from front camera
        
        Args:
            output_path: Where to save the image (default: config.camera_path)
            
        Returns:
            bool: Success status
        """
        path = output_path or self.config.camera_path
        print(f"📷 Capturing camera...")
        return self.device.capture_camera()
    
    def record_audio(self, duration: int, output_path: str = None) -> bool:
        """
        Record audio for specified duration
        
        Args:
            duration: Recording duration in seconds
            output_path: Where to save audio file
            
        Returns:
            bool: Success status
        """
        path = output_path or self.config.audio_input_path
        print(f"🎤 Recording audio for {duration} seconds...")
        return self.device.record_audio(duration, path)
    
    def play_audio(self, audio_path: str) -> bool:
        """
        Play audio file through device speaker
        
        Args:
            audio_path: Path to audio file to play
            
        Returns:
            bool: Success status
        """
        print(f"🔊 Playing audio: {audio_path}")
        return self.device.play_audio(audio_path)
    
    def wake_screen(self) -> bool:
        """
        Wake up device screen if sleeping
        
        Returns:
            bool: Success status
        """
        print("⚡ Waking screen...")
        return self.device.wake_screen()
    
    def unlock_screen(self, pin: str = None) -> bool:
        """
        Unlock device screen with PIN
        
        Args:
            pin: Screen lock PIN (optional, uses config if not provided)
            
        Returns:
            bool: Success status
        """
        print(f"🔓 Unlocking screen...")
        return self.device.unlock_screen(pin)
    
    def type_text(self, text: str) -> bool:
        """
        Type text on device
        
        Args:
            text: Text to type
            
        Returns:
            bool: Success status
        """
        print(f"⌨️  Typing: {text[:50]}{'...' if len(text) > 50 else ''}")
        return self.device.type_text(text)
    
    def is_online(self) -> bool:
        """
        Check if device is reachable
        
        Returns:
            bool: True if device is online
        """
        return self.device.is_online()
    
    def tap(self, x: int, y: int) -> bool:
        """
        Tap at screen coordinates (ADB only)
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            bool: Success status
        """
        print(f"👆 Tapping at ({x}, {y})")
        return self.device._adb_shell(f"input tap {x} {y}") if hasattr(self.device, '_adb_shell') else False
    
    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300) -> bool:
        """
        Swipe from (x1,y1) to (x2,y2)
        
        Args:
            x1, y1: Start coordinates
            x2, y2: End coordinates
            duration: Swipe duration in milliseconds
            
        Returns:
            bool: Success status
        """
        print(f"👆 Swiping from ({x1}, {y1}) to ({x2}, {y2})")
        return self.device._adb_shell(f"input swipe {x1} {y1} {x2} {y2} {duration}") if hasattr(self.device, '_adb_shell') else False
    
    def screenshot(self, output_path: str = "./assets/screen.png") -> bool:
        """
        Take screenshot (ADB only)
        
        Args:
            output_path: Where to save screenshot
            
        Returns:
            bool: Success status
        """
        print(f"📸 Taking screenshot...")
        try:
            import subprocess
            result = subprocess.run([
                "adb", "exec-out", "screencap", "-p"
            ], capture_output=True, timeout=10)
            
            if result.returncode == 0:
                with open(output_path, 'wb') as f:
                    f.write(result.stdout)
                return True
            return False
        except Exception as e:
            print(f"Screenshot error: {e}")
            return False
    
    def get_device_info(self) -> dict:
        """
        Get information about the connected device
        
        Returns:
            dict: Device information
        """
        info = {
            'name': self.config.name,
            'type': self.config.device_type,
            'ip': self.config.ip_address,
            'online': self.is_online()
        }
        
        # Get emulator-specific info if available
        if hasattr(self.device, 'get_emulator_info'):
            info['emulator'] = self.device.get_emulator_info()
        
        return info
    
    def __repr__(self):
        return f"PhoneAgent(device={self.config.name}, type={self.config.device_type}, online={self.is_online()})"


def main():
    """CLI interface for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Universal Phone Agent")
    parser.add_argument('--config', '-c', help='Config file path')
    parser.add_argument('--list', '-l', action='store_true', help='List device info')
    parser.add_argument('--camera', action='store_true', help='Test camera capture')
    parser.add_argument('--record', type=int, help='Record audio for N seconds')
    parser.add_argument('--play', help='Play audio file')
    parser.add_argument('--type', help='Type text on device')
    
    args = parser.parse_args()
    
    try:
        agent = PhoneAgent(config_path=args.config)
        
        if args.list:
            import json
            print(json.dumps(agent.get_device_info(), indent=2))
        
        if args.camera:
            agent.capture_camera()
        
        if args.record:
            agent.record_audio(args.record)
        
        if args.play:
            agent.play_audio(args.play)
        
        if args.type:
            agent.type_text(args.type)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()