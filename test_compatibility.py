#!/usr/bin/env python3
"""
Simple DMR Multi-Version Test (for dagger run)
Tests D-Model-Runner against multiple Python versions
"""

import os
import sys
import subprocess
import time
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"[EXECUTING] {description}")
    print(f"Command: {cmd}")

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("[SUCCESS]")
            return True, result.stdout.strip()
        else:
            print("[FAILED]")
            print(f"Error: {result.stderr[:200]}...")
            return False, result.stderr.strip()
    except Exception as e:
        print(f"[ERROR] {e}")
        return False, str(e)


def test_dmr_compatibility():
    """Test DMR compatibility with current Python version"""

    print("🐍 Testing D-Model-Runner Compatibility")
    print("-" * 45)

    tests_passed = 0
    total_tests = 0

    # Test 1: Python version
    total_tests += 1
    print(f"Python version: {sys.version}")
    if sys.version_info >= (3, 10):
        print("✅ Python version compatible")
        tests_passed += 1
    else:
        print("⚠️  Python version may have compatibility issues")

    # Test 2: Import DMR
    total_tests += 1
    try:
        import dmr
        print("✅ DMR import successful")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ DMR import failed: {e}")
        return False

    # Test 3: Configuration system
    total_tests += 1
    try:
        from dmr.config import ConfigManager
        config = ConfigManager()
        config.load_config('dev')
        print("✅ Configuration system working")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")

    # Test 4: Storage system
    total_tests += 1
    try:
        from dmr.storage import ConversationManager
        cm = ConversationManager()
        conv = cm.create_conversation("Test", "ai/gemma3")
        print("✅ Storage system working")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Storage test failed: {e}")

    # Test 5: Run comprehensive test
    total_tests += 1
    if os.path.exists('comprehensive_test.py'):
        success, output = run_command("python comprehensive_test.py", "Running comprehensive test")
        if success:
            tests_passed += 1
        else:
            print("❌ Comprehensive test failed")
    else:
        print("⚠️  Comprehensive test file not found")
        total_tests -= 1

    print(f"\n📊 Test Results: {tests_passed}/{total_tests} passed")

    if tests_passed == total_tests:
        print("🎉 All compatibility tests PASSED!")
        return True
    else:
        print("⚠️  Some tests failed - check compatibility")
        return tests_passed > total_tests * 0.7  # 70% success rate


def main():
    """Main test function"""
    print("🧪 D-Model-Runner Compatibility Test")
    print("=" * 50)
    print(f"Testing on Python {sys.version.split()[0]}")
    print("=" * 50)

    start_time = time.time()

    if test_dmr_compatibility():
        print("\n✅ DMR is compatible with this Python version!")
    else:
        print("\n❌ DMR has compatibility issues with this Python version")
        sys.exit(1)

    end_time = time.time()
    print(f"Test completed in {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    main()