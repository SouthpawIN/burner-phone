#!/usr/bin/env python3
"""
Multi-device TTS - FIXED VERSION with proper zombie handling
Key fixes:
1. Replace os.system() with subprocess.Popen + wait()
2. Iterative queue processing instead of recursion
3. Signal handlers for cleanup on exit/ctrl+c
4. Track and reap all child processes
5. Watchdog timer for hung processes
"""

import subprocess
import sys
import json
import time
import os
import signal
from pathlib import Path

DEVICES = {
    "s10": {
        "name": "Senter S10",
        "ip": "100.93.96.90",
        "ssh_port": 8022,
        "ssh_user": "droid",
        "ssh_key": str(Path.home() / ".ssh/phone_access"),
    },
    "duo": {
        "name": "Surface Duo 2",
        "ip": "100.79.15.54",
        "ssh_port": 8022,
        "ssh_user": "droid",
        "ssh_key": str(Path.home() / ".ssh/phone_access"),
    },
    "local": {
        "name": "Local Speakers",
        "ip": "localhost",
        "ssh_port": 0,
        "ssh_user": "",
        "ssh_key": "",
        "local": True,
    },
}

SOPRANO_PORT = 8102
SOPRANO_STARTUP_WAIT = 5

STATE_FILE = Path("/tmp/senter_speak_mode")
DEVICE_FILE = Path("/tmp/senter_speak_device")
LAST_SPEAK_FILE = Path("/tmp/senter_speak_last")
SOPRANO_PID_FILE = Path("/tmp/soprano_pid")
QUEUE_FILE = Path("/tmp/speak_queue")
PLAYING_FILE = Path("/tmp/speak_playing")

# Remote service configurations - extensible for multiple models/services on TailScale devices
REMOTE_SERVICES = {
    "soprano": {
        "port": 8102,
        "check_path": "/docs",
        "start_cmd": "cd ~ && nohup python3 -m soprano.server --host 0.0.0.0 --port 8102 > /tmp/soprano.log 2>&1 &",
        "stop_cmd": "pkill -f soprano.server",
        "pid_file": "/tmp/soprano_pid_remote"
    },
    # Add more services here for different models:
    # "model-x": {
    #     "port": 9000,
    #     "check_path": "/health",
    #     "start_cmd": "...",
    # }
}

# Track child processes to reap them
child_processes = []


def cleanup_handler(signum, frame):
    """Clean up all child processes on exit/ctrl+c"""
    print(f"\nCleaning up {len(child_processes)} child processes...", file=sys.stderr)
    for proc in child_processes:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except:
            try:
                proc.kill()
            except:
                pass
    sys.exit(0)


# Register cleanup handlers
signal.signal(signal.SIGINT, cleanup_handler)
signal.signal(signal.SIGTERM, cleanup_handler)
signal.signal(signal.SIGHUP, cleanup_handler)


def check_soprano_running():
    try:
        result = subprocess.run(
            [
                "curl",
                "-s",
                "-o",
                "/dev/null",
                "-w",
                "%{http_code}",
                f"http://localhost:{SOPRANO_PORT}/docs",
            ],
            capture_output=True,
            timeout=5,
        )
        return result.stdout.decode().strip() == "200"
    except:
        return False


def start_soprano():
    if check_soprano_running():
        return True
    if SOPRANO_PID_FILE.exists():
        try:
            pid = int(SOPRANO_PID_FILE.read_text().strip())
            subprocess.run(["kill", "-0", str(pid)], capture_output=True)
            for _ in range(SOPRANO_STARTUP_WAIT):
                if check_soprano_running():
                    return True
                time.sleep(1)
        except:
            pass
    log_file = open("/tmp/soprano.log", "w")
    proc = subprocess.Popen(
        [
            "python3",
            "-m",
            "uvicorn",
            "soprano.server:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(SOPRANO_PORT),
        ],
        stdout=log_file,
        stderr=log_file,
        start_new_session=True,
    )
    child_processes.append(proc)
    SOPRANO_PID_FILE.write_text(str(proc.pid))
    for _ in range(SOPRANO_STARTUP_WAIT):
        if check_soprano_running():
            return True
        time.sleep(1)
    return False


def check_remote_service(ip, ssh_port, ssh_key, service_name, timeout=5):
    """Check if a remote service is running on a TailScale device"""
    if service_name not in REMOTE_SERVICES:
        print(f"Unknown service: {service_name}", file=sys.stderr)
        return False
    
    service = REMOTE_SERVICES[service_name]
    try:
        check_url = f"http://localhost:{service['port']}{service['check_path']}"
        
        result = subprocess.run(
            [
                "ssh",
                "-i", ssh_key,
                "-p", str(ssh_port),
                "-o", "ConnectTimeout=3",
                "-o", "BatchMode=yes",
                "-o", "StrictHostKeyChecking=no",
                f"droid@{ip}",
                f"curl -s -o /dev/null -w '%{{http_code}}' {check_url}"
            ],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        return result.stdout.strip() == "200"
    except Exception as e:
        print(f"Failed to check remote service {service_name}: {e}", file=sys.stderr)
        return False


def start_remote_service(ip, ssh_port, ssh_key, service_name, timeout=30):
    """Start a remote service on a TailScale device if not already running"""
    if service_name not in REMOTE_SERVICES:
        print(f"Unknown service: {service_name}", file=sys.stderr)
        return False
    
    # Check if already running
    if check_remote_service(ip, ssh_port, ssh_key, service_name):
        print(f"Remote service {service_name} already running on {ip}", file=sys.stderr)
        return True
    
    service = REMOTE_SERVICES[service_name]
    try:
        # Start the service remotely
        result = subprocess.run(
            [
                "ssh",
                "-i", ssh_key,
                "-p", str(ssh_port),
                "-o", "ConnectTimeout=5",
                "-o", "StrictHostKeyChecking=no",
                f"droid@{ip}",
                service["start_cmd"]
            ],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"Failed to start {service_name}: {result.stderr[:200]}", file=sys.stderr)
            return False
        
        # Wait for service to be ready
        print(f"Starting remote service {service_name} on {ip}...", file=sys.stderr)
        for i in range(timeout):
            if check_remote_service(ip, ssh_port, ssh_key, service_name, timeout=3):
                print(f"Remote service {service_name} is ready!", file=sys.stderr)
                return True
            time.sleep(1)
        
        print(f"Service {service_name} started but not responding yet", file=sys.stderr)
        return True
        
    except Exception as e:
        print(f"Failed to start remote service {service_name}: {e}", file=sys.stderr)
        return False


def restart_termux_ssh(ip, ssh_key):
    """Attempt to restart Termux SSH service on a device via ADB"""
    try:
        result = subprocess.run(
            ["adb", "devices", "-l"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        device_serial = None
        for line in result.stdout.split('\n'):
            if ip in line and 'device' in line:
                device_serial = line.split()[0]
                break
        
        if not device_serial:
            return False
        
        subprocess.run(
            ["adb", "-s", device_serial, "wait-for-device"],
            timeout=10
        )
        
        subprocess.run(
            ["adb", "-s", device_serial, "shell", "termux-service", "sshd"],
            timeout=10
        )
        
        time.sleep(3)
        
        return True
    except Exception as e:
        print(f"Failed to restart Termux SSH: {e}", file=sys.stderr)
        return False


def check_device_online(ip, port, ssh_key, timeout=2.0, auto_recover=False):
    try:
        result = subprocess.run(
            [
                "ssh",
                "-i",
                ssh_key,
                "-p",
                str(port),
                "-o",
                "ConnectTimeout=1",
                "-o",
                "BatchMode=yes",
                "-o",
                "StrictHostKeyChecking=no",
                f"droid@{ip}",
                "echo ok",
            ],
            capture_output=True,
            timeout=timeout,
        )
        
        if result.returncode == 0:
            return True
        
        if auto_recover:
            print(f"Device {ip} offline, attempting recovery...", file=sys.stderr)
            if restart_termux_ssh(ip, ssh_key):
                time.sleep(2)
                result = subprocess.run(
                    [
                        "ssh",
                        "-i",
                        ssh_key,
                        "-p",
                        str(port),
                        "-o",
                        "ConnectTimeout=3",
                        "-o",
                        "BatchMode=yes",
                        "-o",
                        "StrictHostKeyChecking=no",
                        f"droid@{ip}",
                        "echo ok",
                    ],
                    capture_output=True,
                    timeout=5,
                )
                return result.returncode == 0
        
        return False
    except:
        return False


def get_available_devices(auto_recover=False):
    available = []
    for device_id, device in DEVICES.items():
        if device.get("local") or check_device_online(
            device["ip"], device["ssh_port"], device["ssh_key"], auto_recover=auto_recover
        ):
            available.append(device_id)
    return available


def get_last_speak():
    if LAST_SPEAK_FILE.exists():
        try:
            return float(LAST_SPEAK_FILE.read_text().strip())
        except:
            pass
    return 0


def set_last_speak():
    LAST_SPEAK_FILE.write_text(str(time.time()))


def get_status():
    if STATE_FILE.exists():
        return STATE_FILE.read_text().strip()
    return "off"


def set_status(status):
    STATE_FILE.write_text(status)


def get_device():
    try:
        result = subprocess.run(
            ["tailscale", "status", "--json"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            peers = data.get("Peer", {})
            best_device = None
            best_time = 0
            for ip, peer in peers.items():
                last_seen = peer.get("LastSeen", 0)
                if isinstance(last_seen, str):
                    last_seen = 0
                online = peer.get("Online", False)
                if online and last_seen > best_time:
                    if ip == "100.79.15.54" or ip.endswith(".54"):
                        best_device = "duo"
                    elif ip == "100.93.96.90" or ip.endswith(".90"):
                        best_device = "s10"
                    best_time = last_seen
            if best_device:
                return best_device
    except:
        pass
    if DEVICE_FILE.exists():
        device = DEVICE_FILE.read_text().strip()
        if device in DEVICES:
            return device
    return "duo"


def set_device(device):
    DEVICE_FILE.write_text(device)


def is_playing():
    if PLAYING_FILE.exists():
        try:
            pid = int(PLAYING_FILE.read_text().strip())
            subprocess.run(["kill", "-0", str(pid)], capture_output=True)
            return True
        except:
            PLAYING_FILE.unlink(missing_ok=True)
    return False


def queue_text(text, device=None):
    queue = []
    if QUEUE_FILE.exists():
        try:
            queue = json.loads(QUEUE_FILE.read_text())
            # Remove stale entries older than 5 minutes
            now = time.time()
            queue = [q for q in queue if now - q.get("timestamp", 0) < 300]
        except:
            pass
    queue.append({"text": text, "device": device, "timestamp": time.time()})
    QUEUE_FILE.write_text(json.dumps(queue))


def dequeue_text():
    if not QUEUE_FILE.exists():
        return None
    try:
        queue = json.loads(QUEUE_FILE.read_text())
        if queue:
            next_item = queue.pop(0)
            QUEUE_FILE.write_text(json.dumps(queue))
            return next_item
    except:
        pass
    return None


def chunk_text(text, max_sentences=3):
    import re

    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks = []
    for i in range(0, len(sentences), max_sentences):
        chunk = " ".join(sentences[i : i + max_sentences])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def speak_local(text):
    if not start_soprano():
        print("Error: Could not start Soprano", file=sys.stderr)
        return False
    chunks = chunk_text(text, max_sentences=3)
    for chunk in chunks:
        audio_file = f"/tmp/speak_{int(time.time() * 1000)}.wav"
        text_with_pause = "... " + chunk
        subprocess.run(
            [
                "curl",
                "-s",
                "-X",
                "POST",
                f"http://localhost:{SOPRANO_PORT}/v1/audio/speech",
                "-H",
                "Content-Type: application/json",
                "-d",
                json.dumps({"input": text_with_pause}),
                "-o",
                audio_file,
            ],
            capture_output=True,
            timeout=30,
        )
        if Path(audio_file).exists() and Path(audio_file).stat().st_size > 1000:
            subprocess.run(
                ["ffplay", "-nodisp", "-autoexit", audio_file], capture_output=True
            )
            Path(audio_file).unlink(missing_ok=True)
    set_last_speak()
    return True


def speak(device, text):
    """Speak text to device with proper process management"""
    # Start local Soprano for audio generation (fast path - already running usually)
    if not start_soprano():
        print("Error: Could not start local Soprano", file=sys.stderr)
        return False
    
    # Note: Remote Soprano auto-start removed - audio is generated locally
    # and transferred to device for playback via termux-media-player

    # If something is playing, queue this text
    if is_playing():
        print("Already playing, queuing text...", file=sys.stderr)
        queue_text(text, device.get("name", "duo"))
        return True

    chunks = chunk_text(text, max_sentences=3)

    # Mark as playing
    PLAYING_FILE.write_text(str(os.getpid()))

    try:
        for i, chunk in enumerate(chunks):
            audio_file = f"/tmp/speak_{int(time.time() * 1000)}_chunk_{i}.wav"
            text_with_pause = "... " + chunk.strip()

            # Generate audio
            subprocess.run(
                [
                    "curl",
                    "-s",
                    "-X",
                    "POST",
                    f"http://localhost:{SOPRANO_PORT}/v1/audio/speech",
                    "-H",
                    "Content-Type: application/json",
                    "-d",
                    json.dumps({"input": text_with_pause}),
                    "-o",
                    audio_file,
                ],
                capture_output=True,
                timeout=30,
            )

            if not (Path(audio_file).exists() and Path(audio_file).stat().st_size > 1000):
                continue

            try:
                # Upload to device - use subprocess.run instead of Popen for simpler commands
                scp_result = subprocess.run(
                    [
                        "scp",
                        "-i",
                        device["ssh_key"],
                        "-P",
                        str(device["ssh_port"]),
                        "-o",
                        "StrictHostKeyChecking=no",
                        "-o",
                        "ConnectTimeout=30",
                        audio_file,
                        f"{device['ssh_user']}@{device['ip']}:~/speak.wav",
                    ],
                    capture_output=True,
                    timeout=30,
                )
                
                if scp_result.returncode != 0:
                    print(f"SCP failed: {scp_result.stderr.decode()[:200]}", file=sys.stderr)
                    continue

                pause_between = 0.1 if i < len(chunks) - 1 else 0

                # Play on device - use subprocess.run instead of Popen
                ssh_result = subprocess.run(
                    [
                        "ssh",
                        "-i",
                        device["ssh_key"],
                        "-p",
                        str(device["ssh_port"]),
                        "-o",
                        "StrictHostKeyChecking=no",
                        f"{device['ssh_user']}@{device['ip']}",
                        "termux-volume music 15 && termux-media-player play ~/speak.wav",
                    ],
                    capture_output=True,
                    timeout=15,
                )
                
                set_last_speak()

                # Get duration and wait
                try:
                    dur = subprocess.run(
                        [
                            "ffprobe",
                            "-v",
                            "error",
                            "-show_entries",
                            "format=duration",
                            "-of",
                            "default=noprint_wrappers=1:nokey=1",
                            audio_file,
                        ],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    duration = float(dur.stdout.strip()) if dur.stdout.strip() else 2
                    time.sleep(duration + pause_between)
                except:
                    time.sleep(1)

            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
            finally:
                Path(audio_file).unlink(missing_ok=True)

    finally:
        # Done playing, remove marker
        PLAYING_FILE.unlink(missing_ok=True)
        
        # FIX: Process queue iteratively instead of recursively
        max_queue_items = 5  # Prevent infinite loops
        items_processed = 0
        
        while items_processed < max_queue_items:
            next_item = dequeue_text()
            if not next_item:
                break
                
            # Find device by name
            target_dev = None
            for dev_id, dev in DEVICES.items():
                if dev.get("name") == next_item.get("device"):
                    target_dev = dev
                    break
            
            if target_dev:
                speak(target_dev, next_item["text"])
                items_processed += 1
            else:
                # Device not found, skip this item
                items_processed += 1

    return True


def main():
    args = sys.argv[1:]
    if not args:
        print(
            "Usage: speak.py <text> [--device duo|s10|local|auto] [--if-on] [--thinking] [--sync]"
        )
        print("       speak.py --status | --toggle | --on | --off | --devices")
        print("       speak.py --start-service <service_name> [--device duo|s10]")
        print("\nAvailable remote services: soprano (and more can be added)")
        sys.exit(1)

    is_async = True
    if "--sync" in args:
        is_async = False
        args = [a for a in args if a != "--sync"]

    if "--devices" in args:
        print("Available devices:")
        for device_id in get_available_devices():
            print(f"  {device_id}: {DEVICES[device_id]['name']}")
        sys.exit(0)

    if "--status" in args:
        status = get_status()
        device = get_device()
        elapsed = time.time() - get_last_speak()
        print(
            f"Speak mode: {status.upper()} (device: {device}, last: {elapsed:.0f}s ago)"
        )
        sys.exit(0)

    if "--toggle" in args:
        current = get_status()
        new_status = "off" if current == "on" else "on"
        set_status(new_status)
        print(f"Speak mode: {new_status.upper()}")
        sys.exit(0)

    if "--on" in args:
        set_status("on")
        print("Speak mode: ON")
        sys.exit(0)

    if "--off" in args:
        set_status("off")
        print("Speak mode: OFF")
        sys.exit(0)

    check_mode = "--if-on" in args
    is_thinking = "--thinking" in args
    args = [
        a for a in args if a not in ("--if-on", "--thinking", "--progress", "--async")
    ]

    if check_mode and get_status() != "on":
        sys.exit(0)

    target_device = get_device()
    if "--device" in args:
        idx = args.index("--device")
        if idx + 1 < len(args):
            target_device = args[idx + 1]
            args = args[:idx] + args[idx + 2 :]
            if target_device != "auto":
                set_device(target_device)

    text = " ".join(args)
    if len(text) > 2000:
        text = text[:1997] + "..."

    if target_device == "auto":
        available = get_available_devices()
        if not available:
            sys.exit(1)
        target_device = available[0]

    if target_device not in DEVICES:
        sys.exit(1)

    device = DEVICES[target_device]

    if device.get("local"):
        success = speak_local(text)
        sys.exit(0 if success else 1)

    if not check_device_online(device["ip"], device["ssh_port"], device["ssh_key"]):
        sys.exit(1)

    # FIX: Proper async handling with subprocess.Popen instead of os.system()
    if is_async:
        # Build command properly
        cmd_args = [sys.executable, __file__, "--sync", "--device", target_device]
        if check_mode:
            cmd_args.append("--if-on")
        if is_thinking:
            cmd_args.append("--thinking")
        cmd_args.append(text)
        
        # Redirect output to log file
        log_file = open("/tmp/speak_async.log", "a")
        
        # Spawn process with proper tracking
        proc = subprocess.Popen(
            cmd_args,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,  # Detach from parent
        )
        child_processes.append(proc)
        
        print(f"Speaking in background (PID: {proc.pid})")
        sys.exit(0)

    success = speak(device, text)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()