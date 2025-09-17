"""
AI-powered code analysis functions for Dagger integration
"""

import os
import asyncio
from typing import Optional
from openai import OpenAI
from .config import ConfigManager
from .storage import ConversationManager
from .utils.helpers import format_error_message


async def quick_analyze(source_directory) -> str:
    """
    Analyze a source directory and provide AI insights
    
    Args:
        source_directory: Dagger directory object
        
    Returns:
        AI analysis of the codebase
    """
    try:
        config_manager = ConfigManager()
        config_manager.load_config('dev')
        
        client = OpenAI(
            base_url=config_manager.get_base_url(),
            api_key="anything",
            timeout=30.0,
            max_retries=2
        )
        
        # Get file list from directory (simplified for example)
        prompt = """
        Analyze this codebase structure and provide insights about:
        1. Main functionality and purpose
        2. Code organization and architecture
        3. Potential improvements or issues
        4. Technology stack used
        
        Provide a concise but thorough analysis.
        """
        
        response = client.chat.completions.create(
            model=config_manager.get_default_model(),
            messages=[{"role": "user", "content": prompt}],
            **config_manager.get_model_config(config_manager.get_default_model())
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        error_msg = format_error_message(e, "code analysis")
        return f"❌ Analysis failed: {error_msg}"


async def generate_unit_tests(source_directory):
    """
    Generate unit tests for source code using AI
    
    Args:
        source_directory: Dagger directory object
        
    Returns:
        Directory object containing generated tests
    """
    try:
        config_manager = ConfigManager()
        config_manager.load_config('dev')
        
        client = OpenAI(
            base_url=config_manager.get_base_url(),
            api_key="anything",
            timeout=60.0,  # Longer timeout for test generation
            max_retries=2
        )
        
        prompt = """
        Generate comprehensive unit tests for the provided code.
        Include:
        1. Test cases for main functionality
        2. Edge cases and error scenarios
        3. Mock objects where appropriate
        4. Proper test structure and naming
        
        Use pytest framework and follow best practices.
        """
        
        response = client.chat.completions.create(
            model=config_manager.get_default_model(),
            messages=[{"role": "user", "content": prompt}],
            **config_manager.get_model_config(config_manager.get_default_model())
        )
        
        # In a real implementation, this would create actual test files
        # For now, return the source directory as placeholder
        print("Generated test content:", response.choices[0].message.content)
        return source_directory
        
    except Exception as e:
        error_msg = format_error_message(e, "test generation")
        print(f"❌ Test generation failed: {error_msg}")
        return source_directory


async def explain_file(source_directory, filename: str) -> str:
    """
    Explain what a specific file does using AI
    
    Args:
        source_directory: Dagger directory object
        filename: Name of file to explain
        
    Returns:
        AI explanation of the file
    """
    try:
        config_manager = ConfigManager()
        config_manager.load_config('dev')
        
        client = OpenAI(
            base_url=config_manager.get_base_url(),
            api_key="anything",
            timeout=30.0,
            max_retries=2
        )
        
        prompt = f"""
        Explain what the file '{filename}' does. Include:
        1. Main purpose and functionality
        2. Key classes, functions, or components
        3. How it fits into the larger system
        4. Any dependencies or relationships
        
        Provide a clear, concise explanation suitable for documentation.
        """
        
        response = client.chat.completions.create(
            model=config_manager.get_default_model(),
            messages=[{"role": "user", "content": prompt}],
            **config_manager.get_model_config(config_manager.get_default_model())
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        error_msg = format_error_message(e, "file explanation")
        return f"❌ File explanation failed: {error_msg}"
