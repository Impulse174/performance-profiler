"""
Модуль для профилирования производительности Python функций.

Предоставляет детальные метрики:
- Время выполнения (wall-clock и CPU time)
- Использование памяти (до/после, пиковое)
- Статистика GC
- Размер результата
- Анализ алгоритмической сложности через AST
"""

import time
import psutil
import tracemalloc
import gc
import logging
import asyncio
import sys
import ast
import inspect
import functools
import textwrap
from typing import Any, Callable, Optional, Tuple
from contextlib import contextmanager
from dataclasses import dataclass

from config import ProfilerConfig, get_config


@dataclass
class ProfileMetrics:
    """Структура для хранения метрик профилирования."""
    execution_time: float = 0.0
    cpu_time: float = 0.0
    memory_before_mb: float = 0.0
    memory_after_mb: float = 0.0
    peak_memory_mb: float = 0.0
    gc_count_change: int = 0
    result_size_bytes: Optional[int] = None
    time_complexity: str = "O(?)"
    space_complexity: str = "O(?)"


class PerformanceProfiler:
    """
    Профайлер производительности для Python функций.
    
    Измеряет:
    - Время выполнения (real и CPU)
    - Использование оперативной памяти
    - Пиковое потребление памяти
    - Активность сборщика мусора
    - Размер возвращаемого значения
    - Алгоритмическую сложность (статический анализ AST)
    """
    
    def __init__(self, config: Optional[ProfilerConfig] = None,
                 logger: Optional[logging.Logger] = None):
        """
        Инициализация профайлера.
        
        Args:
            config: Конфигурация профайлера. Если None, используется глобальная.
            logger: Логгер для вывода. Если None, создается консольный логгер
        """
        self.config = config or get_config()
        
        if logger is None:
            logging.basicConfig(
                level=getattr(logging, self.config.log_level, logging.INFO),
                format=self.config.log_format,
                datefmt=self.config.date_format,
                force=True  # Перезаписываем существующие конфиги
            )
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger
    
    def _analyze_complexity(self, func: Callable) -> Tuple[str, str]:
        """
        Статический анализ алгоритмической сложности через AST.
        
        Анализирует:
        - Временную сложность по количеству и вложенности циклов
        - Пространственную сложность по создаваемым структурам данных
        
        Args:
            func: Функция для анализа
            
        Returns:
            Кортеж (временная_сложность, пространственная_сложность)
            Возвращает "O(?)", если анализ не удался
        """
        try:
            source = inspect.getsource(func)
            # Убираем отступы — inspect.getsource для вложенных функций
            # возвращает код с leading whitespace, что ломает ast.parse
            source = textwrap.dedent(source)
            tree = ast.parse(source)
            
            # Анализ временной сложности
            time_complexity = self._analyze_time_complexity(tree)
            
            # Анализ пространственной сложности
            space_complexity = self._analyze_space_complexity(tree)
            
            return time_complexity, space_complexity
                
        except Exception as e:
            self.logger.debug(f"Не удалось проанализировать сложность: {e}")
            return "O(?)", "O(?)"
    
    def _analyze_time_complexity(self, tree: ast.AST) -> str:
        """
        Анализ временной сложности по AST дереву.
        
        Args:
            tree: AST дерево функции
            
        Returns:
            Строка с временной сложностью (например, "O(n)", "O(n²)")
        """
        # Считаем циклы и их вложенность
        loop_stack = []
        max_loop_depth = 0
        loop_nesting_levels = []
        
        class LoopVisitor(ast.NodeVisitor):
            def visit_For(self, node):
                nonlocal max_loop_depth
                current_depth = len(loop_stack)
                loop_stack.append(node)
                max_loop_depth = max(max_loop_depth, current_depth + 1)
                self.generic_visit(node)
                loop_stack.pop()
            
            def visit_While(self, node):
                nonlocal max_loop_depth
                current_depth = len(loop_stack)
                loop_stack.append(node)
                max_loop_depth = max(max_loop_depth, current_depth + 1)
                self.generic_visit(node)
                loop_stack.pop()
        
        LoopVisitor().visit(tree)
        
        # Определяем сложность по максимальной вложенности
        if max_loop_depth == 0:
            return "O(1)"
        elif max_loop_depth == 1:
            return "O(n)"
        elif max_loop_depth == 2:
            return "O(n²)"
        elif max_loop_depth == 3:
            return "O(n³)"
        else:
            return f"O(n^{max_loop_depth})"
    
    def _analyze_space_complexity(self, tree: ast.AST) -> str:
        """
        Анализ пространственной сложности по AST дереву.
        
        Args:
            tree: AST дерево функции
            
        Returns:
            Строка с пространственной сложностью
        """
        # Детекторы структур данных
        has_list_comp = False
        has_dict_comp = False
        has_set_comp = False
        has_large_allocation = False
        max_comp_depth = 0
        
        class MemoryVisitor(ast.NodeVisitor):
            def visit_ListComp(self, node):
                nonlocal has_list_comp, max_comp_depth
                has_list_comp = True
                depth = self._count_nesting(node, ast.ListComp)
                max_comp_depth = max(max_comp_depth, depth)
                self.generic_visit(node)
            
            def visit_DictComp(self, node):
                nonlocal has_dict_comp
                has_dict_comp = True
                self.generic_visit(node)
            
            def visit_SetComp(self, node):
                nonlocal has_set_comp
                has_set_comp = True
                self.generic_visit(node)
            
            def visit_Call(self, node):
                nonlocal has_large_allocation
                # Проверка на list(range(...)), dict(...) и т.д.
                if isinstance(node.func, ast.Name):
                    if node.func.id in ('list', 'dict', 'set', 'tuple'):
                        if node.args and isinstance(node.args[0], ast.Call):
                            if isinstance(node.args[0].func, ast.Name):
                                if node.args[0].func.id == 'range':
                                    has_large_allocation = True
                self.generic_visit(node)
            
            def _count_nesting(self, node, comp_type) -> int:
                """Считает глубину вложенности comprehensions."""
                count = 0
                for child in ast.walk(node):
                    if isinstance(child, comp_type) and child != node:
                        count += 1
                return count + 1
        
        MemoryVisitor().visit(tree)
        
        # Оценка пространственной сложности
        if max_comp_depth >= 3:
            return "O(n³)"
        elif max_comp_depth == 2:
            return "O(n²)"
        elif has_list_comp or has_dict_comp or has_set_comp or has_large_allocation:
            return "O(n)"
        else:
            return "O(1)"
    
    @contextmanager
    def _profiling_context(self):
        """
        Контекстный менеджер для сбора метрик.
        
        Yields:
            ProfileMetrics: Объект для накопления метрик
        """
        if not self.config.enable_profiling:
            yield
            return
        
        if self.config.trace_memory:
            tracemalloc.start()
        if self.config.gc_collect_before:
            gc.collect()
        
        proc = psutil.Process()
        mem_before = proc.memory_info().rss
        gc_before = sum(gc.get_count())
        cpu_before = time.process_time()
        t_start = time.perf_counter()
        
        try:
            yield
        finally:
            t_end = time.perf_counter()
            cpu_after = time.process_time()
            mem_after = proc.memory_info().rss
            
            peak = 0
            if self.config.trace_memory:
                _, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
            
            gc_after = sum(gc.get_count()) if self.config.trace_gc else gc_before
            
            # Сохраняем метрики
            self._metrics = ProfileMetrics(
                execution_time=t_end - t_start,
                cpu_time=cpu_after - cpu_before,
                memory_before_mb=mem_before / 1024**2,
                memory_after_mb=mem_after / 1024**2,
                peak_memory_mb=peak / 1024**2,
                gc_count_change=gc_after - gc_before,
            )
    
    def profile(self, func: Callable) -> Callable:
        """
        Декоратор для профилирования функции.
        
        Args:
            func: Функция для профилирования
            
        Returns:
            Обернутая функция с автоматическим профилированием
        """
        if asyncio.iscoroutinefunction(func):
            return self._async_wrapper(func)
        return self._sync_wrapper(func)
    
    def _async_wrapper(self, func: Callable) -> Callable:
        """
        Обертка для асинхронных функций.
        
        Args:
            func: Асинхронная функция
            
        Returns:
            Обернутая асинхронная функция
        """
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await self._run_profiled_async(func, *args, **kwargs)
        return wrapper
    
    def _sync_wrapper(self, func: Callable) -> Callable:
        """
        Обертка для синхронных функций.
        
        Args:
            func: Синхронная функция
            
        Returns:
            Обернутая синхронная функция
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return self._run_profiled_sync(func, *args, **kwargs)
        return wrapper
    
    def _finalize_metrics(self, func: Callable, result: Any) -> None:
        """
        Дополняет метрики размером результата и анализом сложности.
        
        Args:
            func: Профилируемая функция
            result: Результат выполнения функции
        """
        # Размер результата
        try:
            self._metrics.result_size_bytes = sys.getsizeof(result)
        except Exception:
            pass
        
        # Анализ сложности (если включён)
        if self.config.analyze_complexity and self.config.enable_ast_analysis:
            self._metrics.time_complexity, self._metrics.space_complexity = \
                self._analyze_complexity(func)
    
    def _log_metrics(self, func_name: str, metrics: ProfileMetrics) -> None:
        """
        Логирование метрик профилирования.
        
        Args:
            func_name: Имя функции
            metrics: Объект с метриками
        """
        self.logger.info(
            f"Функция: {func_name}\n"
            f"  Временная сложность: {metrics.time_complexity}\n"
            f"  Пространственная сложность: {metrics.space_complexity}\n"
            f"  Время выполнения: {metrics.execution_time:.6f} c\n"
            f"  CPU time: {metrics.cpu_time:.6f} c\n"
            f"  Память (до/после): {metrics.memory_before_mb:.2f} / {metrics.memory_after_mb:.2f} МБ\n"
            f"  Пиковая память: {metrics.peak_memory_mb:.2f} МБ\n"
            f"  Изменение GC count: {metrics.gc_count_change}\n"
            f"  Размер результата: {metrics.result_size_bytes if metrics.result_size_bytes else 'н/д'} байт\n"
            f"{'='*50}"
        )
    
    async def _run_profiled_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        Выполнение асинхронной функции с профилированием.
        
        Args:
            func: Асинхронная функция
            *args: Позиционные аргументы
            **kwargs: Именованные аргументы
            
        Returns:
            Результат выполнения функции
        """
        with self._profiling_context():
            try:
                result = await func(*args, **kwargs)
            except Exception as e:
                self.logger.exception(f"❌ Ошибка в {func.__name__}: {e}")
                raise
        
        self._finalize_metrics(func, result)
        self._log_metrics(func.__name__, self._metrics)
        
        return result
    
    def _run_profiled_sync(self, func: Callable, *args, **kwargs) -> Any:
        """
        Выполнение синхронной функции с профилированием.
        
        Args:
            func: Синхронная функция
            *args: Позиционные аргументы
            **kwargs: Именованные аргументы
            
        Returns:
            Результат выполнения функции
        """
        with self._profiling_context():
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                self.logger.exception(f"❌ Ошибка в {func.__name__}: {e}")
                raise
        
        self._finalize_metrics(func, result)
        self._log_metrics(func.__name__, self._metrics)
        
        return result


# Создание экземпляра профайлера для удобства использования
profiler = PerformanceProfiler()


# Совместимость с предыдущим API
def profile_it(func: Callable) -> Callable:
    """
    Декоратор для профилирования функции (совместимость с предыдущей версией).
    
    Args:
        func: Функция для профилирования
        
    Returns:
        Обернутая функция с профилированием
    """
    return profiler.profile(func)