"""
Performance monitoring utilities for D-Model-Runner.

This module provides tools to measure and track performance metrics
across the application to identify optimization opportunities.
"""

import time
import functools
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from collections import defaultdict, deque
import json
from datetime import datetime


class PerformanceMetrics:
    """Thread-safe performance metrics collector."""
    
    def __init__(self, max_samples: int = 1000):
        """
        Initialize performance metrics collector.
        
        Args:
            max_samples: Maximum number of samples to keep per metric
        """
        self.max_samples = max_samples
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_samples))
        self._lock = threading.Lock()
        self._start_times: Dict[str, float] = {}
    
    def start_timer(self, operation: str) -> str:
        """
        Start timing an operation.
        
        Args:
            operation: Name of the operation being timed
            
        Returns:
            Timer ID for stopping the timer
        """
        timer_id = f"{operation}_{time.time()}"
        self._start_times[timer_id] = time.time()
        return timer_id
    
    def end_timer(self, timer_id: str, metadata: Optional[Dict[str, Any]] = None) -> float:
        """
        End timing an operation and record the duration.
        
        Args:
            timer_id: Timer ID returned from start_timer
            metadata: Optional metadata to store with the timing
            
        Returns:
            Duration in seconds
        """
        if timer_id not in self._start_times:
            return 0.0
        
        duration = time.time() - self._start_times[timer_id]
        operation = timer_id.split('_')[0]
        
        with self._lock:
            sample = {
                'duration': duration,
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            self._metrics[operation].append(sample)
        
        del self._start_times[timer_id]
        return duration
    
    def record_metric(self, operation: str, value: float, metadata: Optional[Dict[str, Any]] = None):
        """
        Record a metric value directly.
        
        Args:
            operation: Name of the operation
            value: Metric value
            metadata: Optional metadata
        """
        with self._lock:
            sample = {
                'value': value,
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            self._metrics[operation].append(sample)
    
    def get_stats(self, operation: str) -> Dict[str, Any]:
        """
        Get statistics for an operation.
        
        Args:
            operation: Operation name
            
        Returns:
            Dictionary with min, max, mean, count statistics
        """
        with self._lock:
            if operation not in self._metrics:
                return {'count': 0}
            
            samples = list(self._metrics[operation])
            if not samples:
                return {'count': 0}
            
            # Extract values (duration or value field)
            values = []
            for sample in samples:
                if 'duration' in sample:
                    values.append(sample['duration'])
                elif 'value' in sample:
                    values.append(sample['value'])
            
            if not values:
                return {'count': 0}
            
            return {
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'mean': sum(values) / len(values),
                'recent_samples': len([s for s in samples if self._is_recent(s['timestamp'], 300)])  # Last 5 minutes
            }
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all operations."""
        with self._lock:
            return {op: self.get_stats(op) for op in self._metrics.keys()}
    
    def export_metrics(self, output_path: Path) -> None:
        """Export all metrics to a JSON file."""
        with self._lock:
            export_data = {
                'exported_at': datetime.now().isoformat(),
                'metrics': {}
            }
            
            for operation, samples in self._metrics.items():
                export_data['metrics'][operation] = {
                    'samples': list(samples),
                    'stats': self.get_stats(operation)
                }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def clear_metrics(self) -> None:
        """Clear all collected metrics."""
        with self._lock:
            self._metrics.clear()
            self._start_times.clear()
    
    def _is_recent(self, timestamp_str: str, seconds: int) -> bool:
        """Check if timestamp is within the last N seconds."""
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            now = datetime.now()
            return (now - timestamp).total_seconds() <= seconds
        except Exception:
            return False


# Global metrics instance
performance_metrics = PerformanceMetrics()


def measure_performance(operation: str, include_args: bool = False):
    """
    Decorator to measure function execution time.
    
    Args:
        operation: Name of the operation being measured
        include_args: Whether to include function arguments in metadata
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Prepare metadata
            metadata = {}
            if include_args:
                metadata['args_count'] = len(args)
                metadata['kwargs_count'] = len(kwargs)
                # Include some safe argument info
                if args:
                    metadata['first_arg_type'] = type(args[0]).__name__
            
            timer_id = performance_metrics.start_timer(operation)
            try:
                result = func(*args, **kwargs)
                metadata['success'] = True
                return result
            except Exception as e:
                metadata['success'] = False
                metadata['error_type'] = type(e).__name__
                raise
            finally:
                performance_metrics.end_timer(timer_id, metadata)
        
        return wrapper
    return decorator


def track_cache_performance(cache_name: str):
    """
    Decorator to track cache hit/miss performance.
    
    Args:
        cache_name: Name of the cache being tracked
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Assume if result is returned quickly, it's a cache hit
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Heuristic: if operation takes less than 1ms, it's likely a cache hit
            is_cache_hit = duration < 0.001
            
            metadata = {
                'cache_hit': is_cache_hit,
                'duration': duration
            }
            
            operation = f"{cache_name}_{'hit' if is_cache_hit else 'miss'}"
            performance_metrics.record_metric(operation, duration, metadata)
            
            return result
        
        return wrapper
    return decorator


class PerformanceReport:
    """Generate performance reports from collected metrics."""
    
    @staticmethod
    def generate_summary() -> str:
        """Generate a summary report of all performance metrics."""
        stats = performance_metrics.get_all_stats()
        
        if not stats:
            return "📊 No performance metrics collected yet."
        
        lines = ["📊 Performance Summary", "=" * 40]
        
        # Group operations by category
        categories = {
            'Configuration': [k for k in stats.keys() if 'config' in k.lower()],
            'Conversation': [k for k in stats.keys() if 'conversation' in k.lower() or 'search' in k.lower()],
            'Export': [k for k in stats.keys() if 'export' in k.lower()],
            'API': [k for k in stats.keys() if 'chat' in k.lower() or 'api' in k.lower()],
            'Cache': [k for k in stats.keys() if 'cache' in k.lower() or 'hit' in k.lower() or 'miss' in k.lower()],
            'Other': []
        }
        
        # Add uncategorized operations to 'Other'
        categorized = set()
        for cat_ops in categories.values():
            categorized.update(cat_ops)
        categories['Other'] = [k for k in stats.keys() if k not in categorized]
        
        for category, operations in categories.items():
            if not operations:
                continue
                
            lines.append(f"\n🔍 {category}")
            lines.append("-" * 20)
            
            for operation in operations:
                op_stats = stats[operation]
                if op_stats['count'] > 0:
                    mean_ms = op_stats['mean'] * 1000
                    lines.append(f"  {operation:25} {op_stats['count']:4} calls, {mean_ms:6.2f}ms avg")
        
        # Performance recommendations
        lines.append(f"\n💡 Recommendations")
        lines.append("-" * 20)
        
        slow_operations = [(op, st) for op, st in stats.items() 
                          if st['count'] > 0 and st['mean'] > 0.1]  # > 100ms
        
        if slow_operations:
            lines.append("  ⚠️ Slow operations (>100ms average):")
            for op, st in sorted(slow_operations, key=lambda x: x[1]['mean'], reverse=True):
                lines.append(f"    {op}: {st['mean']*1000:.1f}ms")
        else:
            lines.append("  ✅ All operations performing well!")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_cache_report() -> str:
        """Generate a cache performance report."""
        stats = performance_metrics.get_all_stats()
        cache_ops = {k: v for k, v in stats.items() if 'cache' in k.lower() or 'hit' in k or 'miss' in k}
        
        if not cache_ops:
            return "📊 No cache metrics collected yet."
        
        lines = ["🗄️ Cache Performance Report", "=" * 40]
        
        # Group by cache name
        caches = defaultdict(dict)
        for op, stats_data in cache_ops.items():
            if '_hit' in op:
                cache_name = op.replace('_hit', '')
                caches[cache_name]['hits'] = stats_data
            elif '_miss' in op:
                cache_name = op.replace('_miss', '')
                caches[cache_name]['misses'] = stats_data
            else:
                caches[op]['other'] = stats_data
        
        for cache_name, cache_stats in caches.items():
            lines.append(f"\n📁 {cache_name}")
            lines.append("-" * 20)
            
            hits = cache_stats.get('hits', {}).get('count', 0)
            misses = cache_stats.get('misses', {}).get('count', 0)
            total = hits + misses
            
            if total > 0:
                hit_rate = (hits / total) * 100
                lines.append(f"  Hit Rate: {hit_rate:5.1f}% ({hits}/{total})")
                
                if 'hits' in cache_stats:
                    hit_time = cache_stats['hits'].get('mean', 0) * 1000
                    lines.append(f"  Hit Time: {hit_time:5.2f}ms avg")
                
                if 'misses' in cache_stats:
                    miss_time = cache_stats['misses'].get('mean', 0) * 1000
                    lines.append(f"  Miss Time: {miss_time:5.2f}ms avg")
            else:
                lines.append("  No cache activity recorded")
        
        return "\n".join(lines)