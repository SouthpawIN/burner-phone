#!/usr/bin/env python3
"""
Universal Phone Agent - Main Interface
Provides unified control over Android devices regardless of backend (Termux, ADB, Emulator)

Enhanced with direct ADB camera/audio functions for S10 (RF8M221SXHZ)
"""

import sys
import subprocess
import time
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
import io

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

    # ==========================================================================
    # ENHANCED S10 ADB CAMERA/AUDIO FUNCTIONS
    # Direct ADB access for Samsung Galaxy S10 (RF8M221SXHZ)
    # ==========================================================================

    def test_adb_connection(self, device_id: str = "RF8M221SXHZ") -> Dict[str, Any]:
        """
        Test ADB connection and return device information.
        
        Args:
            device_id: ADB device ID (default: RF8M221SXHZ for S10)
            
        Returns:
            Dictionary with connection status and device info
        """
        result = {
            'device_id': device_id,
            'connected': False,
            'model': None,
            'brand': None,
            'serial': device_id,
            'screen_resolution': None,
            'battery_level': None,
            'is_charging': None
        }
        
        try:
            # Test basic connection
            check_cmd = ["adb", "-s", device_id, "shell", "echo", "connected"]
            proc = subprocess.run(check_cmd, capture_output=True, timeout=5)
            if proc.returncode == 0:
                result['connected'] = True
                
                # Get device model and brand
                model_cmd = ["adb", "-s", device_id, "shell", "getprop", "ro.build.model"]
                result['model'] = subprocess.run(model_cmd, capture_output=True, timeout=5).stdout.decode().strip()
                
                brand_cmd = ["adb", "-s", device_id, "shell", "getprop", "ro.product.brand"]
                result['brand'] = subprocess.run(brand_cmd, capture_output=True, timeout=5).stdout.decode().strip()
                
                # Get screen resolution
                wm_size_cmd = ["adb", "-s", device_id, "shell", "wm", "size"]
                wm_output = subprocess.run(wm_size_cmd, capture_output=True, timeout=5).stdout.decode()
                if "Physical size:" in wm_output:
                    parts = wm_output.split("Physical size: ")[1].strip().split("x")
                    result['screen_resolution'] = f"{parts[0]}x{parts[1]}"
                
                # Get battery info
                dumpsys_battery = ["adb", "-s", device_id, "shell", "dumpsys", "battery"]
                battery_output = subprocess.run(dumpsys_battery, capture_output=True, timeout=5).stdout.decode()
                for line in battery_output.split('\n'):
                    if 'level=' in line:
                        result['battery_level'] = int(line.split('level=')[1].split()[0])
                    elif 'status=' in line and 'charging' not in line.lower():
                        result['is_charging'] = 'Charging' in line
                
        except subprocess.TimeoutExpired:
            result['error'] = 'Connection timeout'
        except Exception as e:
            result['error'] = str(e)
        
        return result

    def capture_front_camera(self, device_id: str = "RF8M221SXHZ", 
                           output_path: str = None) -> Optional[bytes]:
        """
        Capture image from front camera using ADB.
        Note: Direct camera access requires MediaProjection API or an app.
        This uses screen capture as fallback (user should have camera app open).
        
        Args:
            device_id: ADB device ID
            output_path: Optional path to save image locally
            
        Returns:
            Image bytes or None on failure
        """
        if output_path is None:
            output_path = "/tmp/s10_front_camera.jpg"
        
        try:
            # Method 1: Try to use MediaScanner to trigger camera (may require permissions)
            # Method 2: Screen capture (requires camera app open on device)
            screencap_cmd = [
                "adb", "-s", device_id, 
                "exec-out", "screencap", "-p"
            ]
            proc = subprocess.run(screencap_cmd, capture_output=True, timeout=10)
            
            if proc.returncode == 0:
                image_data = proc.stdout
                with open(output_path, 'wb') as f:
                    f.write(image_data)
                print(f"📸 Captured screen to {output_path}")
                return image_data
            else:
                print(f"Screen capture failed: {proc.stderr.decode()}")
                return None
                
        except subprocess.TimeoutExpired:
            print("Camera capture timeout")
            return None
        except Exception as e:
            print(f"Camera capture error: {e}")
            return None

    def record_audio_adb(self, device_id: str = "RF8M221SXHZ",
                        duration: int = 5,
                        output_path: str = None) -> Optional[str]:
        """
        Record audio using ADB screenrecord with audio (Android 10+).
        
        Args:
            device_id: ADB device ID
            duration: Recording duration in seconds
            output_path: Output file path (default: /tmp/s10_audio_<timestamp>.wav)
            
        Returns:
            Path to recorded audio file or None on failure
        """
        if output_path is None:
            timestamp = int(time.time())
            output_path = f"/tmp/s10_audio_{timestamp}.wav"
        
        # Screenrecord creates MP4, we'll extract audio
        mp4_path = output_path.replace('.wav', '.mp4')
        remote_mp4 = "/sdcard/senter_record.mp4"
        
        try:
            print(f"🎤 Recording {duration} seconds via ADB screenrecord...")
            
            # Start screenrecord with audio
            record_cmd = [
                "adb", "-s", device_id,
                "shell", "screenrecord",
                "--audio",
                f"--time-limit={duration}",
                remote_mp4
            ]
            proc = subprocess.run(record_cmd, capture_output=True, timeout=duration + 15)
            
            if proc.returncode != 0:
                print(f"Screenrecord failed: {proc.stderr.decode()}")
                return None
            
            # Pull the MP4 file
            pull_cmd = ["adb", "-s", device_id, "pull", remote_mp4, mp4_path]
            subprocess.run(pull_cmd, timeout=30)
            
            # Extract audio to WAV using ffmpeg
            ffmpeg_cmd = [
                "ffmpeg", "-y", "-i", mp4_path,
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                output_path
            ]
            ffmpeg_proc = subprocess.run(ffmpeg_cmd, capture_output=True, timeout=30)
            
            if ffmpeg_proc.returncode == 0:
                # Clean up MP4
                Path(mp4_path).unlink(missing_ok=True)
                print(f"🎤 Audio recorded to {output_path}")
                return output_path
            else:
                print(f"FFmpeg extraction failed")
                return None
                
        except subprocess.TimeoutExpired:
            print("Recording timeout")
            return None
        except Exception as e:
            print(f"Recording error: {e}")
            return None

    def play_audio_adb(self, device_id: str = "RF8M221SXHZ",
                      audio_path: str = None,
                      audio_data: bytes = None) -> bool:
        """
        Play audio through S10 speaker via ADB.
        
        Args:
            device_id: ADB device ID
            audio_path: Path to local audio file
            audio_data: Raw audio bytes (alternative to file path)
            
        Returns:
            True if playback started successfully
        """
        remote_path = "/sdcard/senter_playback.wav"
        
        try:
            # Push audio to device
            if audio_data:
                # Write temp file from bytes
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
                    tmp.write(audio_data)
                    local_path = tmp.name
            else:
                local_path = audio_path
            
            print(f"🔊 Pushing audio to device...")
            push_cmd = ["adb", "-s", device_id, "push", local_path, remote_path]
            subprocess.run(push_cmd, timeout=30)
            
            if audio_data:
                Path(local_path).unlink()
            
            # Play using am (Activity Manager)
            play_cmd = [
                "adb", "-s", device_id,
                "shell", "am", "start",
                "-a", "android.intent.action.VIEW",
                "-t", "audio/*",
                f"-d", f"file://{remote_path}"
            ]
            result = subprocess.run(play_cmd, timeout=5)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"Playback error: {e}")
            return False

    def stream_camera_frames(self, device_id: str = "RF8M221SXHZ",
                           callback=None,
                           duration: int = None):
        """
        Continuously capture screen frames via ADB.
        Note: For actual front camera streaming, an app on device is needed.
        
        Args:
            device_id: ADB device ID
            callback: Function to call with each frame (bytes)
            duration: Stop after N seconds (None for infinite)
        """
        import threading
        stop_event = threading.Event()
        start_time = time.time()
        
        def capture_loop():
            while not stop_event.is_set():
                elapsed = time.time() - start_time
                if duration and elapsed >= duration:
                    break
                    
                try:
                    proc = subprocess.run(
                        ["adb", "-s", device_id, "exec-out", "screencap", "-p"],
                        capture_output=True, timeout=2
                    )
                    if proc.returncode == 0 and callback:
                        callback(proc.stdout)
                except:
                    pass
                time.sleep(0.1)  # ~10 fps
        
        thread = threading.Thread(target=capture_loop, daemon=True)
        thread.start()
        return stop_event

    def stream_audio(self, device_id: str = "RF8M221SXHZ",
                    callback=None,
                    duration: int = None):
        """
        Stream audio from device microphone via ADB.
        Uses screenrecord in background and pipes audio.
        
        Args:
            device_id: ADB device ID
            callback: Function to call with each audio chunk (bytes)
            duration: Stop after N seconds
        """
        import threading
        stop_event = threading.Event()
        
        def record_loop():
            remote_mp4 = "/sdcard/senter_stream.mp4"
            try:
                # Start background recording
                subprocess.Popen([
                    "adb", "-s", device_id,
                    "shell", "screenrecord",
                    "--audio",
                    remote_mp4
                ])
                time.sleep(1)  # Let it start
                
                while not stop_event.is_set():
                    if duration and (time.time() - start_time) >= duration:
                        break
                    time.sleep(0.5)
                
                # Stop recording
                subprocess.run([
                    "adb", "-s", device_id,
                    "shell", "pkill", "-f", "screenrecord"
                ], timeout=2)
                
            except Exception as e:
                print(f"Audio stream error: {e}")
        
        start_time = time.time()
        thread = threading.Thread(target=record_loop, daemon=True)
        thread.start()
        return stop_event

    def wake_device(self, device_id: str = "RF8M221SXHZ") -> bool:
        """
        Wake up the S10 device screen.
        
        Args:
            device_id: ADB device ID
            
        Returns:
            True if command sent successfully
        """
        try:
            result = subprocess.run([
                "adb", "-s", device_id,
                "shell", "input", "keyevent", "KEYCODE_WAKEUP"
            ], timeout=5)
            return result.returncode == 0
        except:
            return False

    def tap_screen(self, x: int, y: int, device_id: str = "RF8M221SXHZ") -> bool:
        """
        Tap at screen coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            device_id: ADB device ID
            
        Returns:
            True if tap sent successfully
        """
        try:
            result = subprocess.run([
                "adb", "-s", device_id,
                "shell", "input", "tap", str(x), str(y)
            ], timeout=5)
            return result.returncode == 0
        except:
            return False

    def swipe_screen(self, x1: int, y1: int, x2: int, y2: int, device_id: str = "RF8M221SXHZ") -> bool:
        """
        Swipe from (x1,y1) to (x2,y2).
        
        Args:
            device_id: ADB device ID
            x1, y1: Start coordinates
            x2, y2: End coordinates
            
        Returns:
            True if swipe sent successfully
        """
        try:
            result = subprocess.run([
                "adb", "-s", device_id,
                "shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2)
            ], timeout=5)
            return result.returncode == 0
        except:
            return False

    def type_on_device(self, text: str, device_id: str = "RF8M221SXHZ") -> bool:
        """
        Type text on the device.
        
        Args:
            text: Text to type
            device_id: ADB device ID
            
        Returns:
            True if text sent successfully
        """
        try:
            escaped = text.replace('\\', '\\\\').replace('\n', '\\n')
            result = subprocess.run([
                "adb", "-s", device_id,
                "shell", "input", "text", escaped
            ], timeout=5)
            return result.returncode == 0
        except:
            return False

    def press_key(self, device_id: str = "RF8M221SXHZ", key_code: str) -> bool:
        """
        Press a key on the device.
        
        Args:
            device_id: ADB device ID
            key_code: Key code (e.g., KEYCODE_ENTER, KEYCODE_BACK, KEYCODE_HOME)
            
        Returns:
            True if key press sent successfully
        """
        try:
            result = subprocess.run([
                "adb", "-s", device_id,
                "shell", "input", "keyevent", key_code
            ], timeout=5)
            return result.returncode == 0
        except:
            return False

    def get_battery_status(self, device_id: str = "RF8M221SXHZ") -> Dict[str, Any]:
        """
        Get battery status from S10.
        
        Args:
            device_id: ADB device ID
            
        Returns:
            Dictionary with battery information
        """
        status = {'level': None, 'charging': None, 'temperature': None, 'health': None}
        
        try:
            output = subprocess.run([
                "adb", "-s", device_id,
                "shell", "dumpsys", "battery"
            ], capture_output=True, timeout=5).stdout.decode()
            
            for line in output.split('\n'):
                if 'level=' in line:
                    status['level'] = int(line.split('level=')[1].split()[0])
                elif 'scale=' in line:
                    status['scale'] = int(line.split('scale=')[1].split()[0])
                elif 'temperature=' in line:
                    status['temperature'] = float(line.split('temperature=')[1].split()[0])
                elif 'health=' in line:
                    status['health'] = line.split('health=')[1].split()[0]
            
            # Check charging status
            status['charging'] = 'Charging' in output
            
        except Exception as e:
            status['error'] = str(e)
        
        return status

    def launch_app(self, device_id: str = "RF8M221SXHZ", package: str) -> bool:
        """
        Launch an app by package name.
        
        Args:
            device_id: ADB device ID
            package: Package name (e.g., com.whatsapp, com.instagram.android)
            
        Returns:
            True if launch command sent successfully
        """
        try:
            result = subprocess.run([
                "adb", "-s", device_id,
                "shell", "monkey", "-p", package, "1"
            ], timeout=5)
            return result.returncode == 0
        except:
            return False

    def install_app(self, device_id: str = "RF8M221SXHZ", apk_path: str) -> bool:
        """
        Install an APK on the device.
        
        Args:
            device_id: ADB device ID
            apk_path: Path to APK file
            
        Returns:
            True if installation successful
        """
        try:
            result = subprocess.run([
                "adb", "-s", device_id,
                "install", "-r", apk_path
            ], capture_output=True, timeout=60)
            return b"Success" in result.stdout or result.returncode == 0
        except:
            return False


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