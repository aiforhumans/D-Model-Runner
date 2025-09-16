"""
Environment variable handler for D-Model-Runner configuration

Handles loading and processing environment variables with validation
and type conversion.
"""

import os
from typing import Dict, Any, Optional, Union


class EnvironmentHandler:
    """Handle environment variable loading and processing."""
    
    # Environment variable prefix for D-Model-Runner
    ENV_PREFIX = "DMR_"
    
    @classmethod
    def load_env_vars(cls) -> Dict[str, Any]:
        """
        Load all D-Model-Runner environment variables.
        
        Returns:
            Dictionary of environment variables with DMR_ prefix removed
        """
        env_vars = {}
        
        for key, value in os.environ.items():
            if key.startswith(cls.ENV_PREFIX):
                # Remove prefix and convert to lowercase
                clean_key = key[len(cls.ENV_PREFIX):].lower()
                env_vars[clean_key] = cls._convert_env_value(value)
        
        return env_vars
    
    @classmethod
    def get_env_var(cls, key: str, default: Any = None, var_type: type = str) -> Any:
        """
        Get a specific environment variable with type conversion.
        
        Args:
            key: Environment variable key (without DMR_ prefix)
            default: Default value if not found
            var_type: Type to convert to (str, int, float, bool)
            
        Returns:
            Environment variable value converted to specified type
        """
        env_key = f"{cls.ENV_PREFIX}{key.upper()}"
        value = os.environ.get(env_key, default)
        
        if value == default:
            return default
        
        return cls._convert_env_value(value, var_type)
    
    @classmethod
    def _convert_env_value(cls, value: str, target_type: type = str) -> Any:
        """
        Convert environment variable string to specified type.
        
        Args:
            value: String value from environment
            target_type: Type to convert to
            
        Returns:
            Converted value
        """
        if target_type == str:
            return value
        
        if target_type == bool:
            return value.lower() in ('true', '1', 'yes', 'on')
        
        if target_type == int:
            try:
                return int(value)
            except ValueError:
                return 0
        
        if target_type == float:
            try:
                return float(value)
            except ValueError:
                return 0.0
        
        # For other types, try direct conversion
        try:
            return target_type(value)
        except (ValueError, TypeError):
            return value
    
    @classmethod
    def set_env_var(cls, key: str, value: Union[str, int, float, bool]) -> None:
        """
        Set an environment variable with DMR_ prefix.
        
        Args:
            key: Variable key (without prefix)
            value: Value to set
        """
        env_key = f"{cls.ENV_PREFIX}{key.upper()}"
        os.environ[env_key] = str(value)
    
    @classmethod
    def get_config_overrides(cls) -> Dict[str, Any]:
        """
        Get environment variables formatted as configuration overrides.
        
        Returns:
            Dictionary suitable for merging with config files
        """
        env_vars = cls.load_env_vars()
        config_overrides = {}
        
        # Map common environment variables to config structure
        mapping = {
            'base_url': 'api.base_url',
            'api_key': 'api.key',
            'default_model': 'api.models.default',
            'max_tokens': 'api.models.max_tokens',
            'temperature': 'api.models.temperature',
            'debug': 'logging.debug',
            'log_level': 'logging.level'
        }
        
        for env_key, config_path in mapping.items():
            if env_key in env_vars:
                cls._set_nested_value(config_overrides, config_path, env_vars[env_key])
        
        return config_overrides
    
    @classmethod
    def _set_nested_value(cls, data: Dict[str, Any], path: str, value: Any) -> None:
        """
        Set a nested value in a dictionary using dot notation.
        
        Args:
            data: Dictionary to modify
            path: Dot-separated path
            value: Value to set
        """
        keys = path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value