#!/bin/bash
# Termux SSH Recovery Script
# Automatically restarts Termux SSH services on Android devices

DEVICES=(
    "duo:100.79.15.54"
    "s10:100.93.96.90"
)

SSH_KEY="$HOME/.ssh/phone_access"
SSH_PORT=8022

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

check_device() {
    local device_name=$1
    local device_ip=$2
    
    log "Checking $device_name at $device_ip..."
    
    if ssh -i "$SSH_KEY" -p $SSH_PORT -o ConnectTimeout=3 -o StrictHostKeyChecking=no \
       droid@$device_ip "echo ok" 2>/dev/null; then
        log "✓ $device_name is already online"
        return 0
    else
        log "✗ $device_name SSH not responding"
        return 1
    fi
}

restart_termux_ssh() {
    local device_name=$1
    local device_ip=$2
    
    log "Attempting to restart Termux SSH on $device_name..."
    
    # Try to start SSH via termux:service command through ADB
    # This requires the device to be accessible via ADB
    
    # First, check if we can reach it via ADB over network
    adb wait-for-device $device_ip 2>/dev/null
    
    # Try starting Termux service
    adb -s $(adb devices | grep $device_ip | cut -f1) shell "termux-service sshd" 2>/dev/null
    
    sleep 3
    
    # Verify it started
    if check_device "$device_name" "$device_ip"; then
        log "✓ Successfully restarted SSH on $device_name"
        return 0
    else
        log "✗ Could not restart SSH on $device_name - may need manual intervention"
        return 1
    fi
}

main() {
    log "=== Termux SSH Recovery Started ==="
    
    local success=0
    local failed=0
    
    for device_info in "${DEVICES[@]}"; do
        IFS=':' read -r name ip <<< "$device_info"
        
        if ! check_device "$name" "$ip"; then
            if restart_termux_ssh "$name" "$ip"; then
                ((success++))
            else
                ((failed++))
            fi
        else
            ((success++))
        fi
    done
    
    log "=== Recovery Complete: $success successful, $failed failed ==="
    
    if [ $failed -gt 0 ]; then
        log "Note: Devices that failed may need manual SSH restart via Termux app"
        return 1
    fi
    return 0
}

main