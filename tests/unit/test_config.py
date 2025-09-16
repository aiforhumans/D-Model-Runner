"""
Unit tests for the configuration management system.

Tests cover:
- ConfigManager functionality
- Profile loading and switching
- Environment variable integration
- YAML/JSON parsing
- Error handling and validation
"""

import unittest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import patch, mock_open

from dmr.config import ConfigManager
from dmr.config.parser import ConfigParser
from dmr.config.env import EnvironmentHandler


class TestConfigManager(unittest.TestCase):
    """Test the ConfigManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir)
        self.manager = ConfigManager(config_dir=self.config_dir)
        
        # Create test configuration files
        self.test_config = {
            'api': {
                'base_url': 'http://localhost:12434/engines/llama.cpp/v1/',
                'api_key': 'test-key',
                'models': {
                    'default': 'ai/test-model',
                    'defaults': {
                        'temperature': 0.7,
                        'max_tokens': 500
                    }
                }
            },
            'logging': {
                'level': 'INFO'
            }
        }
        
        # Create profiles directory
        profiles_dir = self.config_dir / 'profiles'
        profiles_dir.mkdir(exist_ok=True)
        
        # Create test profile
        import yaml
        with open(profiles_dir / 'test.yaml', 'w') as f:
            yaml.dump(self.test_config, f)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_config_manager_initialization(self):
        """Test ConfigManager initialization."""
        self.assertIsInstance(self.manager, ConfigManager)
        self.assertEqual(self.manager.config_dir, self.config_dir)
        self.assertIsNone(self.manager.current_profile)
    
    def test_load_profile(self):
        """Test loading a configuration profile."""
        self.manager.load_config('test')
        self.assertEqual(self.manager.current_profile, 'test')
        self.assertEqual(self.manager.get_base_url(), 'http://localhost:12434/engines/llama.cpp/v1/')
        self.assertEqual(self.manager.get_api_key(), 'test-key')
    
    def test_get_default_model(self):
        """Test getting the default model."""
        self.manager.load_config('test')
        self.assertEqual(self.manager.get_default_model(), 'ai/test-model')
    
    def test_get_model_config(self):
        """Test getting model-specific configuration."""
        self.manager.load_config('test')
        model_config = self.manager.get_model_config('ai/test-model')
        self.assertEqual(model_config['temperature'], 0.7)
        self.assertEqual(model_config['max_tokens'], 500)
    
    def test_get_nested_config(self):
        """Test getting nested configuration values."""
        self.manager.load_config('test')
        self.assertEqual(self.manager.get('api.base_url'), 'http://localhost:12434/engines/llama.cpp/v1/')
        self.assertEqual(self.manager.get('api.models.default'), 'ai/test-model')
        self.assertEqual(self.manager.get('logging.level'), 'INFO')
    
    def test_get_with_default(self):
        """Test getting configuration with default values."""
        self.manager.load_config('test')
        self.assertEqual(self.manager.get('nonexistent.key', 'default'), 'default')
        self.assertEqual(self.manager.get('api.timeout', 30), 30)
    
    def test_list_profiles(self):
        """Test listing available profiles."""
        profiles = self.manager.list_profiles()
        self.assertIn('test', profiles)
    
    def test_load_nonexistent_profile(self):
        """Test loading a nonexistent profile."""
        with self.assertRaises(FileNotFoundError):
            self.manager.load_config('nonexistent')
    
    def test_config_validation(self):
        """Test configuration validation."""
        self.manager.load_config('test')
        # Should not raise any exceptions for valid config
        self.assertTrue(self.manager.validate_config())


class TestConfigParser(unittest.TestCase):
    """Test the ConfigParser class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = ConfigParser()
    
    def test_parse_yaml_valid(self):
        """Test parsing valid YAML content."""
        yaml_content = """
        api:
          base_url: http://localhost:12434
          models:
            default: ai/test
        """
        result = self.parser.parse_yaml_content(yaml_content)
        self.assertEqual(result['api']['base_url'], 'http://localhost:12434')
        self.assertEqual(result['api']['models']['default'], 'ai/test')
    
    def test_parse_yaml_invalid(self):
        """Test parsing invalid YAML content."""
        yaml_content = """
        api:
          base_url: http://localhost:12434
          models:
            - invalid yaml structure [
        """
        with self.assertRaises(Exception):
            self.parser.parse_yaml_content(yaml_content)
    
    def test_parse_json_valid(self):
        """Test parsing valid JSON content."""
        json_content = '{"api": {"base_url": "http://localhost:12434"}}'
        result = self.parser.parse_json_content(json_content)
        self.assertEqual(result['api']['base_url'], 'http://localhost:12434')
    
    def test_parse_json_invalid(self):
        """Test parsing invalid JSON content."""
        json_content = '{"api": {"base_url": "http://localhost:12434"'  # Missing closing brace
        with self.assertRaises(Exception):
            self.parser.parse_json_content(json_content)
    
    def test_load_yaml_file(self):
        """Test loading YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('test_key: test_value\n')
            f.flush()
            
            result = self.parser.load_yaml_file(Path(f.name))
            self.assertEqual(result['test_key'], 'test_value')
            
            os.unlink(f.name)
    
    def test_load_nonexistent_file(self):
        """Test loading nonexistent file."""
        with self.assertRaises(FileNotFoundError):
            self.parser.load_yaml_file(Path('/nonexistent/file.yaml'))


class TestEnvironmentHandler(unittest.TestCase):
    """Test the EnvironmentHandler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.env_handler = EnvironmentHandler()
    
    @patch.dict(os.environ, {
        'DMR_BASE_URL': 'http://custom:8080',
        'DMR_API_KEY': 'custom-key',
        'DMR_MAX_TOKENS': '300',
        'DMR_TEMPERATURE': '0.8',
        'DMR_DEBUG': 'true'
    })
    def test_load_environment_variables(self):
        """Test loading environment variables with DMR_ prefix."""
        env_config = self.env_handler.load_environment_variables()
        
        self.assertEqual(env_config['base_url'], 'http://custom:8080')
        self.assertEqual(env_config['api_key'], 'custom-key')
        self.assertEqual(env_config['max_tokens'], 300)
        self.assertEqual(env_config['temperature'], 0.8)
        self.assertEqual(env_config['debug'], True)
    
    def test_type_conversion(self):
        """Test type conversion for environment variables."""
        # Test integer conversion
        self.assertEqual(self.env_handler._convert_type('123'), 123)
        
        # Test float conversion
        self.assertEqual(self.env_handler._convert_type('12.34'), 12.34)
        
        # Test boolean conversion
        self.assertEqual(self.env_handler._convert_type('true'), True)
        self.assertEqual(self.env_handler._convert_type('false'), False)
        self.assertEqual(self.env_handler._convert_type('True'), True)
        self.assertEqual(self.env_handler._convert_type('False'), False)
        
        # Test string (no conversion)
        self.assertEqual(self.env_handler._convert_type('test_string'), 'test_string')
    
    @patch.dict(os.environ, {}, clear=True)
    def test_no_environment_variables(self):
        """Test behavior when no DMR_ environment variables are set."""
        env_config = self.env_handler.load_environment_variables()
        self.assertEqual(env_config, {})
    
    def test_variable_name_mapping(self):
        """Test mapping of environment variable names to config keys."""
        self.assertEqual(
            self.env_handler._map_variable_name('DMR_BASE_URL'),
            'base_url'
        )
        self.assertEqual(
            self.env_handler._map_variable_name('DMR_API_KEY'),
            'api_key'
        )
        self.assertEqual(
            self.env_handler._map_variable_name('DMR_MAX_TOKENS'),
            'max_tokens'
        )


class TestConfigIntegration(unittest.TestCase):
    """Test integration between configuration components."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir)
        
        # Create test configuration structure
        profiles_dir = self.config_dir / 'profiles'
        profiles_dir.mkdir(exist_ok=True)
        
        # Create test profiles
        import yaml
        
        dev_config = {
            'api': {
                'base_url': 'http://localhost:12434/engines/llama.cpp/v1/',
                'models': {'default': 'ai/dev-model'}
            },
            'logging': {'level': 'DEBUG'}
        }
        
        prod_config = {
            'api': {
                'base_url': 'http://production:12434/engines/llama.cpp/v1/',
                'models': {'default': 'ai/prod-model'}
            },
            'logging': {'level': 'WARNING'}
        }
        
        with open(profiles_dir / 'dev.yaml', 'w') as f:
            yaml.dump(dev_config, f)
        
        with open(profiles_dir / 'prod.yaml', 'w') as f:
            yaml.dump(prod_config, f)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_profile_switching(self):
        """Test switching between different profiles."""
        manager = ConfigManager(config_dir=self.config_dir)
        
        # Load dev profile
        manager.load_config('dev')
        self.assertEqual(manager.get_default_model(), 'ai/dev-model')
        self.assertEqual(manager.get('logging.level'), 'DEBUG')
        
        # Switch to prod profile
        manager.load_config('prod')
        self.assertEqual(manager.get_default_model(), 'ai/prod-model')
        self.assertEqual(manager.get('logging.level'), 'WARNING')
    
    @patch.dict(os.environ, {'DMR_DEFAULT_MODEL': 'ai/env-override'})
    def test_environment_override(self):
        """Test environment variable overrides."""
        manager = ConfigManager(config_dir=self.config_dir)
        manager.load_config('dev')
        
        # Environment variable should override profile setting
        self.assertEqual(manager.get_default_model(), 'ai/env-override')


if __name__ == '__main__':
    unittest.main()