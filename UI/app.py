#!/usr/bin/env python3
"""
D-Model-Runner Web UI
A Flask web interface for testing LLM models through the D-Model-Runner client.
"""

import sys
import os
import json
import time
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
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
DMR_BASE_URL = "http://localhost:12434/engines/llama.cpp/v1/"  # Forced base URL per user request

def initialize_client():
    """Initialize OpenAI client with current configuration"""
    global openai_client, current_model
    
    try:
        # Load default configuration
        config_manager.load_config('dev')  # Start with dev profile
        
        # Initialize OpenAI client with forced base URL (ignore config)
        base_url = DMR_BASE_URL
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
    
    # Get available templates
    available_templates = []
    try:
        templates = template_manager.list_templates()
        available_templates = templates
    except Exception as e:
        print(f"Warning: Could not load templates: {e}")
    
    return render_template('chat.html', 
                         current_model=current_model,
                         available_models=available_models,
                         available_templates=available_templates)

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat completion requests (supports both streaming and non-streaming)"""
    global current_model, openai_client
    
    # Check if streaming is requested
    is_streaming = request.args.get('stream', 'false').lower() == 'true'
    
    if is_streaming:
        return chat_stream()
    
    # Non-streaming implementation (existing logic)
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
        
        # Get model configuration - enable streaming for better UX
        try:
            model_config = config_manager.get_model_config(current_model)
            # Filter to only valid OpenAI parameters to avoid unexpected arguments
            valid_params = {
                'max_tokens': model_config.get('max_tokens', 500),
                'temperature': model_config.get('temperature', 0.7),
                'top_p': model_config.get('top_p', 0.9),
                'stream': True  # Enable streaming for better user experience
            }
        except Exception as e:
            print(f"Warning: Could not get model config: {e}")
            # Use safe defaults
            valid_params = {
                'max_tokens': 500,
                'temperature': 0.7,
                'top_p': 0.9,
                'stream': True
            }
        
        # Create conversation with just the user message for now
        messages = [
            {"role": "user", "content": user_message}
        ]
        
        # Make API call to model (now with streaming enabled)
        try:
            response = openai_client.chat.completions.create(
                model=current_model,
                messages=messages,
                **valid_params
            )
            
            # Handle streaming response
            assistant_response = ""
            if hasattr(response, '__iter__'):  # Streaming response
                for chunk in response:
                    if chunk.choices and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        if delta.content:
                            assistant_response += delta.content
            else:  # Non-streaming response (fallback)
                if response.choices and response.choices[0].message:
                    assistant_response = response.choices[0].message.content
                else:
                    assistant_response = "No response received from model"
                    
        except Exception as e:
            print(f"❌ API call error: {e}")
            return jsonify({'error': f'API call failed: {str(e)}', 'success': False}), 500
        
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
            'base_url': DMR_BASE_URL
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """Handle streaming chat completion requests with Server-Sent Events"""
    global current_model, openai_client
    
    def generate():
        try:
            # Accept JSON or form-encoded bodies
            data = request.get_json(silent=True)
            if not data:
                if request.form:
                    data = request.form.to_dict()
                elif request.data:
                    try:
                        data = json.loads(request.data.decode('utf-8'))
                    except Exception:
                        data = {}
            
            if not data or 'message' not in data:
                yield f"data: {json.dumps({'error': 'Missing message in request', 'done': True})}\n\n"
                return
            
            user_message = data.get('message')
            selected_model = data.get('model') or current_model
            
            # Note: do not reassign global current_model inside generator to avoid scope issues
            if selected_model != current_model:
                print(f"🔄 Using non-default model for this request: {selected_model}")
            
            # Check if client is initialized
            if not openai_client:
                if not initialize_client():
                    yield f"data: {json.dumps({'error': 'Failed to initialize OpenAI client', 'done': True})}\n\n"
                    return
            
            # Get model configuration with streaming enabled
            try:
                model_config = config_manager.get_model_config(selected_model)
                valid_params = {
                    'max_tokens': model_config.get('max_tokens', 500),
                    'temperature': model_config.get('temperature', 0.7),
                    'top_p': model_config.get('top_p', 0.9),
                    'stream': True  # Enable streaming
                }
            except Exception as e:
                print(f"Warning: Could not get model config: {e}")
                valid_params = {
                    'max_tokens': 500,
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'stream': True
                }
            
            messages = [{"role": "user", "content": user_message}]
            
            # Send start event
            yield f"data: {json.dumps({'type': 'start', 'model': selected_model})}\n\n"
            
            # Make streaming API call
            full_response = ""
            try:
                response = openai_client.chat.completions.create(
                    model=selected_model,
                    messages=messages,
                    **valid_params
                )
                
                for chunk in response:
                    if chunk.choices and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        if delta.content:
                            content = delta.content
                            full_response += content
                            # Send content chunk
                            yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                
                # Send completion event
                yield f"data: {json.dumps({'type': 'done', 'full_response': full_response})}\n\n"
                
            except Exception as e:
                error_msg = f"Streaming error: {str(e)}"
                print(f"❌ Streaming error: {e}")
                yield f"data: {json.dumps({'error': error_msg})}\n\n"
            
            # Save conversation after streaming is complete
            try:
                conversation = conversation_manager.create_conversation(
                    title=f"Streaming Chat with {selected_model}",
                    model=selected_model
                )
                conversation.add_message("user", user_message)
                conversation.add_message("assistant", full_response)
                conversation_manager.save_conversation(conversation)
            except Exception as e:
                print(f"Warning: Failed to save conversation: {e}")
        
        except Exception as e:
            error_msg = f"Unexpected streaming error: {str(e)}"
            print(f"❌ Unexpected streaming error: {e}")
            yield f"data: {json.dumps({'error': error_msg, 'done': True})}\n\n"

    # Preserve the request context while streaming and set robust SSE headers
    resp = Response(stream_with_context(generate()), mimetype='text/event-stream')
    resp.headers["Cache-Control"] = "no-cache"
    resp.headers["X-Accel-Buffering"] = "no"  # Disable proxy buffering
    resp.headers["Connection"] = "keep-alive"
    return resp

@app.route('/debug', methods=['GET'])
def debug_page():
        """Lightweight in-app debugger to test health, models, and streaming."""
        html = """
        <!doctype html>
        <html>
        <head>
            <meta charset=\"utf-8\" />
            <title>DMR UI Debugger</title>
            <style>
                body{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:0;padding:16px;background:#0b0c0f;color:#e6e6e6}
                h1{margin:0 0 12px;font-size:20px}
                button{background:#2563eb;color:#fff;border:0;border-radius:6px;padding:8px 12px;margin-right:8px;cursor:pointer}
                button:disabled{opacity:.6;cursor:not-allowed}
                .row{margin:8px 0}
                .log{background:#0f172a;border:1px solid #1f2937;border-radius:8px;padding:12px;height:320px;overflow:auto;white-space:pre-wrap}
                input,select{background:#111827;color:#e5e7eb;border:1px solid #374151;border-radius:6px;padding:6px 8px}
            </style>
        </head>
        <body>
            <h1>DMR Web UI Debugger</h1>
            <div class=\"row\">
                <button id=\"btnHealth\">Check Health</button>
                <button id=\"btnModels\">Get Models</button>
            </div>
            <div class=\"row\">
                <input id=\"msg\" size=\"60\" placeholder=\"Type a message to stream...\" value=\"Say hello in one short sentence\" />
                <select id=\"model\"></select>
                <button id=\"btnStream\">Stream Chat</button>
                <button id=\"btnAbort\">Abort</button>
            </div>
            <div class=\"row\">
                <div id=\"log\" class=\"log\"></div>
            </div>
            <script>
                const log = (m)=>{const el=document.getElementById('log');el.textContent += `\n${new Date().toISOString()}  ${m}`;el.scrollTop=el.scrollHeight}
                let controller = null;
                async function populateModels(){
                    try{
                        const r = await fetch('/api/models');
                        const j = await r.json();
                        const sel = document.getElementById('model');
                        sel.innerHTML = '';
                        (j.models||[]).forEach(m=>{
                            const o=document.createElement('option');o.value=m;o.textContent=m;sel.appendChild(o);
                        });
                        if(j.current_model){ sel.value = j.current_model }
                        log(`Models loaded: ${JSON.stringify(j.models)}`)
                    }catch(e){ log(`Models error: ${e}`) }
                }
                async function doHealth(){
                    try{const r=await fetch('/api/health'); const j=await r.json(); log(`Health: ${JSON.stringify(j)}`)}catch(e){log(`Health error: ${e}`)}
                }
                async function streamChat(){
                    try{
                        controller = new AbortController();
                        const msg = document.getElementById('msg').value;
                        const model = document.getElementById('model').value;
                        log(`Starting stream... model=${model}`);
                        const r = await fetch('/api/chat/stream',{
                            method:'POST',
                            signal: controller.signal,
                            headers:{'Content-Type':'application/json'},
                            body: JSON.stringify({message: msg, model})
                        });
                        if(!r.ok){ log(`Stream HTTP ${r.status}`); return }
                        const reader = r.body.getReader();
                        const decoder = new TextDecoder();
                        let buf = '';
                        while(true){
                            const {value, done} = await reader.read();
                            if(done) break;
                            const chunk = decoder.decode(value, {stream:true});
                            buf += chunk;
                            // Parse SSE lines
                            const lines = buf.split(/\r?\n\r?\n/);
                            buf = lines.pop();
                            for(const block of lines){
                                const m = block.match(/^data: (.*)$/m);
                                if(m){
                                    try{ const evt = JSON.parse(m[1]); log(`event: ${evt.type||'chunk'} => ${evt.content||evt.full_response||evt.error||''}`)}
                                    catch(e){ log(`chunk: ${m[1]}`) }
                                }
                            }
                        }
                        log('Stream finished');
                    }catch(e){ log(`Stream error: ${e}`) }
                }
                document.getElementById('btnHealth').onclick = doHealth;
                document.getElementById('btnModels').onclick = populateModels;
                document.getElementById('btnStream').onclick = streamChat;
                document.getElementById('btnAbort').onclick = ()=>{ if(controller){controller.abort(); log('Aborted')} };
                populateModels();
            </script>
        </body>
        </html>
        """
        return Response(html, mimetype='text/html')

@app.route('/api/templates/<template_id>', methods=['GET'])
def get_template(template_id):
    """Get template details by ID"""
    try:
        template = template_manager.get_template(template_id)
        if template:
            return jsonify({
                'id': template.id,
                'metadata': template.metadata,
                'messages': template.messages,
                'default_model': template.default_model,
                'model_config': template.model_config,
                'success': True
            })
        else:
            return jsonify({'error': 'Template not found', 'success': False}), 404
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

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