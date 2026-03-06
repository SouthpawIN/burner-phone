#!/usr/bin/env python3
"""
Device SSH Watchdog Service
============================
Monitors Termux SSH connectivity and auto-recovers when devices go offline.
Run as a background service: nohup device_watchdog.py &

Features:
- Continuous monitoring of configured devices
- Auto-recovery via ADB when SSH fails
- Logging and status reporting
- Integration with speak skill recovery functions
"""

import os
import sys
import time
import json
import signal
import subprocess
from pathlib import Path
from datetime import datetime
import yaml

# Configuration
CONFIG = {
    "devices": [
        {"name": "duo", "ip": "100.79.15.54", "ssh_port": 8022},
        {"name": "s10", "ip": "100.93.96.90", "ssh_port": 8022},
    ],
    "ssh_key": str(Path.home() / ".ssh/phone_access"),
    "check_interval": 30,  # seconds between checks
    "recovery_delay": 10,  # seconds to wait after recovery attempt
    "log_file": "/tmp/device_watchdog.log",
    "pid_file": "/tmp/device_watchdog.pid",
    "status_file": "/tmp/device_watchdog.status",
}

class Watchdog:
    def __init__(self, config):
        self.config = config
        self.running = True
        self.status = {"devices": {}, "last_check": None, "uptime_start": datetime.now().isoformat()}
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Write PID file
        Path(config["pid_file"]).write_text(str(os.getpid()))
    
    def _signal_handler(self, signum, frame):
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Received signal {signum}, shutting down...")
        self.running = False
        self._save_status()
        Path(self.config["pid_file"]).unlink(missing_ok=True)
        sys.exit(0)
    
    def log(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] {message}"
        print(log_line)
        
        # Append to log file
        with open(self.config["log_file"], "a") as f:
            f.write(log_line + "\n")
    
    def check_ssh_connection(self, device):
        """Check if SSH is responding on a device"""
        try:
            result = subprocess.run(
                [
                    "ssh",
                    "-i", self.config["ssh_key"],
                    "-p", str(device["ssh_port"]),
                    "-o", "ConnectTimeout=5",
                    "-o", "BatchMode=yes",
                    "-o", "StrictHostKeyChecking=no",
                    f"droid@{device['ip']}",
                    "echo ok"
                ],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            self.log(f"{device['name']}: Connection check failed - {e}")
            return False
    
    def recover_via_adb(self, device):
        """Attempt to recover SSH via ADB"""
        self.log(f"{device['name']}: Attempting recovery via ADB...")
        
        try:
            # Find the ADB device serial for this IP
            result = subprocess.run(
                ["adb", "devices", "-l"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            device_serial = None
            for line in result.stdout.split('\n'):
                if device["ip"] in line and 'device' in line:
                    device_serial = line.split()[0]
                    break
            
            if not device_serial:
                self.log(f"{device['name']}: Not found via ADB (IP: {device['ip']})")
                return False
            
            self.log(f"{device['name']}: Found via ADB as {device_serial}")
            
            # Try to start Termux SSH service
            subprocess.run(
                ["adb", "-s", device_serial, "wait-for-device"],
                timeout=10
            )
            
            # Multiple recovery strategies
            strategies = [
                ["termux-service", "sshd"],
                ["/data/data/com.termux/files/usr/bin/sshd"],
                ["am", "start", "-n", "com.termux/.app.TermuxActivity"],
            ]
            
            for strategy in strategies:
                self.log(f"{device['name']}: Trying recovery strategy: {' '.join(strategy)}")
                result = subprocess.run(
                    ["adb", "-s", device_serial, "shell"] + strategy,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    self.log(f"{device['name']}: Recovery command succeeded")
                    time.sleep(self.config["recovery_delay"])
                    
                    # Verify SSH is back up
                    if self.check_ssh_connection(device):
                        self.log(f"{device['name']}: ✓ SSH recovered successfully!")
                        return True
            
            self.log(f"{device['name']}: ✗ All recovery strategies failed")
            return False
            
        except Exception as e:
            self.log(f"{device['name']}: Recovery failed - {e}")
            return False
    
    def _save_status(self):
        """Save current status to file"""
        self.status["last_check"] = datetime.now().isoformat()
        Path(self.config["status_file"]).write_text(json.dumps(self.status, indent=2))
    
    def run(self):
        """Main watchdog loop"""
        self.log("=" * 60)
        self.log("Device Watchdog Started")
        self.log(f"Monitoring: {', '.join(d['name'] for d in self.config['devices'])}")
        self.log(f"Check interval: {self.config['check_interval']} seconds")
        self.log("=" * 60)
        
        while self.running:
            try:
                for device in self.config["devices"]:
                    name = device["name"]
                    
                    # Check SSH connectivity
                    if self.check_ssh_connection(device):
                        self.status["devices"][name] = "online"
                        # Brief info log for online devices every few checks
                        if int(time.time()) % 300 < self.config["check_interval"]:
                            self.log(f"{name}: ✓ Online")
                    else:
                        self.status["devices"][name] = "offline"
                        self.log(f"{name}: ✗ SSH offline!")
                        
                        # Attempt recovery
                        if self.recover_via_adb(device):
                            self.status["devices"][name] = "recovered"
                        else:
                            self.status["devices"][name] = "offline"
                            self.log(f"{name}: Manual intervention may be required")
                
                self._save_status()
                
                # Wait for next check
                for _ in range(self.config["check_interval"]):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.log(f"Error in monitoring loop: {e}")
                time.sleep(5)
        
        self.log("Watchdog stopped")


def main():
    # Load config from file if exists
    config_file = Path("/etc/hermes-phone-agent/watchdog.yaml")
    if config_file.exists():
        with open(config_file) as f:
            user_config = yaml.safe_load(f) or {}
            CONFIG.update(user_config)
    
    watchdog = Watchdog(CONFIG)
    
    try:
        watchdog.run()
    except KeyboardInterrupt:
        watchdog._signal_handler(signal.SIGINT, None)


if __name__ == "__main__":
    main()