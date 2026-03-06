#!/data/data/com.termux/files/usr/bin/bash
# Auto-start SSH service for Termux
# Place this in ~/.termux/boot/ or run on startup

LOGFILE="$HOME/.termux/ssh_startup.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOGFILE"
}

# Wait for network to be ready
log "Waiting for network..."
for i in {1..30}; do
    if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        log "Network is up"
        break
    fi
    sleep 1
done

# Check if sshd is already running
if pgrep -x "sshd" >/dev/null; then
    log "SSH server already running, skipping startup"
    exit 0
fi

# Start SSH server
log "Starting SSH server on port 8022..."
/data/data/com.termux/files/usr/bin/sshd

# Verify it started
sleep 2
if pgrep -x "sshd" >/dev/null; then
    log "SSH server started successfully"
else
    log "ERROR: Failed to start SSH server"
    exit 1
fi