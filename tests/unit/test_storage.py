"""
Unit tests for the conversation persistence system.

Tests cover:
- Conversation save/load functionality
- Template management
- Export functionality (JSON, Markdown, PDF)
- Storage operations and error handling
"""

import unittest
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

from dmr.storage.conversation import Conversation, Message, ConversationMetadata, ConversationManager
from dmr.storage.templates import Template, TemplateManager
from dmr.storage.exporters import ExportManager
from dmr.storage.formats.json_exporter import JSONExporter
from dmr.storage.formats.markdown_exporter import MarkdownExporter


class TestConversation(unittest.TestCase):
    """Test the Conversation data model."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.metadata = ConversationMetadata(
            title="Test Conversation",
            model="ai/test-model",
            tags=["test", "unit-test"],
            description="A test conversation"
        )
        
        self.messages = [
            Message(role="user", content="Hello, how are you?"),
            Message(role="assistant", content="I'm doing well, thank you for asking!"),
            Message(role="user", content="Can you help me with testing?"),
            Message(role="assistant", content="Of course! I'd be happy to help with testing.")
        ]
        
        self.conversation = Conversation(
            metadata=self.metadata,
            messages=self.messages
        )
    
    def test_conversation_creation(self):
        """Test conversation creation."""
        self.assertIsInstance(self.conversation.id, str)
        self.assertEqual(len(self.conversation.id), 36)  # UUID length
        self.assertEqual(self.conversation.metadata.title, "Test Conversation")
        self.assertEqual(len(self.conversation.messages), 4)
        self.assertIsInstance(self.conversation.metadata.created_at, datetime)
        self.assertIsInstance(self.conversation.metadata.updated_at, datetime)
    
    def test_add_message(self):
        """Test adding messages to conversation."""
        initial_count = len(self.conversation.messages)
        new_message = Message(role="user", content="Another message")
        
        self.conversation.add_message(new_message)
        
        self.assertEqual(len(self.conversation.messages), initial_count + 1)
        self.assertEqual(self.conversation.messages[-1].content, "Another message")
        # Updated timestamp should change
        self.assertGreater(self.conversation.metadata.updated_at, self.conversation.metadata.created_at)
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        data = self.conversation.to_dict()
        
        self.assertIn('id', data)
        self.assertIn('metadata', data)
        self.assertIn('messages', data)
        self.assertEqual(data['metadata']['title'], "Test Conversation")
        self.assertEqual(len(data['messages']), 4)
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = self.conversation.to_dict()
        restored = Conversation.from_dict(data)
        
        self.assertEqual(restored.id, self.conversation.id)
        self.assertEqual(restored.metadata.title, self.conversation.metadata.title)
        self.assertEqual(len(restored.messages), len(self.conversation.messages))
        self.assertEqual(restored.messages[0].content, self.conversation.messages[0].content)


class TestMessage(unittest.TestCase):
    """Test the Message data model."""
    
    def test_message_creation(self):
        """Test message creation."""
        message = Message(role="user", content="Test content")
        
        self.assertEqual(message.role, "user")
        self.assertEqual(message.content, "Test content")
        self.assertIsInstance(message.timestamp, datetime)
        self.assertIsInstance(message.id, str)
    
    def test_message_validation(self):
        """Test message validation."""
        # Valid roles
        for role in ["user", "assistant", "system"]:
            message = Message(role=role, content="Test")
            self.assertEqual(message.role, role)
        
        # Invalid role should raise error
        with self.assertRaises(ValueError):
            Message(role="invalid", content="Test")
    
    def test_message_to_dict(self):
        """Test message dictionary conversion."""
        message = Message(role="assistant", content="Test response")
        data = message.to_dict()
        
        self.assertEqual(data['role'], "assistant")
        self.assertEqual(data['content'], "Test response")
        self.assertIn('timestamp', data)
        self.assertIn('id', data)


class TestConversationManager(unittest.TestCase):
    """Test the ConversationManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_dir = Path(self.temp_dir)
        self.manager = ConversationManager(storage_dir=self.storage_dir)
        
        # Create test conversation
        self.test_conversation = Conversation(
            metadata=ConversationMetadata(
                title="Test Conversation",
                model="ai/test-model",
                tags=["test"]
            ),
            messages=[
                Message(role="user", content="Hello"),
                Message(role="assistant", content="Hi there!")
            ]
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_save_conversation(self):
        """Test saving a conversation."""
        conversation_id = self.manager.save_conversation(self.test_conversation)
        
        self.assertEqual(conversation_id, self.test_conversation.id)
        
        # Check file was created
        file_path = self.storage_dir / f"{conversation_id}.json"
        self.assertTrue(file_path.exists())
        
        # Check file contents
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(data['id'], conversation_id)
        self.assertEqual(data['metadata']['title'], "Test Conversation")
    
    def test_load_conversation(self):
        """Test loading a conversation."""
        # Save first
        conversation_id = self.manager.save_conversation(self.test_conversation)
        
        # Load
        loaded = self.manager.load_conversation(conversation_id)
        
        self.assertEqual(loaded.id, self.test_conversation.id)
        self.assertEqual(loaded.metadata.title, self.test_conversation.metadata.title)
        self.assertEqual(len(loaded.messages), len(self.test_conversation.messages))
    
    def test_load_nonexistent_conversation(self):
        """Test loading a nonexistent conversation."""
        with self.assertRaises(FileNotFoundError):
            self.manager.load_conversation("nonexistent-id")
    
    def test_list_conversations(self):
        """Test listing conversations."""
        # Save multiple conversations
        conv1 = self.test_conversation
        conv2 = Conversation(
            metadata=ConversationMetadata(title="Second Conversation", model="ai/test"),
            messages=[Message(role="user", content="Test")]
        )
        
        self.manager.save_conversation(conv1)
        self.manager.save_conversation(conv2)
        
        conversations = self.manager.list_conversations()
        
        self.assertEqual(len(conversations), 2)
        titles = [conv['metadata']['title'] for conv in conversations]
        self.assertIn("Test Conversation", titles)
        self.assertIn("Second Conversation", titles)
    
    def test_delete_conversation(self):
        """Test deleting a conversation."""
        conversation_id = self.manager.save_conversation(self.test_conversation)
        
        # Verify it exists
        self.assertTrue(self.manager.conversation_exists(conversation_id))
        
        # Delete
        self.manager.delete_conversation(conversation_id)
        
        # Verify it's gone
        self.assertFalse(self.manager.conversation_exists(conversation_id))
    
    def test_search_conversations(self):
        """Test searching conversations."""
        # Create conversations with different content
        conv1 = Conversation(
            metadata=ConversationMetadata(title="Python Tutorial", model="ai/test"),
            messages=[Message(role="user", content="Teach me Python")]
        )
        conv2 = Conversation(
            metadata=ConversationMetadata(title="JavaScript Guide", model="ai/test"),
            messages=[Message(role="user", content="Explain JavaScript")]
        )
        
        self.manager.save_conversation(conv1)
        self.manager.save_conversation(conv2)
        
        # Search by title
        results = self.manager.search_conversations("Python")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['metadata']['title'], "Python Tutorial")
        
        # Search by content
        results = self.manager.search_conversations("JavaScript")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['metadata']['title'], "JavaScript Guide")


class TestTemplateManager(unittest.TestCase):
    """Test the TemplateManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_dir = Path(self.temp_dir)
        self.manager = TemplateManager(storage_dir=self.storage_dir)
        
        self.test_template = Template(
            name="test_template",
            title="Test Template",
            description="A template for testing",
            category="testing",
            content="Hello {name}, welcome to {project}!",
            variables=["name", "project"]
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_save_template(self):
        """Test saving a template."""
        template_id = self.manager.save_template(self.test_template)
        
        self.assertEqual(template_id, self.test_template.id)
        
        # Check file was created
        file_path = self.storage_dir / f"{template_id}.json"
        self.assertTrue(file_path.exists())
    
    def test_load_template(self):
        """Test loading a template."""
        template_id = self.manager.save_template(self.test_template)
        loaded = self.manager.load_template(template_id)
        
        self.assertEqual(loaded.name, self.test_template.name)
        self.assertEqual(loaded.title, self.test_template.title)
        self.assertEqual(loaded.content, self.test_template.content)
    
    def test_instantiate_template(self):
        """Test template instantiation with variables."""
        template_id = self.manager.save_template(self.test_template)
        
        variables = {"name": "Alice", "project": "D-Model-Runner"}
        result = self.manager.instantiate_template(template_id, variables)
        
        expected = "Hello Alice, welcome to D-Model-Runner!"
        self.assertEqual(result, expected)
    
    def test_list_templates(self):
        """Test listing templates."""
        template1 = self.test_template
        template2 = Template(
            name="second_template",
            title="Second Template",
            description="Another template",
            category="testing",
            content="Content {var}",
            variables=["var"]
        )
        
        self.manager.save_template(template1)
        self.manager.save_template(template2)
        
        templates = self.manager.list_templates()
        self.assertEqual(len(templates), 2)
        
        names = [t['name'] for t in templates]
        self.assertIn("test_template", names)
        self.assertIn("second_template", names)
    
    def test_get_templates_by_category(self):
        """Test getting templates by category."""
        # Create templates in different categories
        template1 = Template(
            name="code_review",
            title="Code Review",
            category="development",
            content="Review this code: {code}",
            variables=["code"]
        )
        template2 = Template(
            name="bug_report",
            title="Bug Report",
            category="testing",
            content="Bug: {description}",
            variables=["description"]
        )
        
        self.manager.save_template(template1)
        self.manager.save_template(template2)
        
        dev_templates = self.manager.get_templates_by_category("development")
        self.assertEqual(len(dev_templates), 1)
        self.assertEqual(dev_templates[0]['name'], "code_review")
        
        test_templates = self.manager.get_templates_by_category("testing")
        self.assertEqual(len(test_templates), 1)
        self.assertEqual(test_templates[0]['name'], "bug_report")


class TestExportManager(unittest.TestCase):
    """Test the ExportManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.export_dir = Path(self.temp_dir)
        self.manager = ExportManager()
        
        self.test_conversation = Conversation(
            metadata=ConversationMetadata(
                title="Export Test",
                model="ai/test-model",
                tags=["test", "export"]
            ),
            messages=[
                Message(role="user", content="Hello"),
                Message(role="assistant", content="Hi! How can I help you?"),
                Message(role="user", content="Can you help with testing?"),
                Message(role="assistant", content="Absolutely! I'm here to help.")
            ]
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_export_json(self):
        """Test JSON export."""
        output_path = self.export_dir / "test_export.json"
        
        result_path = self.manager.export_conversation(
            self.test_conversation,
            output_path,
            "json"
        )
        
        self.assertEqual(result_path, output_path)
        self.assertTrue(output_path.exists())
        
        # Verify content
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(data['metadata']['title'], "Export Test")
        self.assertEqual(len(data['messages']), 4)
    
    def test_export_markdown(self):
        """Test Markdown export."""
        output_path = self.export_dir / "test_export.md"
        
        result_path = self.manager.export_conversation(
            self.test_conversation,
            output_path,
            "markdown"
        )
        
        self.assertEqual(result_path, output_path)
        self.assertTrue(output_path.exists())
        
        # Verify content
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("# Export Test", content)
        self.assertIn("**User:**", content)
        self.assertIn("**Assistant:**", content)
    
    def test_get_available_formats(self):
        """Test getting available export formats."""
        formats = self.manager.get_available_formats()
        
        self.assertIn("json", formats)
        self.assertIn("markdown", formats)
        self.assertIn("pdf", formats)
    
    def test_export_with_options(self):
        """Test export with custom options."""
        output_path = self.export_dir / "test_options.md"
        
        options = {
            'include_metadata': True,
            'include_timestamps': True,
            'format_code': True
        }
        
        self.manager.export_conversation(
            self.test_conversation,
            output_path,
            "markdown",
            options
        )
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should include metadata section
        self.assertIn("## Metadata", content)
        self.assertIn("Model:", content)
        self.assertIn("Tags:", content)
    
    def test_export_invalid_format(self):
        """Test export with invalid format."""
        output_path = self.export_dir / "test.invalid"
        
        with self.assertRaises(ValueError):
            self.manager.export_conversation(
                self.test_conversation,
                output_path,
                "invalid_format"
            )


class TestJSONExporter(unittest.TestCase):
    """Test the JSONExporter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.exporter = JSONExporter()
        self.test_conversation = Conversation(
            metadata=ConversationMetadata(title="JSON Test", model="ai/test"),
            messages=[Message(role="user", content="Test message")]
        )
    
    def test_export_properties(self):
        """Test exporter properties."""
        self.assertEqual(self.exporter.format_name, "JSON")
        self.assertEqual(self.exporter.file_extension, "json")
        self.assertEqual(self.exporter.mime_type, "application/json")
    
    def test_validate_options(self):
        """Test option validation."""
        options = self.exporter.validate_options({})
        self.assertIn('include_metadata', options)
        self.assertIn('include_timestamps', options)
        self.assertIn('pretty_print', options)


class TestMarkdownExporter(unittest.TestCase):
    """Test the MarkdownExporter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.exporter = MarkdownExporter()
        self.test_conversation = Conversation(
            metadata=ConversationMetadata(title="Markdown Test", model="ai/test"),
            messages=[
                Message(role="user", content="What is Python?"),
                Message(role="assistant", content="Python is a programming language.\n\n```python\nprint('Hello, World!')\n```")
            ]
        )
    
    def test_export_properties(self):
        """Test exporter properties."""
        self.assertEqual(self.exporter.format_name, "Markdown")
        self.assertEqual(self.exporter.file_extension, "md")
        self.assertEqual(self.exporter.mime_type, "text/markdown")
    
    def test_code_detection(self):
        """Test code block detection."""
        # Should detect code blocks
        self.assertTrue(self.exporter._has_code_blocks("Here's some code:\n```python\nprint('hello')\n```"))
        self.assertTrue(self.exporter._has_code_blocks("Inline `code` here"))
        
        # Should not detect regular text
        self.assertFalse(self.exporter._has_code_blocks("This is just regular text"))
    
    def test_validate_options(self):
        """Test option validation."""
        options = self.exporter.validate_options({'custom_option': 'value'})
        self.assertIn('include_metadata', options)
        self.assertIn('format_code', options)
        self.assertIn('custom_option', options)


if __name__ == '__main__':
    unittest.main()