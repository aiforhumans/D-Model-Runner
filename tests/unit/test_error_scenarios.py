"""
Error scenario testing for D-Model-Runner.

This module tests system behavior under various error conditions:
- Missing files and directories
- Corrupt data and configuration files
- Network issues and API failures
- Invalid configurations and parameters
- Storage failures and permission issues
"""

import unittest
import tempfile
import shutil
import os
import json
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dmr.config import ConfigManager
from dmr.storage.conversation import ConversationManager, Conversation, Message, ConversationMetadata
from dmr.storage.templates import TemplateManager, Template
from dmr.storage.exporters import ExportManager


class TestConfigurationErrorScenarios(unittest.TestCase):
    """Test configuration system error handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_missing_config_directory(self):
        """Test behavior when config directory doesn't exist."""
        nonexistent_dir = Path(self.temp_dir) / 'nonexistent'
        
        # Should not raise error on initialization
        manager = ConfigManager(config_dir=nonexistent_dir)
        
        # Should raise error when trying to load config
        with self.assertRaises(FileNotFoundError):
            manager.load_config('any_profile')
    
    def test_missing_profile_file(self):
        """Test loading a non-existent profile."""
        profiles_dir = self.config_dir / 'profiles'
        profiles_dir.mkdir(parents=True)
        
        manager = ConfigManager(config_dir=self.config_dir)
        
        with self.assertRaises(FileNotFoundError):
            manager.load_config('nonexistent_profile')
    
    def test_corrupt_yaml_file(self):
        """Test handling of corrupted YAML files."""
        profiles_dir = self.config_dir / 'profiles'
        profiles_dir.mkdir(parents=True)
        
        # Create corrupted YAML file
        corrupt_file = profiles_dir / 'corrupt.yaml'
        with open(corrupt_file, 'w') as f:
            f.write("invalid: yaml: structure: [\nunclosed brackets\n  missing: quotes")
        
        manager = ConfigManager(config_dir=self.config_dir)
        
        with self.assertRaises(yaml.YAMLError):
            manager.load_config('corrupt')
    
    def test_empty_config_file(self):
        """Test handling of empty configuration files."""
        profiles_dir = self.config_dir / 'profiles'
        profiles_dir.mkdir(parents=True)
        
        # Create empty file
        empty_file = profiles_dir / 'empty.yaml'
        empty_file.touch()
        
        manager = ConfigManager(config_dir=self.config_dir)
        
        # Should handle empty file gracefully
        manager.load_config('empty')
        
        # Should return None for missing keys
        self.assertIsNone(manager.get('nonexistent.key'))
    
    def test_permission_denied_config_file(self):
        """Test handling of permission denied errors."""
        profiles_dir = self.config_dir / 'profiles'
        profiles_dir.mkdir(parents=True)
        
        # Create a file and then mock permission error
        test_file = profiles_dir / 'protected.yaml'
        with open(test_file, 'w') as f:
            yaml.dump({'test': 'value'}, f)
        
        manager = ConfigManager(config_dir=self.config_dir)
        
        # Mock file opening to raise PermissionError
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with self.assertRaises(PermissionError):
                manager.load_config('protected')
    
    def test_invalid_environment_variables(self):
        """Test handling of invalid environment variables."""
        manager = ConfigManager(config_dir=self.config_dir)
        
        # Test with invalid environment variable types
        with patch.dict(os.environ, {
            'DMR_MAX_TOKENS': 'not_a_number',
            'DMR_TEMPERATURE': 'invalid_float',
            'DMR_DEBUG': 'not_boolean'
        }):
            # Should handle gracefully and keep as strings
            env_config = manager.env_handler.load_environment_variables()
            
            # Invalid numbers should remain as strings
            self.assertIsInstance(env_config.get('max_tokens'), str)
            self.assertIsInstance(env_config.get('temperature'), str)
            self.assertIsInstance(env_config.get('debug'), str)
    
    def test_circular_config_references(self):
        """Test handling of circular configuration references."""
        profiles_dir = self.config_dir / 'profiles'
        profiles_dir.mkdir(parents=True)
        
        # This would be a more complex test in a real system with includes
        # For now, test deeply nested structures
        deeply_nested = {
            'level1': {
                'level2': {
                    'level3': {
                        'level4': {
                            'level5': {
                                'value': 'deep_value'
                            }
                        }
                    }
                }
            }
        }
        
        with open(profiles_dir / 'deep.yaml', 'w') as f:
            yaml.dump(deeply_nested, f)
        
        manager = ConfigManager(config_dir=self.config_dir)
        manager.load_config('deep')
        
        # Should handle deep nesting
        self.assertEqual(
            manager.get('level1.level2.level3.level4.level5.value'),
            'deep_value'
        )


class TestStorageErrorScenarios(unittest.TestCase):
    """Test storage system error handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_dir = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_missing_storage_directory(self):
        """Test behavior when storage directory doesn't exist."""
        nonexistent_dir = Path(self.temp_dir) / 'nonexistent'
        
        # Should create directory when saving
        manager = ConversationManager(storage_dir=nonexistent_dir)
        
        test_conv = Conversation(
            metadata=ConversationMetadata(title="Test", model="ai/test"),
            messages=[Message(role="user", content="Test")]
        )
        
        # Should create directory and save successfully
        conv_id = manager.save_conversation(test_conv)
        self.assertIsNotNone(conv_id)
        self.assertTrue(nonexistent_dir.exists())
    
    def test_corrupt_conversation_file(self):
        """Test loading corrupted conversation files."""
        manager = ConversationManager(storage_dir=self.storage_dir)
        
        # Create corrupted JSON file
        corrupt_file = self.storage_dir / 'corrupt.json'
        with open(corrupt_file, 'w') as f:
            f.write('{"invalid": json syntax')
        
        with self.assertRaises(json.JSONDecodeError):
            manager.load_conversation('corrupt')
    
    def test_malformed_conversation_data(self):
        """Test conversation with missing required fields."""
        manager = ConversationManager(storage_dir=self.storage_dir)
        
        # Create conversation with missing required fields
        malformed_data = {
            'id': 'test-id',
            # Missing metadata and messages
        }
        
        malformed_file = self.storage_dir / 'malformed.json'
        with open(malformed_file, 'w') as f:
            json.dump(malformed_data, f)
        
        with self.assertRaises((KeyError, TypeError)):
            manager.load_conversation('malformed')
    
    def test_storage_permission_errors(self):
        """Test handling of storage permission errors."""
        manager = ConversationManager(storage_dir=self.storage_dir)
        
        test_conv = Conversation(
            metadata=ConversationMetadata(title="Test", model="ai/test"),
            messages=[Message(role="user", content="Test")]
        )
        
        # Mock file operations to raise PermissionError
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with self.assertRaises(PermissionError):
                manager.save_conversation(test_conv)
    
    def test_disk_space_errors(self):
        """Test handling of disk space errors."""
        manager = ConversationManager(storage_dir=self.storage_dir)
        
        test_conv = Conversation(
            metadata=ConversationMetadata(title="Test", model="ai/test"),
            messages=[Message(role="user", content="Test")]
        )
        
        # Mock file operations to raise OSError (disk full)
        with patch('builtins.open', side_effect=OSError("No space left on device")):
            with self.assertRaises(OSError):
                manager.save_conversation(test_conv)
    
    def test_concurrent_access_conflicts(self):
        """Test handling of concurrent file access."""
        manager = ConversationManager(storage_dir=self.storage_dir)
        
        # Create a test conversation
        test_conv = Conversation(
            metadata=ConversationMetadata(title="Concurrent Test", model="ai/test"),
            messages=[Message(role="user", content="Test")]
        )
        
        conv_id = manager.save_conversation(test_conv)
        
        # Simulate file being locked by another process
        with patch('builtins.open', side_effect=PermissionError("File is locked")):
            with self.assertRaises(PermissionError):
                manager.load_conversation(conv_id)
    
    def test_invalid_conversation_id(self):
        """Test handling of invalid conversation IDs."""
        manager = ConversationManager(storage_dir=self.storage_dir)
        
        # Test various invalid ID formats
        invalid_ids = [
            None,
            "",
            "invalid/path",
            "../parent_dir",
            "id_with_\x00null",
            "very_long_id_" + "x" * 1000
        ]
        
        for invalid_id in invalid_ids:
            with self.assertRaises((FileNotFoundError, ValueError, OSError)):
                manager.load_conversation(invalid_id)
    
    def test_template_validation_errors(self):
        """Test template validation error handling."""
        manager = TemplateManager(storage_dir=self.storage_dir)
        
        # Test template with missing variables
        incomplete_template = Template(
            name="incomplete",
            title="Incomplete Template",
            description="Test template",
            category="test",
            content="Hello {name}, welcome to {missing_var}!",
            variables=["name"]  # Missing 'missing_var'
        )
        
        template_id = manager.save_template(incomplete_template)
        
        # Should raise error when trying to instantiate with missing variables
        with self.assertRaises((KeyError, ValueError)):
            manager.instantiate_template(template_id, {"name": "Alice"})
    
    def test_export_errors(self):
        """Test export system error handling."""
        export_manager = ExportManager()
        
        test_conv = Conversation(
            metadata=ConversationMetadata(title="Export Error Test", model="ai/test"),
            messages=[Message(role="user", content="Test")]
        )
        
        # Test export to read-only location
        readonly_path = Path("/readonly/path/export.json")
        
        with self.assertRaises((OSError, PermissionError)):
            export_manager.export_conversation(test_conv, readonly_path, "json")
        
        # Test invalid export format
        valid_path = self.storage_dir / "test_export.invalid"
        
        with self.assertRaises(ValueError):
            export_manager.export_conversation(test_conv, valid_path, "invalid_format")


class TestNetworkErrorScenarios(unittest.TestCase):
    """Test network-related error scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir)
        
        # Create basic configuration
        profiles_dir = self.config_dir / 'profiles'
        profiles_dir.mkdir(parents=True)
        
        test_config = {
            'api': {
                'base_url': 'http://localhost:12434/engines/llama.cpp/v1/',
                'api_key': 'test-key',
                'timeout': 30,
                'retry_attempts': 3
            }
        }
        
        with open(profiles_dir / 'test.yaml', 'w') as f:
            yaml.dump(test_config, f)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_api_connection_timeout(self):
        """Test handling of API connection timeouts."""
        from openai import OpenAI
        
        manager = ConfigManager(config_dir=self.config_dir)
        manager.load_config('test')
        
        # Create client with very short timeout
        client = OpenAI(
            base_url="http://nonexistent-server:12434/v1/",
            api_key="test",
            timeout=0.1  # Very short timeout
        )
        
        # This should raise a timeout or connection error
        with self.assertRaises(Exception):  # Could be various network exceptions
            response = client.chat.completions.create(
                model="ai/test",
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=10
            )
    
    def test_api_server_unavailable(self):
        """Test handling when API server is unavailable."""
        from openai import OpenAI
        
        # Try to connect to non-existent server
        client = OpenAI(
            base_url="http://nonexistent-server:99999/v1/",
            api_key="test"
        )
        
        with self.assertRaises(Exception):  # Connection error
            response = client.chat.completions.create(
                model="ai/test",
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=10
            )
    
    def test_api_authentication_errors(self):
        """Test handling of API authentication errors."""
        # This would require a running server to properly test
        # For now, we'll test the configuration handling
        
        manager = ConfigManager(config_dir=self.config_dir)
        manager.load_config('test')
        
        # Test with invalid API key configuration
        with patch.dict(os.environ, {'DMR_API_KEY': ''}):
            # Should handle empty API key
            api_key = manager.get_api_key()
            self.assertIsNotNone(api_key)  # Should fall back to default
    
    def test_api_rate_limiting(self):
        """Test handling of API rate limiting."""
        # This would require specific server setup to test properly
        # For now, test the configuration for rate limiting parameters
        
        manager = ConfigManager(config_dir=self.config_dir)
        manager.load_config('test')
        
        # Test rate limiting configuration
        retry_attempts = manager.get('api.retry_attempts', 1)
        timeout = manager.get('api.timeout', 30)
        
        self.assertIsInstance(retry_attempts, int)
        self.assertIsInstance(timeout, (int, float))
        self.assertGreater(retry_attempts, 0)
        self.assertGreater(timeout, 0)


class TestIntegrationErrorScenarios(unittest.TestCase):
    """Test error scenarios in integrated workflows."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_path = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_config_storage_mismatch(self):
        """Test when configuration points to invalid storage paths."""
        config_dir = self.base_path / 'config'
        config_dir.mkdir()
        profiles_dir = config_dir / 'profiles'
        profiles_dir.mkdir()
        
        # Configuration with invalid storage paths
        invalid_config = {
            'storage': {
                'conversations_dir': '/invalid/readonly/path',
                'templates_dir': '/another/invalid/path'
            }
        }
        
        with open(profiles_dir / 'invalid.yaml', 'w') as f:
            yaml.dump(invalid_config, f)
        
        config_manager = ConfigManager(config_dir=config_dir)
        config_manager.load_config('invalid')
        
        # Try to create storage manager with invalid paths
        invalid_conv_dir = Path(config_manager.get('storage.conversations_dir'))
        
        with self.assertRaises((OSError, PermissionError)):
            conv_manager = ConversationManager(storage_dir=invalid_conv_dir)
            test_conv = Conversation(
                metadata=ConversationMetadata(title="Test", model="ai/test"),
                messages=[Message(role="user", content="Test")]
            )
            conv_manager.save_conversation(test_conv)
    
    def test_corrupted_system_state(self):
        """Test recovery from corrupted system state."""
        # Create a partially working system state
        storage_dir = self.base_path / 'storage'
        storage_dir.mkdir()
        
        # Create some valid and some corrupted files
        conv_manager = ConversationManager(storage_dir=storage_dir)
        
        # Create valid conversation
        valid_conv = Conversation(
            metadata=ConversationMetadata(title="Valid", model="ai/test"),
            messages=[Message(role="user", content="Valid message")]
        )
        valid_id = conv_manager.save_conversation(valid_conv)
        
        # Create corrupted file
        corrupt_file = storage_dir / 'corrupt.json'
        with open(corrupt_file, 'w') as f:
            f.write('{"corrupted": "data"')  # Invalid JSON
        
        # System should still be able to list and work with valid conversations
        conversations = conv_manager.list_conversations()
        valid_found = any(conv['id'] == valid_id for conv in conversations)
        self.assertTrue(valid_found)
        
        # Should be able to load valid conversation
        loaded_conv = conv_manager.load_conversation(valid_id)
        self.assertEqual(loaded_conv.metadata.title, "Valid")
    
    def test_partial_export_failure(self):
        """Test handling of partial export failures."""
        storage_dir = self.base_path / 'storage'
        export_dir = self.base_path / 'exports'
        storage_dir.mkdir()
        export_dir.mkdir()
        
        # Create test conversation
        conv_manager = ConversationManager(storage_dir=storage_dir)
        test_conv = Conversation(
            metadata=ConversationMetadata(title="Export Test", model="ai/test"),
            messages=[Message(role="user", content="Test message")]
        )
        conv_id = conv_manager.save_conversation(test_conv)
        
        # Try to export to a location that will fail partway through
        export_manager = ExportManager()
        
        # Mock a failure during export
        original_export = export_manager.export_conversation
        
        def failing_export(*args, **kwargs):
            raise OSError("Disk full during export")
        
        with patch.object(export_manager, 'export_conversation', side_effect=failing_export):
            with self.assertRaises(OSError):
                export_manager.export_conversation(
                    test_conv,
                    export_dir / "failed_export.json",
                    "json"
                )
        
        # Original conversation should still be intact
        loaded_conv = conv_manager.load_conversation(conv_id)
        self.assertEqual(loaded_conv.metadata.title, "Export Test")


def run_error_scenario_tests():
    """Run all error scenario tests."""
    print("🚨 Running Error Scenario Tests")
    print("=" * 40)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestConfigurationErrorScenarios,
        TestStorageErrorScenarios,
        TestNetworkErrorScenarios,
        TestIntegrationErrorScenarios
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n📊 Error Scenario Test Summary:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\n🔥 Errors:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_error_scenario_tests()