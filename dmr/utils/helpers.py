"""
Helper utilities for D-Model-Runner

Common utility functions used throughout the package.
"""

import re
from typing import Optional, Dict, Any


def validate_model_name(model: str) -> bool:
    """
    Validate if a model name follows the expected format.
    
    Args:
        model: Model name to validate (e.g., 'ai/gemma3', 'ai/qwen3')
        
    Returns:
        True if valid, False otherwise
    """
    if not model or not isinstance(model, str):
        return False
    
    # Pattern: namespace/model (e.g., ai/gemma3)
    pattern = r'^[a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+$'
    return bool(re.match(pattern, model))


def format_error_message(error: Exception, context: Optional[str] = None) -> str:
    """
    Format error messages consistently across the application.
    
    Args:
        error: The exception that occurred
        context: Optional context information
        
    Returns:
        Formatted error message string
    """
    error_msg = str(error)
    if context:
        return f"[{context}] {error_msg}"
    return error_msg


def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge two configuration dictionaries.
    
    Args:
        base_config: Base configuration dictionary
        override_config: Override configuration dictionary
        
    Returns:
        Merged configuration dictionary
    """
    result = base_config.copy()
    
    for key, value in override_config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    
    return result


def safe_get_nested(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    """
    Safely get a nested value from a dictionary using dot notation.
    
    Args:
        data: Dictionary to search
        path: Dot-separated path (e.g., 'api.models.default')
        default: Default value if path not found
        
    Returns:
        Value at path or default
    """
    keys = path.split('.')
    current = data
    
    try:
        for key in keys:
            current = current[key]
        return current
    except (KeyError, TypeError):
        return default