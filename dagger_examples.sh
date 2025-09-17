#!/usr/bin/env dagger shell
# Dagger Shell Examples with Docker Model Runner
# Based on: https://dagger.io/blog/docker-model-runner

echo "🤖 Dagger + Docker Model Runner Examples"
echo "========================================"

# Example 1: Simple LLM interaction
echo ""
echo "📝 Example 1: Simple AI Chat"
echo "----------------------------"
llm | with-prompt "Say hello and introduce yourself briefly" | sync

# Example 2: Code generation
echo ""
echo "💻 Example 2: Code Generation"
echo "------------------------------"
llm | with-prompt "Write a simple Python function to calculate fibonacci numbers" | sync

# Example 3: File creation with AI
echo ""
echo "📄 Example 3: AI File Creation"
echo "------------------------------"
myenv=$(env |
    with-directory-input "empty" $(directory) "empty directory to add new files to" |
    with-directory-output "full" "a directory containing the generated files")

llm |
    with-env $myenv |
    with-prompt "start with empty, add a simple Python hello world script, return as full" |
    env |
    output "full"

# Example 4: Code analysis
echo ""
echo "🔍 Example 4: Code Analysis"
echo "---------------------------"
llm |
    with-prompt "Analyze this Python code for potential improvements: def hello(): print('Hello World')" |
    sync

echo ""
echo "✅ Examples completed!"
echo "======================"
echo ""
echo "💡 Tips:"
echo "   - Use 'llm | model' to see current model"
echo "   - Use 'llm | with-model <model>' to switch models"
echo "   - Use 'sync' to execute LLM calls"
echo "   - Use 'env' to work with file systems"