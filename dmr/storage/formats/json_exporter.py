"""
JSON exporter for D-Model-Runner conversations.

This module provides JSON export functionality with metadata preservation
and import capabilities.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..conversation import Conversation
from ..exporters import BaseExporter


class JSONExporter(BaseExporter):
    """Exporter for JSON format."""
    
    @property
    def format_name(self) -> str:
        return "JSON"
    
    @property
    def file_extension(self) -> str:
        return "json"
    
    @property
    def mime_type(self) -> str:
        return "application/json"
    
    def validate_options(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Validate JSON export options."""
        default_options = {
            'include_metadata': True,
            'include_timestamps': True,
            'pretty_print': True,
            'include_message_metadata': False,
            'indent': 2,
            'ensure_ascii': False
        }
        
        validated = default_options.copy()
        if options:
            validated.update(options)
        
        # Validate specific options
        if 'indent' in validated and not isinstance(validated['indent'], int):
            validated['indent'] = 2
        
        return validated
    
    def export(self, conversation: Conversation, output_path: Path, 
               options: Optional[Dict[str, Any]] = None) -> Path:
        """Export conversation to JSON format with streaming for large conversations."""
        validated_options = self.validate_options(options)
        
        # Use streaming export for large conversations (>1000 messages)
        if len(conversation.messages) > 1000:
            return self._export_streaming(conversation, output_path, validated_options)
        else:
            return self._export_buffered(conversation, output_path, validated_options)
    
    def _export_buffered(self, conversation: Conversation, output_path: Path, 
                        options: Dict[str, Any]) -> Path:
        """Export using traditional buffered approach for smaller conversations."""
        # Build export data
        export_data = self._build_export_data(conversation, options)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            if options['pretty_print']:
                json.dump(
                    export_data, 
                    f, 
                    indent=options['indent'],
                    ensure_ascii=options['ensure_ascii']
                )
            else:
                json.dump(
                    export_data, 
                    f, 
                    ensure_ascii=options['ensure_ascii']
                )
        
        return output_path
    
    def _export_streaming(self, conversation: Conversation, output_path: Path,
                         options: Dict[str, Any]) -> Path:
        """Export using streaming approach for large conversations."""
        with open(output_path, 'w', encoding='utf-8') as f:
            # Write opening structure
            f.write('{\n' if options['pretty_print'] else '{')
            
            # Export info
            export_info = {
                'format': 'json',
                'version': '1.0',
                'exported_at': conversation.metadata.updated_at.isoformat(),
                'exporter': 'D-Model-Runner JSON Exporter (Streaming)'
            }
            
            indent = '  ' if options['pretty_print'] else ''
            f.write(f'{indent}"export_info": ')
            json.dump(export_info, f, ensure_ascii=options['ensure_ascii'])
            f.write(',\n' if options['pretty_print'] else ',')
            
            # Start conversation object
            f.write(f'{indent}"conversation": {{\n' if options['pretty_print'] else '"conversation":{')
            
            # Conversation ID
            f.write(f'{indent}  "id": ' if options['pretty_print'] else '"id":')
            json.dump(conversation.id, f, ensure_ascii=options['ensure_ascii'])
            f.write(',\n' if options['pretty_print'] else ',')
            
            # Metadata if requested
            if options['include_metadata']:
                f.write(f'{indent}  "metadata": ' if options['pretty_print'] else '"metadata":')
                json.dump(conversation.metadata.to_dict(), f, ensure_ascii=options['ensure_ascii'])
                f.write(',\n' if options['pretty_print'] else ',')
            
            # Start messages array
            f.write(f'{indent}  "messages": [\n' if options['pretty_print'] else '"messages":[')
            
            # Stream messages one by one
            for i, message in enumerate(conversation.messages):
                if i > 0:
                    f.write(',\n' if options['pretty_print'] else ',')
                
                message_data = {
                    'role': message.role,
                    'content': message.content
                }
                
                if options['include_timestamps']:
                    message_data['timestamp'] = message.timestamp.isoformat()
                
                if options['include_message_metadata'] and message.metadata:
                    message_data['metadata'] = message.metadata
                
                if options['pretty_print']:
                    f.write(f'{indent}    ')
                
                json.dump(message_data, f, ensure_ascii=options['ensure_ascii'])
            
            # Close messages array and conversation object
            f.write(f'\n{indent}  ]\n' if options['pretty_print'] else ']')
            f.write(f'{indent}}}\n' if options['pretty_print'] else '}')
            f.write('}')
        
        return output_path
    
    def _build_export_data(self, conversation: Conversation, options: Dict[str, Any]) -> Dict[str, Any]:
        """Build the export data structure."""
        export_data = {
            'export_info': {
                'format': 'json',
                'version': '1.0',
                'exported_at': conversation.metadata.updated_at.isoformat(),
                'exporter': 'D-Model-Runner JSON Exporter'
            },
            'conversation': {
                'id': conversation.id,
                'messages': []
            }
        }
        
        # Include metadata if requested
        if options['include_metadata']:
            export_data['conversation']['metadata'] = conversation.metadata.to_dict()
        
        # Process messages
        for message in conversation.messages:
            message_data = {
                'role': message.role,
                'content': message.content
            }
            
            # Include timestamps if requested
            if options['include_timestamps']:
                message_data['timestamp'] = message.timestamp.isoformat()
            
            # Include message metadata if requested
            if options['include_message_metadata'] and message.metadata:
                message_data['metadata'] = message.metadata
            
            export_data['conversation']['messages'].append(message_data)
        
        return export_data
    
    def import_conversation(self, file_path: Path) -> Conversation:
        """Import conversation from JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON formats
        if 'conversation' in data:
            # Our export format
            conversation_data = data['conversation']
        elif 'id' in data and 'messages' in data:
            # Direct conversation format
            conversation_data = data
        else:
            raise ValueError("Invalid JSON format for conversation import")
        
        # Create conversation from data
        return Conversation.from_dict(conversation_data)
    
    def validate_import_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate JSON file for import."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            validation_result = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'info': {}
            }
            
            # Check structure
            if 'conversation' in data:
                conversation_data = data['conversation']
                validation_result['info']['format'] = 'D-Model-Runner Export'
            elif 'id' in data and 'messages' in data:
                conversation_data = data
                validation_result['info']['format'] = 'Direct Conversation'
            else:
                validation_result['valid'] = False
                validation_result['errors'].append("Missing required fields: 'conversation' or 'id' and 'messages'")
                return validation_result
            
            # Validate required fields
            if 'messages' not in conversation_data:
                validation_result['valid'] = False
                validation_result['errors'].append("Missing 'messages' field")
            else:
                messages = conversation_data['messages']
                if not isinstance(messages, list):
                    validation_result['valid'] = False
                    validation_result['errors'].append("'messages' must be a list")
                else:
                    validation_result['info']['message_count'] = len(messages)
                    
                    # Validate message structure
                    for i, message in enumerate(messages):
                        if not isinstance(message, dict):
                            validation_result['errors'].append(f"Message {i} is not a dictionary")
                            continue
                        
                        if 'role' not in message:
                            validation_result['errors'].append(f"Message {i} missing 'role' field")
                        
                        if 'content' not in message:
                            validation_result['errors'].append(f"Message {i} missing 'content' field")
            
            # Check metadata
            if 'metadata' in conversation_data:
                validation_result['info']['has_metadata'] = True
                metadata = conversation_data['metadata']
                if 'title' in metadata:
                    validation_result['info']['title'] = metadata['title']
                if 'model' in metadata:
                    validation_result['info']['model'] = metadata['model']
            else:
                validation_result['warnings'].append("No metadata found")
            
            return validation_result
            
        except json.JSONDecodeError as e:
            return {
                'valid': False,
                'errors': [f"Invalid JSON: {str(e)}"],
                'warnings': [],
                'info': {}
            }
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Error reading file: {str(e)}"],
                'warnings': [],
                'info': {}
            }
    
    def export_multiple_conversations(self, conversations: List[Conversation], 
                                    output_path: Path, 
                                    options: Optional[Dict[str, Any]] = None) -> Path:
        """Export multiple conversations to a single JSON file."""
        validated_options = self.validate_options(options)
        
        export_data = {
            'export_info': {
                'format': 'json_collection',
                'version': '1.0',
                'exported_at': conversations[0].metadata.updated_at.isoformat() if conversations else "",
                'exporter': 'D-Model-Runner JSON Exporter',
                'conversation_count': len(conversations)
            },
            'conversations': []
        }
        
        for conversation in conversations:
            conversation_data = self._build_export_data(conversation, validated_options)
            export_data['conversations'].append(conversation_data['conversation'])
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            if validated_options['pretty_print']:
                json.dump(
                    export_data, 
                    f, 
                    indent=validated_options['indent'],
                    ensure_ascii=validated_options['ensure_ascii']
                )
            else:
                json.dump(
                    export_data, 
                    f, 
                    ensure_ascii=validated_options['ensure_ascii']
                )
        
        return output_path
    
    def import_multiple_conversations(self, file_path: Path) -> List[Conversation]:
        """Import multiple conversations from JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'conversations' not in data:
            raise ValueError("Invalid JSON format for multiple conversation import")
        
        conversations = []
        for conversation_data in data['conversations']:
            conversation = Conversation.from_dict(conversation_data)
            conversations.append(conversation)
        
        return conversations