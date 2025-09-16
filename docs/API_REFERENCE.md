# D-Model-Runner API Reference

This document provides a comprehensive reference for all public classes and functions in the D-Model-Runner package.

## Core Package (`dmr`)

### Configuration Management (`dmr.config`)

#### `ConfigManager`

**Location**: `dmr/config/manager.py`

Central configuration orchestrator that handles loading, merging, and managing configuration from multiple sources with intelligent caching.

**Key Methods**:

```python
def load_config(profile: str = "default", reload: bool = False) -> Dict[str, Any]
    """Load configuration from files and environment variables with caching."""

def get(path: str, default: Any = None) -> Any
    """Get a configuration value using dot notation."""

def get_base_url() -> str
    """Get the API base URL."""

def get_default_model() -> str
    """Get the default model name."""

def get_model_config(model: str) -> Dict[str, Any]
    """Get configuration for a specific model."""
```

#### `ConfigParser`

**Location**: `dmr/config/parser.py`

Parse configuration files in YAML and JSON formats.

**Key Methods**:

```python
@classmethod
def load_config_file(cls, file_path: Union[str, Path]) -> Dict[str, Any]
    """Load and parse a configuration file."""

@classmethod
def validate_config_structure(cls, config: Dict[str, Any]) -> bool
    """Validate configuration structure against schema."""
```

#### `EnvironmentHandler`

**Location**: `dmr/config/env.py`

Handle environment variable overrides for configuration.

### Storage System (`dmr.storage`)

#### `Conversation`

**Location**: `dmr/storage/conversation.py`

Represents a single conversation with messages and metadata.

**Key Methods**:

```python
def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None
    """Add a message to the conversation."""

def get_messages(self) -> List[Message]
    """Get all messages in the conversation."""

def to_dict(self) -> Dict[str, Any]
    """Convert conversation to dictionary format."""

@classmethod
def from_dict(cls, data: Dict[str, Any]) -> 'Conversation'
    """Create conversation from dictionary data."""
```

#### `ConversationManager`

**Location**: `dmr/storage/conversation.py`

Manages conversation persistence, loading, and operations.

**Key Methods**:

```python
def create_conversation(self, title: str, model: str) -> Conversation
    """Create a new conversation."""

def save_conversation(self, conversation: Conversation) -> None
    """Save a conversation to storage."""

def load_conversation(self, conversation_id: str) -> Optional[Conversation]
    """Load a conversation by ID."""

def list_conversations(self) -> List[Dict[str, Any]]
    """List all available conversations."""

def search_conversations(self, query: str) -> List[Dict[str, Any]]
    """Search conversations by title or content."""

def delete_conversation(self, conversation_id: str) -> bool
    """Delete a conversation."""
```

#### `Message`

**Location**: `dmr/storage/conversation.py`

Represents a single message within a conversation.

**Properties**:

```python
role: str                    # 'user', 'assistant', or 'system'
content: str                 # Message content
timestamp: datetime          # When message was created
metadata: Dict[str, Any]     # Additional message metadata
```

#### `Template`

**Location**: `dmr/storage/templates.py`

Represents a conversation template with variable substitution.

**Key Methods**:

```python
def substitute_variables(self, variables: Dict[str, str]) -> List[Message]
    """Substitute template variables and return messages."""

def to_dict(self) -> Dict[str, Any]
    """Convert template to dictionary format."""

@classmethod
def from_dict(cls, data: Dict[str, Any]) -> 'Template'
    """Create template from dictionary data."""
```

#### `TemplateManager`

**Location**: `dmr/storage/templates.py`

Manages templates and provides template operations.

**Key Methods**:

```python
def create_template(self, name: str, description: str, messages: List[Tuple[str, str]], 
                   variables: List[str], **kwargs) -> Template
    """Create a new template."""

def get_template(self, template_id: str) -> Optional[Template]
    """Get a template by ID."""

def list_templates(self) -> List[Dict[str, Any]]
    """List all available templates."""

def create_from_template(self, template_id: str, variables: Dict[str, str]) -> Conversation
    """Create a conversation from a template."""

def search_templates(self, query: str) -> List[Dict[str, Any]]
    """Search templates by name, description, or tags."""
```

### Export System (`dmr.storage.exporters`)

#### `ExportManager`

**Location**: `dmr/storage/exporters.py`

Manages conversation export to multiple formats.

**Key Methods**:

```python
def export_conversation(self, conversation: Conversation, format_name: str, 
                       output_path: Optional[str] = None, **options) -> Path
    """Export a conversation to specified format."""

def get_available_formats() -> List[str]
    """Get list of available export formats."""

def export_multiple_conversations(self, conversations: List[Conversation], 
                                 format_name: str, output_dir: str, **options) -> List[Path]
    """Export multiple conversations to specified format."""
```

#### Export Formats

##### `JSONExporter`

**Location**: `dmr/storage/formats/json_exporter.py`

Export conversations to JSON format with configurable indentation.

##### `MarkdownExporter`

**Location**: `dmr/storage/formats/markdown_exporter.py`

Export conversations to Markdown format with syntax highlighting.

##### `PDFExporter`

**Location**: `dmr/storage/formats/pdf_exporter.py`

Export conversations to PDF format with advanced formatting, code syntax highlighting, and professional styling.

### Utilities (`dmr.utils`)

#### Helper Functions

**Location**: `dmr/utils/helpers.py`

```python
def validate_model_name(model: str) -> bool
    """Validate if a model name follows expected format."""

def format_error_message(error: Exception, context: Optional[str] = None) -> str
    """Format an error message with context for user display."""

def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]
    """Merge two configuration dictionaries recursively."""

def safe_get_nested(data: Dict[str, Any], path: str, default: Any = None) -> Any
    """Safely get a nested value from a dictionary using dot notation."""
```

#### Performance Monitoring

**Location**: `dmr/utils/performance.py`

##### `PerformanceMetrics`

Track performance metrics for operations.

```python
def start_operation(self, operation: str) -> str
    """Start tracking an operation."""

def end_operation(self, operation_id: str) -> Dict[str, Any]
    """End tracking and return metrics."""
```

##### Performance Decorators

```python
@measure_performance(operation: str, include_args: bool = False)
    """Decorator to measure function performance."""

@track_cache_performance(cache_name: str)
    """Decorator to track cache performance."""
```

##### `PerformanceReport`

Generate comprehensive performance reports.

```python
def generate_report(self) -> Dict[str, Any]
    """Generate a comprehensive performance report."""

def export_report(self, format: str = 'json', output_path: Optional[str] = None) -> Path
    """Export performance report to file."""
```

## Web UI (`UI`)

### Flask Application

**Location**: `UI/app.py`

Main Flask web server providing browser-based chat interface.

**Key Endpoints**:

```python
GET  /                    # Main chat interface
POST /api/chat           # Send chat message
GET  /api/models         # Get available models
GET  /api/health         # Server health check
POST /api/chat/stream    # Streaming chat endpoint
GET  /api/templates/<id> # Get template by ID
```

**Key Functions**:

```python
def initialize_client() -> bool
    """Initialize OpenAI client with current configuration."""

def get_available_models() -> List[str]
    """Get list of available models from server."""
```

## Main Entry Points

### Interactive CLI (`main.py`)

Main interactive chat application with conversation persistence.

**Key Functions**:

```python
def main()
    """Main function with model and profile selection."""

def initialize_client() -> OpenAI
    """Initialize OpenAI client with configuration and production-ready settings."""

def check_model_server_health() -> Tuple[bool, List[str]]
    """Check if Docker Model Runner is accessible and return available models."""

def validate_model_availability(model_name: str) -> str
    """Validate if a model is available on the server."""

def handle_export_conversation(conversation: Conversation, format_name: str)
    """Handle exporting a conversation."""

@exponential_backoff_retry(max_retries=3, base_delay=1.0, max_delay=60.0, backoff_factor=2.0)
    """Decorator for exponential backoff retry logic."""
```

### Compatibility Testing (`test/test.py`)

Docker Model Runner parameter validation and compatibility testing.

**Key Functions**:

```python
def test_configuration_system() -> ConfigManager
    """Test the configuration system integration."""

def test_basic_parameters(client: OpenAI, successful_models: List[str])
    """Test basic chat completion parameters."""

def test_advanced_parameters(client: OpenAI, successful_models: List[str])
    """Test advanced parameters."""

def test_streaming_responses(client: OpenAI, successful_models: List[str])
    """Test streaming response handling."""

def test_error_scenarios(client: OpenAI)
    """Test various error scenarios."""

def print_test_summary(successful_models: List[str])
    """Print comprehensive test summary."""
```

### Performance Benchmarking (`tests/performance/benchmark.py`)

Comprehensive performance testing for all system components.

**Key Classes**:

```python
class PerformanceBenchmark
    """Base class for performance benchmarks."""

class ConfigBenchmarks
    """Benchmarks for configuration system."""

class StorageBenchmarks  
    """Benchmarks for storage system."""

class ExportBenchmarks
    """Benchmarks for export system."""
```

**Key Functions**:

```python
def run_comprehensive_benchmarks()
    """Run all performance benchmarks."""

def generate_benchmark_report(results: List[Dict[str, Any]])
    """Generate a comprehensive benchmark report."""
```

## Usage Examples

### Basic Configuration and Chat

```python
from dmr.config import ConfigManager
from dmr.storage import ConversationManager

# Initialize
config_manager = ConfigManager()
config_manager.load_config('dev')
conversation_manager = ConversationManager()

# Create conversation
conversation = conversation_manager.create_conversation("My Chat", "ai/gemma3")
conversation.add_message("user", "Hello!")
conversation.add_message("assistant", "Hi there!")

# Save conversation
conversation_manager.save_conversation(conversation)
```

### Template Usage

```python
from dmr.storage import TemplateManager

template_manager = TemplateManager()

# Use existing template
template = template_manager.get_template("api_design")
conversation = template_manager.create_from_template(
    template.id, 
    {"project_name": "UserAPI", "api_purpose": "User management"}
)
```

### Export Conversations

```python
from dmr.storage import ExportManager

export_manager = ExportManager()

# Export to different formats
pdf_path = export_manager.export_conversation(conversation, "pdf")
md_path = export_manager.export_conversation(conversation, "markdown")
json_path = export_manager.export_conversation(conversation, "json")
```

### Performance Monitoring

```python
from dmr.utils.performance import measure_performance

@measure_performance("my_operation")
def my_function():
    # Your code here
    pass
```

## Error Handling

All functions use consistent error handling patterns:

```python
from dmr.utils.helpers import format_error_message

try:
    # Operation
    result = some_operation()
except Exception as e:
    error_msg = format_error_message(e, "operation_name")
    print(f"Error: {error_msg}")
```

## Configuration Patterns

### Loading Profiles

```python
config_manager = ConfigManager()
config_manager.load_config('dev')     # Development profile
config_manager.load_config('prod')    # Production profile
config_manager.load_config('custom')  # Custom profile
```

### Environment Overrides

Set environment variables with `DMR_` prefix:

- `DMR_BASE_URL`
- `DMR_DEFAULT_MODEL`
- `DMR_MAX_TOKENS`

### Model Configuration

```python
model_config = config_manager.get_model_config("ai/gemma3")
# Returns model-specific parameters like temperature, max_tokens, etc.
```

## Performance Characteristics

- **Configuration loading**: Sub-millisecond (cached after first load)
- **Conversation operations**: <2ms typical
- **Template substitution**: <1ms for simple templates
- **Export operations**: Varies by format and size
  - JSON: <10ms for typical conversations
  - Markdown: <20ms for typical conversations  
  - PDF: <100ms for typical conversations (depends on complexity)
- **Search operations**: ~21ms for <100 conversations

## Testing Infrastructure

The project includes comprehensive testing:

- **Unit Tests**: `tests/unit/` - Component isolation testing
- **Integration Tests**: `tests/integration/` - Cross-component validation
- **Performance Tests**: `tests/performance/` - Benchmarking and optimization validation
- **UI Tests**: `UI/tests/` - Playwright browser automation
- **Error Scenario Tests**: 25+ error scenarios validated

Run tests with:

```bash
python -m pytest tests/ -v                    # All tests
python tests/performance/benchmark.py         # Performance benchmarks
python test/test.py                           # Docker Model Runner compatibility
python UI/tests/test_ui.py                    # UI tests
```
