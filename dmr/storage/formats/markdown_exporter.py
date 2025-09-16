"""
Markdown exporter for D-Model-Runner conversations.

This module provides Markdown export functionality with formatting, styling,
and template support.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..conversation import Conversation
from ..exporters import BaseExporter


class MarkdownExporter(BaseExporter):
    """Exporter for Markdown format."""
    
    @property
    def format_name(self) -> str:
        return "Markdown"
    
    @property
    def file_extension(self) -> str:
        return "md"
    
    @property
    def mime_type(self) -> str:
        return "text/markdown"
    
    def validate_options(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Markdown export options."""
        default_options = {
            'include_metadata': True,
            'include_timestamps': True,
            'use_code_blocks': True,
            'add_table_of_contents': False,
            'template': 'default',
            'custom_css': None,
            'timestamp_format': '%Y-%m-%d %H:%M:%S',
            'message_separator': '\n---\n',
            'escape_markdown': True,
            'include_message_numbers': False
        }
        
        validated = default_options.copy()
        if options:
            validated.update(options)
        
        return validated
    
    def export(self, conversation: Conversation, output_path: Path, 
               options: Optional[Dict[str, Any]] = None) -> Path:
        """Export conversation to Markdown format."""
        validated_options = self.validate_options(options)
        
        # Build markdown content
        markdown_content = self._build_markdown_content(conversation, validated_options)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return output_path
    
    def _build_markdown_content(self, conversation: Conversation, options: Dict[str, Any]) -> str:
        """Build the markdown content."""
        lines = []
        
        # Add title
        title = conversation.metadata.title
        lines.append(f"# {self._escape_markdown(title) if options['escape_markdown'] else title}")
        lines.append("")
        
        # Add metadata section
        if options['include_metadata']:
            lines.extend(self._build_metadata_section(conversation, options))
            lines.append("")
        
        # Add table of contents if requested
        if options['add_table_of_contents']:
            lines.extend(self._build_table_of_contents(conversation))
            lines.append("")
        
        # Add messages
        lines.extend(self._build_messages_section(conversation, options))
        
        # Add custom CSS if provided
        if options['custom_css']:
            lines.append("")
            lines.append("<style>")
            lines.append(options['custom_css'])
            lines.append("</style>")
        
        return "\n".join(lines)
    
    def _build_metadata_section(self, conversation: Conversation, options: Dict[str, Any]) -> List[str]:
        """Build metadata section."""
        lines = ["## Conversation Metadata", ""]
        
        metadata = conversation.metadata
        
        # Basic metadata table
        lines.append("| Field | Value |")
        lines.append("|-------|-------|")
        lines.append(f"| **ID** | `{conversation.id}` |")
        lines.append(f"| **Title** | {self._escape_markdown(metadata.title) if options['escape_markdown'] else metadata.title} |")
        lines.append(f"| **Model** | `{metadata.model}` |")
        
        if options['include_timestamps']:
            created_str = metadata.created_at.strftime(options['timestamp_format'])
            updated_str = metadata.updated_at.strftime(options['timestamp_format'])
            lines.append(f"| **Created** | {created_str} |")
            lines.append(f"| **Updated** | {updated_str} |")
        
        lines.append(f"| **Messages** | {len(conversation.messages)} |")
        
        if metadata.tags:
            tags_str = ", ".join([f"`{tag}`" for tag in metadata.tags])
            lines.append(f"| **Tags** | {tags_str} |")
        
        if metadata.description:
            desc = self._escape_markdown(metadata.description) if options['escape_markdown'] else metadata.description
            lines.append(f"| **Description** | {desc} |")
        
        lines.append("")
        
        # Model configuration if available
        if metadata.model_config:
            lines.append("### Model Configuration")
            lines.append("")
            for key, value in metadata.model_config.items():
                lines.append(f"- **{key}**: `{value}`")
            lines.append("")
        
        return lines
    
    def _build_table_of_contents(self, conversation: Conversation) -> List[str]:
        """Build table of contents."""
        lines = ["## Table of Contents", ""]
        
        # Add metadata link
        lines.append("- [Conversation Metadata](#conversation-metadata)")
        
        # Add message links
        for i, message in enumerate(conversation.messages, 1):
            role_title = message.role.title()
            # Create anchor-safe title
            content_preview = message.content[:30].replace('\n', ' ')
            if len(message.content) > 30:
                content_preview += "..."
            
            # Clean preview for anchor
            anchor = f"message-{i}-{role_title.lower()}"
            lines.append(f"- [Message {i}: {role_title} - {content_preview}](#{anchor})")
        
        return lines
    
    def _build_messages_section(self, conversation: Conversation, options: Dict[str, Any]) -> List[str]:
        """Build messages section."""
        lines = ["## Conversation Messages", ""]
        
        for i, message in enumerate(conversation.messages, 1):
            # Message header
            role_title = message.role.title()
            if options['include_message_numbers']:
                header = f"### Message {i}: {role_title}"
            else:
                header = f"### {role_title}"
            
            lines.append(header)
            
            # Add timestamp if requested
            if options['include_timestamps']:
                timestamp_str = message.timestamp.strftime(options['timestamp_format'])
                lines.append(f"*{timestamp_str}*")
                lines.append("")
            
            # Add message content
            content = message.content
            if options['escape_markdown']:
                content = self._escape_markdown(content)
            
            # Check if content looks like code and use code blocks
            if options['use_code_blocks'] and self._is_code_content(content):
                # Try to detect language
                language = self._detect_code_language(content)
                lines.append(f"```{language}")
                lines.append(content)
                lines.append("```")
            else:
                lines.append(content)
            
            # Add message metadata if available
            if message.metadata:
                lines.append("")
                lines.append("**Message Metadata:**")
                for key, value in message.metadata.items():
                    lines.append(f"- **{key}**: `{value}`")
            
            # Add separator between messages
            if i < len(conversation.messages):
                lines.append(options['message_separator'])
        
        return lines
    
    def _escape_markdown(self, text: str) -> str:
        """Escape special markdown characters."""
        # Escape markdown special characters
        special_chars = ['\\', '`', '*', '_', '{', '}', '[', ']', '(', ')', '#', '+', '-', '.', '!']
        escaped = text
        for char in special_chars:
            escaped = escaped.replace(char, f'\\{char}')
        return escaped
    
    def _is_code_content(self, content: str) -> bool:
        """Heuristically detect if content is code."""
        code_indicators = [
            'def ', 'class ', 'import ', 'from ', 'function', 'var ', 'const ', 'let ',
            '#!/', '<?', '<html', '<div', '{', '}', ';', '  ', '\t'
        ]
        
        content_lower = content.lower()
        for indicator in code_indicators:
            if indicator in content_lower:
                return True
        
        # Check for high ratio of special characters
        special_count = sum(1 for c in content if c in '{}[]();,=<>!@#$%^&*')
        if len(content) > 0 and special_count / len(content) > 0.1:
            return True
        
        return False
    
    def _detect_code_language(self, content: str) -> str:
        """Detect programming language from content."""
        content_lower = content.lower()
        
        # Python indicators
        if any(indicator in content_lower for indicator in ['def ', 'import ', 'from ', 'print(', 'if __name__']):
            return 'python'
        
        # JavaScript indicators
        if any(indicator in content_lower for indicator in ['function ', 'var ', 'const ', 'let ', 'console.log']):
            return 'javascript'
        
        # HTML indicators
        if any(indicator in content_lower for indicator in ['<html', '<div', '<span', '<p>', '<!doctype']):
            return 'html'
        
        # CSS indicators
        if any(indicator in content_lower for indicator in ['color:', 'margin:', 'padding:', 'font-size:']):
            return 'css'
        
        # SQL indicators
        if any(indicator in content_lower for indicator in ['select ', 'from ', 'where ', 'insert ', 'update ']):
            return 'sql'
        
        # JSON indicators
        if content.strip().startswith('{') and content.strip().endswith('}'):
            return 'json'
        
        # Shell script indicators
        if content.startswith('#!') or any(indicator in content_lower for indicator in ['echo ', 'cd ', 'ls ', 'grep ']):
            return 'bash'
        
        return ''  # No language detected
    
    def get_template_options(self) -> Dict[str, Dict[str, Any]]:
        """Get available template options."""
        return {
            'default': {
                'description': 'Standard conversation format',
                'include_metadata': True,
                'include_timestamps': True,
                'use_code_blocks': True,
                'add_table_of_contents': False
            },
            'clean': {
                'description': 'Clean format without metadata',
                'include_metadata': False,
                'include_timestamps': False,
                'use_code_blocks': True,
                'add_table_of_contents': False
            },
            'detailed': {
                'description': 'Detailed format with all metadata and TOC',
                'include_metadata': True,
                'include_timestamps': True,
                'use_code_blocks': True,
                'add_table_of_contents': True,
                'include_message_numbers': True
            },
            'presentation': {
                'description': 'Format suitable for presentations',
                'include_metadata': False,
                'include_timestamps': False,
                'use_code_blocks': True,
                'add_table_of_contents': True,
                'message_separator': '\n\n---\n\n'
            }
        }
    
    def apply_template(self, template_name: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a predefined template to export options."""
        templates = self.get_template_options()
        if template_name not in templates:
            return options
        
        template_options = templates[template_name].copy()
        # Remove description as it's not an export option
        template_options.pop('description', None)
        
        # Merge with provided options (provided options take precedence)
        merged_options = template_options.copy()
        merged_options.update(options)
        
        return merged_options