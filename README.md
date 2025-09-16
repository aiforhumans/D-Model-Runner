# D-Model-Runner

A comprehensive Python client for testing and interacting with local AI models via Docker Model Runner on localhost:12434, now featuring advanced configuration management and modular architecture.

## Overview

This project provides a sophisticated interface to Docker Model Runner, allowing you to easily test and interact with locally-hosted AI models through an OpenAI-compatible API. With the new modular design, you can customize configurations, switch between profiles, and extend functionality seamlessly.

## Features

- **🔧 Advanced Configuration Management**: YAML/JSON configs with profile support and environment variables
- **📦 Modular Architecture**: Clean package structure with separated concerns
- **💾 Conversation Persistence**: Complete save/load system with JSON storage and templates
- **📤 Multi-Format Export**: JSON, Markdown, and PDF export with advanced formatting
- **🌐 Modern Web UI**: Browser-based chat interface with real-time messaging
- **🤖 Multi-Model Support**: Works with `ai/gemma3` and `ai/qwen3` models
- **🧪 Comprehensive Testing**: Unit, integration, performance, and UI testing
- **⚡ Streaming Support**: Real-time response streaming with configurable parameters
- **🛠️ Error Handling**: Robust error handling with detailed messaging and recovery
- **🎯 Profile Management**: Development, production, and custom configuration profiles
- **🔍 Performance Optimized**: Sub-millisecond config access, efficient storage operations
- **📖 Complete Documentation**: Comprehensive API reference and file index

## Implementation Status

✅ **Phase 4 Complete** - Web UI and comprehensive documentation implemented

- **Phase 1**: ✅ Enterprise-grade configuration management with profiles
- **Phase 2**: ✅ Complete conversation persistence with templates and export
- **Phase 3**: ✅ Comprehensive testing, integration validation, and performance optimization
- **Phase 4**: ✅ Web UI implementation and project cleanup/documentation

**Current Capabilities**:

- Full configuration management with environment override support
- Complete conversation save/load with auto-save functionality
- Template-based conversation workflows for common use cases
- Multi-format export (JSON, Markdown, PDF) with batch processing
- Modern web UI with real-time chat interface
- Comprehensive test suite with performance benchmarking
- Complete documentation and API reference
- Enhanced Docker Model Runner compatibility and parameter validation

## Quick Start

### Prerequisites

- Docker Model Runner running on `http://localhost:12434`
- Python 3.7+
- Required models: `ai/gemma3`, `ai/qwen3`

### Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd D-Model-Runner
   ```

2. Create and activate virtual environment:

   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### Quick Start with Defaults

The application works out of the box with sensible defaults. Simply run:

```bash
python main.py
```

### Configuration Profiles

D-Model-Runner supports multiple configuration profiles for different environments:

- **`default`**: Standard settings for general use
- **`dev`**: Development profile with debug logging and modified parameters  
- **`prod`**: Production profile with optimized settings
- **`custom`**: Template for creating your own profiles

#### Using Profiles

```bash
# The application will prompt you to select a profile on startup
python main.py

# Or use environment variables
DMR_PROFILE=dev python main.py
```

### Configuration Files

Configuration is loaded from multiple sources in order of precedence:

1. **Environment Variables** (highest priority)
2. **Profile-specific files** (`dmr/config/profiles/*.yaml`)
3. **Default configuration** (`config/default.yaml`)
4. **Built-in defaults** (lowest priority)

#### Environment Variables

Set environment variables with the `DMR_` prefix:

```bash
# API Configuration
export DMR_BASE_URL="http://localhost:12434/engines/llama.cpp/v1/"
export DMR_DEFAULT_MODEL="ai/qwen3"
export DMR_MAX_TOKENS=300
export DMR_TEMPERATURE=0.8

# Logging
export DMR_DEBUG=true
export DMR_LOG_LEVEL=DEBUG
```

#### Custom Configuration

Create your own configuration file:

```yaml
# config/my-config.yaml
api:
  models:
    default: "ai/qwen3"
    defaults:
      max_tokens: 300
      temperature: 0.8
      
logging:
  level: "DEBUG"
  debug: true
```

Load your custom configuration:

```python
from dmr.config import ConfigManager

# Load specific profile
config = ConfigManager()
config.load_config(profile='dev')  # or 'prod', 'custom'

# Load custom config file
config.load_config(config_path='config/my-config.yaml')

# Access configuration values
base_url = config.get_base_url()
model = config.get_default_model()
model_settings = config.get_model_config(model)
```

### Basic Usage

Run the interactive chat interface:

```bash
python main.py
```

This will start an interactive chat session where you can:

- Choose between different AI models (`ai/gemma3`, `ai/qwen3`)
- Select system prompts (helpful assistant, pirate mode, or custom)
- Have conversations with full context preservation
- Use special commands: `quit`, `clear`, `model <name>`

### Chat Features

The interactive chat interface includes:

- **Conversation History**: All messages are preserved for context
- **Model Switching**: Change models mid-conversation with `model <name>`
- **Configuration Display**: View current settings with `config` command
- **System Prompts**: Choose from presets or create custom ones
- **Streaming Responses**: Real-time response generation with configurable parameters
- **Special Commands**:
  - `quit`, `exit`, `bye`: End the conversation
  - `clear`: Reset conversation history
  - `model <name>`: Switch between available models
  - `config`: Display current configuration settings

### Testing Parameters

Run comprehensive parameter testing:

```bash
python test/test.py
```

This will test various OpenAI-compatible parameters and show what's supported by your Docker Model Runner setup.

## Docker Model Runner Setup

The client expects Docker Model Runner to be running on:

- **Primary URL**: `http://localhost:12434/engines/llama.cpp/v1/`
- **Container URL**: `http://model-runner.docker.internal/` (from within containers)
- **Unix Socket**: Custom Unix socket paths

Models are automatically configured through the configuration system. See the Configuration section above for details.

## Storage & Templates

### Conversation Management

The client includes a comprehensive conversation storage system with templates:

```python
from dmr.storage import ConversationManager, TemplateManager, ExportManager

# Initialize managers
conv_mgr = ConversationManager()
template_mgr = TemplateManager()
export_mgr = ExportManager()

# Save conversations with metadata
conversation_data = {
    "messages": [{"role": "user", "content": "Hello"}],
    "model": "ai/gemma3",
    "timestamp": "2024-11-15T10:30:00Z"
}
conv_id = conv_mgr.save_conversation(conversation_data, metadata={"topic": "greeting"})

# Load conversations
conversation = conv_mgr.load_conversation(conv_id)

# Export in multiple formats
export_mgr.export_conversation(conversation, 'output.json', 'json')
export_mgr.export_conversation(conversation, 'output.md', 'markdown')
export_mgr.export_conversation(conversation, 'output.txt', 'text')
```

### Template Workflows

Create and use conversation templates for common scenarios:

```python
# Create a template
template = {
    "name": "code_review",
    "description": "Template for code review sessions",
    "initial_prompt": "Please review the following code for best practices and potential improvements:",
    "model_config": {
        "temperature": 0.3,
        "max_tokens": 1000
    }
}
template_mgr.save_template("code_review", template)

# Use template in conversation
template = template_mgr.load_template("code_review")
# Apply template settings to your chat session
```

## API Usage Examples

### Basic Chat Completion

```python
from openai import OpenAI
from dmr.config import ConfigManager

# Initialize configuration
config_manager = ConfigManager()
config_manager.load_config()

# Create client with configuration
client = OpenAI(
    base_url=config_manager.get_base_url(),
    api_key=config_manager.get_api_key()
)

# Get model configuration
model = config_manager.get_default_model()
model_config = config_manager.get_model_config(model)

response = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello! How are you?"}
    ],
    max_tokens=model_config.get('max_tokens', 500),
    temperature=model_config.get('temperature', 0.7)
)

print(response.choices[0].message.content)
```

### Using Configuration Profiles

```python
from dmr.config import ConfigManager

# Load development profile
config_manager = ConfigManager()
config_manager.load_config(profile='dev')

# Check if debug mode is enabled
if config_manager.get('logging.debug'):
    print("Debug mode enabled")

# Get profile-specific model settings
max_tokens = config_manager.get('api.models.defaults.max_tokens')
print(f"Max tokens: {max_tokens}")
```

### Streaming Response

```python
from dmr.config import ConfigManager
from openai import OpenAI

config_manager = ConfigManager()
config_manager.load_config()

client = OpenAI(
    base_url=config_manager.get_base_url(),
    api_key=config_manager.get_api_key()
)

model = config_manager.get_default_model()
model_config = config_manager.get_model_config(model)

response = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=model_config.get('stream', True),
    max_tokens=model_config.get('max_tokens', 200)
)

for chunk in response:
    if chunk.choices and len(chunk.choices) > 0:
        delta = chunk.choices[0].delta
        if hasattr(delta, 'content') and delta.content:
            print(delta.content, end="", flush=True)
```

### JSON Response Format

```python
response = client.chat.completions.create(
    model="ai/gemma3",
    messages=[{"role": "user", "content": "Return a JSON object with name and age"}],
    response_format={"type": "json_object"},
    max_tokens=50
)

print(response.choices[0].message.content)  # Will be valid JSON
```

## Supported Parameters

### Core Parameters (Always Supported)

- `model`: Model identifier
- `messages`: Chat conversation history
- `max_tokens`: Maximum response length
- `temperature`: Response randomness (0.0-2.0)
- `top_p`: Nucleus sampling (0-1)
- `stop`: Stop sequences
- `presence_penalty`: Penalize repeated topics (-2.0 to +2.0)
- `frequency_penalty`: Penalize repeated tokens (-2.0 to +2.0)
- `seed`: Deterministic outputs
- `stream`: Enable streaming responses

### Advanced Parameters (Support Varies)

- `response_format`: Force JSON output
- `logprobs`: Token probability information
- `store`: Save completion for later
- `metadata`: Tags for stored completions

## Known Limitations

- `n > 1`: Multiple completions not supported (returns 500 error)
- `tools`/`function_call`: Function calling not supported
- Some advanced OpenAI features may not be implemented by the llama.cpp backend

## Available Endpoints

Docker Model Runner supports these OpenAI-compatible endpoints:

```bash
# Model Management
GET /engines/llama.cpp/v1/models                    # List available models
GET /engines/llama.cpp/v1/models/{namespace}/{name} # Retrieve specific model info

# Text Generation
POST /engines/llama.cpp/v1/chat/completions         # Chat completions (primary)
POST /engines/llama.cpp/v1/completions              # Legacy completions

# Embeddings
POST /engines/llama.cpp/v1/embeddings               # Generate embeddings
```

## Project Structure

```bash
D-Model-Runner/
├── dmr/                        # Main package directory (2,200 LOC)
│   ├── __init__.py            # Package exports
│   ├── config/                # Configuration management
│   │   ├── __init__.py
│   │   ├── manager.py         # Main configuration manager
│   │   ├── parser.py          # YAML/JSON parser
│   │   ├── env.py             # Environment variable handler
│   │   └── profiles/          # Configuration profiles
│   │       ├── dev.yaml       # Development profile
│   │       ├── prod.yaml      # Production profile
│   │       └── custom.yaml    # Custom profile template
│   ├── storage/               # Conversation persistence system
│   │   ├── __init__.py
│   │   ├── conversation.py    # Core conversation management
│   │   ├── templates.py       # Template system
│   │   ├── exporters.py       # Export coordination
│   │   ├── index_cache.py     # Search optimization
│   │   ├── formats/           # Export format implementations
│   │   │   ├── json_exporter.py
│   │   │   ├── markdown_exporter.py
│   │   │   └── pdf_exporter.py
│   │   └── data/              # Storage directory
│   │       ├── conversations/ # Saved conversations
│   │       └── templates/     # Template definitions
│   └── utils/                 # Shared utilities
│       ├── __init__.py
│       ├── helpers.py         # Utility functions
│       └── performance.py     # Performance monitoring
├── UI/                        # Web interface (800 LOC)
│   ├── app.py                 # Flask web server
│   ├── templates/
│   │   └── chat.html          # Chat interface
│   ├── static/
│   │   ├── css/style.css      # Responsive styling
│   │   └── js/chat.js         # Chat functionality
│   ├── tests/
│   │   └── test_ui.py         # UI tests
│   └── requirements.txt       # UI dependencies
├── config/                    # Global configuration
│   ├── default.yaml           # Application defaults
│   └── .env.example           # Environment template
├── docs/                      # 📖 Documentation
│   ├── FILE_INDEX.md          # Comprehensive file index
│   └── API_REFERENCE.md       # Complete API reference
├── tests/                     # Test suite (2,900 LOC)
│   ├── unit/                  # Unit tests
│   │   ├── test_config.py     # Configuration tests
│   │   ├── test_storage.py    # Storage tests
│   │   └── test_error_scenarios.py # Error handling
│   ├── integration/           # Integration tests
│   │   ├── test_integration.py
│   │   └── test_workflows.py
│   └── performance/           # Performance benchmarks
│       └── benchmark.py       # Comprehensive benchmarking
├── TODO/                      # Implementation tracking
│   └── implement_checklist.md # Phase completion status
├── main.py                    # 🚀 Main CLI application
├── test/
│   └── test.py               # Docker Model Runner compatibility
├── requirements.txt           # Core dependencies
├── .gitignore                # Git ignore rules
├── README.md                 # This documentation
├── ENHANCEMENT_IDEAS.md      # Feature roadmap
└── .github/
    └── copilot-instructions.md # Development guidelines
```

## Documentation

- **📋 [FILE_INDEX.md](docs/FILE_INDEX.md)** - Comprehensive index of all files, classes, and functions
- **📚 [API_REFERENCE.md](docs/API_REFERENCE.md)** - Complete API documentation with examples
- **🔧 [Copilot Instructions](.github/copilot-instructions.md)** - Development patterns and architecture guidelines

## Development

### Running Tests

```bash
python test/test.py
```

### Adding New Models

1. Update the `models_to_test` list in `test/test.py`
2. Add model-specific documentation in the README
3. Test parameter compatibility with the new model

### Error Handling

Always wrap API calls in try/except blocks:

```python
try:
    response = client.chat.completions.create(...)
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Error: {e}")
```

## Testing

### Comprehensive Test Suite

Run the complete test suite to validate all functionality:

```bash
# Run all unit tests
python -m pytest tests/unit/ -v

# Run integration tests
python -m pytest tests/integration/ -v

# Run performance benchmarks
python tests/performance/benchmark.py

# Run error scenario tests
python tests/unit/test_error_scenarios.py

# Run end-to-end workflow tests
python tests/integration/test_workflows.py
```

### Parameter Compatibility Testing

Test Docker Model Runner compatibility and supported parameters:

```bash
python test/test.py
```

This will validate:

- Available models and their capabilities
- Supported OpenAI parameters
- Performance characteristics
- Error handling behavior

### Performance Benchmarking

The performance benchmark suite provides comprehensive metrics:

```bash
python tests/performance/benchmark.py
```

**Expected Performance (typical results)**:

- Configuration loading: 0.35-1.3ms
- Conversation save: 0.5-1.4ms
- Conversation load: 0.02ms
- Export operations: 0.9-2.4ms
- Search operations: ~21ms (100 conversations)

## Troubleshooting

### Common Issues

1. **Connection Error**: Ensure Docker Model Runner is running on port 12434
2. **Model Not Found**: Verify the model is pulled and available
3. **Parameter Error**: Check parameter values against OpenAI documentation
4. **Streaming Issues**: Ensure proper chunk handling for streaming responses

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python test/test.py`
5. Submit a pull request

## License

[Add your license information here]

## References

- [Docker Model Runner Documentation](https://docs.docker.com/ai/model-runner/get-started/)
