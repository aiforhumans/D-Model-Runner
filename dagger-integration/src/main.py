"""
Dagger Module for Docker Model Runner Integration

This module leverages Dagger's native LLM integration with Docker Model Runner.
Based on: https://dagger.io/blog/docker-model-runner
"""

import dagger
from dagger import dag, function, object_type


@object_type
class AIModule:
    """AI module using Dagger's native LLM integration with Docker Model Runner."""

    @function
    async def analyze_code(
        self,
        source: dagger.Directory,
        task: str = "review"
    ) -> str:
        """Analyze code using Dagger's native LLM integration."""
        # Get source files
        files = await source.entries()
        code_files = [f for f in files if f.endswith(('.py', '.js', '.ts', '.go', '.rs'))]

        if not code_files:
            return "No code files found to analyze."

        # Read sample files
        analysis_content = ""
        for file_path in code_files[:2]:  # Limit for performance
            try:
                content = await source.file(file_path).contents()
                analysis_content += f"\n--- {file_path} ---\n{content[:500]}\n"
            except:
                continue

        if not analysis_content:
            return "Could not read source files."

        # Use Dagger's native LLM
        prompts = {
            "review": "Review this code for bugs, security issues, and best practices:",
            "document": "Generate documentation for this code:",
            "optimize": "Suggest performance optimizations for this code:"
        }

        prompt = prompts.get(task, prompts["review"])

        # Use Dagger's built-in LLM function
        result = await dag.llm().with_prompt(f"{prompt}\n\n{analysis_content}").sync()
        return result

    @function
    async def generate_tests(
        self,
        source: dagger.Directory,
        language: str = "python"
    ) -> dagger.Directory:
        """Generate unit tests using AI."""
        files = await source.entries()
        source_files = [f for f in files if f.endswith(f".{language}")]

        if not source_files:
            return source

        main_file = source_files[0]
        content = await source.file(main_file).contents()

        # Use Dagger's LLM to generate tests
        prompt = f"Generate comprehensive unit tests for this {language} code:\n\n{content}"
        test_code = await dag.llm().with_prompt(prompt).sync()

        test_filename = f"test_{main_file}"
        return source.with_new_file(test_filename, test_code)

    @function
    async def explain_code(
        self,
        source: dagger.Directory,
        file_path: str
    ) -> str:
        """Explain what a specific file does."""
        try:
            content = await source.file(file_path).contents()
            prompt = f"Explain what this code does in simple terms:\n\n{content[:1000]}"
            return await dag.llm().with_prompt(prompt).sync()
        except Exception as e:
            return f"Error reading file: {e}"

    @function
    async def suggest_improvements(
        self,
        source: dagger.Directory
    ) -> str:
        """Suggest improvements for the codebase."""
        files = await source.entries()
        code_files = [f for f in files if f.endswith(('.py', '.js', '.ts', '.go', '.rs'))]

        if not code_files:
            return "No code files found."

        # Sample a few files
        sample_content = ""
        for file_path in code_files[:3]:
            try:
                content = await source.file(file_path).contents()
                sample_content += f"\n--- {file_path} ---\n{content[:300]}\n"
            except:
                continue

        prompt = f"Suggest improvements for this codebase:\n\n{sample_content}"
        return await dag.llm().with_prompt(prompt).sync()


@function
def ai_module() -> AIModule:
    """Create an AI module instance."""
    return AIModule()


@function
async def quick_analyze(source: dagger.Directory) -> str:
    """Quick code analysis using Dagger's LLM."""
    module = AIModule()
    return await module.analyze_code(source, "review")


@function
async def generate_unit_tests(source: dagger.Directory) -> dagger.Directory:
    """Generate unit tests using AI."""
    module = AIModule()
    return await module.generate_tests(source, "python")


@function
async def explain_file(source: dagger.Directory, file_path: str) -> str:
    """Explain what a file does."""
    module = AIModule()
    return await module.explain_code(source, file_path)