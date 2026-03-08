#!/usr/bin/env python3
"""
Auto SSH Daemon - Automatic SSH Startup for Termux Devices
==========================================================

This script automatically manages SSH daemon on Termux-enabled Android devices.
It detects USB connection, starts sshd via ADB, and monitors SSH connectivity.

Features:
- Auto-detects connected devices via ADB
- Starts Termux SSH daemon automatically
- Monitors SSH connectivity and auto-restarts if needed
- Can run as a background service for 24/7 operation
- Supports multiple devices (Duo, S10, etc.)

Usage:
    python3 auto_ssh_daemon.py              # Interactive mode with logging
    python3 auto_ssh_daemon.py --daemon     # Run as background daemon
    python3 auto_ssh_daemon.py --device duo # Manage specific device
    python3 auto_ssh_daemon.py --once       # Start SSH once and exit

Configuration:
    Edit devices in the DEVICES dict below or use --config flag
"""

import subprocess
import time
import sys
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
import yaml


# Device configurations
DEVICES = {
    "duo": {
        "name": "Surface Duo 2",
        "ip": "100.79.15.54",
        "ssh_port": 8022,
        "ssh_user": "droid",
        "ssh_key": str(Path.home() / ".ssh/phone_access"),
        "usb_serial": None,  # Auto-detect
    },
    "s10": {
        "name": "Samsung Galaxy S10",
        "ip": "100.93.96.90",
        "ssh_port": 8022,
        "ssh_user": "droid",
        "ssh_key": str(Path.home() / ".ssh/phone_access"),
        "usb_serial": None,  # Auto-detect
    },
}


class Logger:
    """Simple file and console logger"""
    
    def __init__(self, log_file: str = "/tmp/auto_ssh_daemon.log", verbose: bool = True):
        self.log_file = Path(log_file)
        self.verbose = verbose
        self._ensure_log_dir()
    
    def _ensure_log_dir(self):
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _write(self, level: str, message: str):
        line = f"[{self._timestamp()}] [{level}] {message}\n"
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(line)
        except Exception as e:
            print(f"Failed to write to log: {e}", file=sys.stderr)
    
    def log(self, level: str, message: str):
        self._write(level, message)
        
        if self.verbose or level in ("ERROR", "WARN"):
            print(f"[{level}] {message}")
    
    def info(self, msg: str):
        self.log("INFO", msg)
    
    def warn(self, msg: str):
        self.log("WARN", msg)
    
    def error(self, msg: str):
        self.log("ERROR", msg)
    
    def debug(self, msg: str):
        if self.verbose:
            self.log("DEBUG", msg)


class DeviceSSHManager:
    """Manages SSH daemon on a single Termux device"""
    
    def __init__(self, device_id: str, config: Dict, logger: Logger):
        self.device_id = device_id
        self.config = config
        self.logger = logger
        self._serial = None
    
    def _get_adb_devices(self) -> List[Dict]:
        """Get list of connected ADB devices with details"""
        try:
            result = subprocess.run(
                ["adb", "devices", "-l"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            devices = []
            for line in result.stdout.strip().split("\n")[1:]:
                if "device" in line:
                    parts = line.split()
                    serial = parts[0]
                    props = {}
                    for part in parts[2:]:
                        if "=" in part:
                            key, value = part.split("=", 1)
                            props[key] = value
                    
                    devices.append({
                        "serial": serial,
                        "properties": props,
                        "raw": line
                    })
            
            return devices
        except Exception as e:
            self.logger.error(f"Failed to get ADB devices: {e}")
            return []
    
    def _find_device_serial(self) -> Optional[str]:
        """Find the ADB serial for this device by IP or other properties"""
        adb_devices = self._get_adb_devices()
        
        if not adb_devices:
            return None
        
        # Try to match by product model or other properties
        target_ip = self.config["ip"]
        
        for device in adb_devices:
            props = device["properties"]
            
            # Check if this looks like our device (by IP in props or model name)
            device_name_lower = self.config["name"].lower()
            
            # Try matching by model/product
            product = props.get("product", "").lower()
            model = props.get("model", "").lower()
            
            if "duo" in device_name_lower and ("duo" in product or "duo" in model):
                return device["serial"]
            elif "s10" in device_name_lower and ("s10" in product or "star2" in product):
                return device["serial"]
        
        # If no specific match, return first available device
        self.logger.debug(f"No specific match found, using first available device")
        return adb_devices[0]["serial"]
    
    def is_adb_connected(self) -> bool:
        """Check if device is connected via ADB"""
        self._serial = self._find_device_serial()
        return self._serial is not None
    
    def is_ssh_online(self, timeout: float = 3.0) -> bool:
        """Check if SSH daemon is running on the device"""
        try:
            result = subprocess.run(
                [
                    "ssh",
                    "-i", self.config["ssh_key"],
                    "-p", str(self.config["ssh_port"]),
                    "-o", f"ConnectTimeout={int(timeout)}",
                    "-o", "BatchMode=yes",
                    "-o", "StrictHostKeyChecking=no",
                    f"{self.config['ssh_user']}@{self.config['ip']}",
                    "echo ok"
                ],
                capture_output=True,
                timeout=timeout + 2
            )
            return result.returncode == 0
        except:
            return False
    
    def start_ssh_via_adb(self) -> bool:
        """Start Termux SSH daemon via ADB"""
        if not self._serial:
            self._serial = self._find_device_serial()
        
        if not self._serial:
            self.logger.error(f"Device {self.device_id} not connected via ADB")
            return False
        
        self.logger.info(f"Starting SSH on {self.config['name']} via ADB (serial: {self._serial})")
        
        # Wait for device
        try:
            subprocess.run(
                ["adb", "-s", self._serial, "wait-for-device"],
                timeout=10
            )
        except Exception as e:
            self.logger.error(f"Device not responding: {e}")
            return False
        
        # Start Termux SSH service
        try:
            # First, try to start the sshd service
            result = subprocess.run(
                ["adb", "-s", self._serial, "shell", "termux-service", "sshd"],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode != 0:
                self.logger.warn(f"termux-service sshd failed: {result.stderr}")
                # Alternative: try direct execution
                subprocess.run(
                    ["adb", "-s", self._serial, "shell", "$PREFIX/bin/sshd"],
                    capture_output=True,
                    timeout=10
                )
            
            self.logger.info(f"✓ SSH start command sent to {self.config['name']}")
            
            # Wait for SSH to become available
            self.logger.info("Waiting for SSH daemon to start...")
            for i in range(10):
                time.sleep(2)
                if self.is_ssh_online():
                    self.logger.info(f"✓ SSH is now online on {self.config['name']}")
                    return True
            
            self.logger.warn(f"SSH command sent but device not responding yet")
            return True  # Still consider success - might start in background
            
        except Exception as e:
            self.logger.error(f"Failed to start SSH: {e}")
            return False
    
    def ensure_ssh_running(self) -> bool:
        """Ensure SSH is running, start if needed"""
        if self.is_ssh_online():
            self.logger.debug(f"SSH already running on {self.config['name']}")
            return True
        
        if not self.is_adb_connected():
            self.logger.warn(f"{self.config['name']} not connected via ADB")
            return False
        
        return self.start_ssh_via_adb()


class AutoSSHDaemon:
    """Main daemon that manages SSH for multiple devices"""
    
    def __init__(self, config_path: str = None, verbose: bool = True):
        self.logger = Logger(verbose=verbose)
        self.config = self._load_config(config_path)
        self.managers: Dict[str, DeviceSSHManager] = {}
        self._running = False
        
        # Initialize managers for all configured devices
        for device_id, config in self.config["devices"].items():
            self.managers[device_id] = DeviceSSHManager(device_id, config, self.logger)
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file or use defaults"""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f) or {"devices": DEVICES}
        
        # Default config
        return {"devices": DEVICES, "check_interval": 30}
    
    def check_all_devices(self):
        """Check and ensure SSH is running on all devices"""
        for device_id, manager in self.managers.items():
            self.logger.info(f"Checking {manager.config['name']}...")
            manager.ensure_ssh_running()
    
    def start_daemon(self):
        """Start the monitoring daemon"""
        self.logger.info("Starting Auto SSH Daemon...")
        self._running = True
        
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Write PID file
        try:
            with open("/tmp/auto_ssh_daemon.pid", 'w') as f:
                f.write(str(os.getpid()))
        except:
            pass
        
        check_interval = self.config.get("check_interval", 30)
        
        self.logger.info(f"Monitoring devices every {check_interval} seconds")
        self.logger.info("Press Ctrl+C to stop\n")
        
        # Initial check
        self.check_all_devices()
        
        # Main loop
        while self._running:
            try:
                time.sleep(check_interval)
                self.check_all_devices()
            except KeyboardInterrupt:
                break
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self._running = False
        
        # Clean up PID file
        try:
            Path("/tmp/auto_ssh_daemon.pid").unlink(missing_ok=True)
        except:
            pass
        
        self.logger.info("Auto SSH Daemon stopped")
        sys.exit(0)
    
    def once_mode(self):
        """Start SSH on all devices once and exit"""
        self.logger.info("Starting SSH on all devices (once mode)...")
        self.check_all_devices()
        
        # Summary
        print("\n=== Device Status ===")
        for device_id, manager in self.managers.items():
            adb_status = "✓" if manager.is_adb_connected() else "✗"
            ssh_status = "✓" if manager.is_ssh_online() else "✗"
            print(f"{manager.config['name']}: ADB {adb_status}, SSH {ssh_status}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto SSH Daemon for Termux Devices")
    parser.add_argument("--daemon", action="store_true", help="Run as background daemon")
    parser.add_argument("--once", action="store_true", help="Start SSH once and exit")
    parser.add_argument("--device", choices=["duo", "s10"], help="Manage specific device")
    parser.add_argument("--config", "-c", help="Config file path")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode")
    
    args = parser.parse_args()
    
    # Create daemon
    daemon = AutoSSHDaemon(config_path=args.config, verbose=not args.quiet)
    
    if args.once or not args.daemon:
        # Once mode (default if neither --daemon nor --once specified)
        daemon.once_mode()
    
    elif args.daemon:
        # Daemon mode
        daemon.start_daemon()


if __name__ == "__main__":
    main()