from openai import OpenAI
from dmr.config import ConfigManager
from dmr.utils.helpers import validate_model_name, format_error_message
from dmr.storage import ConversationManager, TemplateManager, ExportManager
from pathlib import Path
from datetime import datetime

# Initialize configuration manager
config_manager = ConfigManager()

# Initialize storage managers
conversation_manager = ConversationManager()
template_manager = TemplateManager()
export_manager = ExportManager()

def initialize_client():
    """Initialize OpenAI client with configuration."""
    config = config_manager.load_config()
    base_url = config_manager.get_base_url()
    api_key = config_manager.get_api_key()
    
    return OpenAI(base_url=base_url, api_key=api_key)

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
    
    # Validate model name
    if not validate_model_name(model):
        print(f"❌ Invalid model name: {model}")
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
                
                response = client.chat.completions.create(
                    model=current_model,
                    messages=messages,
                    max_tokens=model_config.get('max_tokens', 500),
                    temperature=model_config.get('temperature', 0.7),
                    top_p=model_config.get('top_p', 0.9),
                    stream=model_config.get('stream', True)
                )

                # Stream the response
                assistant_response = ""
                for chunk in response:
                    if chunk.choices and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, 'content') and delta.content:
                            print(delta.content, end="", flush=True)
                            assistant_response += delta.content

                print()  # New line after streaming

                # Add assistant response to conversation and history
                conversation.add_message("assistant", assistant_response)
                messages = conversation.get_openai_messages()

            except Exception as e:
                error_msg = format_error_message(e, f"API call to {current_model}")
                print(f"\n❌ Error: {error_msg}")
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

def main():
    """
    Main function with model and profile selection
    """
    print("🚀 D-Model-Runner Chat Interface with Conversation Persistence")
    print("=" * 65)

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
    available_models = config_manager.get_available_models()
    default_model = config_manager.get_default_model()
    
    for i, model in enumerate(available_models, 1):
        model_config = config_manager.get_model_config(model)
        description = model_config.get('description', 'No description')
        default_marker = " (default)" if model == default_model else ""
        print(f"{i}. {model}{default_marker} - {description}")

    while True:
        choice = input(f"\nSelect model (1-{len(available_models)}) or press Enter for default: ").strip()

        if choice == "":
            selected_model = default_model
            break
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(available_models):
                selected_model = available_models[idx]
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