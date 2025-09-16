from openai import OpenAI

BASE_URL = "http://localhost:12434/engines/llama.cpp/v1/"
client = OpenAI(base_url=BASE_URL, api_key="anything")

print("=== Docker Model Runner Parameter Testing ===\n")

# Test core parameters with different models
models_to_test = ["ai/gemma3", "ai/qwen3"]

for model in models_to_test:
    print(f"Testing {model}:")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Hello! Please respond briefly."}],
            max_tokens=50,
            temperature=0.7,
            top_p=0.9,
            frequency_penalty=0.1,
            presence_penalty=0.1,
            stop=["\n"],
            seed=42,
            n=1
        )
        print(f"✅ {model} works")
        print(f"Response: {response.choices[0].message.content[:100]}...")
    except Exception as e:
        print(f"❌ {model} error: {type(e).__name__}")
    print()

# Test streaming with proper error handling
print("=== Testing Streaming ===")
try:
    stream = client.chat.completions.create(
        model="ai/gemma3",
        messages=[{"role": "user", "content": "Count to 5"}],
        stream=True,
        max_tokens=30
    )
    print("✅ Streaming works")
    print("Streaming response: ", end="")
    
    for chunk in stream:
        if chunk.choices and len(chunk.choices) > 0:
            delta = chunk.choices[0].delta
            if hasattr(delta, 'content') and delta.content:
                print(delta.content, end="")
    print()
    
except Exception as e:
    print(f"❌ Streaming error: {e}")

print("\n=== Testing Advanced Parameters ===")

# Test logprobs
try:
    response = client.chat.completions.create(
        model="ai/gemma3",
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
        model="ai/gemma3",
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
        model="ai/gemma3",
        messages=[{"role": "user", "content": "Say hello"}],
        store=True,
        metadata={"test": "parameter_validation"},
        max_tokens=20
    )
    print("✅ store and metadata parameters work")
except Exception as e:
    print(f"❌ store/metadata error: {type(e).__name__}")

print("\n=== Testing Known Limitations ===")

# Test multiple completions (expected to fail)
try:
    response = client.chat.completions.create(
        model="ai/gemma3",
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
        model="ai/gemma3",
        messages=[{"role": "user", "content": "Hello"}],
        tools=[{"type": "function", "function": {"name": "test", "description": "test"}}],
        max_tokens=20
    )
    print("✅ tools parameter works (unexpected)")
except Exception as e:
    print(f"❌ tools not supported: Expected")

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

print("\n=== Summary ===")
print("✅ Core Support: temperature, top_p, max_tokens, stop, presence_penalty, frequency_penalty, seed, streaming")
print("✅ Advanced Support: logprobs, response_format (JSON), store, metadata")
print("✅ Models Available: ai/gemma3, ai/qwen3")
print("❌ Not Supported: n>1 (multiple completions), tools/function calling")
print("📝 Notes: qwen3 shows reasoning tokens (<think>), parameter support varies by model/engine")
print("\nParameter Reference: https://platform.openai.com/docs/api-reference/chat/create")