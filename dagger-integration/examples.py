"""
Example usage of Dagger + Docker Model Runner integration
Using Dagger's native LLM integration
"""

import asyncio
import dagger
from dmr import quick_analyze, generate_unit_tests, explain_file # type: ignore


async def native_llm_example():
    """Example using Dagger's native LLM integration"""
    async with dagger.Connection() as client:
        print("🤖 Using Dagger's Native LLM Integration")
        print("=" * 50)

        # Direct LLM usage
        result = await client.llm().with_prompt("Hello! Introduce yourself briefly.").sync()
        print("AI Response:", result)


async def code_analysis_example():
    """AI-powered code analysis"""
    async with dagger.Connection() as client:
        print("\n🔍 AI Code Analysis:")
        print("-" * 30)

        source = client.host().directory(".")
        analysis = await quick_analyze(source)
        print(analysis)


async def test_generation_example():
    """Generate unit tests with AI"""
    async with dagger.Connection() as client:
        print("\n🧪 Generating Tests:")
        print("-" * 25)

        source = client.host().directory("./src")
        test_dir = await generate_unit_tests(source)
        await test_dir.export("./generated-tests")
        print("✅ Tests exported to ./generated-tests/")


async def file_explanation_example():
    """Explain what a file does"""
    async with dagger.Connection() as client:
        print("\n📄 File Explanation:")
        print("-" * 25)

        source = client.host().directory(".")
        explanation = await explain_file(source, "main.py")
        print(explanation)


async def advanced_llm_example():
    """Advanced LLM usage with environment"""
    async with dagger.Connection() as client:
        print("\n🚀 Advanced LLM Example:")
        print("-" * 30)

        # Create environment for LLM to work with
        myenv = (
            client.env()
            .with_directory_input("source", client.host().directory(".")) # type: ignore
            .with_directory_output("result")
        )

        # Use LLM with the environment
        result = await (
            client.llm()
            .with_env(myenv)
            .with_prompt("Analyze the source directory and create a summary file in result")
            .sync()
        )

        print("Advanced analysis completed")


async def main():
    """Run all examples"""
    print("🤖 Dagger + Docker Model Runner Examples")
    print("Using Native LLM Integration")
    print("=" * 60)

    try:
        await native_llm_example()
        await code_analysis_example()
        await test_generation_example()
        await file_explanation_example()
        await advanced_llm_example()

        print("\n✅ All examples completed!")
        print("\n💡 Tips:")
        print("   - Use 'dagger' command for interactive shell")
        print("   - Try: llm | with-prompt 'your question' | sync")
        print("   - Models run locally via Docker Model Runner")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure Docker Model Runner is running and environment is configured")


if __name__ == "__main__":
    asyncio.run(main())