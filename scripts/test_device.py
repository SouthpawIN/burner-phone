#!/usr/bin/env python3
"""
Test Device Connection
Quick script to verify device connectivity and capabilities
"""

import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from phone_agent import PhoneAgent
from config.device_config import create_example_config


def test_connection(agent: PhoneAgent):
    """Test basic device connectivity"""
    print("\n" + "="*50)
    print("DEVICE CONNECTION TEST")
    print("="*50)
    
    # Get device info
    info = agent.get_device_info()
    print(f"\n📱 Device: {info['name']}")
    print(f"🔧 Type: {info['type']}")
    print(f"🌐 IP: {info['ip']}")
    
    # Test online status
    print(f"\n🔍 Testing connectivity...")
    if agent.is_online():
        print("✅ Device is ONLINE and reachable")
    else:
        print("❌ Device is OFFLINE or unreachable")
        return False
    
    return True


def test_camera(agent: PhoneAgent):
    """Test camera capture"""
    print("\n📷 Testing camera...")
    
    if agent.capture_camera():
        print("✅ Camera capture successful")
        return True
    else:
        print("❌ Camera capture failed")
        return False


def test_audio(agent: PhoneAgent, duration: int = 2):
    """Test audio recording"""
    print(f"\n🎤 Testing audio recording ({duration}s)...")
    
    if agent.record_audio(duration, "/tmp/test_audio.wav"):
        print("✅ Audio recording successful")
        
        # Test playback (optional, can be loud!)
        play = input("\n🔊 Play back the recording? (y/N): ")
        if play.lower() == 'y':
            if agent.play_audio("/tmp/test_audio.wav"):
                print("✅ Audio playback successful")
            else:
                print("❌ Audio playback failed")
        return True
    else:
        print("❌ Audio recording failed")
        return False


def test_screen(agent: PhoneAgent):
    """Test screen control"""
    print("\n🖥️  Testing screen control...")
    
    # Test wake
    if agent.wake_screen():
        print("✅ Screen wake successful")
    else:
        print("⚠️  Screen wake failed (may already be awake)")
    
    # Test screenshot (ADB only)
    if hasattr(agent, 'screenshot'):
        if agent.screenshot("/tmp/test_screenshot.png"):
            print("✅ Screenshot successful")
        else:
            print("❌ Screenshot failed")


def main():
    """Run all tests"""
    print("\n" + "="*50)
    print("UNIVERSAL PHONE AGENT - DEVICE TESTER")
    print("="*50)
    
    # Check if config exists
    try:
        agent = PhoneAgent()
    except FileNotFoundError:
        print("\n❌ No configuration file found!")
        print("\nCreating example configuration...")
        create_example_config()
        print("\nPlease edit the config file and run this test again.")
        sys.exit(1)
    
    # Test connection
    if not test_connection(agent):
        print("\n" + "="*50)
        print("TROUBLESHOOTING:")
        print("="*50)
        print(f"1. Check if device is powered on")
        print(f"2. Verify IP address in config: {agent.config.ip_address}")
        print(f"3. For Termux: Ensure SSH is running on device")
        print(f"4. For ADB: Run 'adb connect {agent.config.ip_address}:5555'")
        print(f"5. Check Tailscale connection if using remote device")
        sys.exit(1)
    
    # Ask which tests to run
    print("\n" + "="*50)
    print("SELECT TESTS TO RUN")
    print("="*50)
    print("1. Camera only")
    print("2. Audio only (2 second recording)")
    print("3. Screen control only")
    print("4. All tests")
    print("5. Just connection test (already done)")
    
    choice = input("\nChoose test (1-4, default=4): ").strip() or "4"
    
    results = []
    
    if choice == "1" or choice == "4":
        results.append(("Camera", test_camera(agent)))
    
    if choice == "2" or choice == "4":
        results.append(("Audio", test_audio(agent)))
    
    if choice == "3" or choice == "4":
        test_screen(agent)
        results.append(("Screen", True))
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:15} {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Device is ready to use.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    print("="*50)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⛔ Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)