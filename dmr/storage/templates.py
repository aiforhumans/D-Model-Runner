"""
Template management system for D-Model-Runner.

This module provides template creation, storage, and instantiation functionality
for conversation workflows and common use cases.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field

from .conversation import Conversation, ConversationMetadata, Message


@dataclass
class TemplateMessage:
    """Template message with placeholders."""
    role: str  # 'user', 'assistant', 'system'
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def render(self, variables: Dict[str, str]) -> str:
        """Render template content with variables."""
        content = self.content
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            content = content.replace(placeholder, str(value))
        return content
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template message to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemplateMessage':
        """Create template message from dictionary."""
        return cls(**data)


@dataclass
class TemplateMetadata:
    """Metadata for a conversation template."""
    name: str
    description: str
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    author: str = "D-Model-Runner"
    version: str = "1.0"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    variables: List[str] = field(default_factory=list)  # Required template variables
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemplateMetadata':
        """Create metadata from dictionary."""
        data = data.copy()
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


class Template:
    """Represents a conversation template."""
    
    def __init__(self, id: Optional[str] = None, metadata: Optional[TemplateMetadata] = None):
        self.id = id or str(uuid.uuid4())
        self.metadata = metadata or TemplateMetadata(name="New Template", description="")
        self.messages: List[TemplateMessage] = []
        self.default_model = "ai/gemma3"
        self.model_config: Dict[str, Any] = {}
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> TemplateMessage:
        """Add a message to the template."""
        message = TemplateMessage(role=role, content=content, metadata=metadata or {})
        self.messages.append(message)
        self.metadata.updated_at = datetime.now()
        return message
    
    def get_required_variables(self) -> List[str]:
        """Get all required variables from template messages."""
        variables = set()
        for message in self.messages:
            # Simple extraction of {variable} patterns
            import re
            found_vars = re.findall(r'\{(\w+)\}', message.content)
            variables.update(found_vars)
        return list(variables)
    
    def validate_variables(self, variables: Dict[str, str]) -> List[str]:
        """Validate that all required variables are provided."""
        required = set(self.get_required_variables())
        provided = set(variables.keys())
        missing = required - provided
        return list(missing)
    
    def instantiate(self, variables: Dict[str, str], title: Optional[str] = None) -> Conversation:
        """Create a conversation instance from the template."""
        missing_vars = self.validate_variables(variables)
        if missing_vars:
            raise ValueError(f"Missing required variables: {', '.join(missing_vars)}")
        
        # Create conversation metadata
        conversation_title = title or f"{self.metadata.name} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        conv_metadata = ConversationMetadata(
            title=conversation_title,
            model=self.default_model,
            description=f"Created from template: {self.metadata.name}",
            tags=self.metadata.tags.copy(),
            model_config=self.model_config.copy()
        )
        
        # Create conversation
        conversation = Conversation(metadata=conv_metadata)
        
        # Add rendered messages
        for template_msg in self.messages:
            rendered_content = template_msg.render(variables)
            conversation.add_message(
                role=template_msg.role,
                content=rendered_content,
                metadata=template_msg.metadata.copy()
            )
        
        return conversation
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary."""
        return {
            'id': self.id,
            'metadata': self.metadata.to_dict(),
            'messages': [msg.to_dict() for msg in self.messages],
            'default_model': self.default_model,
            'model_config': self.model_config,
            'version': '1.0'
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Template':
        """Create template from dictionary."""
        template = cls(
            id=data['id'],
            metadata=TemplateMetadata.from_dict(data['metadata'])
        )
        template.messages = [TemplateMessage.from_dict(msg) for msg in data.get('messages', [])]
        template.default_model = data.get('default_model', 'ai/gemma3')
        template.model_config = data.get('model_config', {})
        return template
    
    def save(self, file_path: Path) -> None:
        """Save template to file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load(cls, file_path: Path) -> 'Template':
        """Load template from file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)


class TemplateManager:
    """Manages templates and provides template operations."""
    
    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path.cwd() / "dmr" / "storage" / "data" / "templates"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._templates: Dict[str, Template] = {}
        self._create_default_templates()
    
    def _create_default_templates(self) -> None:
        """Create default templates if they don't exist."""
        default_templates = [
            {
                'name': 'Code Review',
                'description': 'Template for code review conversations',
                'category': 'development',
                'tags': ['code', 'review', 'development'],
                'messages': [
                    ('system', 'You are an expert code reviewer. Provide detailed, constructive feedback on code quality, best practices, and potential improvements.'),
                    ('user', 'Please review the following {language} code:\n\n```{language}\n{code}\n```\n\nFocus on: {focus_areas}')
                ],
                'variables': ['language', 'code', 'focus_areas']
            },
            {
                'name': 'Technical Documentation',
                'description': 'Template for generating technical documentation',
                'category': 'documentation',
                'tags': ['documentation', 'technical', 'writing'],
                'messages': [
                    ('system', 'You are a technical writer who creates clear, comprehensive documentation. Focus on clarity, accuracy, and usefulness for developers.'),
                    ('user', 'Create documentation for {project_name}:\n\nType: {doc_type}\nAudience: {audience}\nKey topics to cover: {topics}\n\nAdditional requirements: {requirements}')
                ],
                'variables': ['project_name', 'doc_type', 'audience', 'topics', 'requirements']
            },
            {
                'name': 'Problem Solving',
                'description': 'Template for structured problem-solving conversations',
                'category': 'analysis',
                'tags': ['problem-solving', 'analysis', 'debugging'],
                'messages': [
                    ('system', 'You are a systematic problem solver. Break down complex problems into manageable parts and provide step-by-step solutions.'),
                    ('user', 'I need help solving this problem:\n\nProblem: {problem_description}\n\nContext: {context}\nConstraints: {constraints}\nDesired outcome: {desired_outcome}')
                ],
                'variables': ['problem_description', 'context', 'constraints', 'desired_outcome']
            },
            {
                'name': 'Learning Assistant',
                'description': 'Template for educational conversations',
                'category': 'education',
                'tags': ['learning', 'education', 'teaching'],
                'messages': [
                    ('system', 'You are a patient and knowledgeable learning assistant. Explain concepts clearly, provide examples, and adapt your teaching style to the learner\'s level.'),
                    ('user', 'I want to learn about {topic}.\n\nMy current level: {skill_level}\nLearning goals: {goals}\nPreferred learning style: {learning_style}\nTime available: {time_commitment}')
                ],
                'variables': ['topic', 'skill_level', 'goals', 'learning_style', 'time_commitment']
            },
            {
                'name': 'API Design',
                'description': 'Template for API design discussions',
                'category': 'development',
                'tags': ['api', 'design', 'architecture', 'development'],
                'messages': [
                    ('system', 'You are an API design expert. Help design well-structured, RESTful APIs that follow best practices for security, performance, and maintainability.'),
                    ('user', 'I need to design an API for {project_name}.\n\nPurpose: {api_purpose}\nKey entities: {entities}\nMain operations: {operations}\nAuthentication requirements: {auth_requirements}\nPerformance considerations: {performance_notes}')
                ],
                'variables': ['project_name', 'api_purpose', 'entities', 'operations', 'auth_requirements', 'performance_notes']
            }
        ]
        
        for template_data in default_templates:
            template_file = self.storage_dir / f"{template_data['name'].lower().replace(' ', '_')}.json"
            if not template_file.exists():
                self._create_default_template(template_data, template_file)
    
    def _create_default_template(self, template_data: Dict[str, Any], file_path: Path) -> None:
        """Create a default template file."""
        metadata = TemplateMetadata(
            name=template_data['name'],
            description=template_data['description'],
            category=template_data['category'],
            tags=template_data['tags'],
            variables=template_data.get('variables', [])
        )
        
        template = Template(metadata=metadata)
        
        for role, content in template_data['messages']:
            template.add_message(role, content)
        
        template.save(file_path)
    
    def create_template(self, name: str, description: str, **metadata_kwargs) -> Template:
        """Create a new template."""
        metadata = TemplateMetadata(name=name, description=description, **metadata_kwargs)
        template = Template(metadata=metadata)
        self._templates[template.id] = template
        return template
    
    def get_template(self, template_id: str) -> Optional[Template]:
        """Get a template by ID."""
        if template_id in self._templates:
            return self._templates[template_id]
        
        # Try to load from disk
        for file_path in self.storage_dir.glob("*.json"):
            try:
                template = Template.load(file_path)
                if template.id == template_id:
                    self._templates[template.id] = template
                    return template
            except (json.JSONDecodeError, KeyError):
                continue
        
        return None
    
    def get_template_by_name(self, name: str) -> Optional[Template]:
        """Get a template by name."""
        for template in self.list_templates():
            if template['name'].lower() == name.lower():
                return self.get_template(template['id'])
        return None
    
    def save_template(self, template: Template) -> Path:
        """Save a template to disk."""
        file_name = f"{template.metadata.name.lower().replace(' ', '_')}_{template.id[:8]}.json"
        file_path = self.storage_dir / file_name
        template.save(file_path)
        return file_path
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List all available templates with metadata."""
        templates = []
        
        # Load templates from disk
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                templates.append({
                    'id': data['id'],
                    'name': data['metadata']['name'],
                    'description': data['metadata']['description'],
                    'category': data['metadata']['category'],
                    'tags': data['metadata'].get('tags', []),
                    'author': data['metadata'].get('author', 'Unknown'),
                    'created_at': data['metadata']['created_at'],
                    'variables': data['metadata'].get('variables', [])
                })
            except (json.JSONDecodeError, KeyError):
                continue
        
        # Sort by name
        templates.sort(key=lambda x: x['name'])
        return templates
    
    def list_templates_by_category(self, category: str) -> List[Dict[str, Any]]:
        """List templates filtered by category."""
        all_templates = self.list_templates()
        return [t for t in all_templates if t['category'].lower() == category.lower()]
    
    def search_templates(self, query: str) -> List[Dict[str, Any]]:
        """Search templates by name, description, or tags."""
        query = query.lower()
        results = []
        
        for template_info in self.list_templates():
            if (query in template_info['name'].lower() or 
                query in template_info['description'].lower() or
                any(query in tag.lower() for tag in template_info['tags'])):
                results.append(template_info)
        
        return results
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a template."""
        # Find and remove file
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if data['id'] == template_id:
                    file_path.unlink()
                    break
            except (json.JSONDecodeError, KeyError):
                continue
        
        # Remove from memory cache
        if template_id in self._templates:
            del self._templates[template_id]
        
        return True
    
    def instantiate_template(self, template_id: str, variables: Dict[str, str], 
                           title: Optional[str] = None) -> Conversation:
        """Instantiate a template with given variables."""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template with ID {template_id} not found")
        
        return template.instantiate(variables, title)
    
    def get_categories(self) -> List[str]:
        """Get all available template categories."""
        categories = set()
        for template_info in self.list_templates():
            categories.add(template_info['category'])
        return sorted(list(categories))