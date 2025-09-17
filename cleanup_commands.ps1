# D-Model-Runner Cleanup Script for Dagger CLI
# This script provides comprehensive cleanup commands for the D-Model-Runner project

Write-Host '=== D-Model-Runner Cleanup Commands for Dagger CLI ===' -ForegroundColor Cyan
Write-Host ''

Write-Host '1. CLEAN PYTHON CACHE FILES (__pycache__ directories)' -ForegroundColor Yellow
Write-Host '   These are auto-generated Python bytecode files that can be safely deleted'
Write-Host '   Dagger Command:'
Write-Host '   dagger run find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true'
Write-Host ''

Write-Host '2. CLEAN BUILD ARTIFACTS (if any exist)' -ForegroundColor Yellow
Write-Host '   Remove build, dist, and egg directories'
Write-Host '   Dagger Command:'
Write-Host '   dagger run find . -type d \( -name build -o -name dist -o -name *.egg-info -o -name .eggs \) -exec rm -rf {} + 2>/dev/null || true'
Write-Host ''

Write-Host '3. CLEAN TEMPORARY FILES' -ForegroundColor Yellow
Write-Host '   Remove common temporary and backup files'
Write-Host '   Dagger Command:'
Write-Host '   dagger run find . -type f \( -name "*.tmp" -o -name "*.temp" -o -name "*.bak" -o -name "*.orig" -o -name "*.swp" -o -name "*.swo" -o -name ".DS_Store" -o -name "Thumbs.db" \) -delete'
Write-Host ''

Write-Host '4. CLEAN LOG FILES' -ForegroundColor Yellow
Write-Host '   Remove log files that may have accumulated'
Write-Host '   Dagger Command:'
Write-Host '   dagger run find . -type f \( -name "*.log" -o -name "*.log.*" \) -delete'
Write-Host ''

Write-Host '5. CLEAN COVERAGE AND TEST ARTIFACTS' -ForegroundColor Yellow
Write-Host '   Remove test coverage and cache files'
Write-Host '   Dagger Command:'
Write-Host '   dagger run find . -type d \( -name ".coverage" -o -name "htmlcov" -o -name ".pytest_cache" -o -name ".mypy_cache" \) -exec rm -rf {} + 2>/dev/null || true'
Write-Host ''

Write-Host '6. CLEAN DOCKER ARTIFACTS' -ForegroundColor Yellow
Write-Host '   Remove Docker build cache and temporary files'
Write-Host '   Dagger Command:'
Write-Host '   dagger run docker system prune -f && docker image prune -f'
Write-Host ''

Write-Host '7. COMPREHENSIVE CLEANUP SCRIPT' -ForegroundColor Green
Write-Host '   Run all cleanup commands in sequence:'
Write-Host ''
Write-Host '   # Create cleanup script'
Write-Host '   cat > cleanup.sh << '\''EOF'\'''
Write-Host '   #!/bin/bash'
Write-Host '   echo "Starting comprehensive cleanup..."'
Write-Host '   '
Write-Host '   # Clean Python cache'
Write-Host '   find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true'
Write-Host '   find . -type f -name "*.pyc" -delete'
Write-Host '   find . -type f -name "*.pyo" -delete'
Write-Host '   '
Write-Host '   # Clean build artifacts'
Write-Host '   find . -type d \( -name build -o -name dist -o -name *.egg-info -o -name .eggs \) -exec rm -rf {} + 2>/dev/null || true'
Write-Host '   '
Write-Host '   # Clean temporary files'
Write-Host '   find . -type f \( -name "*.tmp" -o -name "*.temp" -o -name "*.bak" -o -name "*.orig" -o -name "*.swp" -o -name "*.swo" -o -name ".DS_Store" -o -name "Thumbs.db" \) -delete'
Write-Host '   '
Write-Host '   # Clean log files'
Write-Host '   find . -type f \( -name "*.log" -o -name "*.log.*" \) -delete'
Write-Host '   '
Write-Host '   # Clean test and coverage artifacts'
Write-Host '   find . -type d \( -name ".coverage" -o -name "htmlcov" -o -name ".pytest_cache" -o -name ".mypy_cache" -o -name ".tox" \) -exec rm -rf {} + 2>/dev/null || true'
Write-Host '   '
Write-Host '   echo "Cleanup completed!"'
Write-Host '   EOF'
Write-Host '   '
Write-Host '   # Make executable and run'
Write-Host '   chmod +x cleanup.sh'
Write-Host '   dagger run ./cleanup.sh'
Write-Host ''

Write-Host '8. DISK USAGE ANALYSIS' -ForegroundColor Magenta
Write-Host '   Analyze disk usage before and after cleanup:'
Write-Host '   Dagger Command:'
Write-Host '   dagger run du -sh . && echo "--- Running cleanup ---" && ./cleanup.sh && echo "--- After cleanup ---" && du -sh .'
Write-Host ''

Write-Host '9. SAFE CLEANUP (Interactive)' -ForegroundColor Green
Write-Host '   For safer cleanup with confirmation:'
Write-Host '   Dagger Command:'
Write-Host '   dagger run find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true'
Write-Host '   dagger run find . -name "*.pyc" -exec rm -f {} + 2>/dev/null || true'
Write-Host ''

Write-Host '10. CLEANUP VERIFICATION' -ForegroundColor Cyan
Write-Host '    Verify cleanup was successful:'
Write-Host '    Dagger Command:'
Write-Host '    dagger run find . -type d -name __pycache__ | wc -l && echo "Python cache directories remaining"'
Write-Host '    dagger run find . -name "*.pyc" | wc -l && echo "Python bytecode files remaining"'
Write-Host ''

Write-Host '=== RECOMMENDED CLEANUP ORDER ===' -ForegroundColor Red
Write-Host '1. Start with Python cache cleanup (safest)'
Write-Host '2. Remove temporary files'
Write-Host '3. Clean log files'
Write-Host '4. Remove build artifacts (if any)'
Write-Host '5. Clean test artifacts'
Write-Host '6. Verify with disk usage analysis'
Write-Host ''

Write-Host '=== NOTES ===' -ForegroundColor Yellow
Write-Host '- Always backup important files before running cleanup'
Write-Host '- The .venv directory is NOT included in cleanup (needed for development)'
Write-Host '- These commands are safe to run multiple times'
Write-Host '- Use dagger run to execute in containerized environment'
