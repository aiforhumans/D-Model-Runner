"""
Test suite for D-Model-Runner.

This package contains comprehensive tests for all components of the D-Model-Runner
system, including unit tests, integration tests, and performance benchmarks.

Test Structure:
- unit/: Unit tests for individual components
- integration/: Integration tests for component interactions
- performance/: Performance benchmarks and profiling
- fixtures/: Test data and configuration fixtures
"""

import sys
from pathlib import Path

# Add the project root to the Python path for testing
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))