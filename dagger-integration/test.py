#!/usr/bin/env python3
"""
Test script for Dagger + Docker Model Runner integration
"""

import asyncio
import subprocess
import sys
from pathlib import Path


def check_docker_model_runner():
    """Check if Docker Model Runner is running"""
    print("🔍 Checking Docker Model Runner...")
    try:
        import requests
        response = requests.get("http://localhost:12434/engines/llama.cpp/v1/models", timeout=5)
        if response.status_code == 200:
            print("✅ Docker Model Runner is running")
            return True
    except:
        pass
    print("❌ Docker Model Runner not accessible")
    return False


def check_dagger():
    """Check if Dagger CLI is installed"""
    print("🔍 Checking Dagger CLI...")
    try:
        result = subprocess.run(["dagger", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Dagger CLI is installed")
            return True
    except:
        pass
    print("❌ Dagger CLI not found")
    return False


def test_dagger_module():
    """Test the Dagger module"""
    print("🔍 Testing Dagger module...")
    if not Path("dagger.json").exists():
        print("❌ dagger.json not found")
        return False

    try:
        result = subprocess.run(["dagger", "functions"], capture_output=True, text=True, cwd=".")
        if result.returncode == 0:
            print("✅ Dagger module loaded successfully")
            return True
    except:
        pass
    print("❌ Failed to load Dagger module")
    return False


async def test_dagger_connection():
    """Test Dagger Python SDK connection"""
    print("🔍 Testing Dagger Python SDK...")
    try:
        import dagger
        async with dagger.Connection() as client:
            print("✅ Dagger Python SDK connection successful")
            return True
    except ImportError:
        print("❌ Dagger Python SDK not installed")
        return False
    except Exception as e:
        print(f"❌ Dagger connection failed: {e}")
        return False


async def test_llm_integration():
    """Test LLM integration"""
    print("🔍 Testing LLM integration...")
    try:
        import dagger
        async with dagger.Connection() as client:
            llm = client.llm()
            print("✅ LLM object created successfully")
            return True
    except Exception as e:
        print(f"❌ LLM integration failed: {e}")
        return False


async def test_environment_config():
    """Test environment variable configuration"""
    print("🔍 Testing environment configuration...")
    import os

    required_vars = [
        "OPENAI_BASE_URL",
        "OPENAI_DISABLE_STREAMING",
        "OPENAI_MODEL"
    ]

    all_set = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var} = {value}")
        else:
            print(f"   ❌ {var} = NOT SET")
            all_set = False

    return all_set


async def run_async_tests():
    """Run all async tests"""
    print("\n🔬 Running Advanced Tests:")
    print("-" * 30)

    async_tests = [
        ("Dagger SDK Connection", test_dagger_connection),
        ("LLM Integration", test_llm_integration),
        ("Environment Config", test_environment_config),
    ]

    async_passed = 0
    for test_name, test_func in async_tests:
        print(f"\n📋 Testing {test_name}...")
        if await test_func():
            async_passed += 1

    return async_passed


def main():
    """Run all tests"""
    print("🧪 Dagger + Docker Model Runner Integration Test")
    print("=" * 60)

    # Basic tests
    basic_tests = [
        ("Docker Model Runner", check_docker_model_runner),
        ("Dagger CLI", check_dagger),
        ("Dagger Module", test_dagger_module),
    ]

    basic_passed = 0
    for test_name, test_func in basic_tests:
        print(f"\n📋 Testing {test_name}...")
        if test_func():
            basic_passed += 1

    # Async tests
    async_passed = asyncio.run(run_async_tests())

    # Summary
    total_passed = basic_passed + async_passed
    total_tests = len(basic_tests) + 3  # 3 async tests

    print(f"\n🎯 Results: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("\n🚀 Ready to use! Try:")
        print("  dagger call analyze-codebase --source=. --task=review")
        print("  python examples.py")
        print("  dagger shell  # Interactive mode")
    else:
        print("\n💡 Setup Instructions:")
        print("  1. Install Dagger: pip install dagger-io")
        print("  2. Install Dagger CLI: https://docs.dagger.io/install")
        print("  3. Set environment variables (see .env.example)")
        print("  4. Start Docker Model Runner")
        print("  5. Run: python setup_docker_model_runner.sh")

    return total_passed == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)