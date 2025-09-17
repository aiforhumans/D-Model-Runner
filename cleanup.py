#!/usr/bin/env python3
# D-Model-Runner Cleanup Script
# Python-based cleanup for Dagger CLI execution

import os
import shutil
import glob
import time
from pathlib import Path

def safe_remove_dir(path):
    '''Safely remove a directory if it exists'''
    try:
        if os.path.exists(path) and os.path.isdir(path):
            shutil.rmtree(path)
            print(f'Removed directory: {path}')
    except Exception as e:
        print(f'Warning: Could not remove {path}: {e}')

def safe_remove_files(pattern):
    '''Safely remove files matching a pattern'''
    try:
        files = glob.glob(pattern, recursive=True)
        for file_path in files:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f'Removed file: {file_path}')
    except Exception as e:
        print(f'Warning: Could not remove files matching {pattern}: {e}')

def main():
    print('=== D-Model-Runner Cleanup Started ===')
    print(f'Timestamp: {time.ctime()}')
    print()

    # Change to the project root (where this script is located)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    print('1. Cleaning Python cache directories...')
    for root, dirs, files in os.walk('.'):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                cache_path = os.path.join(root, dir_name)
                safe_remove_dir(cache_path)
    print('   Python cache directories cleaned')
    print()

    print('2. Cleaning Python bytecode files...')
    safe_remove_files('**/*.pyc')
    safe_remove_files('**/*.pyo')
    print('   Python bytecode files cleaned')
    print()

    print('3. Cleaning temporary files...')
    patterns = [
        '**/*.tmp', '**/*.temp', '**/*.bak', '**/*.orig',
        '**/*.swp', '**/*.swo', '**/.DS_Store', '**/Thumbs.db'
    ]
    for pattern in patterns:
        safe_remove_files(pattern)
    print('   Temporary files cleaned')
    print()

    print('4. Cleaning log files...')
    safe_remove_files('**/*.log')
    safe_remove_files('**/*.log.*')
    print('   Log files cleaned')
    print()

    print('5. Cleaning test and coverage artifacts...')
    artifacts = [
        '.coverage', 'htmlcov', '.pytest_cache',
        '.mypy_cache', '.tox'
    ]
    for artifact in artifacts:
        safe_remove_dir(artifact)
    print('   Test artifacts cleaned')
    print()

    print('6. Cleaning build artifacts...')
    build_dirs = ['build', 'dist', '.eggs']
    for build_dir in build_dirs:
        safe_remove_dir(build_dir)

    # Clean egg-info directories
    for root, dirs, files in os.walk('.'):
        for dir_name in dirs:
            if dir_name.endswith('.egg-info'):
                egg_path = os.path.join(root, dir_name)
                safe_remove_dir(egg_path)
    print('   Build artifacts cleaned')
    print()

    print('=== Cleanup Summary ===')
    print('Cleanup completed successfully!')
    print(f'Timestamp: {time.ctime()}')

if __name__ == '__main__':
    main()
