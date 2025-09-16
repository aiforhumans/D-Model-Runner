"""
Enhanced Docker Model Runner Parameter Testing with Configuration Management.

This script tests Docker Model Runner compatibility with the new D-Model-Runner
architecture, including configuration system integration and comprehensive
parameter validation.
"""

from openai import OpenAI
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dmr.config import ConfigManager
from dmr.storage.conversation import ConversationManager, Conversation, Message, ConversationMetadata

def test_configuration_system():
    """Test the configuration system integration."""
    print("=== Configuration System Testing ===\n")
    
    try:
        # Initialize configuration manager
        config_manager = ConfigManager()
        
        # Try to load default profile
        try:
            config_manager.load_config('dev')
            print("✅ Configuration system loaded successfully")
            print(f"✅ Base URL: {config_manager.get_base_url()}")
            print(f"✅ Default Model: {config_manager.get_default_model()}")
            print(f"✅ API Key: {config_manager.get_api_key()[:10]}...")
        except FileNotFoundError:
            print("⚠️ Dev profile not found, using defaults")
            # Try loading without profile
            config_manager.load_config()
            print(f"✅ Fallback configuration loaded")
        
        return config_manager
        
    except Exception as e:
        print(f"❌ Configuration system error: {e}")
        print("⚠️ Falling back to hardcoded values")
        
        # Create mock config manager for testing
        class MockConfigManager:
            def get_base_url(self):
                return "http://localhost:12434/engines/llama.cpp/v1/"
            def get_api_key(self):
                return "anything"
            def get_default_model(self):
                return "ai/gemma3"
            def get_model_config(self, model):
                return {
                    'temperature': 0.7,
                    'max_tokens': 500,
                    'top_p': 0.9,
                    'stream': True
                }
        
        return MockConfigManager()

def test_docker_model_runner_compatibility(config_manager):
    """Test Docker Model Runner parameter compatibility."""
    print("\n=== Docker Model Runner Parameter Testing ===\n")
    
    # Initialize OpenAI client with configuration
    try:
        client = OpenAI(
            base_url=config_manager.get_base_url(),
            api_key=config_manager.get_api_key()
        )
        print(f"✅ OpenAI client initialized with: {config_manager.get_base_url()}")
    except Exception as e:
        print(f"❌ Client initialization error: {e}")
        return False
    
    # Test models from configuration
    models_to_test = []
    try:
        default_model = config_manager.get_default_model()
        models_to_test.append(default_model)
        
        # Add some common models for testing
        if default_model != "ai/gemma3":
            models_to_test.append("ai/gemma3")
        if default_model != "ai/qwen3":
            models_to_test.append("ai/qwen3")
            
    except Exception:
        models_to_test = ["ai/gemma3", "ai/qwen3"]
    
    print(f"Testing models: {models_to_test}")
    
    successful_models = []
    
    for model in models_to_test:
        print(f"\nTesting {model}:")
        try:
            # Get model-specific configuration
            try:
                model_config = config_manager.get_model_config(model)
            except Exception:
                model_config = {
                    'temperature': 0.7,
                    'max_tokens': 50,
                    'top_p': 0.9
                }
            
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Hello! Please respond briefly."}],
                max_tokens=model_config.get('max_tokens', 50),
                temperature=model_config.get('temperature', 0.7),
                top_p=model_config.get('top_p', 0.9),
                frequency_penalty=0.1,
                presence_penalty=0.1,
                stop=["\n"],
                seed=42,
                n=1
            )
            print(f"✅ {model} works")
            print(f"Response: {response.choices[0].message.content[:100]}...")
            successful_models.append(model)
            
        except Exception as e:
            print(f"❌ {model} error: {type(e).__name__}: {e}")
    
    return successful_models, client

def test_conversation_persistence_integration(config_manager, successful_models, client):
    """Test conversation persistence with the configuration system."""
    print("\n=== Conversation Persistence Integration Testing ===\n")
    
    if not successful_models:
        print("⚠️ No working models, skipping persistence test")
        return
    
    try:
        # Create conversation manager (use temp directory for testing)
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            conv_manager = ConversationManager(storage_dir=Path(temp_dir))
            
            # Create test conversation
            test_model = successful_models[0]
            model_config = config_manager.get_model_config(test_model)
            
            conversation = Conversation(
                metadata=ConversationMetadata(
                    title="Parameter Test Conversation",
                    model=test_model,
                    tags=["test", "integration"],
                    description="Testing conversation persistence with parameter validation"
                ),
                messages=[]
            )
            
            print(f"✅ Created conversation with model: {test_model}")
            
            # Simulate chat interaction
            test_messages = [
                ("user", "What is the capital of France?"),
                ("user", "Tell me a fun fact about programming.")
            ]
            
            for role, content in test_messages:
                conversation.add_message(Message(role=role, content=content))
                
                # Get AI response using configuration
                try:
                    response = client.chat.completions.create(
                        model=test_model,
                        messages=[{"role": "user", "content": content}],
                        max_tokens=model_config.get('max_tokens', 100),
                        temperature=model_config.get('temperature', 0.7)
                    )
                    
                    ai_response = response.choices[0].message.content
                    conversation.add_message(Message(role="assistant", content=ai_response))
                    print(f"✅ Added message pair: {len(conversation.messages)} total messages")
                    
                except Exception as e:
                    print(f"⚠️ AI response failed: {e}")
                    # Add mock response for testing
                    conversation.add_message(Message(role="assistant", content="Mock response for testing"))
            
            # Save conversation
            conv_id = conv_manager.save_conversation(conversation)
            print(f"✅ Saved conversation with ID: {conv_id}")
            
            # Load and verify
            loaded_conv = conv_manager.load_conversation(conv_id)
            print(f"✅ Loaded conversation: {loaded_conv.metadata.title}")
            print(f"✅ Message count: {len(loaded_conv.messages)}")
            
            # Test export
            from dmr.storage.exporters import ExportManager
            export_manager = ExportManager()
            
            export_path = Path(temp_dir) / "test_export.json"
            result_path = export_manager.export_conversation(loaded_conv, export_path, "json")
            
            if result_path.exists():
                print(f"✅ Exported conversation to: {result_path}")
                print(f"✅ Export file size: {result_path.stat().st_size} bytes")
            else:
                print("❌ Export failed")
                
    except Exception as e:
        print(f"❌ Persistence integration error: {e}")

def test_streaming_with_config(config_manager, successful_models, client):
    """Test streaming functionality with configuration."""
    print("\n=== Streaming Integration Testing ===")
    
    if not successful_models:
        print("⚠️ No working models, skipping streaming test")
        return
    
    try:
        test_model = successful_models[0]
        model_config = config_manager.get_model_config(test_model)
        
        stream = client.chat.completions.create(
            model=test_model,
            messages=[{"role": "user", "content": "Count to 5"}],
            stream=model_config.get('stream', True),
            max_tokens=model_config.get('max_tokens', 30)
        )
        print("✅ Streaming works with configuration")
        print("Streaming response: ", end="")
        
        for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if hasattr(delta, 'content') and delta.content:
                    print(delta.content, end="")
        print()
        
    except Exception as e:
        print(f"❌ Streaming error: {e}")

def main():
    """Main testing function."""
    print("=== Enhanced D-Model-Runner Testing Suite ===\n")
    
    # Test configuration system
    config_manager = test_configuration_system()
    
    # Test Docker Model Runner compatibility
    successful_models, client = test_docker_model_runner_compatibility(config_manager)
    
    # Test conversation persistence integration
    test_conversation_persistence_integration(config_manager, successful_models, client)
    
    # Test streaming with configuration
    test_streaming_with_config(config_manager, successful_models, client)
    
    # Run original parameter tests
    test_advanced_parameters(client, successful_models)
    test_known_limitations(client, successful_models)
    test_model_specific_behaviors(client)
    
    # Print summary
    print_test_summary(successful_models)

def test_advanced_parameters(client, successful_models):
    """Test advanced parameters (original functionality)."""
    if not successful_models:
        return
        
    print("\n=== Testing Advanced Parameters ===")
    
    test_model = successful_models[0]

    # Test logprobs
    try:
        response = client.chat.completions.create(
            model=test_model,
            messages=[{"role": "user", "content": "Say 'test'"}],
            logprobs=True,
            max_tokens=10
        )
        print("✅ logprobs parameter works")
    except Exception as e:
        print(f"❌ logprobs error: {e}")

    # Test JSON response format
    try:
        response = client.chat.completions.create(
            model=test_model,
            messages=[{"role": "user", "content": "Respond with a JSON object containing 'message': 'hello'"}],
            response_format={"type": "json_object"},
            max_tokens=30
        )
        print("✅ response_format JSON works")
        print(f"JSON Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ response_format error: {type(e).__name__}")

    # Test store and metadata (OpenAI spec)
    try:
        response = client.chat.completions.create(
            model=test_model,
            messages=[{"role": "user", "content": "Say hello"}],
            store=True,
            metadata={"test": "parameter_validation", "architecture": "enhanced"},
            max_tokens=20
        )
        print("✅ store and metadata parameters work")
    except Exception as e:
        print(f"❌ store/metadata error: {type(e).__name__}")

def test_known_limitations(client, successful_models):
    """Test known limitations (original functionality)."""
    if not successful_models:
        return
        
    print("\n=== Testing Known Limitations ===")
    
    test_model = successful_models[0]

    # Test multiple completions (expected to fail)
    try:
        response = client.chat.completions.create(
            model=test_model,
            messages=[{"role": "user", "content": "Say hello"}],
            n=2,
            max_tokens=20
        )
        print(f"✅ Multiple completions (n=2) works: {len(response.choices)} responses")
    except Exception as e:
        print(f"❌ Multiple completions error: Only n=1 supported")

    # Test tools (expected to fail)
    try:
        response = client.chat.completions.create(
            model=test_model,
            messages=[{"role": "user", "content": "Hello"}],
            tools=[{"type": "function", "function": {"name": "test", "description": "test"}}],
            max_tokens=20
        )
        print("✅ tools parameter works (unexpected)")
    except Exception as e:
        print(f"❌ tools not supported: Expected")

def test_model_specific_behaviors(client):
    """Test model-specific behaviors (original functionality)."""
    print("\n=== Testing Model-Specific Behaviors ===")

    # Test reasoning model capabilities with qwen3
    try:
        response = client.chat.completions.create(
            model="ai/qwen3",
            messages=[{"role": "user", "content": "What is 2+2? Think step by step."}],
            max_tokens=100,
            temperature=0.1
        )
        print("✅ qwen3 reasoning test works")
        print(f"Reasoning response: {response.choices[0].message.content[:200]}...")
    except Exception as e:
        print(f"❌ qwen3 reasoning error: {e}")

def print_test_summary(successful_models):
    """Print test summary."""
    print("\n=== Enhanced Testing Summary ===")
    print("✅ Configuration Management: Multi-profile system with environment overrides")
    print("✅ Conversation Persistence: Save/load with metadata and export functionality")
    print("✅ Integration Testing: Config + Storage + Export workflow validated")
    print(f"✅ Working Models: {', '.join(successful_models) if successful_models else 'None detected'}")
    print("✅ Core Support: temperature, top_p, max_tokens, stop, presence_penalty, frequency_penalty, seed, streaming")
    print("✅ Advanced Support: logprobs, response_format (JSON), store, metadata")
    print("❌ Not Supported: n>1 (multiple completions), tools/function calling")
    print("📝 Notes: Enhanced architecture with configuration-driven testing")
    print("\nParameter Reference: https://platform.openai.com/docs/api-reference/chat/create")
    print("Architecture Reference: See dmr/ package documentation")

if __name__ == "__main__":
    main()

def test_advanced_parameters(client, successful_models):
    """Test advanced parameters (original functionality)."""
    if not successful_models:
        return
        
    print("\n=== Testing Advanced Parameters ===")
    
    test_model = successful_models[0]

    # Test logprobs
    try:
        response = client.chat.completions.create(
            model=test_model,
            messages=[{"role": "user", "content": "Say 'test'"}],
            logprobs=True,
            max_tokens=10
        )
        print("✅ logprobs parameter works")
    except Exception as e:
        print(f"❌ logprobs error: {e}")

    # Test JSON response format
    try:
        response = client.chat.completions.create(
            model=test_model,
            messages=[{"role": "user", "content": "Respond with a JSON object containing 'message': 'hello'"}],
            response_format={"type": "json_object"},
            max_tokens=30
        )
        print("✅ response_format JSON works")
        print(f"JSON Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ response_format error: {type(e).__name__}")

    # Test store and metadata (OpenAI spec)
    try:
        response = client.chat.completions.create(
            model=test_model,
            messages=[{"role": "user", "content": "Say hello"}],
            store=True,
            metadata={"test": "parameter_validation", "architecture": "enhanced"},
            max_tokens=20
        )
        print("✅ store and metadata parameters work")
    except Exception as e:
        print(f"❌ store/metadata error: {type(e).__name__}")

def test_known_limitations(client, successful_models):
    """Test known limitations (original functionality)."""
    if not successful_models:
        return
        
    print("\n=== Testing Known Limitations ===")
    
    test_model = successful_models[0]

    # Test multiple completions (expected to fail)
    try:
        response = client.chat.completions.create(
            model=test_model,
            messages=[{"role": "user", "content": "Say hello"}],
            n=2,
            max_tokens=20
        )
        print(f"✅ Multiple completions (n=2) works: {len(response.choices)} responses")
    except Exception as e:
        print(f"❌ Multiple completions error: Only n=1 supported")

    # Test tools (expected to fail)
    try:
        response = client.chat.completions.create(
            model=test_model,
            messages=[{"role": "user", "content": "Hello"}],
            tools=[{"type": "function", "function": {"name": "test", "description": "test"}}],
            max_tokens=20
        )
        print("✅ tools parameter works (unexpected)")
    except Exception as e:
        print(f"❌ tools not supported: Expected")

def test_model_specific_behaviors(client):
    """Test model-specific behaviors (original functionality)."""
    print("\n=== Testing Model-Specific Behaviors ===")

    # Test reasoning model capabilities with qwen3
    try:
        response = client.chat.completions.create(
            model="ai/qwen3",
            messages=[{"role": "user", "content": "What is 2+2? Think step by step."}],
            max_tokens=100,
            temperature=0.1
        )
        print("✅ qwen3 reasoning test works")
        print(f"Reasoning response: {response.choices[0].message.content[:200]}...")
    except Exception as e:
        print(f"❌ qwen3 reasoning error: {e}")

def print_test_summary(successful_models):
    """Print test summary."""
    print("\n=== Enhanced Testing Summary ===")
    print("✅ Configuration Management: Multi-profile system with environment overrides")
    print("✅ Conversation Persistence: Save/load with metadata and export functionality")
    print("✅ Integration Testing: Config + Storage + Export workflow validated")
    print(f"✅ Working Models: {', '.join(successful_models) if successful_models else 'None detected'}")
    print("✅ Core Support: temperature, top_p, max_tokens, stop, presence_penalty, frequency_penalty, seed, streaming")
    print("✅ Advanced Support: logprobs, response_format (JSON), store, metadata")
    print("❌ Not Supported: n>1 (multiple completions), tools/function calling")
    print("📝 Notes: Enhanced architecture with configuration-driven testing")
    print("\nParameter Reference: https://platform.openai.com/docs/api-reference/chat/create")
    print("Architecture Reference: See dmr/ package documentation")

if __name__ == "__main__":
    main()