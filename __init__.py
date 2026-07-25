"""
Performance Profiler - Инструмент для анализа производительности Python кода.

Возможности:
- Профилирование времени выполнения (real/CPU)
- Отслеживание использования памяти
- Анализ алгоритмической сложности через AST
- Поддержка синхронных и асинхронных функций
- Детальная статистика по GC и размерам объектов

Пример использования:
    from performance import auto_profile
    
    @auto_profile
    def my_function():
        # ваш код
        pass
"""

__version__ = "2.0.0"
__author__ = "Performance Team"

from .performance_inspect import PerformanceProfiler, ProfileMetrics
from .auto_profile import auto_profile, apply_to_all_functions
from .config import ProfilerConfig, get_config, update_config, reset_config

__all__ = [
    'PerformanceProfiler',
    'ProfileMetrics',
    'auto_profile',
    'apply_to_all_functions',
    'ProfilerConfig',
    'get_config',
    'update_config',
    'reset_config',
]
