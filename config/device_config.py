#!/usr/bin/env python3
"""Device Configuration Loader"""

import yaml
from pathlib import Path
from typing import Optional
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from backends import DeviceConfig


def load_config(config_path: Optional[str] = None) -> DeviceConfig:
    """Load device configuration from YAML file"""
    
    if config_path is None:
        # Default locations
        possible_paths = [
            Path("~/.hermes-phone-agent/config.yaml").expanduser(),
            Path("./config.yaml"),
            Path("/etc/hermes-phone-agent/config.yaml")
        ]
        
        for path in possible_paths:
            if path.exists():
                config_path = str(path)
                break
        else:
            raise FileNotFoundError(
                "No configuration file found. Create one at ~/.hermes-phone-agent/config.yaml"
            )
    
    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)
    
    return DeviceConfig(
        name=data.get('name', 'Unknown Device'),
        device_type=data['device_type'],  # Required: termux, adb, or emulator
        ip_address=data.get('ip_address'),
        ssh_port=data.get('ssh_port', 8022),
        adb_port=data.get('adb_port', 5555),
        ssh_key=data.get('ssh_key', '~/.ssh/phone_access'),
        ssh_user=data.get('ssh_user', 'droid'),
        screen_pin=data.get('screen_pin'),
        camera_path=data.get('camera_path', '/sdcard/senter_gaze.jpg'),
        audio_input_path=data.get('audio_input_path', '/sdcard/senter_in.wav'),
        audio_output_path=data.get('audio_output_path', '/sdcard/senter_out.wav')
    )


def create_example_config(output_path: Optional[str] = None):
    """Create an example configuration file"""
    
    if output_path is None:
        output_path = Path("~/.hermes-phone-agent/config.yaml.example").expanduser()
    
    example = """# Hermes Phone Agent - Device Configuration
# Copy this to ~/.hermes-phone-agent/config.yaml and edit for your device

# Device name (for logging)
name: "My Phone"

# Device type: 'termux', 'adb', or 'emulator'
# - termux: Android phone with Termux installed (best performance)
# - adb: Standard Android device via ADB only
# - emulator: Android emulator (Android Studio, Genymotion, Waydroid)
device_type: "termux"

# Network configuration
ip_address: "100.93.96.90"  # Tailscale IP for physical devices, "localhost" for emulators
ssh_port: 8022              # SSH port (Termux only)
adb_port: 5555              # ADB port

# Authentication
ssh_key: "~/.ssh/phone_access"  # Path to SSH private key
ssh_user: "droid"                # SSH username (Termux default)

# Screen unlock PIN (optional, remove if no PIN)
screen_pin: "4658"

# File paths on device (usually don't need to change)
camera_path: "/sdcard/senter_gaze.jpg"
audio_input_path: "/sdcard/senter_in.wav"
audio_output_path: "/sdcard/senter_out.wav"

# Example configurations for different setups:

# === Samsung Galaxy S10 with Termux (current Senter setup) ===
# device_type: "termux"
# ip_address: "100.93.96.90"
# ssh_port: 8022
# ssh_key: "~/.ssh/phone_access"
# screen_pin: "4658"

# === Surface Duo 2 with Termux ===
# device_type: "termux"
# ip_address: "100.79.15.54"
# ssh_port: 8022
# ssh_key: "~/.ssh/phone_access"

# === Standard Android phone (no Termux) ===
# device_type: "adb"
# ip_address: "100.x.x.x"  # Your phone's Tailscale IP
# adb_port: 5555
# screen_pin: "your_pin"

# === Android Studio Emulator ===
# device_type: "emulator"
# ip_address: "localhost"
# adb_port: 5555
# screen_pin: null  # Emulators usually don't have PIN

# === Waydroid (Android in container) ===
# device_type: "emulator"
# ip_address: "localhost"
# adb_port: 5555
"""
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(example)
    
    print(f"Example configuration created at: {output_path}")
    return output_path


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--example":
        create_example_config()
    else:
        try:
            config = load_config()
            print(f"Loaded configuration for: {config.name}")
            print(f"Device type: {config.device_type}")
            print(f"IP address: {config.ip_address}")
        except FileNotFoundError as e:
            print(f"Error: {e}")
            print("\nCreating example configuration...")
            create_example_config()