#!/usr/bin/env python3
"""
D-Model-Runner Web UI
A Flask web interface for testing LLM models through the D-Model-Runner client.
"""

import sys
import os
import json
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

# Add the parent directory to sys.path to import dmr package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dmr.config import ConfigManager
    from dmr.storage import ConversationManager, TemplateManager
    import openai
except ImportError as e:
    print(f"Error importing dmr package: {e}")
    print("Make sure you're running this from the D-Model-Runner directory")
    sys.exit(1)

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# Initialize DMR components
config_manager = ConfigManager()
conversation_manager = ConversationManager()
template_manager = TemplateManager()

# Global variables for current state
current_model = None
openai_client = None

def initialize_client():
    """Initialize OpenAI client with current configuration"""
    global openai_client, current_model
    
    try:
        # Load default configuration
        config_manager.load_config('dev')  # Start with dev profile
        
        # Initialize OpenAI client
        base_url = config_manager.get_base_url()
        openai_client = openai.OpenAI(
            base_url=base_url,
            api_key="anything",  # Docker Model Runner placeholder
            timeout=30.0,
            max_retries=2
        )
        
        # Set default model
        current_model = config_manager.get_default_model()
        
        print(f"✅ Initialized client with base URL: {base_url}")
        print(f"✅ Default model: {current_model}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return False

def get_available_models():
    """Get list of available models from configuration"""
    try:
        # Get the available models list from configuration
        available_models = config_manager.get('api.models.available', [])
        
        # If no models found in config, provide fallbacks
        if not available_models:
            available_models = ['ai/gemma3', 'ai/qwen3']
            
        return available_models
    except Exception:
        return ['ai/gemma3', 'ai/qwen3']  # Fallback models

@app.route('/')
def index():
    """Main chat interface"""
    available_models = get_available_models()
    return render_template('chat.html', 
                         current_model=current_model,
                         available_models=available_models)

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat completion requests"""
    global current_model, openai_client
    
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Missing message in request'}), 400
        
        user_message = data['message']
        model = data.get('model', current_model)
        
        # Update current model if changed
        if model != current_model:
            current_model = model
            print(f"🔄 Switched to model: {current_model}")
        
        # Check if client is initialized
        if not openai_client:
            if not initialize_client():
                return jsonify({'error': 'Failed to initialize OpenAI client'}), 500
        
        # Get model configuration - only use basic OpenAI parameters
        try:
            model_config = config_manager.get_model_config(current_model)
            # Filter to only valid OpenAI parameters to avoid unexpected arguments
            valid_params = {
                'max_tokens': model_config.get('max_tokens', 500),
                'temperature': model_config.get('temperature', 0.7),
                'top_p': model_config.get('top_p', 0.9),
                'stream': False  # Disable streaming for basic implementation
            }
        except Exception as e:
            print(f"Warning: Could not get model config: {e}")
            # Use safe defaults
            valid_params = {
                'max_tokens': 500,
                'temperature': 0.7,
                'top_p': 0.9,
                'stream': False
            }
        
        # Create conversation with just the user message for now
        messages = [
            {"role": "user", "content": user_message}
        ]
        
        # Make API call to model
        response = openai_client.chat.completions.create(
            model=current_model,
            messages=messages,
            **valid_params
        )
        
        # Extract response
        if response.choices and response.choices[0].message:
            assistant_response = response.choices[0].message.content
        else:
            assistant_response = "No response received from model"
        
        # Save conversation (optional for basic testing)
        try:
            conversation = conversation_manager.create_conversation(
                title=f"Chat with {current_model}",
                model=current_model
            )
            conversation.add_message("user", user_message)
            conversation.add_message("assistant", assistant_response)
            conversation_manager.save_conversation(conversation)
        except Exception as e:
            print(f"Warning: Failed to save conversation: {e}")
        
        return jsonify({
            'response': assistant_response,
            'model': current_model,
            'success': True
        })
        
    except openai.APIConnectionError as e:
        error_msg = "Cannot connect to model server. Is Docker Model Runner running?"
        print(f"❌ Connection error: {e}")
        return jsonify({'error': error_msg, 'success': False}), 503
        
    except openai.APITimeoutError as e:
        error_msg = "Request timed out. Model may be loading or server is slow."
        print(f"❌ Timeout error: {e}")
        return jsonify({'error': error_msg, 'success': False}), 504
        
    except openai.APIStatusError as e:
        error_msg = f"API error: {e.status_code} - {e.response.text if hasattr(e, 'response') else str(e)}"
        print(f"❌ API error: {e}")
        return jsonify({'error': error_msg, 'success': False}), e.status_code
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ Unexpected error: {e}")
        return jsonify({'error': error_msg, 'success': False}), 500

@app.route('/api/models', methods=['GET'])
def models():
    """Get available models"""
    try:
        available_models = get_available_models()
        return jsonify({
            'models': available_models,
            'current_model': current_model,
            'success': True
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        # Try to initialize client if not already done
        if not openai_client:
            client_ok = initialize_client()
        else:
            client_ok = True
            
        return jsonify({
            'status': 'healthy' if client_ok else 'degraded',
            'client_initialized': client_ok,
            'current_model': current_model,
            'base_url': config_manager.get_base_url() if config_manager else 'unknown'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 Starting D-Model-Runner Web UI...")
    
    # Initialize the client on startup
    if initialize_client():
        print("✅ Client initialized successfully")
    else:
        print("⚠️ Client initialization failed - will retry on first request")
    
    print("🌐 Web UI will be available at: http://localhost:5000")
    print("📋 Available endpoints:")
    print("  - GET  /           - Main chat interface") 
    print("  - POST /api/chat   - Chat completion API")
    print("  - GET  /api/models - Get available models")
    print("  - GET  /api/health - Health check")
    
    app.run(debug=True, host='0.0.0.0', port=5000)