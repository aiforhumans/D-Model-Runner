#!/usr/bin/env python3
"""
Test Docker Model Runner API endpoints locally
"""

import requests
import json
import sys
import os
from datetime import datetime

# Try to import requests_unixsocket for Unix socket support
try:
    import requests_unixsocket
    UNIX_SOCKET_AVAILABLE = True
except ImportError:
    requests_unixsocket = None
    UNIX_SOCKET_AVAILABLE = False
    print("⚠️ requests-unixsocket not available. Install with: pip install requests-unixsocket")

def get_socket_path():
    """Get the Docker Model Runner Unix socket path"""
    if os.name == 'nt':  # Windows
        user_profile = os.environ.get('USERPROFILE', '')
        return os.path.join(user_profile, 'AppData', 'Local', 'Docker', 'run', 'inference-0.sock')
    else:  # Linux/Mac
        return "/var/run/docker.sock"

def test_api_endpoint(name, url, method='GET', data=None):
    """Test an API endpoint and return the result"""
    print(f"🔍 Testing {name}: {url}")

    try:
        if UNIX_SOCKET_AVAILABLE and requests_unixsocket and ('localhost:12434' in url or 'localhost/v1' in url) and os.name != 'nt':
            # Use Unix socket connection (Linux/Mac only)
            socket_path = get_socket_path()
            print(f"   🔌 Using Unix socket: {socket_path}")

            # Convert HTTP URL to Unix socket URL
            # requests_unixsocket expects: http+unix://socket_path/http/path
            path_part = url.replace('http://localhost:12434', '')
            unix_url = f'http+unix://{socket_path}{path_part}'
            session = requests_unixsocket.Session()
            adapter = requests_unixsocket.UnixAdapter()
            session.mount('http+unix://', adapter)

            try:
                if method == 'GET':
                    response = session.get(unix_url, timeout=10)
                elif method == 'POST':
                    headers = {'Content-Type': 'application/json'}
                    response = session.post(unix_url, json=data, headers=headers, timeout=30)
                else:
                    print(f"   ❌ Unsupported method: {method}")
                    return False, None
            except Exception as e:
                print(f"   ❌ Unix socket connection failed: {e}")
                return False, None
        elif os.name == 'nt' and ('localhost:12434' in url or 'localhost/v1' in url):
            # Use curl with Unix socket on Windows
            import subprocess
            socket_path = get_socket_path()
            print(f"   🔌 Using curl with Unix socket: {socket_path}")

            # Create a mock response object class
            class MockResponse:
                def __init__(self, text, status_code=200):
                    self.text = text
                    self.status_code = status_code
                def json(self):
                    return json.loads(self.text)

            try:
                if method == 'GET':
                    cmd = ['curl', '--unix-socket', socket_path, url]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        response_text = result.stdout
                        response = MockResponse(response_text)
                    else:
                        print(f"   ❌ curl failed: {result.stderr}")
                        return False, None
                elif method == 'POST' and data:
                    # Write JSON data to a temporary file
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                        json.dump(data, f)
                        temp_file = f.name

                    cmd = ['curl', '--unix-socket', socket_path, '-X', 'POST',
                           '-H', 'Content-Type: application/json',
                           '-d', f'@{temp_file}', url]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

                    # Clean up temp file
                    os.unlink(temp_file)

                    if result.returncode == 0:
                        response_text = result.stdout
                        response = MockResponse(response_text)
                    else:
                        print(f"   ❌ curl POST failed: {result.stderr}")
                        return False, None
                else:
                    print(f"   ❌ Unsupported method on Windows: {method}")
                    return False, None
            except Exception as e:
                print(f"   ❌ curl connection failed: {e}")
                return False, None
        else:
            # Use regular HTTP connection
            if method == 'GET':
                response = requests.get(url, timeout=10)
            elif method == 'POST':
                headers = {'Content-Type': 'application/json'}
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                print(f"   ❌ Unsupported method: {method}")
                return False, None

        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            try:
                result = response.json()
                print(f"   ✅ Success - {len(json.dumps(result))} bytes")
                return True, result
            except:
                print(f"   ✅ Success - {len(response.text)} bytes (non-JSON)")
                return True, response.text
        else:
            print(f"   ❌ Failed with status {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False, None

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Connection failed: {e}")
        return False, None

        if response.status_code == 200:
            try:
                result = response.json()
                print(f"   ✅ Success - {len(json.dumps(result))} bytes")
                return True, result
            except:
                print(f"   ✅ Success - {len(response.text)} bytes (non-JSON)")
                return True, response.text
        else:
            print(f"   ❌ Failed with status {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False, None

    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False, None

def main():
    """Test all Docker Model Runner API endpoints"""
    print("🧪 Testing Docker Model Runner API Endpoints")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    base_url = "http://localhost/v1"
    print(f"Base URL: {base_url}")
    print()

    # Test endpoints
    endpoints = [
        ("List Models", f"{base_url}/models", "GET"),
        ("Model Info (gemma3)", f"{base_url}/models/ai/gemma3", "GET"),
        ("Model Info (qwen3)", f"{base_url}/models/ai/qwen3", "GET"),
    ]

    results = {}
    success_count = 0

    for name, url, method in endpoints:
        success, data = test_api_endpoint(name, url, method)
        results[name] = {'success': success, 'data': data}
        if success:
            success_count += 1
        print()

    # Test chat completions if models are available
    if results["List Models"]['success']:
        models_data = results["List Models"]['data']
        if 'data' in models_data and models_data['data']:
            model_id = models_data['data'][0]['id']
            print("💬 Testing Chat Completions with model:", model_id)

            chat_data = {
                "model": model_id,
                "messages": [
                    {"role": "user", "content": "Hello! Please respond with just 'Hello from Docker Model Runner!'"}
                ],
                "max_tokens": 50,
                "temperature": 0.7
            }

            success, chat_result = test_api_endpoint(
                "Chat Completions",
                f"{base_url}/chat/completions",
                "POST",
                chat_data
            )

            if success and chat_result:
                success_count += 1
                if isinstance(chat_result, dict) and 'choices' in chat_result and chat_result['choices']:
                    try:
                        response_content = chat_result['choices'][0]['message']['content']
                        print(f"   🤖 AI Response: {response_content}")
                    except (KeyError, IndexError, TypeError) as e:
                        print(f"   ⚠️ Could not parse AI response: {e}")
                else:
                    print(f"   🤖 AI Response received ({len(str(chat_result))} chars)")
            print()

    # Summary
    print("📊 Test Summary")
    print("-" * 30)
    print(f"Total endpoints tested: {len(endpoints) + 1}")  # +1 for chat completions
    print(f"Successful: {success_count}")
    print(f"Failed: {len(endpoints) + 1 - success_count}")

    if success_count >= len(endpoints):
        print("✅ All core endpoints are working!")
        print()
        print("🚀 Ready for Dagger integration!")
        print("   Run: python dagger-integration/test.py")
    else:
        print("❌ Some endpoints failed. Check Docker Model Runner status.")
        print()
        print("🔧 Troubleshooting:")
        print("   1. Ensure Docker Model Runner is running: docker model ls")
        print("   2. Start a model: docker model run ai/gemma3")
        print("   3. Wait for model to load (may take several minutes)")
        print("   4. Check logs: docker logs <container-id>")

    return success_count >= len(endpoints)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)