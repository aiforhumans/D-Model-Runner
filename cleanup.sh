#!/bin/sh
# D-Model-Runner Cleanup Script
# Safe cleanup commands for Dagger CLI execution

echo '=== D-Model-Runner Cleanup Started ==='
echo 'Timestamp:' \09/17/2025 18:31:42
echo ''

echo '1. Cleaning Python cache directories...'
find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
echo '   Python cache directories cleaned'

echo ''
echo '2. Cleaning Python bytecode files...'
find . -type f -name '*.pyc' -delete 2>/dev/null || true
find . -type f -name '*.pyo' -delete 2>/dev/null || true
echo '   Python bytecode files cleaned'

echo ''
echo '3. Cleaning temporary files...'
find . -type f \( -name '*.tmp' -o -name '*.temp' -o -name '*.bak' -o -name '*.orig' -o -name '*.swp' -o -name '*.swo' -o -name '.DS_Store' -o -name 'Thumbs.db' \) -delete 2>/dev/null || true
echo '   Temporary files cleaned'

echo ''
echo '4. Cleaning log files...'
find . -type f \( -name '*.log' -o -name '*.log.*' \) -delete 2>/dev/null || true
echo '   Log files cleaned'

echo ''
echo '5. Cleaning test and coverage artifacts...'
find . -type d \( -name '.coverage' -o -name 'htmlcov' -o -name '.pytest_cache' -o -name '.mypy_cache' -o -name '.tox' \) -exec rm -rf {} + 2>/dev/null || true
echo '   Test artifacts cleaned'

echo ''
echo '6. Cleaning build artifacts...'
find . -type d \( -name 'build' -o -name 'dist' -o -name '*.egg-info' -o -name '.eggs' \) -exec rm -rf {} + 2>/dev/null || true
echo '   Build artifacts cleaned'

echo ''
echo '=== Cleanup Summary ==='
echo 'Cleanup completed successfully!'
echo 'Timestamp:' \09/17/2025 18:31:42
