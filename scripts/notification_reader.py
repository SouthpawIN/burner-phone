#!/usr/bin/env python3
"""
Android Notification Reader
===========================

Reads and summarizes Android notifications for Hermes Phone Agent.
Requires notification access permissions (handled via Termux helper app).

Usage:
    python3 notification_reader.py --test      # Single check
    python3 notification_reader.py --daemon    # Continuous monitoring
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import re


class NotificationReader:
    """Read Android notifications via ADB/Termux"""
    
    def __init__(self, device_ip: str = "100.93.96.90", ssh_key: str = "~/.ssh/phone_access"):
        self.device_ip = device_ip
        self.ssh_key = Path(ssh_key).expanduser()
        
        # Notification categories to prioritize
        self.high_priority_packages = [
            "com.whatsapp",  # WhatsApp
            "com.facebook.orca",  # Messenger
            "com.telegram.messenger",  # Telegram
            "com.google.android.apps.messaging",  # SMS
            "com.google.android.gm",  # Gmail
            "com.slack"  # Slack
        ]
    
    def _ssh(self, command: str, timeout: int = 10) -> str:
        """Execute SSH command"""
        try:
            result = subprocess.run(
                ["ssh", "-i", str(self.ssh_key), "-p", "8022",
                 "-o", "StrictHostKeyChecking=no",
                 f"droid@{self.device_ip}", command],
                capture_output=True, text=True, timeout=timeout
            )
            return result.stdout.strip()
        except Exception as e:
            print(f"SSH error: {e}")
            return ""
    
    def _adb_shell(self, command: str) -> str:
        """Execute ADB shell command"""
        try:
            result = subprocess.run(
                ["adb", "-s", f"{self.device_ip}:5555", "shell"] + command.split(),
                capture_output=True, text=True, timeout=10
            )
            return result.stdout.strip()
        except Exception as e:
            print(f"ADB error: {e}")
            return ""
    
    def get_notifications(self) -> List[Dict]:
        """
        Get recent notifications
        
        Returns list of notification dicts with:
        - package: App package name
        - title: Notification title
        - text: Notification content
        - timestamp: When it arrived
        - importance: high/normal/low
        """
        notifications = []
        
        try:
            # Method 1: Try dumpsys (Android 10+)
            output = self._adb_shell("dumpsys notification")
            
            if "rankId=" in output or "NotificationRecord" in output:
                # Parse dumpsys output (simplified)
                # In production, use a proper parser or helper app
                notifications = self._parse_dumpsys(output)
            
            # Method 2: Fall back to Termux notification listener
            if not notifications:
                termux_output = self._ssh("termux-notification-get 2>/dev/null || echo ''")
                if termux_output and termux_output != "":
                    try:
                        data = json.loads(termux_output)
                        notifications = self._parse_termux_notifications(data)
                    except json.JSONDecodeError:
                        pass
            
            # Filter and prioritize
            notifications = self._prioritize_notifications(notifications)
            
        except Exception as e:
            print(f"Notification read error: {e}")
        
        return notifications
    
    def _parse_dumpsys(self, output: str) -> List[Dict]:
        """Parse dumpsys notification output"""
        notifications = []
        
        # This is a simplified parser - production would need more robust parsing
        lines = output.split('\n')
        current_notification = {}
        
        for line in lines:
            if 'pkg=' in line:
                if current_notification:
                    notifications.append(current_notification)
                current_notification = {'package': line.split('pkg=')[1].split()[0]}
            
            elif 'title=' in line:
                current_notification['title'] = line.split('title=')[1].strip()
            
            elif 'text=' in line:
                current_notification['text'] = line.split('text=')[1].strip()
        
        if current_notification:
            notifications.append(current_notification)
        
        return notifications
    
    def _parse_termux_notifications(self, data: dict) -> List[Dict]:
        """Parse Termux notification helper output"""
        notifications = []
        
        if isinstance(data, list):
            for notif in data:
                notifications.append({
                    'package': notif.get('pkg', ''),
                    'title': notif.get('title', ''),
                    'text': notif.get('text', ''),
                    'timestamp': notif.get('time', datetime.now().isoformat())
                })
        elif isinstance(data, dict):
            notifications.append({
                'package': data.get('pkg', ''),
                'title': data.get('title', ''),
                'text': data.get('text', ''),
                'timestamp': data.get('time', datetime.now().isoformat())
            })
        
        return notifications
    
    def _prioritize_notifications(self, notifications: List[Dict]) -> List[Dict]:
        """Add importance scores and sort"""
        for notif in notifications:
            pkg = notif.get('package', '')
            
            # Set importance based on package
            if any(priority in pkg for priority in self.high_priority_packages):
                notif['importance'] = 'high'
            else:
                notif['importance'] = 'normal'
            
            # Add timestamp if missing
            if 'timestamp' not in notif:
                notif['timestamp'] = datetime.now().isoformat()
        
        # Sort by importance (high first)
        return sorted(notifications, key=lambda x: 0 if x.get('importance') == 'high' else 1)
    
    def summarize_notifications(self, notifications: List[Dict] = None) -> str:
        """
        Generate natural language summary of notifications
        
        Returns a human-readable summary suitable for TTS
        """
        if notifications is None:
            notifications = self.get_notifications()
        
        if not notifications:
            return "You have no new notifications."
        
        # Separate high and normal priority
        high_priority = [n for n in notifications if n.get('importance') == 'high']
        normal = [n for n in notifications if n.get('importance') != 'high']
        
        parts = []
        
        # High priority first
        if high_priority:
            if len(high_priority) == 1:
                n = high_priority[0]
                pkg_name = self._get_app_name(n.get('package', ''))
                title = n.get('title', 'Notification')
                parts.append(f"You have an important {pkg_name} notification: {title}")
            else:
                parts.append(f"You have {len(high_priority)} important notifications")
        
        # Normal priority
        if normal:
            if len(normal) == 1:
                n = normal[0]
                pkg_name = self._get_app_name(n.get('package', ''))
                title = n.get('title', 'Notification')
                parts.append(f"and a {pkg_name} notification: {title}")
            else:
                parts.append(f"and {len(normal)} other notifications")
        
        return " ".join(parts)
    
    def _get_app_name(self, package: str) -> str:
        """Convert package name to human-readable app name"""
        app_names = {
            'com.whatsapp': 'WhatsApp',
            'com.facebook.orca': 'Messenger',
            'com.telegram.messenger': 'Telegram',
            'com.google.android.apps.messaging': 'Messages',
            'com.google.android.gm': 'Gmail',
            'com.slack': 'Slack',
            'com.instagram.android': 'Instagram',
            'com.twitter.android': 'Twitter',
            'com.facebook.katana': 'Facebook',
        }
        return app_names.get(package, package.replace('.', ' ').title())


# ============ MAIN ============

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Android Notification Reader")
    parser.add_argument("--test", action="store_true", help="Single check")
    parser.add_argument("--daemon", action="store_true", help="Continuous monitoring")
    parser.add_argument("--interval", "-i", type=float, default=30.0, help="Check interval (seconds)")
    parser.add_argument("--device", "-d", default="100.93.96.90", help="Device IP")
    
    args = parser.parse_args()
    
    reader = NotificationReader(device_ip=args.device)
    
    if args.test:
        # Single check
        notifications = reader.get_notifications()
        
        if notifications:
            print(f"\n🔔 Found {len(notifications)} notification(s):\n")
            for i, notif in enumerate(notifications, 1):
                importance = "⚠️  HIGH" if notif.get('importance') == 'high' else "•"
                pkg = reader._get_app_name(notif.get('package', ''))
                title = notif.get('title', 'No title')
                text = notif.get('text', '')[:100]  # Truncate long messages
                
                print(f"{i}. {importance} {pkg}")
                print(f"   {title}")
                if text:
                    print(f"   {text}...")
                print()
            
            # Summary for TTS
            summary = reader.summarize_notifications(notifications)
            print(f"\n📢 Summary: {summary}")
        else:
            print("No new notifications")
    
    elif args.daemon:
        # Continuous monitoring
        print(f"🔍 Starting notification monitor (interval: {args.interval}s)")
        
        last_notifications = []
        
        while True:
            try:
                import time
                notifications = reader.get_notifications()
                
                # Check for new notifications
                new_notifs = [n for n in notifications if n not in last_notifications]
                
                if new_notifs:
                    high_priority = [n for n in new_notifs if n.get('importance') == 'high']
                    
                    if high_priority:
                        summary = reader.summarize_notifications(new_notifs)
                        print(f"\n🔔 {summary}")
                        
                        # Could trigger speak here
                        # speak(summary)
                
                last_notifications = notifications
                time.sleep(args.interval)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(5)


if __name__ == "__main__":
    main()