#!/usr/bin/env python3
"""
Dagger Module for D-Model-Runner Multi-Version Testing
Tests DMR against multiple Python versions concurrently
"""

import dagger
from dagger import dag, function, object_type


@object_type
class DMRTest:
    """D-Model-Runner testing utilities"""

    @function
    async def test_multi_version(self) -> str:
        """Test DMR against multiple Python versions concurrently"""

        versions = ["3.10", "3.11", "3.12"]
        results = []

        # Get reference to the local project
        src = dag.host().directory(".")

        for version in versions:
            print(f"🐍 Testing DMR with Python {version}")

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
            )

            try:
                # Test DMR compatibility
                result = await python.with_exec([
                    "python", "-c", """
import sys
print(f'Python version: {sys.version.split()[0]}')

# Test imports
try:
    import dmr
    print('✅ DMR import successful')
except ImportError as e:
    print(f'❌ DMR import failed: {e}')
    exit(1)

# Test configuration
try:
    from dmr.config import ConfigManager
    config = ConfigManager()
    config.load_config('dev')
    print('✅ Configuration system working')
except Exception as e:
    print(f'❌ Configuration test failed: {e}')
    exit(1)

# Test storage
try:
    from dmr.storage import ConversationManager
    cm = ConversationManager()
    conv = cm.create_conversation('Test', 'ai/gemma3')
    print('✅ Storage system working')
except Exception as e:
    print(f'❌ Storage test failed: {e}')
    exit(1)

print('🎉 All tests passed!')
"""
                ]).sync()

                results.append(f"✅ Python {version}: SUCCESS")
                print(f"✅ Python {version} test completed successfully")

            except Exception as e:
                results.append(f"❌ Python {version}: FAILED - {e}")
                print(f"❌ Python {version} test failed: {e}")

        # Return summary
        summary = "\n".join(results)
        summary += f"\n\n🎯 Multi-version testing completed!"
        summary += f"\n📊 Tested versions: {', '.join(versions)}"
        summary += f"\n✅ Successful: {sum(1 for r in results if 'SUCCESS' in r)}/{len(versions)}"

        return summary

    @function
    async def benchmark_performance(self) -> str:
        """Benchmark DMR performance across Python versions"""

        versions = ["3.10", "3.11", "3.12"]
        benchmarks = []

        # Get reference to the local project
        src = dag.host().directory(".")

        for version in versions:
            print(f"⚡ Benchmarking Python {version}")

            try:
                # Create container for performance test
                container = (
                    dag.container()
                    .from_(f"python:{version}-slim")
                    .with_directory("/dmr", src)
                    .with_workdir("/dmr")
                    .with_exec(["apt-get", "update"])
                    .with_exec(["apt-get", "install", "-y", "gcc", "g++", "libyaml-dev"])
                    .with_exec(["pip", "install", "--upgrade", "pip"])
                    .with_exec(["pip", "install", "-r", "requirements.txt"])
                    .with_exec(["python", "-c", """
import time
from dmr.config import ConfigManager
from dmr.storage import ConversationManager

print('Running performance benchmark...')

# Performance test
start = time.time()

# Test configuration loading (100 iterations)
config = ConfigManager()
for i in range(100):
    config.load_config('dev')

# Test storage operations (50 conversations)
cm = ConversationManager()
for i in range(50):
    conv = cm.create_conversation(f'Benchmark-{i}', 'ai/gemma3')
    conv.add_message('user', f'Performance test message {i}')
    conv.add_message('assistant', f'Response {i}')

end = time.time()
duration = end - start

print(f'Benchmark completed in {duration:.3f} seconds')
print(f'Operations per second: {(100 + 50 * 2) / duration:.1f}')
"""])
                )

                # Execute container
                await container.sync()

                benchmarks.append(f"⚡ Python {version}: Completed")
                print(f"✅ Python {version} benchmark completed")

            except Exception as e:
                benchmarks.append(f"❌ Python {version}: FAILED")
                print(f"❌ Python {version} benchmark failed: {e}")

        # Return benchmark results
        summary = "Performance Benchmark Results:\n"
        summary += "\n".join(benchmarks)
        summary += "\n\n📊 Benchmarking completed!"

        return summary

    @function
    async def test_dagger_integration(self) -> str:
        """Test Dagger CLI integration with DMR"""

        print("🔧 Testing Dagger + DMR Integration")

        try:
            # Get reference to the local project
            src = dag.host().directory(".")

            # Test basic Dagger + DMR integration
            result = await (
                dag.container()
                .from_("python:3.11-slim")
                .with_directory("/dmr", src)
                .with_workdir("/dmr")
                .with_exec(["apt-get", "update"])
                .with_exec(["apt-get", "install", "-y", "gcc", "g++", "libyaml-dev"])
                .with_exec(["pip", "install", "--upgrade", "pip"])
                .with_exec(["pip", "install", "-r", "requirements.txt"])
                .with_exec(["python", "-c", """
print('Testing Dagger + DMR integration...')

# Test DMR functionality
from dmr.config import ConfigManager
from dmr.storage import ConversationManager

config = ConfigManager()
config.load_config('dev')
print('✅ Configuration loaded')

cm = ConversationManager()
conv = cm.create_conversation('Dagger Test', 'ai/gemma3')
conv.add_message('user', 'Hello from Dagger!')
print('✅ Conversation created')

print('🎉 Dagger + DMR integration successful!')
"""])
            ).sync()

            return "✅ Dagger CLI integration test PASSED"

        except Exception as e:
            return f"❌ Dagger CLI integration test FAILED: {e}"