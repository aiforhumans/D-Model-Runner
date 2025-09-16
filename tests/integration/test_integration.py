"""
Integration tests for D-Model-Runner.

Tests the interaction between different components:
- Configuration system + Storage system
- Main application workflow
- Profile-specific storage settings
- Cross-component error handling
"""

import unittest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import yaml

from dmr.config import ConfigManager
from dmr.storage.conversation import ConversationManager, Conversation, Message, ConversationMetadata
from dmr.storage.templates import TemplateManager
from dmr.storage.exporters import ExportManager


class TestConfigStorageIntegration(unittest.TestCase):
    """Test integration between configuration and storage systems."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_path = Path(self.temp_dir)
        
        # Create configuration structure
        self.config_dir = self.base_path / 'config'
        self.config_dir.mkdir()
        
        profiles_dir = self.config_dir / 'profiles'
        profiles_dir.mkdir()
        
        # Create storage structure
        self.storage_dir = self.base_path / 'storage'
        self.storage_dir.mkdir()
        
        # Create test profiles with storage settings
        self.dev_config = {
            'api': {
                'base_url': 'http://localhost:12434/engines/llama.cpp/v1/',
                'models': {'default': 'ai/dev-model'}
            },
            'storage': {
                'conversations_dir': str(self.storage_dir / 'dev_conversations'),
                'templates_dir': str(self.storage_dir / 'dev_templates'),
                'exports_dir': str(self.storage_dir / 'dev_exports'),
                'auto_save': True,
                'backup_enabled': True
            }
        }
        
        self.prod_config = {
            'api': {
                'base_url': 'http://production:12434/engines/llama.cpp/v1/',
                'models': {'default': 'ai/prod-model'}
            },
            'storage': {
                'conversations_dir': str(self.storage_dir / 'prod_conversations'),
                'templates_dir': str(self.storage_dir / 'prod_templates'),
                'exports_dir': str(self.storage_dir / 'prod_exports'),
                'auto_save': False,
                'backup_enabled': True,
                'retention_days': 30
            }
        }
        
        # Save profiles
        with open(profiles_dir / 'dev.yaml', 'w') as f:
            yaml.dump(self.dev_config, f)
        
        with open(profiles_dir / 'prod.yaml', 'w') as f:
            yaml.dump(self.prod_config, f)
        
        # Initialize managers
        self.config_manager = ConfigManager(config_dir=self.config_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_profile_specific_storage_paths(self):
        """Test that storage paths change with profiles."""
        # Load dev profile
        self.config_manager.load_config('dev')
        
        dev_conv_dir = self.config_manager.get('storage.conversations_dir')
        dev_templates_dir = self.config_manager.get('storage.templates_dir')
        
        self.assertIn('dev_conversations', dev_conv_dir)
        self.assertIn('dev_templates', dev_templates_dir)
        
        # Switch to prod profile
        self.config_manager.load_config('prod')
        
        prod_conv_dir = self.config_manager.get('storage.conversations_dir')
        prod_templates_dir = self.config_manager.get('storage.templates_dir')
        
        self.assertIn('prod_conversations', prod_conv_dir)
        self.assertIn('prod_templates', prod_templates_dir)
        
        # Paths should be different
        self.assertNotEqual(dev_conv_dir, prod_conv_dir)
        self.assertNotEqual(dev_templates_dir, prod_templates_dir)
    
    def test_storage_manager_with_config(self):
        """Test storage managers using configuration."""
        self.config_manager.load_config('dev')
        
        # Create storage managers with config-driven paths
        conv_dir = Path(self.config_manager.get('storage.conversations_dir'))
        conv_dir.mkdir(exist_ok=True, parents=True)
        
        conv_manager = ConversationManager(storage_dir=conv_dir)
        
        # Test saving conversation
        test_conv = Conversation(
            metadata=ConversationMetadata(
                title="Integration Test",
                model=self.config_manager.get_default_model()
            ),
            messages=[Message(role="user", content="Test message")]
        )
        
        conv_id = conv_manager.save_conversation(test_conv)
        self.assertIsNotNone(conv_id)
        
        # Verify file was saved in correct location
        expected_path = conv_dir / f"{conv_id}.json"
        self.assertTrue(expected_path.exists())
        
        # Load and verify
        loaded_conv = conv_manager.load_conversation(conv_id)
        self.assertEqual(loaded_conv.metadata.title, "Integration Test")
        self.assertEqual(loaded_conv.metadata.model, 'ai/dev-model')
    
    def test_auto_save_configuration(self):
        """Test auto-save behavior based on configuration."""
        # Dev profile has auto_save: True
        self.config_manager.load_config('dev')
        auto_save_dev = self.config_manager.get('storage.auto_save')
        self.assertTrue(auto_save_dev)
        
        # Prod profile has auto_save: False
        self.config_manager.load_config('prod')
        auto_save_prod = self.config_manager.get('storage.auto_save')
        self.assertFalse(auto_save_prod)
    
    def test_environment_storage_override(self):
        """Test environment variable overrides for storage settings."""
        with patch.dict(os.environ, {
            'DMR_STORAGE_CONVERSATIONS_DIR': '/custom/conversations',
            'DMR_STORAGE_AUTO_SAVE': 'false'
        }):
            self.config_manager.load_config('dev')
            
            # Environment should override profile settings
            conv_dir = self.config_manager.get('storage.conversations_dir')
            auto_save = self.config_manager.get('storage.auto_save')
            
            self.assertEqual(conv_dir, '/custom/conversations')
            self.assertFalse(auto_save)
    
    def test_export_with_profile_settings(self):
        """Test export functionality with profile-specific settings."""
        self.config_manager.load_config('prod')
        
        # Create export directory from config
        export_dir = Path(self.config_manager.get('storage.exports_dir'))
        export_dir.mkdir(exist_ok=True, parents=True)
        
        # Create test conversation
        test_conv = Conversation(
            metadata=ConversationMetadata(title="Export Test", model="ai/test"),
            messages=[Message(role="user", content="Test export")]
        )
        
        # Export using configured directory
        export_manager = ExportManager()
        output_path = export_dir / "test_export.json"
        
        result_path = export_manager.export_conversation(test_conv, output_path, "json")
        
        self.assertTrue(result_path.exists())
        self.assertTrue(str(result_path).startswith(str(export_dir)))


class TestMainApplicationIntegration(unittest.TestCase):
    """Test main application integration with all components."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_path = Path(self.temp_dir)
        
        # Mock the main application components
        self.config_manager = MagicMock()
        self.conv_manager = MagicMock()
        self.template_manager = MagicMock()
        self.export_manager = MagicMock()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_chat_session_workflow(self):
        """Test complete chat session workflow."""
        # Configure mocks
        self.config_manager.get_default_model.return_value = 'ai/test-model'
        self.config_manager.get_model_config.return_value = {
            'temperature': 0.7,
            'max_tokens': 500
        }
        self.config_manager.get.return_value = True  # auto_save enabled
        
        # Simulate chat session
        messages = [
            ("user", "Hello, can you help me?"),
            ("assistant", "Of course! I'm here to help."),
            ("user", "Tell me about Python"),
            ("assistant", "Python is a versatile programming language...")
        ]
        
        # Mock conversation creation and saving
        mock_conversation = MagicMock()
        mock_conversation.id = "test-conv-123"
        self.conv_manager.create_conversation.return_value = mock_conversation
        self.conv_manager.save_conversation.return_value = "test-conv-123"
        
        # Simulate the workflow
        conversation = self.conv_manager.create_conversation("Test Chat", "ai/test-model")
        
        for role, content in messages:
            conversation.add_message.return_value = None
            
        # Auto-save should be called
        conversation_id = self.conv_manager.save_conversation(conversation)
        
        # Verify workflow
        self.conv_manager.create_conversation.assert_called_once()
        self.conv_manager.save_conversation.assert_called_once()
        self.assertEqual(conversation_id, "test-conv-123")
    
    def test_template_workflow_integration(self):
        """Test template-based conversation workflow."""
        # Mock template loading
        mock_template = {
            'id': 'template-123',
            'name': 'code_review',
            'title': 'Code Review Template',
            'content': 'Please review this code: {code}\n\nFocus on: {focus_areas}',
            'variables': ['code', 'focus_areas']
        }
        
        self.template_manager.load_template.return_value = mock_template
        self.template_manager.instantiate_template.return_value = \
            "Please review this code: def hello(): print('hello')\n\nFocus on: performance, readability"
        
        # Mock conversation creation from template
        mock_conversation = MagicMock()
        mock_conversation.id = "template-conv-456"
        
        # Simulate template workflow
        template = self.template_manager.load_template('template-123')
        variables = {
            'code': "def hello(): print('hello')",
            'focus_areas': "performance, readability"
        }
        
        instantiated_content = self.template_manager.instantiate_template(
            template['id'], variables
        )
        
        # Verify template workflow
        self.template_manager.load_template.assert_called_once_with('template-123')
        self.template_manager.instantiate_template.assert_called_once()
        self.assertIn("Please review this code", instantiated_content)
    
    def test_export_workflow_integration(self):
        """Test conversation export workflow."""
        # Mock conversation loading
        mock_conversation = MagicMock()
        mock_conversation.id = "export-conv-789"
        mock_conversation.metadata.title = "Export Test"
        
        self.conv_manager.load_conversation.return_value = mock_conversation
        
        # Mock export
        export_path = self.base_path / "exported_conversation.md"
        self.export_manager.export_conversation.return_value = export_path
        
        # Simulate export workflow
        conversation = self.conv_manager.load_conversation("export-conv-789")
        result_path = self.export_manager.export_conversation(
            conversation, export_path, "markdown"
        )
        
        # Verify export workflow
        self.conv_manager.load_conversation.assert_called_once_with("export-conv-789")
        self.export_manager.export_conversation.assert_called_once()
        self.assertEqual(result_path, export_path)


class TestErrorHandlingIntegration(unittest.TestCase):
    """Test error handling across components."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager(config_dir=Path(self.temp_dir))
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_missing_configuration_profile(self):
        """Test behavior when configuration profile is missing."""
        with self.assertRaises(FileNotFoundError):
            self.config_manager.load_config('nonexistent_profile')
    
    def test_invalid_storage_directory(self):
        """Test behavior with invalid storage directory."""
        # Try to create storage manager with invalid path
        invalid_path = Path('/invalid/nonexistent/path')
        
        with self.assertRaises((FileNotFoundError, PermissionError, OSError)):
            # This should fail when trying to create files
            conv_manager = ConversationManager(storage_dir=invalid_path)
            test_conv = Conversation(
                metadata=ConversationMetadata(title="Test", model="ai/test"),
                messages=[Message(role="user", content="Test")]
            )
            conv_manager.save_conversation(test_conv)
    
    def test_corrupted_configuration_file(self):
        """Test handling of corrupted configuration files."""
        # Create corrupted YAML file
        profiles_dir = Path(self.temp_dir) / 'profiles'
        profiles_dir.mkdir(exist_ok=True)
        
        corrupted_file = profiles_dir / 'corrupted.yaml'
        with open(corrupted_file, 'w') as f:
            f.write("invalid: yaml: content: [\n")  # Invalid YAML
        
        with self.assertRaises(Exception):
            self.config_manager.load_config('corrupted')
    
    def test_storage_permission_errors(self):
        """Test handling of storage permission errors."""
        # This test would be platform-specific and might require special setup
        # For now, we'll create a mock scenario
        
        conv_manager = ConversationManager(storage_dir=Path(self.temp_dir))
        
        # Mock permission error during save
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            test_conv = Conversation(
                metadata=ConversationMetadata(title="Test", model="ai/test"),
                messages=[Message(role="user", content="Test")]
            )
            
            with self.assertRaises(PermissionError):
                conv_manager.save_conversation(test_conv)


class TestPerformanceIntegration(unittest.TestCase):
    """Test performance characteristics of integrated components."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / 'config'
        self.storage_dir = Path(self.temp_dir) / 'storage'
        
        self.config_dir.mkdir()
        self.storage_dir.mkdir()
        
        # Create simple test profile
        profiles_dir = self.config_dir / 'profiles'
        profiles_dir.mkdir()
        
        test_config = {
            'api': {'models': {'default': 'ai/test'}},
            'storage': {'conversations_dir': str(self.storage_dir)}
        }
        
        with open(profiles_dir / 'test.yaml', 'w') as f:
            yaml.dump(test_config, f)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_large_conversation_handling(self):
        """Test handling of large conversations."""
        config_manager = ConfigManager(config_dir=self.config_dir)
        config_manager.load_config('test')
        
        conv_manager = ConversationManager(storage_dir=self.storage_dir)
        
        # Create large conversation
        large_conversation = Conversation(
            metadata=ConversationMetadata(title="Large Test", model="ai/test"),
            messages=[]
        )
        
        # Add many messages
        for i in range(1000):
            large_conversation.add_message(
                Message(role="user" if i % 2 == 0 else "assistant", 
                       content=f"Message {i}: " + "Content " * 50)
            )
        
        # Test saving and loading
        import time
        
        start_time = time.time()
        conv_id = conv_manager.save_conversation(large_conversation)
        save_time = time.time() - start_time
        
        start_time = time.time()
        loaded_conv = conv_manager.load_conversation(conv_id)
        load_time = time.time() - start_time
        
        # Verify correctness
        self.assertEqual(len(loaded_conv.messages), 1000)
        self.assertEqual(loaded_conv.metadata.title, "Large Test")
        
        # Performance should be reasonable (adjust thresholds as needed)
        self.assertLess(save_time, 5.0)  # Save should take less than 5 seconds
        self.assertLess(load_time, 5.0)  # Load should take less than 5 seconds
    
    def test_multiple_profiles_switching(self):
        """Test performance of switching between profiles."""
        # Create multiple profiles
        profiles_dir = self.config_dir / 'profiles'
        
        for i in range(10):
            profile_config = {
                'api': {'models': {'default': f'ai/model-{i}'}},
                'storage': {'conversations_dir': str(self.storage_dir / f'profile_{i}')}
            }
            
            with open(profiles_dir / f'profile_{i}.yaml', 'w') as f:
                yaml.dump(profile_config, f)
        
        config_manager = ConfigManager(config_dir=self.config_dir)
        
        import time
        
        # Test rapid profile switching
        start_time = time.time()
        
        for i in range(10):
            config_manager.load_config(f'profile_{i}')
            model = config_manager.get_default_model()
            self.assertEqual(model, f'ai/model-{i}')
        
        total_time = time.time() - start_time
        
        # Profile switching should be fast
        self.assertLess(total_time, 2.0)  # 10 switches in less than 2 seconds
        average_time = total_time / 10
        self.assertLess(average_time, 0.2)  # Each switch less than 200ms


if __name__ == '__main__':
    unittest.main()