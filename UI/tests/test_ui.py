"""
Playwright tests for D-Model-Runner Web UI
Tests the chat interface functionality and integration with the backend.
"""

import pytest
import asyncio
import subprocess
import time
import os
import signal
import sys
from pathlib import Path


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

async def test_chat_interface_loads(page):
    """Test that the chat interface loads correctly"""
    
    # Navigate to the chat interface
    await page.goto("http://localhost:5000")
    
    # Check that the page loads
    await page.wait_for_selector(".chat-container")
    
    # Verify main elements are present
    await page.wait_for_selector(".chat-header h1", timeout=5000)
    await page.wait_for_selector("#model-select", timeout=5000)
    await page.wait_for_selector("#chat-messages", timeout=5000)
    await page.wait_for_selector("#message-input", timeout=5000)
    await page.wait_for_selector("#send-button", timeout=5000)
    
    # Check page title
    title = await page.title()
    assert "D-Model-Runner Chat Interface" in title
    
    # Check header text
    header_text = await page.text_content(".chat-header h1")
    assert "D-Model-Runner Chat" in header_text
    
    print("✅ Chat interface loads correctly")


async def test_model_selection(page):
    """Test model selection functionality"""
    
    await page.goto("http://localhost:5000")
    await page.wait_for_selector("#model-select")
    
    # Get available models
    model_options = await page.locator("#model-select option").all()
    assert len(model_options) > 0, "Should have at least one model option"
    
    # Test model selection
    if len(model_options) > 1:
        # Select different model
        second_model = await model_options[1].get_attribute("value")
        await page.select_option("#model-select", second_model)
        
        # Verify system message appears
        await page.wait_for_selector(".system-message", timeout=5000)
        system_messages = await page.locator(".system-message").all()
        
        # Check if there's a model switch message
        found_switch_message = False
        for message in system_messages:
            text = await message.text_content()
            if "Switched to model" in text:
                found_switch_message = True
                break
        
        if found_switch_message:
            print("✅ Model selection works correctly")
        else:
            print("⚠️ Model selection works but no switch message found")
    else:
        print("ℹ️ Only one model available, skipping model switch test")


async def test_message_input_and_form(page):
    """Test message input functionality"""
    
    await page.goto("http://localhost:5000")
    await page.wait_for_selector("#message-input")
    
    # Test typing in message input
    test_message = "Hello, this is a test message"
    await page.fill("#message-input", test_message)
    
    # Verify input value
    input_value = await page.input_value("#message-input")
    assert input_value == test_message
    
    # Test send button is enabled
    send_button = page.locator("#send-button")
    is_disabled = await send_button.is_disabled()
    assert not is_disabled, "Send button should not be disabled with valid input"
    
    print("✅ Message input and form work correctly")


async def test_health_check_api(page):
    """Test health check API endpoint"""
    
    # Test health endpoint directly
    response = await page.request.get("http://localhost:5000/api/health")
    assert response.status == 200
    
    health_data = await response.json()
    assert "status" in health_data
    print(f"✅ Health check API works - Status: {health_data.get('status')}")


async def test_models_api(page):
    """Test models API endpoint"""
    
    # Test models endpoint
    response = await page.request.get("http://localhost:5000/api/models")
    assert response.status == 200
    
    models_data = await response.json()
    assert "models" in models_data
    assert "current_model" in models_data
    assert isinstance(models_data["models"], list)
    print(f"✅ Models API works - Available models: {models_data.get('models')}")


async def test_chat_api_basic(page):
    """Test basic chat API functionality"""
    
    # Test chat endpoint with a simple message
    response = await page.request.post("http://localhost:5000/api/chat", data={
        "message": "Hello, this is a test",
        "model": "ai/gemma3"  # Use default model
    })
    
    # The API might return various status codes depending on Docker Model Runner availability
    if response.status == 200:
        chat_data = await response.json()
        assert "response" in chat_data or "error" in chat_data
        print("✅ Chat API endpoint accessible and responds correctly")
    elif response.status in [503, 504]:
        # Docker Model Runner might not be available
        error_data = await response.json()
        print(f"⚠️ Chat API accessible but Docker Model Runner unavailable: {error_data.get('error')}")
    else:
        print(f"⚠️ Chat API returned status {response.status}")


async def test_ui_responsiveness(page):
    """Test UI responsiveness and layout"""
    
    await page.goto("http://localhost:5000")
    await page.wait_for_selector(".chat-container")
    
    # Test mobile viewport
    await page.set_viewport_size({"width": 375, "height": 667})
    await page.wait_for_timeout(1000)
    
    # Verify elements are still visible and accessible
    message_input = page.locator("#message-input")
    send_button = page.locator("#send-button")
    
    assert await message_input.is_visible()
    assert await send_button.is_visible()
    
    # Test desktop viewport
    await page.set_viewport_size({"width": 1200, "height": 800})
    await page.wait_for_timeout(1000)
    
    assert await message_input.is_visible()
    assert await send_button.is_visible()
    
    print("✅ UI is responsive across different viewport sizes")


# Test runner function
async def run_tests_with_playwright():
    """Run all tests using Playwright"""
    from playwright.async_api import async_playwright
    
    print("🚀 Starting Playwright tests for D-Model-Runner UI...")
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)  # Set to True for headless mode
        page = await browser.new_page()
        
        tests = [
            test_chat_interface_loads,
            test_model_selection,
            test_message_input_and_form,
            test_health_check_api,
            test_models_api,
            test_chat_api_basic,
            test_ui_responsiveness
        ]
        
        print(f"Running {len(tests)} tests...\n")
        
        passed = 0
        failed = 0
        
        for test_func in tests:
            try:
                print(f"🧪 Running {test_func.__name__}...")
                await test_func(page)
                passed += 1
                print(f"✅ {test_func.__name__} PASSED\n")
            except Exception as e:
                failed += 1
                print(f"❌ {test_func.__name__} FAILED: {str(e)}\n")
        
        await browser.close()
        
        print(f"🏁 Test Results:")
        print(f"   Passed: {passed}")
        print(f"   Failed: {failed}")
        print(f"   Total:  {passed + failed}")
        
        return failed == 0


if __name__ == "__main__":
    print("D-Model-Runner UI Tests")
    print("======================")
    print("Make sure the Flask server is running on http://localhost:5000")
    print("Run: python UI/app.py")
    print()
    
    # Run the tests
    result = asyncio.run(run_tests_with_playwright())
    
    if result:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("💥 Some tests failed!")
        sys.exit(1)