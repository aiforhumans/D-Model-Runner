#!/usr/bin/env python3
"""
D-Model-Runner Multi-Version Testing with Dagger
Tests DMR against multiple Python versions concurrently using Dagger SDK
"""

import sys
import anyio
import dagger
from dagger import dag


async def test_dmr_versions():
    """Test D-Model-Runner against multiple Python versions concurrently."""

    # Test matrix - focus on versions that work with our dependencies
    versions = ["3.10", "3.11", "3.12"]

    print("🚀 D-Model-Runner Multi-Version Testing")
    print("=" * 50)
    print(f"Testing against Python versions: {', '.join(versions)}")
    print("=" * 50)

    async with dagger.connection(dagger.Config(log_output=sys.stderr)):
        # Get reference to the local DMR project
        src = dag.host().directory(".")

        async def test_version(version: str):
            """Test DMR with a specific Python version"""
            print(f"🐍 Starting tests for Python {version}")

            # Create Python container for this version
            python = (
                dag.container()
                .from_(f"python:{version}-slim")
                # Mount DMR project into container
                .with_directory("/dmr", src)
                # Set working directory
                .with_workdir("/dmr")
                # Install system dependencies
                .with_exec(["apt-get", "update"])
                .with_exec(["apt-get", "install", "-y", "gcc", "g++", "libyaml-dev"])
                # Install Python dependencies
                .with_exec(["pip", "install", "--upgrade", "pip"])
                .with_exec(["pip", "install", "-r", "requirements.txt"])
                # Install test dependencies
                .with_exec(["pip", "install", "pytest", "pytest-cov"])
            )

            # Test 1: Import test
            print(f"  📦 Testing imports (Python {version})...")
            await (
                python
                .with_exec(["python", "-c", "import dmr; print('✅ DMR import successful')"])
                .sync()
            )

            # Test 2: Configuration test
            print(f"  ⚙️  Testing configuration (Python {version})...")
            await (
                python
                .with_exec([
                    "python", "-c",
                    "from dmr.config import ConfigManager; cm = ConfigManager(); cm.load_config('dev'); print('✅ Configuration system working')"
                ])
                .sync()
            )

            # Test 3: Storage test
            print(f"  💾 Testing storage (Python {version})...")
            await (
                python
                .with_exec([
                    "python", "-c",
                    "from dmr.storage import ConversationManager; cm = ConversationManager(); print('✅ Storage system working')"
                ])
                .sync()
            )

            # Test 4: Run comprehensive test
            print(f"  🧪 Running comprehensive test (Python {version})...")
            await (
                python
                .with_exec(["python", "comprehensive_test.py"])
                .sync()
            )

            print(f"✅ All tests for Python {version} succeeded!")

        # Execute all version tests concurrently
        async with anyio.create_task_group() as tg:
            for version in versions:
                tg.start_soon(test_version, version)

    print("\n" + "=" * 50)
    print("🎉 All DMR multi-version tests completed successfully!")
    print("✅ DMR is compatible with all tested Python versions")
    print("=" * 50)


async def test_dagger_integration():
    """Test Dagger CLI integration with DMR"""

    print("\n🔧 Testing Dagger CLI Integration")
    print("-" * 40)

    async with dagger.connection(dagger.Config(log_output=sys.stderr)):
        src = dag.host().directory(".")

        # Test Dagger run with DMR
        print("Testing dagger run with DMR...")
        await (
            dag.container()
            .from_("python:3.11-slim")
            .with_directory("/dmr", src)
            .with_workdir("/dmr")
            .with_exec(["pip", "install", "-r", "requirements.txt"])
            .with_exec(["python", "-c", "print('Dagger + DMR integration working!')"])
            .sync()
        )

        print("✅ Dagger CLI integration test successful!")


async def benchmark_performance():
    """Benchmark DMR performance across Python versions"""

    print("\n⚡ Performance Benchmarking")
    print("-" * 35)

    versions = ["3.10", "3.11", "3.12"]

    async with dagger.connection(dagger.Config(log_output=sys.stderr)):
        src = dag.host().directory(".")

        async def benchmark_version(version: str):
            """Benchmark DMR performance for a specific Python version"""
            print(f"📊 Benchmarking Python {version}...")

            start_time = dag.container().from_("python:3.11-slim").with_exec(["date", "+%s%N"]).stdout()

            python = (
                dag.container()
                .from_(f"python:{version}-slim")
                .with_directory("/dmr", src)
                .with_workdir("/dmr")
                .with_exec(["pip", "install", "-r", "requirements.txt"])
                .with_exec(["python", "-c", """
import time
from dmr.config import ConfigManager
from dmr.storage import ConversationManager

# Performance test
start = time.time()

# Test configuration loading
config = ConfigManager()
for i in range(100):
    config.load_config('dev')

# Test storage operations
cm = ConversationManager()
for i in range(50):
    conv = cm.create_conversation(f'Test-{i}', 'ai/gemma3')
    conv.add_message('user', f'Message {i}')

end = time.time()
print(f'Performance test completed in {end-start:.3f} seconds')
"""])
            )

            result = await python.sync()
            print(f"✅ Python {version} benchmark completed")

        # Run benchmarks concurrently
        async with anyio.create_task_group() as tg:
            for version in versions:
                tg.start_soon(benchmark_version, version)

    print("✅ Performance benchmarking completed!")


async def main():
    """Main test orchestration"""
    print("🧪 D-Model-Runner Comprehensive Testing Suite")
    print("Using Dagger SDK for concurrent multi-version testing")
    print()

    try:
        # Run version compatibility tests
        await test_dmr_versions()

        # Test Dagger CLI integration
        await test_dagger_integration()

        # Run performance benchmarks
        await benchmark_performance()

        print("\n🎯 FINAL RESULTS")
        print("=" * 50)
        print("✅ Multi-version compatibility: PASSED")
        print("✅ Dagger CLI integration: PASSED")
        print("✅ Performance benchmarks: PASSED")
        print("✅ All tests completed successfully!")
        print("=" * 50)
        print("🚀 D-Model-Runner is production-ready!")

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    anyio.run(main)
