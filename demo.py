#!/usr/bin/env python3
"""
Hermes Phone Agent - Live Demo Script
======================================

Demonstrates the complete 24/7 always-on phone agent system to Hermes creators.
Runs through all major features with visual feedback.

Usage:
    python3 demo.py              # Full demo
    python3 demo.py --attention  # Just attention detection
    python3 demo.py --automation # Just app automation
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Try to import components
try:
    from phone_agent import PhoneAgent
except ImportError:
    print("Warning: burner-phone not fully installed, using mock")
    PhoneAgent = None


def print_banner():
    """Print demo banner"""
    print("\n" + "="*70)
    print("       HERMES PHONE AGENT - LIVE DEMO")
    print("   Always-On Embodied AI via Android Device")
    print("="*70)
    print(f"\n📱 Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Showing how Hermes becomes a persistent physical presence\n")


def check_prerequisites():
    """Verify everything is set up"""
    print("🔍 Checking prerequisites...")
    
    checks = [
        ("Config file", Path("~/.hermes-phone-agent/config.yaml").expanduser().exists()),
        ("Attention skill", Path("/home/sovthpaw/Senter/skills/senter-attention/").exists()),
        ("Speak skill", Path("/home/sovthpaw/Senter/skills/speak/").exists()),
        ("Hermes hook", Path("~/.hermes/hooks/senter-wake/").expanduser().exists()),
    ]
    
    all_ok = True
    for name, ok in checks:
        status = "✅" if ok else "❌"
        print(f"   {status} {name}")
        if not ok:
            all_ok = False
    
    print()
    return all_ok


def demo_attention_detection():
    """Demo 1: Continuous attention detection"""
    print("\n" + "="*70)
    print("DEMO 1: ALWAYS-ON ATTENTION DETECTION")
    print("="*70)
    
    print("\n👁️  Current state: Phone is streaming camera + mic to Qwen Omni")
    print("📊 Monitoring attention log in real-time...\n")
    
    log_file = Path("/tmp/senter-attention.log")
    
    if not log_file.exists():
        print(f"⚠️  Attention log not found at {log_file}")
        print("   Make sure stream-attention.py is running:")
        print("   python3 /home/sovthpaw/Senter/skills/senter-attention/scripts/stream-attention.py --daemon")
        return False
    
    # Show last few entries
    print("Recent attention states:")
    with open(log_file, 'r') as f:
        lines = f.readlines()[-5:]  # Last 5 entries
        
        for line in lines:
            try:
                entry = json.loads(line)
                addressing = entry.get('addressing', False)
                confidence = entry.get('confidence', 0)
                ts = entry.get('ts', '')[:19]  # Timestamp
                
                indicator = "🔴 ADDRESSING" if addressing else "🟢 Idle"
                print(f"   [{ts}] {indicator} (confidence: {confidence:.2f})")
                
            except json.JSONDecodeError:
                continue
    
    print("\n🎤 Try it yourself:")
    print("   1. Look at the phone camera")
    print("   2. Say 'Senter' or 'Hermes'")
    print("   3. Watch the log update in real-time")
    
    return True


def demo_app_automation():
    """Demo 2: Vision-guided app automation"""
    print("\n" + "="*70)
    print("DEMO 2: VISION-GUIDED APP AUTOMATION")
    print("="*70)
    
    if not PhoneAgent:
        print("⚠️  PhoneAgent not available, showing concept only")
        
        print("\n📸 How it works:")
        print("   1. Take screenshot of home screen")
        print("   2. Send to Qwen Omni Vision model")
        print("   3. Model returns: 'Twitter icon at coordinates (540, 1200)'")
        print("   4. Execute: adb shell input tap 540 1200")
        print("   5. App opens!")
        
        print("\n📝 Example command:")
        print('   python3 scripts/vision_helper.py ./assets/screen.png "Find Twitter icon coordinates"')
        return False
    
    try:
        agent = PhoneAgent()
        
        if not agent.is_online():
            print(f"❌ Device offline: {agent.config.name}")
            return False
        
        print(f"\n✅ Connected to: {agent.config.name}")
        
        # Take screenshot
        print("\n📸 Taking screenshot...")
        if agent.screenshot("./assets/demo_screen.png"):
            print("✅ Screenshot saved to ./assets/demo_screen.png")
            
            # Analyze with vision
            print("\n🧠 Analyzing screen with Qwen Omni Vision...")
            print("   (This would normally find app icons and coordinates)")
            
            print("\n💡 Try commands:")
            print('   "Open Twitter" → Finds icon, taps it')
            print('   "Scroll down" → Swipes screen')
            print('   "Type hello" → Enters text in active field')
            
            return True
        else:
            print("❌ Screenshot failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def_demo_proactive_monitoring():
    """Demo 3: Proactive alerts"""
    print("\n" + "="*70)
    print("DEMO 3: PROACTIVE MONITORING")
    print("="*70)
    
    print("\n🔍 Phone agent monitors:")
    print("   • Battery level (alerts at <20% and <10%)")
    print("   • Notifications (summarizes important ones)")
    print("   • System health (storage, memory)")
    print("   • Network connectivity")
    
    try:
        from proactive_monitor import ProactiveMonitor
        
        monitor = ProactiveMonitor()
        
        # Check battery
        print("\n🔋 Current battery status:")
        battery = monitor.get_battery_status()
        
        if battery:
            print(f"   Level: {battery.level}%")
            print(f"   Charging: {'Yes' if battery.charging else 'No'}")
            print(f"   Temperature: {battery.temperature}°C")
            print(f"   Health: {battery.health}")
        else:
            print("   Unable to retrieve (device may be offline)")
        
        # Check notifications
        print("\n🔔 Recent notifications:")
        from scripts.notification_reader import NotificationReader
        
        reader = NotificationReader()
        notifs = reader.get_notifications()
        
        if notifs:
            summary = reader.summarize_notifications(notifs)
            print(f"   {summary}")
        else:
            print("   No new notifications")
        
        return True
        
    except ImportError:
        print("\n⚠️  Proactive monitor not available")
        return False
    except Exception as e:
        print(f"\n⚠️  Error: {e}")
        return False


def demo_multi_device():
    """Demo 4: Multi-device routing"""
    print("\n" + "="*70)
    print("DEMO 4: MULTI-DEVICE AUDIO ROUTING")
    print("="*70)
    
    print("\n📱 Available devices:")
    
    # Check speak skill config
    speak_config = Path("/home/sovthpaw/Senter/skills/speak/speak.py")
    
    if speak_config.exists():
        print("   • duo (Surface Duo 2 - 100.79.15.54)")
        print("   • s10 (Samsung Galaxy S10 - 100.93.96.90)")
        print("   • local (Server speakers)")
        
        print("\n🔄 Audio routing:")
        print("   Current device: auto (detects most recent active)")
        print("   Switch command: python3 speak.py --device duo")
        
        print("\n🎤 Test speech routing:")
        print('   python3 /home/sovthpaw/Senter/skills/speak/speak.py "Testing audio routing" --device duo')
        print('   python3 /home/sovthpaw/Senter/skills/speak/speak.py "Testing audio routing" --device s10')
        
        return True
    else:
        print("   Speak skill not found")
        return False


def demo_conversation_memory():
    """Demo 5: Persistent conversation memory"""
    print("\n" + "="*70)
    print("DEMO 5: CONVERSATION MEMORY PERSISTENCE")
    print("="*70)
    
    memory_file = Path("~/.hermes-phone-agent/memory.json").expanduser()
    
    if not memory_file.exists():
        print(f"\n⚠️  No conversation history yet at {memory_file}")
        print("   Memory will be created after first interaction")
        return False
    
    try:
        with open(memory_file, 'r') as f:
            memory = json.load(f)
        
        print(f"\n📚 Current session: {memory.get('current_session', 'None')}")
        print(f"   Total sessions: {len(memory.get('sessions', []))}")
        print(f"   Stored facts: {len(memory.get('facts', {}))}")
        
        if memory.get('sessions'):
            latest = memory['sessions'][-1]
            print(f"\n🕐 Latest session started: {latest.get('started', 'Unknown')}")
            print(f"   Messages exchanged: {len(latest.get('messages', []))}")
        
        print("\n💡 Memory persists across:")
        print("   • Device reboots")
        print("   • Hermes gateway restarts")
        print("   • Days/weeks of conversations")
        
        return True
        
    except Exception as e:
        print(f"\n⚠️  Error reading memory: {e}")
        return False


def run_full_demo():
    """Run complete demo sequence"""
    print_banner()
    
    if not check_prerequisites():
        print("\n⚠️  Some prerequisites missing - demo may be limited\n")
    
    # Run all demos
    demo_attention_detection()
    demo_app_automation()
    demo_proactive_monitoring()
    demo_multi_device()
    demo_conversation_memory()
    
    # Summary
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    
    print("\n🎯 Key takeaways for Hermes creators:")
    print("   1. Continuous attention via multimodal streaming (not polling)")
    print("   2. Model-native logic through instructions (not Python conditionals)")
    print("   3. Skills-based architecture following Hermes conventions")
    print("   4. Embodied AI using $0 hardware (old Android phones)")
    print("   5. Persistent intelligence across sessions and days")
    
    print("\n📁 Documentation:")
    print("   • HACKATHON_OVERVIEW.md - Full project overview")
    print("   • HERMES_INTEGRATION.md - How this extends Hermes")
    print("   • burner-phone/SKILL.md - Device control skill")
    print("   • senter-attention/SKILL.md - Attention detection skill")
    
    print("\n🚀 Next steps:")
    print("   1. Review code structure in /home/sovthpaw/burner-phone/")
    print("   2. Check Hermes hook integration at ~/.hermes/hooks/senter-wake/")
    print("   3. Run live attention test: look at phone + speak")
    print("   4. Try app automation: 'Open Twitter' or similar")
    
    print("\n" + "="*70)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Hermes Phone Agent Demo")
    parser.add_argument("--attention", action="store_true", help="Just attention detection")
    parser.add_argument("--automation", action="store_true", help="Just app automation")
    parser.add_argument("--proactive", action="store_true", help="Just proactive monitoring")
    parser.add_argument("--devices", action="store_true", help="Just multi-device routing")
    
    args = parser.parse_args()
    
    if args.attention:
        demo_attention_detection()
    elif args.automation:
        demo_app_automation()
    elif args.proactive:
        demo_proactive_monitoring()
    elif args.devices:
        demo_multi_device()
    else:
        run_full_demo()


if __name__ == "__main__":
    main()