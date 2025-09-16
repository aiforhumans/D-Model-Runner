"""
Main configuration manager for D-Model-Runner

Central configuration orchestrator that handles loading, merging,
and managing configuration from multiple sources with intelligent caching.
"""

import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

from .parser import ConfigParser
from .env import EnvironmentHandler
from ..utils.helpers import merge_configs, safe_get_nested, validate_model_name
from ..utils.performance import measure_performance, track_cache_performance


class ConfigManager:
    """Central configuration manager for D-Model-Runner with intelligent caching."""
    
    def __init__(self, config_dir: Optional[Union[str, Path]] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir) if config_dir else Path.cwd() / "config"
        self._config: Dict[str, Any] = {}
        self._profile: str = "default"
        self._loaded = False
        
        # Caching infrastructure
        self._file_cache: Dict[str, Dict[str, Any]] = {}  # file_path -> {config, mtime}
        self._profile_cache: Dict[str, Dict[str, Any]] = {}  # profile -> config
        self._cache_valid = True
        self._last_env_check = 0
        self._env_cache: Optional[Dict[str, Any]] = None
    
    @measure_performance("config_load", include_args=True)
    def load_config(self, profile: str = "default", reload: bool = False) -> Dict[str, Any]:
        """
        Load configuration from files and environment variables with caching.
        
        Args:
            profile: Configuration profile to load
            reload: Force reload even if already loaded
            
        Returns:
            Complete merged configuration dictionary
        """
        # Check if we can use cached configuration
        if self._loaded and not reload and self._profile == profile and self._cache_valid:
            # Quick check if any files have changed
            if not self._files_changed():
                return self._config
        
        self._profile = profile
        
        # Start with default configuration
        config = self._load_default_config_cached()
        
        # Load profile-specific configuration
        profile_config = self._load_profile_config_cached(profile)
        if profile_config:
            config = merge_configs(config, profile_config)
        
        # Apply environment variable overrides
        env_overrides = self._get_env_overrides_cached()
        if env_overrides:
            config = merge_configs(config, env_overrides)
        
        # Validate the final configuration
        ConfigParser.validate_config_structure(config)
        
        self._config = config
        self._loaded = True
        self._cache_valid = True
        
        return self._config
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            path: Dot-separated configuration path
            default: Default value if path not found
            
        Returns:
            Configuration value or default
        """
        if not self._loaded:
            self.load_config()
        
        return safe_get_nested(self._config, path, default)
    
    def get_api_config(self) -> Dict[str, Any]:
        """
        Get API-specific configuration.
        
        Returns:
            API configuration dictionary
        """
        return self.get('api', {})
    
    def get_base_url(self) -> str:
        """
        Get the API base URL.
        
        Returns:
            Base URL string
        """
        return self.get('api.base_url', 'http://localhost:12434/engines/llama.cpp/v1/')
    
    def get_api_key(self) -> str:
        """
        Get the API key.
        
        Returns:
            API key string
        """
        return self.get('api.key', 'anything')
    
    def get_default_model(self) -> str:
        """
        Get the default model name.
        
        Returns:
            Default model name
        """
        return self.get('api.models.default', 'ai/gemma3')
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available models.
        
        Returns:
            List of model names
        """
        return self.get('api.models.available', ['ai/gemma3', 'ai/qwen3'])
    
    def get_model_config(self, model: str) -> Dict[str, Any]:
        """
        Get configuration for a specific model.
        
        Args:
            model: Model name
            
        Returns:
            Model-specific configuration
        """
        if not validate_model_name(model):
            raise ValueError(f"Invalid model name: {model}")
        
        # Get default model parameters
        defaults = self.get('api.models.defaults', {})
        
        # Get model-specific overrides
        model_key = model.replace('/', '_')  # Convert ai/gemma3 to ai_gemma3
        model_config = self.get(f'api.models.configs.{model_key}', {})
        
        return merge_configs(defaults, model_config)
    
    def get_current_profile(self) -> str:
        """
        Get the currently loaded configuration profile.
        
        Returns:
            Profile name
        """
        return self._profile
    
    def list_available_profiles(self) -> List[str]:
        """
        List all available configuration profiles.
        
        Returns:
            List of profile names
        """
        profiles = ["default"]
        
        # Check both config/profiles and dmr/config/profiles directories
        profile_dirs = [
            self.config_dir / "profiles",
            Path(__file__).parent / "profiles"  # dmr/config/profiles
        ]
        
        for profiles_dir in profile_dirs:
            if profiles_dir.exists():
                for file_path in profiles_dir.glob("*.yaml"):
                    if file_path.stem not in profiles:
                        profiles.append(file_path.stem)
                
                for file_path in profiles_dir.glob("*.yml"):
                    if file_path.stem not in profiles:
                        profiles.append(file_path.stem)
        
        return sorted(profiles)
    
    def reload_config(self) -> Dict[str, Any]:
        """
        Force reload the configuration.
        
        Returns:
            Reloaded configuration dictionary
        """
        return self.load_config(profile=self._profile, reload=True)
    
    def invalidate_cache(self) -> None:
        """Invalidate all cached configuration data."""
        self._file_cache.clear()
        self._profile_cache.clear()
        self._env_cache = None
        self._cache_valid = False
        self._last_env_check = 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about configuration caching."""
        return {
            'files_cached': len(self._file_cache),
            'profiles_cached': len(self._profile_cache),
            'env_cached': self._env_cache is not None,
            'cache_valid': self._cache_valid,
            'loaded': self._loaded,
            'current_profile': self._profile
        }
    
    def _files_changed(self) -> bool:
        """Check if any cached configuration files have been modified."""
        for file_path, cache_entry in self._file_cache.items():
            path_obj = Path(file_path)
            if path_obj.exists():
                current_mtime = path_obj.stat().st_mtime
                if current_mtime > cache_entry['mtime']:
                    return True
            else:
                # File was deleted
                return True
        return False
    
    @track_cache_performance("config_file_cache")
    def _get_cached_file_config(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Get configuration from file cache or load and cache it."""
        file_str = str(file_path)
        
        if file_path.exists():
            current_mtime = file_path.stat().st_mtime
            
            # Check if we have a valid cached version
            if (file_str in self._file_cache and 
                self._file_cache[file_str]['mtime'] >= current_mtime):
                return self._file_cache[file_str]['config']
            
            # Load and cache the file
            try:
                config = ConfigParser.load_config_file(file_path)
                self._file_cache[file_str] = {
                    'config': config,
                    'mtime': current_mtime
                }
                return config
            except Exception:
                return None
        
        return None
    
    def _get_env_overrides_cached(self) -> Optional[Dict[str, Any]]:
        """Get environment overrides with caching (refresh every 30 seconds)."""
        current_time = time.time()
        
        # Refresh environment cache every 30 seconds
        if (self._env_cache is None or 
            current_time - self._last_env_check > 30):
            self._env_cache = EnvironmentHandler.get_config_overrides()
            self._last_env_check = current_time
        
        return self._env_cache
    
    def _load_default_config_cached(self) -> Dict[str, Any]:
        """Load default configuration with caching."""
        # Built-in default configuration
        default_config = {
            'api': {
                'base_url': 'http://localhost:12434/engines/llama.cpp/v1/',
                'key': 'anything',
                'timeout': 30,
                'client': {
                    'timeout': 30.0,
                    'max_retries': 2,
                    'connection_check': True
                },
                'models': {
                    'default': 'ai/gemma3',
                    'available': ['ai/gemma3', 'ai/qwen3'],
                    'defaults': {
                        'max_tokens': 500,
                        'temperature': 0.7,
                        'top_p': 0.9,
                        'stream': True
                    },
                    'configs': {
                        'ai_gemma3': {
                            'description': 'General conversation model',
                            'max_tokens': 500
                        },
                        'ai_qwen3': {
                            'description': 'Reasoning model with thinking tokens',
                            'max_tokens': 800
                        }
                    }
                }
            },
            'error_handling': {
                'show_detailed_errors': True,
                'suggest_fixes': True,
                'retry_on_timeout': True
            },
            'logging': {
                'level': 'INFO',
                'debug': False
            },
            'ui': {
                'show_model_info': True,
                'stream_responses': True,
                'max_history': 100
            }
        }
        
        # Try to load from file and merge if it exists
        default_file = self.config_dir / "default.yaml"
        file_config = self._get_cached_file_config(default_file)
        if file_config:
            return merge_configs(default_config, file_config)
        
        return default_config
    
    def _load_profile_config_cached(self, profile: str) -> Optional[Dict[str, Any]]:
        """Load profile-specific configuration with caching."""
        if profile == "default":
            return None
        
        # Check profile cache first
        if profile in self._profile_cache:
            return self._profile_cache[profile]
        
        # Check both config/profiles and dmr/config/profiles directories
        profile_dirs = [
            self.config_dir / "profiles",
            Path(__file__).parent / "profiles"  # dmr/config/profiles
        ]
        
        for profiles_dir in profile_dirs:
            profile_files = [
                profiles_dir / f"{profile}.yaml",
                profiles_dir / f"{profile}.yml"
            ]
            
            for profile_file in profile_files:
                config = self._get_cached_file_config(profile_file)
                if config:
                    # Cache the profile config
                    self._profile_cache[profile] = config
                    return config
        
        # Cache that this profile doesn't exist
        self._profile_cache[profile] = None
        return None
    
    def _load_default_config(self) -> Dict[str, Any]:
        """
        Load the default configuration.
        
        Returns:
            Default configuration dictionary
        """
        default_config = {
            'api': {
                'base_url': 'http://localhost:12434/engines/llama.cpp/v1/',
                'key': 'anything',
                'timeout': 30,
                'models': {
                    'default': 'ai/gemma3',
                    'available': ['ai/gemma3', 'ai/qwen3'],
                    'defaults': {
                        'max_tokens': 500,
                        'temperature': 0.7,
                        'top_p': 0.9,
                        'stream': True
                    },
                    'configs': {
                        'ai_gemma3': {
                            'description': 'General conversation model',
                            'max_tokens': 500
                        },
                        'ai_qwen3': {
                            'description': 'Reasoning model with thinking tokens',
                            'max_tokens': 800
                        }
                    }
                }
            },
            'logging': {
                'level': 'INFO',
                'debug': False
            },
            'ui': {
                'show_model_info': True,
                'stream_responses': True,
                'max_history': 100
            }
        }
        
        # Try to load from file if it exists
        default_file = self.config_dir / "default.yaml"
        if default_file.exists():
            try:
                file_config = ConfigParser.load_config_file(default_file)
                return merge_configs(default_config, file_config)
            except Exception:
                # If file loading fails, use built-in defaults
                pass
        
        return default_config
    
    def _load_profile_config(self, profile: str) -> Optional[Dict[str, Any]]:
        """
        Load profile-specific configuration.
        
        Args:
            profile: Profile name to load
            
        Returns:
            Profile configuration or None if not found
        """
        if profile == "default":
            return None
        
        # Check both config/profiles and dmr/config/profiles directories
        profile_dirs = [
            self.config_dir / "profiles",
            Path(__file__).parent / "profiles"  # dmr/config/profiles
        ]
        
        for profiles_dir in profile_dirs:
            profile_files = [
                profiles_dir / f"{profile}.yaml",
                profiles_dir / f"{profile}.yml"
            ]
            
            for profile_file in profile_files:
                if profile_file.exists():
                    try:
                        return ConfigParser.load_config_file(profile_file)
                    except Exception:
                        # Continue to next file if this one fails
                        continue
        
        return None