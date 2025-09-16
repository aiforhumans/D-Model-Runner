# D-Model-Runner Copilot Instructions

This project is a production-ready Python client for Docker Model Runner with enterprise-grade configuration management, conversation persistence, comprehensive testing, and a modern web UI. Phases 1-4 complete as of September 2025.

## Core Architecture & Entry Points

**Main Entry Points**:
- `python main.py` - Interactive chat with conversation persistence and model selection
- `python UI/app.py` - Web UI server for browser-based chat interface
- `python test/test.py` - Parameter validation and Docker Model Runner compatibility testing
- `python tests/performance/benchmark.py` - Performance benchmarking

**Package Structure**:
```python
dmr/                    # Core package (2,197 LOC)
├── config/            # Multi-source configuration (files, env vars, profiles)
├── storage/           # Conversation persistence, templates, multi-format export
├── utils/            # Shared utilities and validation
└── __init__.py       # Package exports: ConfigManager, storage classes

UI/                     # Web interface (Flask-based, ~800 LOC)
├── app.py            # Flask web server with DMR integration
├── templates/        # HTML templates
├── static/           # CSS/JS assets
├── tests/            # Playwright test suite
└── Checklist_ui.md   # UI development roadmap
```

**Critical Integration Pattern**:
```python
# Standard initialization pattern used throughout
from dmr.config import ConfigManager
from dmr.storage import ConversationManager, TemplateManager, ExportManager

config_manager = ConfigManager()
config_manager.load_config(profile='dev')  # dev/prod/custom profiles
conversation_manager = ConversationManager()
```

## Essential Development Workflows

**Testing Commands**:
```bash
# Run all tests with coverage
python -m pytest tests/ -v
python tests/performance/benchmark.py  # Performance validation
python test/test.py                     # Docker Model Runner compatibility
```

**Configuration Management**:
- Configuration sources: `dmr/config/profiles/` (dev.yaml, prod.yaml, custom.yaml)
- Environment overrides: `DMR_BASE_URL`, `DMR_DEFAULT_MODEL`, `DMR_MAX_TOKENS`
- Profile switching: `config_manager.load_config('dev')` vs `config_manager.load_config('prod')`

**Current Phase**: ✅ **Phase 4 Complete** (September 2025) - Web UI Implementation

## Docker Model Runner Integration

**Connection Details**:
- Base URL: `http://localhost:12434/engines/llama.cpp/v1/`
- Models: `ai/gemma3` (standard chat), `ai/qwen3` (reasoning with `<think>` tokens)
- API: OpenAI-compatible but with llama.cpp backend limitations

**Verified Parameter Support**:
```python
# Configuration-driven client setup with proper error handling
try:
    client = OpenAI(
        base_url=config_manager.get_base_url(), 
        api_key="anything",  # Docker Model Runner placeholder
        timeout=30.0,        # Custom timeout for local server
        max_retries=2        # Retry on connection issues
    )
    model = config_manager.get_default_model()
    model_config = config_manager.get_model_config(model)

    response = client.chat.completions.create(
        model=model,
        messages=[...],
        # Core parameters (verified working)
        temperature=model_config.get('temperature', 0.7),
        max_tokens=model_config.get('max_tokens', 500), 
        top_p=0.9, presence_penalty=0.1, frequency_penalty=0.1,
        seed=42, stream=True,
        # Advanced (model-dependent)
        response_format={"type": "json_object"}, logprobs=True
    )
except openai.APIConnectionError as e:
    # Docker Model Runner not available
    print(f"Cannot connect to model server: {e}")
except openai.APITimeoutError as e:
    # Model loading can be slow
    print(f"Request timed out: {e}")
except openai.APIStatusError as e:
    # Invalid parameters or model not loaded
    print(f"API error {e.status_code}: {e.response.text}")
```

**Modern Streaming Pattern** (implemented in `main.py`):
```python
# Modern streaming API with fallback compatibility
try:
    with client.chat.completions.stream(
        model=current_model,
        messages=messages,
        **model_config
    ) as stream:
        assistant_response = ""
        for event in stream:
            if event.type == "content.delta":
                print(event.delta, end="", flush=True)
                assistant_response += event.delta
        
        # Get final accumulated response
        final_completion = stream.get_final_completion()
        if final_completion and final_completion.choices:
            assistant_response = final_completion.choices[0].message.content
            
except AttributeError:
    # Fallback to traditional streaming for compatibility
    response = client.chat.completions.create(model=model, messages=messages, stream=True)
    for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
except openai.LengthFinishReasonError:
    print("⚠️ Response truncated due to max_tokens limit")
```

**Server Health Check** (integrated startup):
```python
# Health check with configuration control
connection_check = config_manager.get('api.client.connection_check', True)
if connection_check:
    health_ok, available_models = check_model_server_health()
    if health_ok:
        print(f"✅ Server accessible. Models: {', '.join(available_models)}")
```

**Known Limitations**: `n > 1` (500 error), `tools`/`function_call` not supported

## Configuration System Architecture

**Multi-Source Loading Priority**:
1. `dmr/config/defaults.yaml` (base configuration)
2. `dmr/config/profiles/{profile}.yaml` (dev/prod/custom)
3. Environment variables with `DMR_` prefix
4. Runtime overrides

**Key Configuration Methods**:
```python
config_manager = ConfigManager()
config_manager.load_config('dev')           # Load development profile
base_url = config_manager.get_base_url()    # Get configured base URL  
model = config_manager.get_default_model()  # Get default model name
model_config = config_manager.get_model_config(model)  # Model-specific params
```

**Client Configuration Best Practices**:
```python
# Proper client initialization with Docker Model Runner
client = OpenAI(
    base_url=config_manager.get_base_url(),  # Custom backend URL
    api_key="anything",                      # Placeholder for local server
    timeout=30.0,                           # Longer timeout for local models
    max_retries=2                           # Retry connection issues
)

# Per-request configuration override for slow operations
response = client.with_options(timeout=60.0).chat.completions.create(...)

# Server health check before operations
health_ok, models = check_model_server_health()
if health_ok:
    validated_model = validate_model_availability(selected_model)
```

**Configuration Structure** (`dmr/config/profiles/`):
```yaml
api:
  client:
    timeout: 30.0          # Request timeout in seconds
    max_retries: 2         # Number of retries on failure
    connection_check: true # Validate server on startup
  
error_handling:
  show_detailed_errors: true
  suggest_fixes: true
  retry_on_timeout: true
```

**Profile Examples**:
- `dev.yaml`: `ai/qwen3` model, debug logging, lower token limits
- `prod.yaml`: `ai/gemma3` model, optimized for production use
- Environment: `DMR_DEFAULT_MODEL=ai/custom` overrides profile setting

## Storage & Conversation System

**Storage Architecture** (`dmr/storage/` - 1,536 LOC):
```python
# Conversation persistence pattern
conversation_manager = ConversationManager()
conversation = conversation_manager.create_conversation("Session Title", "ai/gemma3")
conversation.add_message("user", "Hello")
conversation.add_message("assistant", "Hi there!")
conversation_manager.save_conversation(conversation)

# Template workflow system  
template_manager = TemplateManager()
template = template_manager.get_template("api_design")
conversation = template_manager.create_from_template(template.id, {"api_name": "UserAPI"})

# Multi-format export
export_manager = ExportManager()
export_manager.export_conversation(conversation, "markdown", "output.md")
export_manager.export_conversation(conversation, "pdf", "output.pdf")  # Advanced formatting
```

**Data Models**:
- `Conversation`: Contains `messages[]`, `metadata`, auto-generates UUID
- `Message`: `role`, `content`, `timestamp`, `metadata`
- `Template`: JSON-based with variable substitution support

## Web UI Architecture

**UI Entry Point**:
- `python UI/app.py` - Flask web server with DMR integration

**UI Architecture** (`UI/` - ~800 LOC):
```python
UI/
├── app.py              # Flask web server with DMR integration
├── templates/
│   └── chat.html      # Modern chat interface
├── static/
│   ├── css/style.css  # Responsive styling
│   └── js/chat.js     # Real-time chat functionality
├── tests/
│   └── test_ui.py     # Playwright test suite
└── Checklist_ui.md    # UI development roadmap
```

**UI Integration Pattern**:
```python
# Standard UI initialization pattern
from dmr.config import ConfigManager
from dmr.storage import ConversationManager

# Flask app with DMR integration
config_manager = ConfigManager()
conversation_manager = ConversationManager()

# API endpoints integrate with existing DMR infrastructure
@app.route('/api/chat', methods=['POST'])
def chat():
    # Uses ConfigManager for model configuration
    # Uses ConversationManager for persistence
    # Returns OpenAI-compatible responses
```

**UI Features**:
- Modern chat interface with real-time messaging
- Model selection dropdown (ai/gemma3, ai/qwen3)
- Conversation persistence with timestamps
- Responsive design for desktop and mobile
- Health monitoring and connection status
- Error handling with user-friendly messages

**UI Testing**:
- Playwright browser automation for UI testing
- API endpoint validation
- Cross-browser compatibility testing
- Mobile responsiveness verification

## Testing Infrastructure Pattern

**Test Categories** (`tests/` - 2,904 LOC):
```bash
tests/unit/              # Component isolation (config, storage, error scenarios)
tests/integration/       # Cross-component validation 
tests/performance/       # Benchmarking (config: 0.35-1.3ms, storage: 0.02-1.4ms)
```

**Test Isolation Pattern**:
```python
# Standard test setup across all test modules
def setUp(self):
    self.temp_dir = tempfile.mkdtemp()
    self.config_manager = ConfigManager(config_dir=self.temp_dir)
    
def tearDown(self):
    shutil.rmtree(self.temp_dir)
```

**Performance Benchmarks**: Run `python tests/performance/benchmark.py` for optimization validation

## Common Patterns & Anti-Patterns

**✅ Configuration-Driven Pattern**:
```python
# Always use ConfigManager for settings
config_manager = ConfigManager()
config_manager.load_config(profile)
setting = config_manager.get('api.models.defaults.max_tokens')
```

**✅ Storage Manager Pattern**:
```python  
# Use managers for persistence operations
conversation_manager = ConversationManager()
conversation = conversation_manager.create_conversation(title, model)
conversation_manager.save_conversation(conversation)
```

**❌ Avoid**: Direct file I/O, hardcoded configuration values, bypassing the configuration system

## Error Handling & Resilience

**Comprehensive Error Testing**: 25+ error scenarios validated in `tests/unit/test_error_scenarios.py`

**Standard Error Pattern**:
```python
from dmr.utils.helpers import format_error_message
import openai

try:
    # Configuration or API operation
    response = client.chat.completions.create(...)
except openai.APIConnectionError as e:
    # Server unreachable (Docker Model Runner down)
    error_msg = format_error_message(e, "connecting to model server")
    print(f"Connection error: {error_msg}")
except openai.APITimeoutError as e:
    # Request timeout (model loading slowly)
    error_msg = format_error_message(e, "API request timeout")
    print(f"Timeout: {error_msg}")
except openai.APIStatusError as e:
    # HTTP error responses (invalid params, model not found)
    error_msg = format_error_message(e, f"API call (status {e.status_code})")
    print(f"API error: {error_msg}")
except Exception as e:
    # Fallback for unexpected errors
    error_msg = format_error_message(e, "operation_name")
    print(f"Unexpected error: {error_msg}")
```

**Docker Model Runner Resilience**: 
- Always wrap API calls in try/except blocks
- Service may be unavailable or models unloaded
- Use timeouts and retries for reliability
- Check streaming chunks structure before accessing content

## Modification Guidelines

**Adding New Features**:
1. Follow modular package structure in `dmr/` and `UI/`
2. Add configuration support in `dmr/config/profiles/`  
3. Implement comprehensive tests (unit + integration + Playwright UI tests)
4. Use established patterns: Repository, Factory, Strategy
5. Reference `TODO/implement_checklist.md` and `UI/Checklist_ui.md` for phase planning
6. For UI features: Follow Flask REST API patterns and integrate with DMR managers

**UI Development Guidelines**:
1. Keep UI lightweight - use vanilla HTML/CSS/JS for core functionality
2. Integrate with existing DMR ConfigManager and ConversationManager
3. Add Playwright tests for new UI features
4. Maintain responsive design for mobile and desktop
5. Follow established error handling patterns from DMR

**Performance Considerations**:
- Configuration loading: Sub-millisecond (cached after first load)
- Conversation operations: <2ms typical
- UI API responses: <500ms for good user experience
- Search optimization needed for >100 conversations (currently ~21ms)

**Dependencies**: Minimal external deps (`openai`, `PyYAML`, `requests`, `flask`, `flask-cors`) - avoid adding heavy dependencies

**Ready for Phase 5**: Real-time streaming, advanced UI features, plugin system, production deployment