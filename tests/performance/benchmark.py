"""
Performance benchmarks for D-Model-Runner.

This module provides comprehensive performance testing and benchmarking
for all major components of the system.
"""

import time
import tempfile
import shutil
import statistics
from pathlib import Path
from typing import List, Dict, Any, Callable
import json
import yaml
import sys

# Optional dependency for enhanced memory monitoring
try:
    import psutil  # type: ignore  # Optional dependency
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None  # Set to None for type checking
    print("Note: psutil not available. Memory monitoring will be limited.")

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dmr.config import ConfigManager
from dmr.storage.conversation import ConversationManager, Conversation, Message, ConversationMetadata
from dmr.storage.templates import TemplateManager, Template
from dmr.storage.exporters import ExportManager


class PerformanceBenchmark:
    """Base class for performance benchmarks."""
    
    def __init__(self, name: str):
        self.name = name
        self.results = []
    
    def run_benchmark(self, func: Callable, iterations: int = 100, **kwargs) -> Dict[str, Any]:
        """Run a benchmark function multiple times and collect metrics."""
        print(f"\n🔄 Running benchmark: {self.name}")
        print(f"   Iterations: {iterations}")
        
        times = []
        memory_usage = []
        
        # Warmup run
        func(**kwargs)
        
        for i in range(iterations):
            # Measure memory before (if available)
            memory_before = 0
            if PSUTIL_AVAILABLE:
                process = psutil.Process()
                memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            # Measure execution time
            start_time = time.perf_counter()
            result = func(**kwargs)
            end_time = time.perf_counter()
            
            # Measure memory after (if available)
            memory_after = 0
            if PSUTIL_AVAILABLE:
                memory_after = process.memory_info().rss / 1024 / 1024  # MB
            
            execution_time = end_time - start_time
            memory_delta = memory_after - memory_before
            
            times.append(execution_time)
            memory_usage.append(memory_delta)
            
            if (i + 1) % 10 == 0:
                print(f"   Completed {i + 1}/{iterations} iterations...")
        
        # Calculate statistics
        result = {
            'name': self.name,
            'iterations': iterations,
            'execution_time': {
                'mean': statistics.mean(times),
                'median': statistics.median(times),
                'min': min(times),
                'max': max(times),
                'std_dev': statistics.stdev(times) if len(times) > 1 else 0
            },
            'memory_usage': {
                'mean': statistics.mean(memory_usage),
                'median': statistics.median(memory_usage),
                'min': min(memory_usage),
                'max': max(memory_usage),
                'std_dev': statistics.stdev(memory_usage) if len(memory_usage) > 1 else 0
            }
        }
        
        self.results.append(result)
        self.print_results(result)
        return result
    
    def print_results(self, result: Dict[str, Any]):
        """Print benchmark results."""
        exec_time = result['execution_time']
        memory = result['memory_usage']
        
        print(f"   ✅ Execution Time:")
        print(f"      Mean: {exec_time['mean']*1000:.2f}ms")
        print(f"      Median: {exec_time['median']*1000:.2f}ms")
        print(f"      Min: {exec_time['min']*1000:.2f}ms")
        print(f"      Max: {exec_time['max']*1000:.2f}ms")
        print(f"   📊 Memory Usage:")
        print(f"      Mean: {memory['mean']:.2f}MB")
        print(f"      Peak: {memory['max']:.2f}MB")


class ConfigBenchmarks:
    """Benchmarks for configuration system."""
    
    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        self.setup_test_configs()
    
    def setup_test_configs(self):
        """Set up test configuration files."""
        config_dir = self.temp_dir / 'config'
        config_dir.mkdir(exist_ok=True)
        
        profiles_dir = config_dir / 'profiles'
        profiles_dir.mkdir(exist_ok=True)
        
        # Create test profiles
        test_configs = {
            'small': {
                'api': {'base_url': 'http://localhost:12434', 'models': {'default': 'ai/test'}}
            },
            'medium': {
                'api': {
                    'base_url': 'http://localhost:12434',
                    'models': {
                        'default': 'ai/test',
                        'alternatives': ['ai/model1', 'ai/model2', 'ai/model3'],
                        'defaults': {
                            'temperature': 0.7,
                            'max_tokens': 500,
                            'top_p': 0.9
                        }
                    }
                },
                'logging': {'level': 'INFO', 'file': 'app.log'},
                'storage': {
                    'conversations_dir': '/path/to/conversations',
                    'templates_dir': '/path/to/templates'
                }
            },
            'large': {
                'api': {
                    'base_url': 'http://localhost:12434',
                    'models': {
                        'default': 'ai/test',
                        'alternatives': [f'ai/model{i}' for i in range(20)],
                        'defaults': {key: 0.5 for key in ['temperature', 'top_p', 'frequency_penalty', 'presence_penalty']}
                    }
                },
                'logging': {
                    'level': 'DEBUG',
                    'handlers': ['console', 'file', 'syslog'],
                    'formatters': {'detailed': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'}
                },
                'storage': {
                    'conversations_dir': '/path/to/conversations',
                    'templates_dir': '/path/to/templates',
                    'exports_dir': '/path/to/exports',
                    'backup_enabled': True,
                    'compression': True,
                    'retention_days': 365
                },
                'performance': {
                    'cache_size': 1000,
                    'batch_size': 50,
                    'connection_pool': 10
                }
            }
        }
        
        for name, config in test_configs.items():
            with open(profiles_dir / f'{name}.yaml', 'w') as f:
                yaml.dump(config, f)
        
        self.config_dir = config_dir
    
    def benchmark_config_loading(self, profile: str = 'medium'):
        """Benchmark configuration loading."""
        def load_config():
            manager = ConfigManager(config_dir=self.config_dir)
            manager.load_config(profile)
            return manager
        
        benchmark = PerformanceBenchmark(f"Configuration Loading ({profile})")
        return benchmark.run_benchmark(load_config, iterations=100)
    
    def benchmark_profile_switching(self):
        """Benchmark profile switching."""
        manager = ConfigManager(config_dir=self.config_dir)
        profiles = ['small', 'medium', 'large']
        
        def switch_profiles():
            for profile in profiles:
                manager.load_config(profile)
        
        benchmark = PerformanceBenchmark("Profile Switching")
        return benchmark.run_benchmark(switch_profiles, iterations=50)
    
    def benchmark_config_access(self):
        """Benchmark configuration value access."""
        manager = ConfigManager(config_dir=self.config_dir)
        manager.load_config('large')
        
        def access_config_values():
            # Access various configuration values
            manager.get('api.base_url')
            manager.get('api.models.default')
            manager.get('api.models.defaults.temperature')
            manager.get('logging.level')
            manager.get('storage.conversations_dir')
            manager.get('performance.cache_size')
            manager.get_default_model()
            manager.get_model_config('ai/test')
        
        benchmark = PerformanceBenchmark("Configuration Access")
        return benchmark.run_benchmark(access_config_values, iterations=1000)


class StorageBenchmarks:
    """Benchmarks for storage system."""
    
    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        self.storage_dir = temp_dir / 'storage'
        self.storage_dir.mkdir(exist_ok=True)
    
    def create_test_conversation(self, message_count: int = 10) -> Conversation:
        """Create a test conversation with specified message count."""
        conversation = Conversation(
            metadata=ConversationMetadata(
                title=f"Benchmark Conversation ({message_count} messages)",
                model="ai/benchmark",
                tags=["benchmark", "performance"],
                description="A conversation created for performance testing"
            )
        )
        
        for i in range(message_count):
            role = "user" if i % 2 == 0 else "assistant"
            content = f"Message {i+1}: " + "This is test content. " * 10  # ~200 chars per message
            conversation.add_message(role, content)
        
        return conversation
    
    def benchmark_conversation_save(self, message_count: int = 10):
        """Benchmark conversation saving."""
        manager = ConversationManager(storage_dir=self.storage_dir)
        
        def save_conversation():
            conv = self.create_test_conversation(message_count)
            conv_id = manager.save_conversation(conv)
            # Clean up
            manager.delete_conversation(conv_id)
            return conv_id
        
        benchmark = PerformanceBenchmark(f"Conversation Save ({message_count} messages)")
        return benchmark.run_benchmark(save_conversation, iterations=50)
    
    def benchmark_conversation_load(self, message_count: int = 10):
        """Benchmark conversation loading."""
        manager = ConversationManager(storage_dir=self.storage_dir)
        
        # Pre-create conversation
        conv = self.create_test_conversation(message_count)
        conv_id = manager.save_conversation(conv)
        
        def load_conversation():
            return manager.load_conversation(conv_id)
        
        benchmark = PerformanceBenchmark(f"Conversation Load ({message_count} messages)")
        result = benchmark.run_benchmark(load_conversation, iterations=100)
        
        # Clean up
        manager.delete_conversation(conv_id)
        return result
    
    def benchmark_conversation_search(self, conversation_count: int = 100):
        """Benchmark conversation search."""
        manager = ConversationManager(storage_dir=self.storage_dir)
        
        # Pre-create conversations
        conversation_ids = []
        for i in range(conversation_count):
            conv = Conversation(
                metadata=ConversationMetadata(
                    title=f"Search Test {i}",
                    model="ai/test",
                    tags=["search", f"batch{i//10}"]
                )
            )
            conv.add_message("user", f"Search content {i}")
            conv_id = manager.save_conversation(conv)
            conversation_ids.append(conv_id)
        
        def search_conversations():
            return manager.search_conversations("Search")
        
        benchmark = PerformanceBenchmark(f"Conversation Search ({conversation_count} conversations)")
        result = benchmark.run_benchmark(search_conversations, iterations=20)
        
        # Clean up
        for conv_id in conversation_ids:
            manager.delete_conversation(conv_id)
        
        return result
    
    def benchmark_bulk_operations(self, conversation_count: int = 50):
        """Benchmark bulk conversation operations."""
        manager = ConversationManager(storage_dir=self.storage_dir)
        
        def bulk_save_load():
            # Save multiple conversations
            conv_ids = []
            for i in range(conversation_count):
                conv = self.create_test_conversation(5)  # Small conversations for bulk test
                conv_id = manager.save_conversation(conv)
                conv_ids.append(conv_id)
            
            # Load all conversations
            loaded_convs = []
            for conv_id in conv_ids:
                loaded_conv = manager.load_conversation(conv_id)
                loaded_convs.append(loaded_conv)
            
            # Clean up
            for conv_id in conv_ids:
                manager.delete_conversation(conv_id)
            
            return len(loaded_convs)
        
        benchmark = PerformanceBenchmark(f"Bulk Operations ({conversation_count} conversations)")
        return benchmark.run_benchmark(bulk_save_load, iterations=5)


class ExportBenchmarks:
    """Benchmarks for export system."""
    
    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        self.export_dir = temp_dir / 'exports'
        self.export_dir.mkdir(exist_ok=True)
        self.export_manager = ExportManager()
    
    def create_large_conversation(self, message_count: int = 100) -> Conversation:
        """Create a large conversation for export testing."""
        conversation = Conversation(
            metadata=ConversationMetadata(
                title="Large Export Test Conversation",
                model="ai/export-test",
                tags=["export", "performance", "large"],
                description="A large conversation for testing export performance"
            )
        )
        
        for i in range(message_count):
            role = "user" if i % 2 == 0 else "assistant"
            # Create varied content lengths
            if i % 10 == 0:
                # Long message every 10th message
                content = f"Long message {i+1}: " + "This is a much longer message with more content. " * 20
            else:
                content = f"Message {i+1}: " + "Regular content. " * 5
            
            conversation.add_message(role, content)
        
        return conversation
    
    def benchmark_json_export(self, message_count: int = 100):
        """Benchmark JSON export."""
        conv = self.create_large_conversation(message_count)
        
        def export_json():
            output_path = self.export_dir / f"benchmark_{time.time()}.json"
            result_path = self.export_manager.export_conversation(conv, "json", output_path)
            # Clean up
            if result_path.exists():
                result_path.unlink()
            return result_path
        
        benchmark = PerformanceBenchmark(f"JSON Export ({message_count} messages)")
        return benchmark.run_benchmark(export_json, iterations=20)
    
    def benchmark_markdown_export(self, message_count: int = 100):
        """Benchmark Markdown export."""
        conv = self.create_large_conversation(message_count)
        
        def export_markdown():
            output_path = self.export_dir / f"benchmark_{time.time()}.md"
            result_path = self.export_manager.export_conversation(conv, "markdown", output_path)
            # Clean up
            if result_path.exists():
                result_path.unlink()
            return result_path
        
        benchmark = PerformanceBenchmark(f"Markdown Export ({message_count} messages)")
        return benchmark.run_benchmark(export_markdown, iterations=20)
    
    def benchmark_multi_format_export(self, message_count: int = 50):
        """Benchmark exporting to multiple formats."""
        conv = self.create_large_conversation(message_count)
        
        def export_multi_format():
            formats = ["json", "markdown"]
            exported_files = []
            
            for fmt in formats:
                output_path = self.export_dir / f"multi_{time.time()}.{fmt}"
                result_path = self.export_manager.export_conversation(conv, fmt, output_path)
                exported_files.append(result_path)
            
            # Clean up
            for file_path in exported_files:
                if file_path.exists():
                    file_path.unlink()
            
            return len(exported_files)
        
        benchmark = PerformanceBenchmark(f"Multi-format Export ({message_count} messages)")
        return benchmark.run_benchmark(export_multi_format, iterations=10)


def run_comprehensive_benchmarks():
    """Run all performance benchmarks."""
    print("🚀 D-Model-Runner Performance Benchmarks")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        all_results = []
        
        # Configuration benchmarks
        print("\n📁 Configuration System Benchmarks")
        config_bench = ConfigBenchmarks(temp_path)
        
        all_results.append(config_bench.benchmark_config_loading('small'))
        all_results.append(config_bench.benchmark_config_loading('medium'))
        all_results.append(config_bench.benchmark_config_loading('large'))
        all_results.append(config_bench.benchmark_profile_switching())
        all_results.append(config_bench.benchmark_config_access())
        
        # Storage benchmarks
        print("\n💾 Storage System Benchmarks")
        storage_bench = StorageBenchmarks(temp_path)
        
        # Test different conversation sizes
        for msg_count in [10, 50, 100]:
            all_results.append(storage_bench.benchmark_conversation_save(msg_count))
            all_results.append(storage_bench.benchmark_conversation_load(msg_count))
        
        all_results.append(storage_bench.benchmark_conversation_search(100))
        all_results.append(storage_bench.benchmark_bulk_operations(50))
        
        # Export benchmarks
        print("\n📤 Export System Benchmarks")
        export_bench = ExportBenchmarks(temp_path)
        
        for msg_count in [50, 100, 200]:
            all_results.append(export_bench.benchmark_json_export(msg_count))
            all_results.append(export_bench.benchmark_markdown_export(msg_count))
        
        all_results.append(export_bench.benchmark_multi_format_export(100))
        
        # Generate summary report
        generate_benchmark_report(all_results)


def generate_benchmark_report(results: List[Dict[str, Any]]):
    """Generate a comprehensive benchmark report."""
    print("\n📊 Benchmark Summary Report")
    print("=" * 50)
    
    # Overall performance metrics
    total_benchmarks = len(results)
    
    # Find fastest and slowest operations
    execution_times = [(r['name'], r['execution_time']['mean']) for r in results]
    execution_times.sort(key=lambda x: x[1])
    
    fastest = execution_times[0]
    slowest = execution_times[-1]
    
    print(f"\n📈 Performance Summary:")
    print(f"   Total benchmarks: {total_benchmarks}")
    print(f"   Fastest operation: {fastest[0]} ({fastest[1]*1000:.2f}ms)")
    print(f"   Slowest operation: {slowest[0]} ({slowest[1]*1000:.2f}ms)")
    
    # Category breakdown
    categories = {
        'Configuration': [r for r in results if 'Configuration' in r['name']],
        'Conversation': [r for r in results if 'Conversation' in r['name']],
        'Export': [r for r in results if 'Export' in r['name']],
        'Bulk': [r for r in results if 'Bulk' in r['name']]
    }
    
    print(f"\n📁 Performance by Category:")
    for category, cat_results in categories.items():
        if cat_results:
            avg_time = statistics.mean([r['execution_time']['mean'] for r in cat_results])
            avg_memory = statistics.mean([r['memory_usage']['mean'] for r in cat_results])
            print(f"   {category}:")
            print(f"     Average time: {avg_time*1000:.2f}ms")
            print(f"     Average memory: {avg_memory:.2f}MB")
    
    # Performance thresholds and recommendations
    print(f"\n⚡ Performance Analysis:")
    
    slow_operations = [r for r in results if r['execution_time']['mean'] > 0.1]  # > 100ms
    if slow_operations:
        print(f"   ⚠️  Slow operations (>100ms):")
        for op in slow_operations:
            print(f"      - {op['name']}: {op['execution_time']['mean']*1000:.2f}ms")
    
    memory_intensive = [r for r in results if r['memory_usage']['max'] > 5.0]  # > 5MB
    if memory_intensive:
        print(f"   📊 Memory-intensive operations (>5MB):")
        for op in memory_intensive:
            print(f"      - {op['name']}: {op['memory_usage']['max']:.2f}MB")
    
    # Performance recommendations
    print(f"\n💡 Optimization Recommendations:")
    
    if any(r['execution_time']['mean'] > 0.5 for r in results):
        print("   🔧 Consider implementing caching for slow operations")
    
    if any(r['memory_usage']['max'] > 10.0 for r in results):
        print("   🔧 Consider implementing lazy loading for memory-intensive operations")
    
    config_results = categories.get('Configuration', [])
    if config_results and any(r['execution_time']['mean'] > 0.05 for r in config_results):
        print("   🔧 Consider caching parsed configuration files")
    
    export_results = categories.get('Export', [])
    if export_results and any(r['execution_time']['mean'] > 1.0 for r in export_results):
        print("   🔧 Consider streaming export for large conversations")
    
    print(f"\n✅ Benchmark suite completed successfully!")
    print(f"   Total execution time: {sum(r['execution_time']['mean'] for r in results):.2f}s")


if __name__ == "__main__":
    run_comprehensive_benchmarks()