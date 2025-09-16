"""
Configuration parser for D-Model-Runner

Handles loading and parsing YAML and JSON configuration files
with validation and error handling.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
from ..utils.helpers import format_error_message


class ConfigParser:
    """Parse configuration files in YAML and JSON formats."""
    
    @classmethod
    def load_config_file(cls, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load configuration from a YAML or JSON file.
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            Parsed configuration dictionary
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If file format is unsupported or invalid
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Determine file type by extension
            if file_path.suffix.lower() in ['.yaml', '.yml']:
                return cls._parse_yaml(content, str(file_path))
            elif file_path.suffix.lower() == '.json':
                return cls._parse_json(content, str(file_path))
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        except Exception as e:
            raise ValueError(format_error_message(e, f"loading config from {file_path}"))
    
    @classmethod
    def _parse_yaml(cls, content: str, file_path: str) -> Dict[str, Any]:
        """
        Parse YAML content.
        
        Args:
            content: YAML content string
            file_path: File path for error reporting
            
        Returns:
            Parsed dictionary
        """
        try:
            data = yaml.safe_load(content)
            if data is None:
                return {}
            if not isinstance(data, dict):
                raise ValueError("YAML content must be a dictionary")
            return data
        except yaml.YAMLError as e:
            raise ValueError(format_error_message(e, f"parsing YAML in {file_path}"))
    
    @classmethod
    def _parse_json(cls, content: str, file_path: str) -> Dict[str, Any]:
        """
        Parse JSON content.
        
        Args:
            content: JSON content string
            file_path: File path for error reporting
            
        Returns:
            Parsed dictionary
        """
        try:
            data = json.loads(content)
            if not isinstance(data, dict):
                raise ValueError("JSON content must be an object")
            return data
        except json.JSONDecodeError as e:
            raise ValueError(format_error_message(e, f"parsing JSON in {file_path}"))
    
    @classmethod
    def save_config_file(cls, config: Dict[str, Any], file_path: Union[str, Path]) -> None:
        """
        Save configuration to a YAML or JSON file.
        
        Args:
            config: Configuration dictionary to save
            file_path: Path where to save the file
            
        Raises:
            ValueError: If file format is unsupported
        """
        file_path = Path(file_path)
        
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.safe_dump(config, f, default_flow_style=False, indent=2)
                elif file_path.suffix.lower() == '.json':
                    json.dump(config, f, indent=2, ensure_ascii=False)
                else:
                    raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        except Exception as e:
            raise ValueError(format_error_message(e, f"saving config to {file_path}"))
    
    @classmethod
    def validate_config_structure(cls, config: Dict[str, Any]) -> bool:
        """
        Validate basic configuration structure.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            True if structure is valid
            
        Raises:
            ValueError: If structure is invalid
        """
        if not isinstance(config, dict):
            raise ValueError("Configuration must be a dictionary")
        
        # Check for required top-level sections
        required_sections = ['api']
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required configuration section: {section}")
        
        # Validate API section
        api_config = config['api']
        if not isinstance(api_config, dict):
            raise ValueError("API configuration must be a dictionary")
        
        # Check for required API fields
        if 'base_url' not in api_config:
            raise ValueError("Missing required field: api.base_url")
        
        return True