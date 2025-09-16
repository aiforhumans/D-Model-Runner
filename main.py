from openai import OpenAI
import openai
from dmr.config import ConfigManager
from dmr.utils.helpers import validate_model_name, format_error_message
from dmr.storage import ConversationManager, TemplateManager, ExportManager
from dmr.utils.performance import performance_metrics, PerformanceReport
from pathlib import Path
from datetime import datetime
import time
import random
from functools import wraps

# Initialize configuration manager
config_manager = ConfigManager()

# Initialize storage managers
conversation_manager = ConversationManager()
template_manager = TemplateManager()
export_manager = ExportManager()

def exponential_backoff_retry(max_retries=3, base_delay=1.0, max_delay=60.0, backoff_factor=2.0):
    """
    Decorator for exponential backoff retry logic on API calls.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay between retries
        backoff_factor: Multiplier for delay on each retry
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):  # +1 for initial attempt
                try:
                    return func(*args, **kwargs)
                    
                except (openai.APIConnectionError, openai.APITimeoutError, openai.APIStatusError) as e:
                    last_exception = e
                    
                    # Don't retry on certain status codes
                    if isinstance(e, openai.APIStatusError):
                        if e.status_code in [400, 401, 403, 404, 422]:  # Client errors
                            raise e
                    
                    if attempt >= max_retries:
                        break
                    
                    # Calculate delay with exponential backoff and jitter
                    delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                    jitter = random.uniform(0, 0.1 * delay)  # Add 10% jitter
                    total_delay = delay + jitter
                    
                    print(f"⚠️ API call failed (attempt {attempt + 1}/{max_retries + 1}), retrying in {total_delay:.1f}s...")
                    time.sleep(total_delay)
                    
                except Exception as e:
                    # Don't retry on non-API errors
                    raise e
            
            # If we get here, all retries failed
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator

def initialize_client():
    """Initialize OpenAI client with configuration and production-ready settings."""
    config = config_manager.load_config()
    base_url = config_manager.get_base_url()
    api_key = config_manager.get_api_key()
    
    # Get client configuration from config manager
    client_config = config_manager.get('api.client', {})
    timeout = client_config.get('timeout', 30.0)  # Custom timeout for local Docker Model Runner
    max_retries = client_config.get('max_retries', 2)  # Retry on connection issues
    
    return OpenAI(
        base_url=base_url, 
        api_key=api_key,
        timeout=timeout,
        max_retries=max_retries
    )

def check_model_server_health():
    """Check if Docker Model Runner is accessible and return available models."""
    try:
        client = initialize_client()
        # Try to list models as a health check
        models = client.models.list()
        raw_models = [model.id for model in models.data]
        
        # Normalize model names by removing :latest and other tags
        available_models = []
        for model in raw_models:
            # Remove tag suffixes like :latest, :q4_k_m, etc.
            base_model = model.split(':')[0]
            # Also handle hf.co/ prefixes by taking just the model name
            if base_model.startswith('hf.co/'):
                base_model = base_model.split('/')[-1]
            if base_model not in available_models:
                available_models.append(base_model)
        
        print(f"✅ Server accessible. Available models: {', '.join(available_models)}")
        print(f"   Raw server models: {', '.join(raw_models[:3])}{'...' if len(raw_models) > 3 else ''}")
        return True, available_models
    except openai.APIConnectionError as e:
        print("❌ Cannot connect to Docker Model Runner")
        print("💡 Start with: docker run -p 12434:12434 docker/model-runner")
        print(f"Connection details: {e}")
        return False, []
    except openai.APITimeoutError as e:
        print("⏱️ Connection to Docker Model Runner timed out")
        print("💡 Server may be starting up. Try again in a moment.")
        print(f"Timeout details: {e}")
        return False, []
    except openai.APIStatusError as e:
        print(f"🚫 Server returned error {e.status_code}")
        if hasattr(e, 'response'):
            print(f"Response: {e.response.text}")
        return False, []
    except Exception as e:
        print(f"⚠️ Unexpected error during server health check: {e}")
        return False, []

def resolve_model_name_for_server(model_name):
    """Resolve config model name to actual server model name."""
    try:
        client = initialize_client()
        models = client.models.list()
        server_models = [model.id for model in models.data]
        
        # Try exact match first
        if model_name in server_models:
            return model_name
        
        # Try with :latest suffix
        model_with_latest = f"{model_name}:latest"
        if model_with_latest in server_models:
            return model_with_latest
        
        # Try partial matches (for models like ai/gemma3)
        for server_model in server_models:
            if server_model.startswith(model_name):
                return server_model
        
        # Fallback to original name
        print(f"⚠️ Model '{model_name}' not found on server, using as-is")
        return model_name
        
    except Exception as e:
        print(f"⚠️ Could not resolve model name: {e}")
        return model_name

def validate_model_availability(model_name):
    """Validate model is available on the Docker Model Runner server."""
    try:
        client = initialize_client()
        models = client.models.list()
        server_models = [model.id for model in models.data]
        
        # Check various forms of the model name
        model_forms = [
            model_name,
            f"{model_name}:latest",
        ]
        
        # Add partial matches
        for server_model in server_models:
            if server_model.startswith(model_name):
                model_forms.append(server_model)
        
        for form in model_forms:
            if form in server_models:
                return True
        
        print(f"❌ Model '{model_name}' not available on server")
        print(f"Available models: {', '.join([m.split(':')[0] for m in server_models[:5]])}{'...' if len(server_models) > 5 else ''}")
        return False
        
    except openai.APIConnectionError:
        print(f"⚠️ Cannot validate model '{model_name}' - server unreachable")
        return False  # Fail closed for safety
    except Exception as e:
        print(f"⚠️ Could not validate model availability: {e}")
        return False  # Fail closed for safety
    """Validate model is available on the Docker Model Runner server."""
    try:
        client = initialize_client()
        models = client.models.list()
        available_models = [model.id for model in models.data]
        
        if model_name in available_models:
            return True
        else:
            print(f"❌ Model '{model_name}' not available on server")
            print(f"Available models: {', '.join(available_models)}")
            return False
    except openai.APIConnectionError:
        print(f"⚠️ Cannot validate model '{model_name}' - server unreachable")
        return False  # Fail closed for safety
    except Exception as e:
        print(f"⚠️ Could not validate model availability: {e}")
        return False  # Fail closed for safety

@exponential_backoff_retry(max_retries=3, base_delay=1.0, max_delay=30.0)
def chat_with_extended_timeout(client, model, messages, model_config, timeout=60.0):
    """Chat with extended timeout for potentially slow operations with exponential backoff."""
    try:
        with client.with_options(timeout=timeout).chat.completions.stream(
            model=model,
            messages=messages,
            max_tokens=model_config.get('max_tokens', 500),
            temperature=model_config.get('temperature', 0.7),
            top_p=model_config.get('top_p', 0.9),
        ) as stream:
            assistant_response = ""
            try:
                for event in stream:
                    if event.type == "content.delta":
                        print(event.delta, end="", flush=True)
                        assistant_response += event.delta
                
                print()  # New line after streaming
                
                # Get the final accumulated response if available
                try:
                    final_completion = stream.get_final_completion()
                    if final_completion and final_completion.choices:
                        final_content = final_completion.choices[0].message.content
                        if final_content:
                            assistant_response = final_content
                except Exception:
                    # Fallback to accumulated response
                    pass
                
            except openai.LengthFinishReasonError:
                print("\n⚠️ Response truncated due to max_tokens limit")
            except openai.ContentFilterFinishReasonError:
                print("\n⚠️ Response filtered by content policy")
            
            return assistant_response
            
    except openai.APITimeoutError:
        print(f"\n⏱️ Extended timeout ({timeout}s) exceeded for {model}")
        print("💡 Try reducing max_tokens or using a faster model")
        return None

def chat_with_model(model=None, system_prompt=None, conversation=None):
    """
    Interactive chat interface with conversation history and persistence
    """
    # Get defaults from configuration if not provided
    if model is None:
        model = config_manager.get_default_model()
    if system_prompt is None:
        system_prompt = config_manager.get('ui.system_prompts.default', 
                                         "You are a helpful AI assistant. Be concise but informative in your responses.")
    
    # Validate model name and server availability
    if not validate_model_name(model):
        print(f"❌ Invalid model name format: {model}")
        return
    
    if not validate_model_availability(model):
        print(f"❌ Model '{model}' not available on Docker Model Runner")
        return
    
    # Initialize client
    client = initialize_client()
    
    # Initialize or use existing conversation
    if conversation is None:
        conversation_title = f"Chat Session - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        conversation = conversation_manager.create_conversation(conversation_title, model)
        conversation.add_message("system", system_prompt)
        print(f"🆕 Created new conversation: {conversation_title}")
    else:
        print(f"📖 Continuing conversation: {conversation.metadata.title}")
    
    # Enable auto-save
    conversation_manager.enable_auto_save(conversation)
    
    print(f"🤖 Starting chat with {model}")
    print("System prompt:", system_prompt)
    print("=" * 60)
    print("💬 CHAT COMMANDS:")
    print("  quit, exit, bye     - End conversation")
    print("  clear               - Reset conversation history")
    print("  model <name>        - Switch models")
    print("  config              - Show current configuration")
    print("  save                - Save conversation manually")
    print("  load                - Load a previous conversation")
    print("  list                - List all conversations")
    print("  export <format>     - Export conversation (json/markdown/pdf)")
    print("  template            - Create conversation from template")
    print("  templates           - List available templates")
    print("=" * 60)
    print(f"Available models: {', '.join(config_manager.get_available_models())}")
    print("-" * 50)

    # Get conversation messages in OpenAI format
    messages = conversation.get_openai_messages()
    current_model = model

    while True:
        try:
            # Get user input
            user_input = input("\n👤 You: ").strip()

            # Handle special commands
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("� Saving conversation...")
                conversation_manager.save_conversation(conversation)
                print("�👋 Goodbye!")
                break

            if user_input.lower() == 'clear':
                # Reset conversation but keep metadata
                conversation.messages.clear()
                conversation.add_message("system", system_prompt)
                messages = conversation.get_openai_messages()
                print("🧹 Conversation history cleared!")
                continue

            if user_input.lower().startswith('model '):
                new_model = user_input[6:].strip()
                available_models = config_manager.get_available_models()
                if new_model in available_models:
                    current_model = new_model
                    conversation.update_metadata(model=new_model)
                    print(f"🔄 Switched to model: {current_model}")
                else:
                    print(f"❌ Invalid model. Available: {', '.join(available_models)}")
                continue

            if user_input.lower() == 'config':
                print(f"📊 Current Configuration:")
                print(f"   Profile: {config_manager.get_current_profile()}")
                print(f"   Base URL: {config_manager.get_base_url()}")
                print(f"   Default Model: {config_manager.get_default_model()}")
                print(f"   Available Models: {', '.join(config_manager.get_available_models())}")
                print(f"   Conversation ID: {conversation.id}")
                print(f"   Messages: {len(conversation.messages)}")
                continue

            if user_input.lower() == 'save':
                path = conversation_manager.save_conversation(conversation)
                print(f"💾 Conversation saved to: {path}")
                continue

            if user_input.lower() == 'load':
                handle_load_conversation()
                continue

            if user_input.lower() == 'list':
                handle_list_conversations()
                continue

            if user_input.lower().startswith('export '):
                format_name = user_input[7:].strip()
                handle_export_conversation(conversation, format_name)
                continue

            if user_input.lower() == 'template':
                new_conversation = handle_create_from_template()
                if new_conversation:
                    conversation = new_conversation
                    messages = conversation.get_openai_messages()
                    current_model = conversation.metadata.model
                    print(f"🔄 Switched to new conversation from template")
                continue

            if user_input.lower() == 'templates':
                handle_list_templates()
                continue

            if not user_input:
                continue

            # Add user message to conversation and history
            conversation.add_message("user", user_input)
            messages = conversation.get_openai_messages()

            # Get response from model
            print(f"🤖 {current_model}: ", end="", flush=True)

            try:
                # Get model-specific configuration
                model_config = config_manager.get_model_config(current_model)
                
                # Resolve model name for server (handle :latest suffixes etc.)
                server_model_name = resolve_model_name_for_server(current_model)
                
                # Check if streaming is enabled in configuration
                stream_enabled = model_config.get('stream', True)
                
                if stream_enabled:
                    # Try modern streaming API first, fallback to traditional if needed
                    try:
                        with client.chat.completions.stream(
                            model=server_model_name,
                            messages=messages,
                            max_tokens=model_config.get('max_tokens', 500),
                            temperature=model_config.get('temperature', 0.7),
                            top_p=model_config.get('top_p', 0.9),
                        ) as stream:
                            assistant_response = ""
                            try:
                                for event in stream:
                                    if event.type == "content.delta":
                                        print(event.delta, end="", flush=True)
                                        assistant_response += event.delta
                                
                                print()  # New line after streaming
                                
                                # Get the final accumulated response if available
                                try:
                                    final_completion = stream.get_final_completion()
                                    if final_completion and final_completion.choices:
                                        final_content = final_completion.choices[0].message.content
                                        if final_content:
                                            assistant_response = final_content
                                except Exception:
                                    # Fallback to accumulated response
                                    pass
                                
                            except openai.LengthFinishReasonError:
                                print("\n⚠️ Response truncated due to max_tokens limit")
                            except openai.ContentFilterFinishReasonError:
                                print("\n⚠️ Response filtered by content policy")
                    
                    except AttributeError:
                        # Fallback to traditional streaming if modern API not available
                        response = client.chat.completions.create(
                            model=server_model_name,
                            messages=messages,
                            max_tokens=model_config.get('max_tokens', 500),
                            temperature=model_config.get('temperature', 0.7),
                            top_p=model_config.get('top_p', 0.9),
                            stream=True
                        )
                        
                        assistant_response = ""
                        for chunk in response:
                            if chunk.choices and len(chunk.choices) > 0:
                                delta = chunk.choices[0].delta
                                if hasattr(delta, 'content') and delta.content:
                                    print(delta.content, end="", flush=True)
                                    assistant_response += delta.content
                        
                        print()  # New line after streaming
                else:
                    # Non-streaming mode
                    response = client.chat.completions.create(
                        model=server_model_name,
                        messages=messages,
                        max_tokens=model_config.get('max_tokens', 500),
                        temperature=model_config.get('temperature', 0.7),
                        top_p=model_config.get('top_p', 0.9),
                        stream=False
                    )
                    
                    assistant_response = response.choices[0].message.content
                    print(assistant_response)

                # Add assistant response to conversation and history
                conversation.add_message("assistant", assistant_response)
                messages = conversation.get_openai_messages()

            except openai.APIConnectionError as e:
                # Docker Model Runner not available
                error_msg = format_error_message(e, "connecting to model server")
                print(f"\n🔌 Connection Error: {error_msg}")
                print("💡 Tip: Make sure Docker Model Runner is running on localhost:12434")
                # Remove the failed user message from conversation
                if conversation.messages and conversation.messages[-1].role == "user":
                    conversation.messages.pop()
                messages = conversation.get_openai_messages()
            except openai.APITimeoutError as e:
                # Model loading can be slow
                error_msg = format_error_message(e, "API request timeout")
                print(f"\n⏱️ Timeout Error: {error_msg}")
                print("💡 Tip: Model might be loading. Try again in a moment.")
                # Remove the failed user message from conversation
                if conversation.messages and conversation.messages[-1].role == "user":
                    conversation.messages.pop()
                messages = conversation.get_openai_messages()
            except openai.APIStatusError as e:
                # Invalid parameters or model not loaded
                error_msg = format_error_message(e, f"API call (status {e.status_code})")
                print(f"\n🚫 API Error: {error_msg}")
                if hasattr(e, 'response'):
                    print(f"Response: {e.response.text}")
                # Remove the failed user message from conversation
                if conversation.messages and conversation.messages[-1].role == "user":
                    conversation.messages.pop()
                messages = conversation.get_openai_messages()
            except openai.RateLimitError as e:
                # Rate limiting (if Docker Model Runner implements it)
                print(f"\n⚡ Rate Limit: {e}")
                print("💡 Tip: Wait a moment before trying again.")
                # Remove the failed user message from conversation
                if conversation.messages and conversation.messages[-1].role == "user":
                    conversation.messages.pop()
                messages = conversation.get_openai_messages()
            except Exception as e:
                # Fallback for unexpected errors
                error_msg = format_error_message(e, f"API call to {current_model}")
                print(f"\n❌ Unexpected Error: {error_msg}")
                # Remove the failed user message from conversation
                if conversation.messages and conversation.messages[-1].role == "user":
                    conversation.messages.pop()
                messages = conversation.get_openai_messages()

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except EOFError:
            print("\n👋 Goodbye!")
            break

def handle_load_conversation():
    """Handle loading a previous conversation."""
    conversations = conversation_manager.list_conversations()
    if not conversations:
        print("📭 No saved conversations found.")
        return None
    
    print("\n📚 Saved Conversations:")
    for i, conv in enumerate(conversations[:10], 1):  # Show latest 10
        created = datetime.fromisoformat(conv['created_at']).strftime('%Y-%m-%d %H:%M')
        print(f"{i}. {conv['title']} ({conv['message_count']} msgs, {created})")
    
    try:
        choice = input(f"\nSelect conversation (1-{min(len(conversations), 10)}): ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < min(len(conversations), 10):
                conv_id = conversations[idx]['id']
                loaded_conv = conversation_manager.load_conversation(conv_id)
                if loaded_conv:
                    conversation_manager.set_current_conversation(loaded_conv)
                    print(f"📖 Loaded conversation: {loaded_conv.metadata.title}")
                    return loaded_conv
    except (ValueError, IndexError):
        pass
    
    print("❌ Invalid selection.")
    return None

def handle_list_conversations():
    """Handle listing all conversations."""
    conversations = conversation_manager.list_conversations()
    if not conversations:
        print("📭 No saved conversations found.")
        return
    
    print(f"\n📚 All Conversations ({len(conversations)} total):")
    for i, conv in enumerate(conversations, 1):
        created = datetime.fromisoformat(conv['created_at']).strftime('%Y-%m-%d %H:%M')
        updated = datetime.fromisoformat(conv['updated_at']).strftime('%Y-%m-%d %H:%M')
        tags_str = f" [{', '.join(conv['tags'])}]" if conv['tags'] else ""
        print(f"{i:2}. {conv['title']}")
        print(f"    Model: {conv['model']} | Messages: {conv['message_count']} | Created: {created}{tags_str}")
        if i >= 20:  # Limit display
            print(f"    ... and {len(conversations) - 20} more")
            break

def handle_export_conversation(conversation, format_name):
    """Handle exporting a conversation."""
    if not format_name:
        print("❌ Please specify format: json, markdown, or pdf")
        return
    
    try:
        output_path = export_manager.export_conversation(conversation, format_name)
        print(f"📤 Exported to: {output_path}")
    except Exception as e:
        print(f"❌ Export failed: {e}")

def handle_create_from_template():
    """Handle creating conversation from template."""
    templates = template_manager.list_templates()
    if not templates:
        print("📭 No templates available.")
        return None
    
    print("\n📝 Available Templates:")
    for i, template in enumerate(templates, 1):
        print(f"{i}. {template['name']} ({template['category']})")
        print(f"   {template['description']}")
    
    try:
        choice = input(f"\nSelect template (1-{len(templates)}): ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(templates):
                template_id = templates[idx]['id']
                template = template_manager.get_template(template_id)
                
                if template:
                    # Get required variables
                    required_vars = template.get_required_variables()
                    variables = {}
                    
                    if required_vars:
                        print(f"\n📝 Please provide values for template variables:")
                        for var in required_vars:
                            value = input(f"  {var}: ").strip()
                            if value:
                                variables[var] = value
                            else:
                                print("❌ All variables are required.")
                                return None
                    
                    # Create conversation from template
                    new_conversation = template_manager.instantiate_template(
                        template_id, variables
                    )
                    conversation_manager.set_current_conversation(new_conversation)
                    print(f"✨ Created conversation from template: {template.metadata.name}")
                    return new_conversation
    except (ValueError, IndexError):
        pass
    
    print("❌ Invalid selection.")
    return None

def handle_list_templates():
    """Handle listing available templates."""
    templates = template_manager.list_templates()
    if not templates:
        print("📭 No templates available.")
        return
    
    print(f"\n📝 Available Templates ({len(templates)} total):")
    
    # Group by category
    categories = {}
    for template in templates:
        category = template['category']
        if category not in categories:
            categories[category] = []
        categories[category].append(template)
    
    for category, category_templates in categories.items():
        print(f"\n📂 {category.title()}:")
        for template in category_templates:
            vars_str = f" (vars: {', '.join(template['variables'])})" if template['variables'] else ""
            print(f"  • {template['name']}{vars_str}")
            print(f"    {template['description']}")

def handle_performance_metrics():
    """Display current performance metrics."""
    print("\n" + PerformanceReport.generate_summary())
    print("\n" + PerformanceReport.generate_cache_report())
    
    # Show cache statistics
    config_stats = config_manager.get_cache_stats()
    conv_stats = conversation_manager.get_cache_stats()
    
    print(f"\n🗄️ Cache Statistics")
    print("-" * 20)
    print(f"Configuration Cache:")
    print(f"  Files cached: {config_stats['files_cached']}")
    print(f"  Profiles cached: {config_stats['profiles_cached']}")
    print(f"  Environment cached: {config_stats['env_cached']}")
    print(f"  Cache valid: {config_stats['cache_valid']}")
    
    print(f"\nConversation Cache:")
    print(f"  Conversations indexed: {conv_stats['conversation_count']}")
    print(f"  Cache file exists: {conv_stats['cache_file_exists']}")
    
    # Offer to export metrics
    export_choice = input("\nExport metrics to file? (y/N): ").strip().lower()
    if export_choice == 'y':
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = Path(f"performance_metrics_{timestamp}.json")
        performance_metrics.export_metrics(export_path)
        print(f"📁 Metrics exported to: {export_path}")

def handle_clear_performance_metrics():
    """Clear all performance metrics."""
    performance_metrics.clear_metrics()
    print("🗑️ Performance metrics cleared.")

def main():
    """
    Main function with model and profile selection
    """
    print("🚀 D-Model-Runner Chat Interface with Conversation Persistence")
    print("=" * 65)

    # Health check for Docker Model Runner (if enabled in config)
    health_ok = True
    available_models = []
    
    # Check if connection check is enabled in configuration
    connection_check = config_manager.get('api.client.connection_check', True)
    
    if connection_check:
        print("\n🔍 Checking Docker Model Runner connection...")
        health_ok, available_models = check_model_server_health()
        if not health_ok:
            print("\n⚠️ Continuing without server validation...")
            available_models = []  # Will fall back to config-based models
    else:
        print("\n⏩ Skipping connection check (disabled in configuration)")
        available_models = []

    # Profile selection
    try:
        available_profiles = config_manager.list_available_profiles()
        if len(available_profiles) > 1:
            print("Available profiles:")
            for i, profile in enumerate(available_profiles, 1):
                print(f"{i}. {profile}")
            
            while True:
                choice = input(f"\nSelect profile (1-{len(available_profiles)}) or press Enter for default: ").strip()
                
                if choice == "":
                    selected_profile = "default"
                    break
                elif choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(available_profiles):
                        selected_profile = available_profiles[idx]
                        break
                
                print("❌ Invalid choice.")
        else:
            selected_profile = "default"
        
        # Load configuration with selected profile
        config_manager.load_config(profile=selected_profile)
        print(f"📝 Using profile: {selected_profile}")
        
    except Exception as e:
        print(f"⚠️  Warning: {format_error_message(e, 'loading config')}. Using defaults.")
        config_manager.load_config()

    # Model selection
    print("\nAvailable models:")
    config_models = config_manager.get_available_models()
    
    # If server health check was successful, show which models are validated
    if health_ok and available_models:
        # Only show models that we have configuration for
        display_models = config_models
        print("(✅ = Server Validated)")
    else:
        # Fall back to config-based models only
        display_models = config_models
    
    default_model = config_manager.get_default_model()
    
    for i, model in enumerate(display_models, 1):
        try:
            model_config = config_manager.get_model_config(model)
            description = model_config.get('description', 'No description')
        except ValueError:
            # Skip models we don't have configuration for
            continue
            
        default_marker = " (default)" if model == default_model else ""
        server_validated = " ✅" if model in available_models else ""
        print(f"{i}. {model}{default_marker}{server_validated} - {description}")

    while True:
        choice = input(f"\nSelect model (1-{len(display_models)}) or press Enter for default: ").strip()

        if choice == "":
            selected_model = default_model
            break
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(display_models):
                selected_model = display_models[idx]
                break
        
        print("❌ Invalid choice.")

    # System prompt selection
    print("\nSystem prompt options:")
    system_prompts = config_manager.get('ui.system_prompts', {})
    prompt_options = list(system_prompts.keys())
    
    for i, prompt_key in enumerate(prompt_options, 1):
        print(f"{i}. {prompt_key.title()}")
    print(f"{len(prompt_options) + 1}. Custom - Enter your own")

    while True:
        prompt_choice = input(f"\nSelect system prompt (1-{len(prompt_options) + 1}): ").strip()

        if prompt_choice.isdigit():
            idx = int(prompt_choice) - 1
            if 0 <= idx < len(prompt_options):
                prompt_key = prompt_options[idx]
                system_prompt = system_prompts[prompt_key]
                break
            elif idx == len(prompt_options):
                system_prompt = input("Enter your custom system prompt: ").strip()
                if system_prompt:
                    break
                else:
                    print("❌ System prompt cannot be empty.")
            else:
                print("❌ Invalid choice.")
        else:
            print("❌ Invalid choice.")

    # Conversation options
    print("\n💬 Conversation Options:")
    print("1. Start new conversation")
    print("2. Load existing conversation")
    print("3. Create from template")
    
    conversation = None
    while True:
        conv_choice = input("\nSelect option (1-3): ").strip()
        
        if conv_choice == "1":
            # New conversation - will be created in chat_with_model
            break
        elif conv_choice == "2":
            conversation = handle_load_conversation()
            if conversation:
                selected_model = conversation.metadata.model
                # Get system prompt from first message if it exists
                if conversation.messages and conversation.messages[0].role == "system":
                    system_prompt = conversation.messages[0].content
                break
            else:
                continue  # Try again
        elif conv_choice == "3":
            conversation = handle_create_from_template()
            if conversation:
                selected_model = conversation.metadata.model
                # Get system prompt from first message if it exists
                if conversation.messages and conversation.messages[0].role == "system":
                    system_prompt = conversation.messages[0].content
                break
            else:
                continue  # Try again
        else:
            print("❌ Invalid choice.")

    # Start the chat
    chat_with_model(model=selected_model, system_prompt=system_prompt, conversation=conversation)

if __name__ == "__main__":
    main()