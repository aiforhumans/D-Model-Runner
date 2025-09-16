# D-Model-Runner Copilot Instructions

This project is a comprehensive Python client that interfaces with Docker Model Runner through an OpenAI-compatible API, featuring advanced configuration management and modular architecture.

## Project Architecture

**Core Purpose**: Sophisticated Python client for testing and interacting with local AI models via Docker Model Runner on localhost:12434, with enterprise-grade configuration management and extensible architecture.

**Key Components**:
- `main.py`: Interactive chat interface with conversation history, model selection, and configuration integration
- `dmr/`: Main package with modular architecture (✅ **PHASE 1 COMPLETE**)
- `dmr/config/`: Advanced configuration management system (YAML/JSON, profiles, environment variables)
- `dmr/utils/`: Shared utilities and helper functions
- `config/`: Global configuration files and profiles
- `test/test.py`: Parameter testing utility to validate Docker Model Runner capabilities
- `TODO/`: Implementation tracking and project management
- `ENHANCEMENT_IDEAS.md`: Comprehensive roadmap of potential feature enhancements

**Dependencies**: 
- OpenAI Python SDK for Docker Model Runner compatibility
- PyYAML for configuration file parsing
- Minimal additional dependencies: `requests`

**Architecture Features**:
- **Modular Design**: Clean separation of concerns with dedicated packages
- **Configuration Management**: Multi-source configuration with profile support (✅ **IMPLEMENTED**)
- **Environment Integration**: Environment variable overrides with DMR_ prefix
- **Profile System**: Development, production, and custom configuration profiles
- **Conversation Persistence**: Complete storage system with save/load functionality (✅ **IMPLEMENTED**)
- **Export System**: Multi-format export (JSON, Markdown, Text) with template support (✅ **IMPLEMENTED**)
- **Comprehensive Testing**: Unit, integration, performance, and error scenario testing (✅ **IMPLEMENTED**)
- **Implementation Tracking**: Comprehensive TODO system with phase-based development

## Implementation Status

**Current Phase**: ✅ **Phase 3 Complete** (November 2024)

**Phase 1 - Configuration Management** (COMPLETE):
- ✅ Enterprise-grade configuration system with YAML/JSON support
- ✅ Multi-source configuration loading (files, environment variables, profiles)
- ✅ Profile system: `default`, `dev`, `prod`, `custom`
- ✅ Environment variable integration with `DMR_` prefix
- ✅ Complete package restructuring with modular architecture
- ✅ Updated main application with configuration integration

**Phase 2 - Conversation Persistence** (COMPLETE):
- ✅ Conversation save/load system with JSON storage
- ✅ Template management for conversation workflows
- ✅ Export functionality (JSON, Markdown, Text formats)
- ✅ Auto-save and session management
- ✅ Comprehensive storage architecture with ConversationManager, TemplateManager, ExportManager

**Phase 3 - Integration & Testing** (COMPLETE):
- ✅ Comprehensive test suite: unit tests, integration tests, performance benchmarks
- ✅ Error scenario testing for robustness validation
- ✅ End-to-end workflow testing covering complete user scenarios
- ✅ Performance analysis: Config (0.35-1.3ms), Storage (0.02-1.4ms), Export (0.9-2.4ms)
- ✅ Enhanced Docker Model Runner compatibility with new architecture
- ✅ Complete system integration validation
- ✅ Complete package restructuring with modular architecture
- ✅ Updated main application with configuration integration
- ✅ Comprehensive documentation and implementation tracking

**Next Phase**: � **Phase 4 - Advanced Features** (Future Enhancements)
- 📋 Real-time streaming improvements and WebSocket support
- 📋 Advanced AI model integration and multi-model support
- 📋 Plugin system for extensible functionality
- 📋 Web UI for browser-based interaction
- 📋 Advanced analytics and conversation insights

**Implementation Tracking**:
- `TODO/implement_checklist.md`: Detailed phase-by-phase implementation checklist
- `TODO/phase3_complete.md`: Phase 3 completion summary and achievements
- All phases tracked with comprehensive testing and validation

## Local Development Setup

**Docker Model Runner Configuration**:
- Expects Docker Model Runner running on `http://localhost:12434/engines/llama.cpp/v1/`
- Alternative base URLs: `http://model-runner.docker.internal/` (from containers), Unix socket paths
- Default model: `ai/gemma3` (pulled from Docker Hub on first use)
- API key is placeholder ("anything") - Docker Model Runner runs without authentication
- Models are automatically pulled from Docker Hub and cached locally
- Models load into memory at runtime and unload when not in use for resource optimization

**How Docker Model Runner Works**:
Models are pulled from Docker Hub the first time you use them and are stored locally. They load into memory only at runtime when a request is made, and unload when not in use to optimize resources. Because models can be large, the initial pull may take some time. After that, they're cached locally for faster access.

Reference: https://docs.docker.com/ai/model-runner/get-started/

**Running the Client**:
```bash
python main.py      # Interactive chat with configuration management
python test/test.py # Test supported parameters
```

**Environment Setup**:
```bash
pip install -r requirements.txt  # Includes openai, requests, PyYAML
# Or use the existing .venv virtual environment
```

**Configuration System**:
- Multi-source configuration: files, environment variables, profiles
- Profile support: `default`, `dev`, `prod`, `custom`
- Environment variables with `DMR_` prefix
- YAML/JSON configuration files
- Automatic configuration discovery and merging

## Code Patterns

**Configuration-Driven Architecture**:
```python
from dmr.config import ConfigManager

# Initialize configuration manager
config_manager = ConfigManager()
config_manager.load_config(profile='dev')  # Load specific profile

# Get configuration values
base_url = config_manager.get_base_url()
model = config_manager.get_default_model()
model_config = config_manager.get_model_config(model)
```

**API Client Pattern**:
```python
from openai import OpenAI
from dmr.config import ConfigManager

# Configuration-driven client initialization
config_manager = ConfigManager()
config_manager.load_config()

client = OpenAI(
    base_url=config_manager.get_base_url(),
    api_key=config_manager.get_api_key()
)

# Model-specific configuration
model = config_manager.get_default_model()
model_config = config_manager.get_model_config(model)

response = client.chat.completions.create(
    model=model,
    messages=[...],
    max_tokens=model_config.get('max_tokens', 500),
    temperature=model_config.get('temperature', 0.7),
    stream=model_config.get('stream', True)
)
```

**Available OpenAI Endpoints** (Docker Model Runner supported):
```bash
# Model Management
GET /engines/llama.cpp/v1/models                    # List available models
GET /engines/llama.cpp/v1/models/{namespace}/{name} # Retrieve specific model info

# Text Generation
POST /engines/llama.cpp/v1/chat/completions         # Chat completions (primary endpoint)
POST /engines/llama.cpp/v1/completions              # Legacy completions

# Embeddings
POST /engines/llama.cpp/v1/embeddings               # Generate embeddings
```

**Configuration Management Examples**:
```python
# Environment variable overrides
DMR_BASE_URL=http://localhost:12434/engines/llama.cpp/v1/
DMR_DEFAULT_MODEL=ai/qwen3
DMR_MAX_TOKENS=300

# Profile-specific settings
config_manager.load_config('dev')    # Development profile
config_manager.load_config('prod')   # Production profile

# Custom configuration paths
custom_config = ConfigManager(config_dir='/path/to/configs')
```
**Core Parameters** (OpenAI-compatible, verified working):
```python
from dmr.config import ConfigManager

config_manager = ConfigManager()
model = config_manager.get_default_model()
model_config = config_manager.get_model_config(model)

response = client.chat.completions.create(
    model=model,                                     # From configuration: ai/gemma3, ai/qwen3
    messages=[...],                                  # Required - OpenAI chat format
    temperature=model_config.get('temperature', 0.7), # From model config or default
    top_p=model_config.get('top_p', 0.9),           # From model config or default
    max_tokens=model_config.get('max_tokens', 500), # From model config or default
    stop=["\n"],                                    # Stop sequences (small set)
    presence_penalty=0.1,                           # -2.0 to +2.0, penalize repeated topics
    frequency_penalty=0.1,                          # -2.0 to +2.0, penalize frequent tokens
    seed=42,                                        # For deterministic outputs
    stream=model_config.get('stream', True),        # SSE streaming from config
)
```

**Advanced Parameters** (support varies by model):
```python
from dmr.config import ConfigManager

config_manager = ConfigManager()
model = config_manager.get_default_model()

response = client.chat.completions.create(
    model=model,
    messages=[...],
    response_format={"type": "json_object"},  # Force JSON output
    logprobs=True,             # Token probabilities if implemented
    n=1,                      # Number of completions (>1 may not work)
    store=True,               # Save completion for later (OpenAI spec)
    metadata={"key": "value"}, # Tags when store=true
)
```

**Model-Specific Behaviors**:
- `ai/gemma3`: Standard chat responses, good for general conversation
- `ai/qwen3`: Reasoning model that shows `<think>` tokens for step-by-step thinking

**Verified Limitations** (Docker Model Runner/llama.cpp restrictions):
- `n > 1`: Only one completion choice allowed (returns 500 error)
- `tools`/`function_call`: Not supported (InternalServerError)
- Some advanced OpenAI features may not be implemented by llama.cpp backend

**Error Handling Pattern**:
- Always wrap API calls in try/except blocks
- Docker Model Runner may be unavailable or model not loaded
- Check streaming chunks for proper structure before accessing content
- Engine/model-dependent support for advanced parameters

## External Dependencies

**Docker Model Runner**: Requires a running Docker Model Runner instance on port 12434
**Model Loading**: Models (`ai/gemma3`, `ai/qwen3`) must be available on the local server
**llama.cpp Backend**: DMR uses llama.cpp under the hood, which affects parameter support

## Common Modifications

When adapting this code:
- Modify configuration files in `config/` or `dmr/config/profiles/` for different environments
- Use environment variables with `DMR_` prefix for deployment-specific settings
- Create custom profiles for different use cases
- Update `dmr/config/profiles/` for new model configurations
- Use `test/test.py` to validate parameter support when trying new models/features
- Extend the configuration system by modifying `dmr/config/manager.py`
- Reference implementation tracking in `TODO/` for planned features and roadmap
- Follow phase-based development approach outlined in `TODO/implement_checklist.md`
- Reference OpenAI's Chat Completions docs for parameter semantics: https://platform.openai.com

## Testing Approach

**Manual Testing**: 
- Run `python main.py` for interactive chat with configuration management
- Run `python test/test.py` for comprehensive parameter validation and model comparison

**Configuration Testing**:
```python
from dmr.config import ConfigManager

# Test different profiles
config_manager = ConfigManager()
config_manager.load_config('dev')
print("Dev config:", config_manager.get('api.models.defaults.max_tokens'))

config_manager.load_config('prod')
print("Prod config:", config_manager.get('api.models.defaults.max_tokens'))
```

**Parameter Testing**: Use `test/test.py` to discover which OpenAI parameters work with your specific Docker Model Runner setup. The test validates supported parameters and provides a summary of capabilities.

**Common Test Commands**:
```bash
python test/test.py               # Full parameter compatibility test
python main.py                    # Interactive chat interface
```

**Verified Test Results**:
- ✅ **Core Support**: temperature, top_p, max_tokens, stop, presence_penalty, frequency_penalty, seed, streaming
- ✅ **Advanced Support**: logprobs, response_format (JSON), store, metadata
- ✅ **Models Available**: ai/gemma3, ai/qwen3
- ❌ **Not Supported**: n>1 (multiple completions), tools/function calling
- 📝 **Notes**: qwen3 shows reasoning tokens (`<think>`), parameter support varies by model/engine

**Parameter Reference**: Follow OpenAI's Chat Completions specification for full parameter details - DMR intentionally follows that interface with llama.cpp backend limitations.

## Project Status & Implementation Tracking

**Phase 3 Complete** (September 16, 2025):
- ✅ All integration and testing objectives achieved
- ✅ Comprehensive test suite with unit, integration, performance, and error scenario tests
- ✅ End-to-end workflow validation covering complete user scenarios
- ✅ Performance benchmarking with optimization recommendations
- ✅ Enhanced Docker Model Runner compatibility with new architecture
- ✅ Complete system integration and validation
- ✅ Documentation and tracking systems updated

**Phase 1-3 Complete**:
- ✅ Configuration Management (Phase 1): Enterprise-grade config system with profiles
- ✅ Conversation Persistence (Phase 2): Complete storage system with templates and export
- ✅ Integration & Testing (Phase 3): Comprehensive testing and performance validation

**Ready for Phase 4**:
- � Advanced features: streaming improvements, multi-model support, plugin system
- 🚀 Web UI for browser-based interaction
- 🚀 Advanced analytics and conversation insights

**Implementation Resources**:
- `TODO/implement_checklist.md`: Comprehensive roadmap with detailed task tracking
- `TODO/phase3_complete.md`: Phase 3 completion summary and achievements
- `ENHANCEMENT_IDEAS.md`: Long-term feature roadmap and enhancement ideas

**Development Approach**:
- Phase-based implementation with clear milestones
- Comprehensive task tracking with time estimates
- Thorough testing and validation at each phase
- Modular architecture supporting iterative enhancement