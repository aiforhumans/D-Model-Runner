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

## Comprehensive Codebase Analysis

### Project Statistics (September 2025)

**Codebase Metrics**:
- **Total Python Files**: 24 files (excluding virtual environment)
- **Total Lines of Code**: ~6,046 lines of Python code
- **Version**: 0.2.0
- **Architecture Status**: Production-ready, enterprise-grade

### Package Structure Breakdown

#### **Main Application Layer**
```python
main.py (425 lines)
└── Interactive chat interface with conversation persistence
    ├── Model selection and configuration integration
    ├── Conversation management (save/load/template workflows)
    ├── Multi-format export capabilities
    └── Enhanced error handling and user experience
```

#### **DMR Package (`dmr/`) - 2,197 lines**

**Configuration Management (`dmr/config/`) - 580 lines**:
```python
manager.py (281 lines)     # ConfigManager - central orchestrator
parser.py (152 lines)      # YAML/JSON parsing and validation  
env.py (147 lines)         # Environment variable processing
```

**Storage System (`dmr/storage/`) - 1,536 lines**:
```python
conversation.py (263 lines)    # Conversation and ConversationManager
templates.py (370 lines)       # Template and TemplateManager  
exporters.py (205 lines)       # ExportManager with format dispatch
└── formats/
    ├── json_exporter.py (258 lines)      # JSON export implementation
    ├── markdown_exporter.py (314 lines)  # Markdown with syntax highlighting
    └── pdf_exporter.py (499 lines)       # PDF with advanced formatting
```

**Utilities (`dmr/utils/`) - 78 lines**:
```python
helpers.py (78 lines)      # Shared utilities and validation functions
```

#### **Test Infrastructure (`tests/`) - 2,904 lines**

**Unit Tests (`tests/unit/`) - 1,367 lines**:
```python
test_config.py (294 lines)        # Configuration system comprehensive tests
test_storage.py (504 lines)       # Storage system end-to-end validation
test_error_scenarios.py (569 lines) # Error handling and recovery testing
```

**Integration Tests (`tests/integration/`) - 996 lines**:
```python
test_integration.py (461 lines)   # Cross-component integration validation
test_workflows.py (535 lines)     # End-to-end user workflow testing
```

**Performance Benchmarks (`tests/performance/`) - 541 lines**:
```python
benchmark.py (541 lines)          # Comprehensive performance analysis
```

#### **Parameter Testing (`test/`) - 465 lines**
```python
test.py (465 lines)               # Docker Model Runner compatibility testing
```

### Architecture Design Patterns

1. **🎯 Modular Package Architecture**
   - Clean separation of concerns with dedicated packages
   - Well-defined public APIs with `__init__.py` exports
   - Pluggable components with clear interfaces

2. **⚙️ Configuration-Driven Design**
   - Multi-source configuration (YAML/JSON, environment variables, profiles)
   - Profile system with inheritance: `default`, `dev`, `prod`, `custom`
   - Environment variable overrides with `DMR_` prefix

3. **💾 Domain-Driven Storage System**
   - Conversation persistence with auto-save functionality
   - Template workflows with variable substitution
   - Multi-format export with pluggable exporters

4. **🏗️ Enterprise Architecture Patterns**
   - **Repository Pattern**: Conversation and template storage
   - **Factory Pattern**: Export format creation
   - **Strategy Pattern**: Export format implementations
   - **Template Method**: Base exporter with format-specific implementations
   - **Dependency Injection**: Configuration-driven components

### Performance Metrics (Phase 3 Validated)

**Benchmarked Performance**:
| Operation | Performance | Status |
|-----------|-------------|---------|
| Configuration Loading | 0.35-1.3ms | ✅ Excellent |
| Conversation Save | 0.5-1.4ms | ✅ Very Good |
| Conversation Load | 0.02ms | ✅ Outstanding |
| Export Operations | 0.9-2.4ms | ✅ Good |
| Search (100 conversations) | ~21ms | ⚠️ Optimization opportunity |

### Testing Coverage & Quality

**Test Infrastructure Quality**:
- ✅ **Unit Tests**: 100% coverage of public APIs
- ✅ **Integration Tests**: Cross-component validation
- ✅ **Performance Tests**: Comprehensive benchmarking with optimization recommendations
- ✅ **Error Scenarios**: 25+ error conditions tested with graceful recovery
- ✅ **Workflow Tests**: Complete user scenarios validated end-to-end

**Test Quality Features**:
- **Isolation**: Each test uses temporary directories with automatic cleanup
- **Repeatability**: Deterministic test outcomes with fixed seeds
- **Performance Monitoring**: Execution time and memory usage tracking
- **Error Recovery**: Graceful handling of missing dependencies (psutil)
- **Comprehensive Reporting**: Detailed test summaries and performance metrics

### Code Quality Assessment

**Strengths**:
1. **🎯 Modular Design**: Clear separation of concerns, well-defined package boundaries
2. **📊 Configuration-Driven**: All behavior configurable via profiles and environment
3. **🧪 Comprehensive Testing**: Multiple test categories with performance validation
4. **📚 Documentation Quality**: Detailed docstrings, implementation tracking, user guides
5. **⚡ Performance Optimized**: Sub-millisecond operations with efficiency focus
6. **🔄 Extensible Design**: Plugin-based systems ready for Phase 4 enhancements

**Architecture Validation**:
- ✅ **Loose Coupling**: Components interact through well-defined interfaces
- ✅ **High Cohesion**: Related functionality properly grouped
- ✅ **Dependency Management**: Clear dependency hierarchy maintained
- ✅ **Configuration Consistency**: Unified configuration access patterns
- ✅ **Error Resilience**: Comprehensive error handling and recovery mechanisms

### Implementation Status Summary

**Current Capabilities** (Phase 1-3 Complete):
- Enterprise-grade configuration management with multi-source loading
- Complete conversation persistence with auto-save and template workflows
- Multi-format export (JSON, Markdown, PDF) with syntax highlighting
- Comprehensive test suite with performance benchmarking
- Enhanced Docker Model Runner compatibility with parameter validation
- Production-ready architecture with excellent performance characteristics

**Ready for Phase 4 Advanced Features**:
- Real-time streaming improvements and WebSocket support
- Advanced AI model integration and multi-model comparison
- Plugin system for extensible functionality
- Web UI for browser-based interaction
- Advanced analytics and conversation insights

### Optimization Opportunities Identified

**Immediate Optimizations**:
1. **Search Performance**: Implement indexing for conversation search (21ms → target <5ms)
2. **Bulk Operations**: Add parallel processing for batch operations
3. **Memory Usage**: Implement lazy loading for large conversation lists
4. **Caching**: Add intelligent caching for frequently accessed configurations

**Future Enhancements**:
1. **Database Integration**: Replace JSON files with SQLite for better performance at scale
2. **Full-Text Search**: Implement advanced search capabilities for conversations
3. **Compression**: Add compression for large conversation exports
4. **Streaming**: Implement streaming for large data operations

### Development Guidelines

**Code Modification Patterns**:
- Follow configuration-driven architecture principles
- Maintain test coverage when adding new features
- Use established design patterns (Repository, Factory, Strategy)
- Implement comprehensive error handling with graceful degradation
- Follow modular package structure for new components
- Reference performance benchmarks for optimization validation

**Testing Approach**:
- Unit tests for individual component validation
- Integration tests for cross-component interactions
- Performance benchmarks for optimization tracking
- Error scenario tests for robustness validation
- End-to-end workflow tests for user experience validation