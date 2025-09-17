#!/usr/bin/env python3
"""
D-Model-Runner Dagger SDK Demo
Simple demonstration of multi-version testing
"""

import sys
import anyio
import dagger
from dagger import dag


async def demo_dagger_sdk():
    """Demonstrate Dagger SDK with DMR"""

    print("🚀 D-Model-Runner Dagger SDK Demo")
    print("=" * 50)

    async with dagger.connection(dagger.Config(log_output=sys.stderr)):
        # Get reference to the local project
        src = dag.host().directory(".")

        # Test with current Python version
        print("🐍 Testing DMR with current Python environment")

        python = (
            dag.container()
            .from_("python:3.12-slim")
            .with_directory("/dmr", src)
            .with_workdir("/dmr")
            .with_exec(["apt-get", "update"])
            .with_exec(["apt-get", "install", "-y", "gcc", "g++", "libyaml-dev"])
            .with_exec(["pip", "install", "--upgrade", "pip"])
            .with_exec(["pip", "install", "-r", "requirements.txt"])
        )

        # Run a simple DMR test
        await python.with_exec([
            "python", "-c", """
print('=== D-Model-Runner Dagger SDK Test ===')

# Test basic functionality
from dmr.config import ConfigManager
from dmr.storage import ConversationManager

print('✅ Imports successful')

# Test configuration
config = ConfigManager()
config.load_config('dev')
print('✅ Configuration loaded')

# Test storage
cm = ConversationManager()
conv = cm.create_conversation('Dagger SDK Demo', 'ai/gemma3')
print('✅ Conversation created')

print('🎉 Dagger SDK + DMR integration working!')
"""
        ]).sync()

        print("✅ Dagger SDK demo completed successfully!")


if __name__ == "__main__":
    anyio.run(demo_dagger_sdk)