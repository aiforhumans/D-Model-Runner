"""
End-to-end workflow testing for D-Model-Runner.

This module tests complete user scenarios and workflows:
- Complete chat sessions with conversation saving
- Template-based conversation workflows
- Export and import workflows
- Multi-profile configuration workflows
- Cross-component integration scenarios
"""

import unittest
import tempfile
import shutil
import os
import json
import yaml
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dmr.config import ConfigManager
from dmr.storage.conversation import ConversationManager, Conversation, Message, ConversationMetadata
from dmr.storage.templates import TemplateManager, Template
from dmr.storage.exporters import ExportManager


class TestCompleteWorkflows(unittest.TestCase):
    """Test complete user workflows end-to-end."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_path = Path(self.temp_dir)
        
        # Set up directory structure
        self.config_dir = self.base_path / 'config'
        self.storage_dir = self.base_path / 'storage'
        self.export_dir = self.base_path / 'exports'
        
        for dir_path in [self.config_dir, self.storage_dir, self.export_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create test configurations
        self._create_test_configurations()
        
        # Initialize managers
        self.config_manager = ConfigManager(config_dir=self.config_dir)
        self.conversation_manager = ConversationManager(storage_dir=self.storage_dir)
        self.template_manager = TemplateManager(storage_dir=self.storage_dir)
        self.export_manager = ExportManager()
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def _create_test_configurations(self):
        """Create test configuration files."""
        profiles_dir = self.config_dir / 'profiles'
        profiles_dir.mkdir(parents=True, exist_ok=True)
        
        # Development profile
        dev_config = {
            'api': {
                'base_url': 'http://localhost:12434/engines/llama.cpp/v1/',
                'api_key': 'dev-key',
                'timeout': 10
            },
            'models': {
                'defaults': {
                    'temperature': 0.7,
                    'max_tokens': 150,
                    'stream': True
                },
                'ai/gemma3': {
                    'temperature': 0.8,
                    'max_tokens': 200
                }
            },
            'storage': {
                'conversations_dir': str(self.storage_dir / 'conversations'),
                'templates_dir': str(self.storage_dir / 'templates'),
                'auto_save': True,
                'backup_enabled': False
            }
        }
        
        # Production profile
        prod_config = {
            'api': {
                'base_url': 'http://production-server:12434/engines/llama.cpp/v1/',
                'api_key': 'prod-key',
                'timeout': 30
            },
            'models': {
                'defaults': {
                    'temperature': 0.5,
                    'max_tokens': 500,
                    'stream': False
                }
            },
            'storage': {
                'conversations_dir': str(self.storage_dir / 'prod_conversations'),
                'templates_dir': str(self.storage_dir / 'prod_templates'),
                'auto_save': True,
                'backup_enabled': True
            }
        }
        
        with open(profiles_dir / 'dev.yaml', 'w') as f:
            yaml.dump(dev_config, f)
        
        with open(profiles_dir / 'prod.yaml', 'w') as f:
            yaml.dump(prod_config, f)
    
    def test_complete_chat_workflow(self):
        """Test a complete chat session with saving and loading."""
        # Load development configuration
        self.config_manager.load_config('dev')
        
        # Simulate a chat session
        conversation = Conversation(
            metadata=ConversationMetadata(
                title="Complete Chat Test",
                model="ai/gemma3",
                profile="dev"
            ),
            messages=[]
        )
        
        # Simulate user messages and responses
        chat_messages = [
            ("user", "Hello, can you help me with Python?"),
            ("assistant", "Of course! I'd be happy to help you with Python. What specific topic would you like to learn about?"),
            ("user", "I want to learn about list comprehensions."),
            ("assistant", "List comprehensions are a concise way to create lists in Python. Here's the basic syntax:\n[expression for item in iterable if condition]"),
            ("user", "Can you give me an example?"),
            ("assistant", "Sure! Here's a simple example:\nnumbers = [1, 2, 3, 4, 5]\nsquares = [x**2 for x in numbers]\n# Result: [1, 4, 9, 16, 25]")
        ]
        
        # Add messages to conversation
        for role, content in chat_messages:
            message = Message(role=role, content=content)
            conversation.add_message(message)
        
        # Save conversation
        conv_id = self.conversation_manager.save_conversation(conversation)
        self.assertIsNotNone(conv_id)
        
        # Load conversation back
        loaded_conversation = self.conversation_manager.load_conversation(conv_id)
        
        # Verify conversation integrity
        self.assertEqual(loaded_conversation.metadata.title, "Complete Chat Test")
        self.assertEqual(loaded_conversation.metadata.model, "ai/gemma3")
        self.assertEqual(len(loaded_conversation.messages), 6)
        
        # Verify message content
        self.assertEqual(loaded_conversation.messages[0].role, "user")
        self.assertEqual(loaded_conversation.messages[0].content, "Hello, can you help me with Python?")
        
        # Verify conversation appears in list
        conversations = self.conversation_manager.list_conversations()
        conv_found = any(conv['id'] == conv_id for conv in conversations)
        self.assertTrue(conv_found)
    
    def test_template_based_workflow(self):
        """Test workflow using conversation templates."""
        # Load configuration
        self.config_manager.load_config('dev')
        
        # Create a code review template
        code_review_template = Template(
            name="code_review",
            title="Code Review Assistant",
            description="Template for conducting code reviews",
            category="development",
            content="""I need you to review the following {language} code:

```{language}
{code}
```

Please check for:
- Code quality and best practices
- Potential bugs or issues
- Performance considerations
- Readability and maintainability

Specific focus areas: {focus_areas}""",
            variables=["language", "code", "focus_areas"]
        )
        
        # Save template
        template_id = self.template_manager.save_template(code_review_template)
        
        # Instantiate template with specific code
        template_vars = {
            "language": "Python",
            "code": """def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)""",
            "focus_areas": "Error handling and edge cases"
        }
        
        instantiated_content = self.template_manager.instantiate_template(template_id, template_vars)
        
        # Create conversation from template
        conversation = Conversation(
            metadata=ConversationMetadata(
                title="Code Review: Python Function",
                model="ai/gemma3",
                template_id=template_id
            ),
            messages=[Message(role="user", content=instantiated_content)]
        )
        
        # Simulate assistant response
        assistant_response = """I've reviewed your Python function. Here are my findings:

**Issues Found:**
1. **Zero Division Error**: The function will crash if an empty list is passed
2. **Type Safety**: No validation that inputs are numbers

**Suggested Improvements:**
```python
def calculate_average(numbers):
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    
    if not all(isinstance(num, (int, float)) for num in numbers):
        raise TypeError("All elements must be numbers")
    
    return sum(numbers) / len(numbers)
```

**Performance**: Using `sum()` is more efficient than manual accumulation."""
        
        conversation.add_message(Message(role="assistant", content=assistant_response))
        
        # Save conversation
        conv_id = self.conversation_manager.save_conversation(conversation)
        
        # Verify template-based conversation
        loaded_conversation = self.conversation_manager.load_conversation(conv_id)
        self.assertEqual(loaded_conversation.metadata.template_id, template_id)
        self.assertIn("Code Review Assistant", loaded_conversation.messages[0].content)
        
        # Verify template is still available
        loaded_template = self.template_manager.load_template(template_id)
        self.assertEqual(loaded_template.name, "code_review")
    
    def test_export_import_workflow(self):
        """Test complete export and import workflow."""
        # Load configuration
        self.config_manager.load_config('dev')
        
        # Create a test conversation
        conversation = Conversation(
            metadata=ConversationMetadata(
                title="Export Test Conversation",
                model="ai/qwen3",
                tags=["test", "export", "workflow"]
            ),
            messages=[
                Message(role="user", content="What is machine learning?"),
                Message(role="assistant", content="Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed."),
                Message(role="user", content="Can you give me some examples?"),
                Message(role="assistant", content="Sure! Examples include:\n1. Image recognition\n2. Speech recognition\n3. Recommendation systems\n4. Fraud detection\n5. Natural language processing")
            ]
        )
        
        # Save original conversation
        original_id = self.conversation_manager.save_conversation(conversation)
        
        # Export to different formats
        export_formats = ['json', 'markdown', 'text']
        exported_files = {}
        
        for format_type in export_formats:
            export_path = self.export_dir / f"test_conversation.{format_type}"
            self.export_manager.export_conversation(conversation, export_path, format_type)
            
            # Verify file was created and has content
            self.assertTrue(export_path.exists())
            self.assertGreater(export_path.stat().st_size, 0)
            exported_files[format_type] = export_path
        
        # Verify export content quality
        # Check JSON export
        with open(exported_files['json'], 'r') as f:
            json_data = json.load(f)
            self.assertEqual(json_data['metadata']['title'], "Export Test Conversation")
            self.assertEqual(len(json_data['messages']), 4)
        
        # Check Markdown export
        with open(exported_files['markdown'], 'r') as f:
            md_content = f.read()
            self.assertIn("# Export Test Conversation", md_content)
            self.assertIn("**User:**", md_content)
            self.assertIn("**Assistant:**", md_content)
        
        # Check text export
        with open(exported_files['text'], 'r') as f:
            text_content = f.read()
            self.assertIn("Export Test Conversation", text_content)
            self.assertIn("machine learning", text_content.lower())
        
        # Test batch export
        # Create another conversation
        conversation2 = Conversation(
            metadata=ConversationMetadata(
                title="Second Test Conversation",
                model="ai/gemma3"
            ),
            messages=[
                Message(role="user", content="Hello again!"),
                Message(role="assistant", content="Hello! How can I help you today?")
            ]
        )
        
        conv_id2 = self.conversation_manager.save_conversation(conversation2)
        
        # Batch export all conversations
        all_conversations = [
            self.conversation_manager.load_conversation(original_id),
            self.conversation_manager.load_conversation(conv_id2)
        ]
        
        batch_export_dir = self.export_dir / "batch_export"
        self.export_manager.batch_export_conversations(all_conversations, batch_export_dir, "json")
        
        # Verify batch export
        self.assertTrue(batch_export_dir.exists())
        exported_files = list(batch_export_dir.glob("*.json"))
        self.assertEqual(len(exported_files), 2)
    
    def test_multi_profile_workflow(self):
        """Test workflow switching between different profiles."""
        # Start with development profile
        self.config_manager.load_config('dev')
        dev_storage_dir = Path(self.config_manager.get('storage.conversations_dir'))
        dev_storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Create conversation in dev environment
        dev_conversation = Conversation(
            metadata=ConversationMetadata(
                title="Development Conversation",
                model="ai/gemma3",
                profile="dev"
            ),
            messages=[
                Message(role="user", content="This is a dev environment test"),
                Message(role="assistant", content="I'm responding in the development environment with relaxed settings.")
            ]
        )
        
        dev_conv_manager = ConversationManager(storage_dir=dev_storage_dir)
        dev_conv_id = dev_conv_manager.save_conversation(dev_conversation)
        
        # Switch to production profile
        self.config_manager.load_config('prod')
        prod_storage_dir = Path(self.config_manager.get('storage.conversations_dir'))
        prod_storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Create conversation in prod environment
        prod_conversation = Conversation(
            metadata=ConversationMetadata(
                title="Production Conversation",
                model="ai/qwen3",
                profile="prod"
            ),
            messages=[
                Message(role="user", content="This is a production environment test"),
                Message(role="assistant", content="I'm responding in the production environment with strict settings.")
            ]
        )
        
        prod_conv_manager = ConversationManager(storage_dir=prod_storage_dir)
        prod_conv_id = prod_conv_manager.save_conversation(prod_conversation)
        
        # Verify profile-specific configurations
        dev_temp = self.config_manager.get('models.defaults.temperature')
        prod_temp = self.config_manager.get('models.defaults.temperature')
        
        # Switch back to dev and verify isolation
        self.config_manager.load_config('dev')
        dev_conversations = dev_conv_manager.list_conversations()
        dev_conv_found = any(conv['id'] == dev_conv_id for conv in dev_conversations)
        self.assertTrue(dev_conv_found)
        
        # Verify prod conversation is not visible in dev storage
        try:
            dev_conv_manager.load_conversation(prod_conv_id)
            self.fail("Should not be able to load prod conversation from dev storage")
        except FileNotFoundError:
            pass  # Expected behavior
        
        # Verify both conversations exist in their respective environments
        self.config_manager.load_config('prod')
        prod_conversations = prod_conv_manager.list_conversations()
        prod_conv_found = any(conv['id'] == prod_conv_id for conv in prod_conversations)
        self.assertTrue(prod_conv_found)
    
    def test_configuration_environment_override_workflow(self):
        """Test workflow with environment variable overrides."""
        # Set environment variables
        env_overrides = {
            'DMR_API_BASE_URL': 'http://custom-server:8080/v1/',
            'DMR_DEFAULT_MODEL': 'ai/custom-model',
            'DMR_MAX_TOKENS': '300',
            'DMR_TEMPERATURE': '0.9',
            'DMR_STORAGE_AUTO_SAVE': 'false'
        }
        
        with patch.dict(os.environ, env_overrides):
            # Load configuration with environment overrides
            self.config_manager.load_config('dev')
            
            # Verify environment overrides took effect
            self.assertEqual(
                self.config_manager.get_base_url(),
                'http://custom-server:8080/v1/'
            )
            self.assertEqual(
                self.config_manager.get_default_model(),
                'ai/custom-model'
            )
            self.assertEqual(
                self.config_manager.get('models.defaults.max_tokens'),
                300
            )
            self.assertEqual(
                self.config_manager.get('models.defaults.temperature'),
                0.9
            )
            self.assertEqual(
                self.config_manager.get('storage.auto_save'),
                False
            )
            
            # Create conversation with overridden settings
            conversation = Conversation(
                metadata=ConversationMetadata(
                    title="Environment Override Test",
                    model=self.config_manager.get_default_model()
                ),
                messages=[
                    Message(role="user", content="Testing with environment overrides")
                ]
            )
            
            # Save conversation
            conv_id = self.conversation_manager.save_conversation(conversation)
            
            # Verify conversation was saved with custom model
            loaded_conversation = self.conversation_manager.load_conversation(conv_id)
            self.assertEqual(loaded_conversation.metadata.model, 'ai/custom-model')
    
    def test_error_recovery_workflow(self):
        """Test workflow with error recovery scenarios."""
        # Load configuration
        self.config_manager.load_config('dev')
        
        # Create a conversation
        conversation = Conversation(
            metadata=ConversationMetadata(
                title="Error Recovery Test",
                model="ai/gemma3"
            ),
            messages=[
                Message(role="user", content="Initial message")
            ]
        )
        
        # Save conversation
        conv_id = self.conversation_manager.save_conversation(conversation)
        
        # Simulate system interruption by corrupting the file
        conv_file = self.storage_dir / f"{conv_id}.json"
        with open(conv_file, 'w') as f:
            f.write('{"corrupted": "data"')  # Invalid JSON
        
        # Attempt to load corrupted conversation (should fail)
        with self.assertRaises(json.JSONDecodeError):
            self.conversation_manager.load_conversation(conv_id)
        
        # Recover by recreating the conversation
        recovered_conversation = Conversation(
            id=conv_id,  # Use same ID
            metadata=ConversationMetadata(
                title="Error Recovery Test (Recovered)",
                model="ai/gemma3"
            ),
            messages=[
                Message(role="user", content="Initial message"),
                Message(role="system", content="Conversation recovered from error")
            ]
        )
        
        # Save recovered conversation
        recovered_id = self.conversation_manager.save_conversation(recovered_conversation)
        
        # Verify recovery
        loaded_recovered = self.conversation_manager.load_conversation(recovered_id)
        self.assertEqual(loaded_recovered.metadata.title, "Error Recovery Test (Recovered)")
        self.assertEqual(len(loaded_recovered.messages), 2)
        self.assertIn("recovered", loaded_recovered.messages[1].content.lower())


def run_workflow_tests():
    """Run all workflow tests."""
    print("🔄 Running End-to-End Workflow Tests")
    print("=" * 40)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestCompleteWorkflows)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n📊 Workflow Test Summary:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   - {test}")
    
    if result.errors:
        print(f"\n🔥 Errors:")
        for test, traceback in result.errors:
            print(f"   - {test}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_workflow_tests()