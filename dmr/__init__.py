"""
D-Model-Runner: Python client for Docker Model Runner with OpenAI-compatible API

This package provides configuration management, conversation persistence,
and utilities for interacting with local AI models via Docker Model Runner.
"""

__version__ = "0.2.0"
__author__ = "D-Model-Runner Project"

from .config import ConfigManager
from .utils.helpers import validate_model_name, format_error_message
from .storage import (
    Conversation, ConversationManager,
    Template, TemplateManager,
    ExportManager
)

__all__ = [
    "ConfigManager",
    "validate_model_name", 
    "format_error_message",
    "Conversation",
    "ConversationManager",
    "Template", 
    "TemplateManager",
    "ExportManager"
]