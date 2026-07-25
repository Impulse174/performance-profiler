"""
Модульные тесты для профайлера производительности.

Запуск:
    python -m pytest tests/test_profiler.py -v
    или
    python -m unittest tests/test_profiler.py
"""

import unittest
import asyncio
import sys
from io import StringIO

# Добавляем корень проекта в path
sys.path.insert(0, '.')

from performance_inspect import PerformanceProfiler, ProfileMetrics
from auto_profile import auto_profile


class TestPerformanceProfiler(unittest.TestCase):
    """Тесты для класса PerformanceProfiler."""
    
    def setUp(self):
        """Подготовка к тесту."""
        self.profiler = PerformanceProfiler()
        self.output = StringIO()
    
    def test_sync_function_profiling(self):
        """Тест профилирования синхронной функции."""
        
        @auto_profile
        def simple_func(x, y):
            return x + y
        
        result = simple_func(2, 3)
        self.assertEqual(result, 5)
    
    def test_async_function_profiling(self):
        """Тест профилирования асинхронной функции."""
        
        @auto_profile
        async def async_func(delay):
            await asyncio.sleep(delay)
            return "done"
        
        async def run_test():
            result = await async_func(0.1)
            self.assertEqual(result, "done")
        
        asyncio.run(run_test())
    
    def test_complexity_analysis_constant_time(self):
        """Тест анализа сложности: O(1)."""
        
        @auto_profile
        def constant_func(n):
            return n * 2
        
        # Функция должна выполниться без ошибок
        result = constant_func(10)
        self.assertEqual(result, 20)
    
    def test_complexity_analysis_linear_time(self):
        """Тест анализа сложности: O(n)."""
        
        @auto_profile
        def linear_func(n):
            total = 0
            for i in range(n):
                total += i
            return total
        
        result = linear_func(100)
        self.assertEqual(result, 4950)
    
    def test_complexity_analysis_quadratic_time(self):
        """Тест анализа сложности: O(n²)."""
        
        @auto_profile
        def quadratic_func(n):
            total = 0
            for i in range(n):
                for j in range(n):
                    total += i * j
            return total
        
        result = quadratic_func(10)
        self.assertEqual(result, 2025)
    
    def test_memory_tracking(self):
        """Тест отслеживания памяти."""
        
        @auto_profile
        def memory_func(size):
            return [i for i in range(size)]
        
        result = memory_func(10000)
        self.assertEqual(len(result), 10000)
    
    def test_error_handling_in_profiled_function(self):
        """Тест обработки ошибок в профилируемой функции."""
        
        @auto_profile
        def error_func():
            raise ValueError("Test error")
        
        with self.assertRaises(ValueError):
            error_func()
    
    def test_large_result_formatting(self):
        """Тест форматирования больших результатов."""
        
        @auto_profile
        def large_list_func():
            return list(range(1_000_000))
        
        result = large_list_func()
        self.assertEqual(len(result), 1_000_000)
    
    def test_decorator_preserves_function_metadata(self):
        """Тест сохранения метаданных функции после декоратора."""
        
        @auto_profile
        def documented_func(x):
            """Это документированная функция."""
            return x * 2
        
        self.assertEqual(documented_func.__name__, "documented_func")
        self.assertIsNotNone(documented_func.__doc__)
    
    def test_multiple_calls_same_function(self):
        """Тест множественных вызовов одной функции."""
        
        @auto_profile
        def counter():
            return 1
        
        results = [counter() for _ in range(5)]
        self.assertEqual(results, [1, 1, 1, 1, 1])


class TestProfileMetrics(unittest.TestCase):
    """Тесты для структуры ProfileMetrics."""
    
    def test_metrics_creation(self):
        """Тест создания объекта метрик."""
        metrics = ProfileMetrics(
            execution_time=0.1,
            cpu_time=0.09,
            memory_before_mb=10.0,
            memory_after_mb=12.0,
            peak_memory_mb=15.0,
            gc_count_change=5,
            result_size_bytes=1024,
            time_complexity="O(n)",
            space_complexity="O(n)"
        )
        
        self.assertEqual(metrics.execution_time, 0.1)
        self.assertEqual(metrics.cpu_time, 0.09)
        self.assertEqual(metrics.time_complexity, "O(n)")


class TestAutoProfileDecorator(unittest.TestCase):
    """Тесты для декоратора auto_profile."""
    
    def test_auto_profile_with_args_and_kwargs(self):
        """Тест декоратора с аргументами и kwargs."""
        
        @auto_profile
        def func_with_all_args(a, b, c=10, **kwargs):
            return a + b + c + sum(kwargs.values())
        
        result = func_with_all_args(1, 2, c=5, x=3, y=4)
        self.assertEqual(result, 15)
    
    def test_auto_profile_recursive_function(self):
        """Тест декоратора с рекурсивной функцией."""
        
        @auto_profile
        def factorial(n):
            if n <= 1:
                return 1
            return n * factorial(n - 1)
        
        result = factorial(5)
        self.assertEqual(result, 120)


class TestEdgeCases(unittest.TestCase):
    """Тесты граничных случаев."""
    
    def test_empty_function(self):
        """Тест пустой функции."""
        
        @auto_profile
        def empty():
            pass
        
        result = empty()
        self.assertIsNone(result)
    
    def test_function_returning_none(self):
        """Тест функции возвращающей None."""
        
        @auto_profile
        def returns_none():
            return None
        
        result = returns_none()
        self.assertIsNone(result)
    
    def test_very_fast_function(self):
        """Тест очень быстрой функции."""
        
        @auto_profile
        def very_fast():
            return 42
        
        result = very_fast()
        self.assertEqual(result, 42)
    
    def test_generator_function(self):
        """Тест функции-генератора."""
        
        @auto_profile
        def gen_func(n):
            for i in range(n):
                yield i * 2
        
        result = list(gen_func(5))
        self.assertEqual(result, [0, 2, 4, 6, 8])


def run_tests():
    """Запуск всех тестов."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Добавляем все тесты
    suite.addTests(loader.loadTestsFromTestCase(TestPerformanceProfiler))
    suite.addTests(loader.loadTestsFromTestCase(TestProfileMetrics))
    suite.addTests(loader.loadTestsFromTestCase(TestAutoProfileDecorator))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    
    # Запускаем с verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
