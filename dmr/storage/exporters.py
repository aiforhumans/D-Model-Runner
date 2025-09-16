"""
Export management system for D-Model-Runner.

This module provides export format selection, routing, and configuration
management for conversation exports.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Any, Type
from enum import Enum

from .conversation import Conversation


class ExportFormat(Enum):
    """Supported export formats."""
    JSON = "json"
    MARKDOWN = "markdown"
    PDF = "pdf"


class BaseExporter(ABC):
    """Base class for all conversation exporters."""
    
    @property
    @abstractmethod
    def format_name(self) -> str:
        """Name of the export format."""
        pass
    
    @property
    @abstractmethod
    def file_extension(self) -> str:
        """File extension for exported files."""
        pass
    
    @property
    @abstractmethod
    def mime_type(self) -> str:
        """MIME type of exported files."""
        pass
    
    @abstractmethod
    def export(self, conversation: Conversation, output_path: Path, 
               options: Optional[Dict[str, Any]] = None) -> Path:
        """Export conversation to specified path."""
        pass
    
    def validate_options(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and process export options."""
        return options or {}
    
    def get_default_filename(self, conversation: Conversation) -> str:
        """Generate default filename for the conversation."""
        title = conversation.metadata.title.replace(" ", "_").replace("/", "_")
        timestamp = conversation.metadata.created_at.strftime("%Y%m%d_%H%M%S")
        return f"{title}_{timestamp}.{self.file_extension}"


class ExportManager:
    """Manages conversation export operations."""
    
    def __init__(self):
        self._exporters: Dict[str, BaseExporter] = {}
        self._register_default_exporters()
    
    def _register_default_exporters(self) -> None:
        """Register default exporters."""
        from .formats import JSONExporter, MarkdownExporter, PDFExporter
        
        self.register_exporter(JSONExporter())
        self.register_exporter(MarkdownExporter())
        self.register_exporter(PDFExporter())
    
    def register_exporter(self, exporter: BaseExporter) -> None:
        """Register a new exporter."""
        self._exporters[exporter.format_name.lower()] = exporter
    
    def get_exporter(self, format_name: str) -> Optional[BaseExporter]:
        """Get exporter by format name."""
        return self._exporters.get(format_name.lower())
    
    def get_available_formats(self) -> List[Dict[str, str]]:
        """Get list of available export formats."""
        return [
            {
                'name': exporter.format_name,
                'extension': exporter.file_extension,
                'mime_type': exporter.mime_type
            }
            for exporter in self._exporters.values()
        ]
    
    def export_conversation(self, conversation: Conversation, format_name: str, 
                          output_path: Optional[Path] = None, 
                          options: Optional[Dict[str, Any]] = None) -> Path:
        """Export conversation in specified format."""
        exporter = self.get_exporter(format_name)
        if not exporter:
            available = list(self._exporters.keys())
            raise ValueError(f"Unsupported format '{format_name}'. Available: {available}")
        
        # Generate output path if not provided
        if output_path is None:
            default_filename = exporter.get_default_filename(conversation)
            output_path = Path.cwd() / "exports" / default_filename
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Validate options
        validated_options = exporter.validate_options(options or {})
        
        # Perform export
        return exporter.export(conversation, output_path, validated_options)
    
    def export_multiple(self, conversations: List[Conversation], format_name: str,
                       output_dir: Optional[Path] = None,
                       options: Optional[Dict[str, Any]] = None) -> List[Path]:
        """Export multiple conversations in specified format."""
        if output_dir is None:
            output_dir = Path.cwd() / "exports"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        exported_files = []
        
        for conversation in conversations:
            exporter = self.get_exporter(format_name)
            if exporter:
                filename = exporter.get_default_filename(conversation)
                output_path = output_dir / filename
                try:
                    exported_path = self.export_conversation(
                        conversation, format_name, output_path, options
                    )
                    exported_files.append(exported_path)
                except Exception as e:
                    print(f"Failed to export conversation {conversation.id}: {e}")
        
        return exported_files
    
    def create_export_bundle(self, conversations: List[Conversation], 
                           formats: List[str], output_dir: Optional[Path] = None,
                           options: Optional[Dict[str, Any]] = None) -> Dict[str, List[Path]]:
        """Export conversations in multiple formats."""
        if output_dir is None:
            output_dir = Path.cwd() / "exports"
        
        results = {}
        for format_name in formats:
            try:
                exported_files = self.export_multiple(
                    conversations, format_name, output_dir, options
                )
                results[format_name] = exported_files
            except Exception as e:
                print(f"Failed to export in format {format_name}: {e}")
                results[format_name] = []
        
        return results
    
    def get_export_summary(self, conversation: Conversation) -> Dict[str, Any]:
        """Get export summary information for a conversation."""
        return {
            'conversation_id': conversation.id,
            'title': conversation.metadata.title,
            'message_count': len(conversation.messages),
            'created_at': conversation.metadata.created_at.isoformat(),
            'updated_at': conversation.metadata.updated_at.isoformat(),
            'model': conversation.metadata.model,
            'tags': conversation.metadata.tags,
            'available_formats': [fmt['name'] for fmt in self.get_available_formats()]
        }


class ExportOptions:
    """Common export options and utilities."""
    
    @staticmethod
    def json_options() -> Dict[str, Any]:
        """Default options for JSON export."""
        return {
            'include_metadata': True,
            'include_timestamps': True,
            'pretty_print': True,
            'include_message_metadata': False
        }
    
    @staticmethod
    def markdown_options() -> Dict[str, Any]:
        """Default options for Markdown export."""
        return {
            'include_metadata': True,
            'include_timestamps': True,
            'use_code_blocks': True,
            'add_table_of_contents': False,
            'custom_css': None,
            'template': 'default'
        }
    
    @staticmethod
    def pdf_options() -> Dict[str, Any]:
        """Default options for PDF export."""
        return {
            'include_metadata': True,
            'include_timestamps': True,
            'page_size': 'A4',
            'margin': '1in',
            'font_family': 'Arial',
            'font_size': 12,
            'add_page_numbers': True,
            'add_header': True,
            'add_footer': True,
            'custom_css': None
        }