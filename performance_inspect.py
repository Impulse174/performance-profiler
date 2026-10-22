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
from typing import Any, Callable, Iterator, Optional, Tuple, Union
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from threading import RLock

if __package__:
    from .config import ProfilerConfig, get_config
else:
    from config import ProfilerConfig, get_config


_SCOPE_DISABLED = "отключено"
_SCOPE_SHARED = "общий сеанс трассировки процесса"

_trace_lock = RLock()
_trace_users = 0
_trace_owned = False


@contextmanager
def _tracing_session(start_if_needed: bool) -> Iterator[bool]:
    """Разделяет трассировку на весь процесс, не останавливая чужой сеанс."""
    global _trace_users, _trace_owned
    with _trace_lock:
        if _trace_users == 0:
            _trace_owned = not tracemalloc.is_tracing() and start_if_needed
            if _trace_owned:
                tracemalloc.start()
        active = tracemalloc.is_tracing()
        if active:
            _trace_users += 1
    try:
        yield active
    finally:
        if active:
            with _trace_lock:
                _trace_users -= 1
                if _trace_users == 0:
                    try:
                        if _trace_owned:
                            tracemalloc.stop()
                    finally:
                        _trace_owned = False


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
    peak_memory_scope: str = _SCOPE_DISABLED
    collection_error: Optional[str] = None


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
                 logger: Optional[logging.Logger] = None) -> None:
        """
        Инициализация профайлера.
        
        Args:
            config: Конфигурация профайлера. Если None, используется глобальная.
            logger: Логгер для вывода. Если None, создается консольный логгер
        """
        self.config = config or get_config()
        self._console_handler = None

        if logger is None:
            self.logger = logging.Logger(__name__, level=logging.DEBUG)
            handler = logging.StreamHandler()
            handler.setLevel(self.config.log_level)
            handler.setFormatter(logging.Formatter(
                self.config.log_format, datefmt=self.config.date_format
            ))
            self.logger.addHandler(handler)
            self._console_handler = handler
        else:
            self.logger = logger

    @staticmethod
    def _get_func_name(func: Callable) -> str:
        """Получает имя функции для логирования."""
        return getattr(func, '__name__', type(func).__name__)

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
            if len(tree.body) != 1 or not isinstance(
                tree.body[0], (ast.FunctionDef, ast.AsyncFunctionDef)
            ):
                return "O(?)", "O(?)"
            if inspect.isgeneratorfunction(func) or inspect.isasyncgenfunction(func):
                return "O(?)", "O(?)"
            tree = ast.Module(body=tree.body[0].body, type_ignores=[])

            # Анализ временной сложности
            time_complexity = self._analyze_time_complexity(tree)
            
            # Анализ пространственной сложности
            space_complexity = self._analyze_space_complexity(tree)
            
            return time_complexity, space_complexity
                
        except Exception as e:
            self.logger.debug("Не удалось проанализировать сложность: %s", e)
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
        max_loop_depth = 0

        class LoopVisitor(ast.NodeVisitor):
            """Обходчик AST для подсчёта максимальной вложенности циклов."""

            def __init__(self) -> None:
                self.depth = 0

            def visit_FunctionDef(self, node: ast.AST) -> None:
                return

            visit_AsyncFunctionDef = visit_FunctionDef
            visit_ClassDef = visit_FunctionDef
            visit_Lambda = visit_FunctionDef

            def visit_For(self, node: ast.AST) -> None:
                nonlocal max_loop_depth
                self.depth += 1
                max_loop_depth = max(max_loop_depth, self.depth)
                self.generic_visit(node)
                self.depth -= 1

            visit_While = visit_For
            visit_AsyncFor = visit_For

            def visit_ListComp(
                self, node: Union[ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp]
            ) -> None:
                nonlocal max_loop_depth
                previous_depth = self.depth
                for generator in node.generators:
                    self.visit(generator.iter)
                    self.depth += 1
                    max_loop_depth = max(max_loop_depth, self.depth)
                    for condition in generator.ifs:
                        self.visit(condition)
                if isinstance(node, ast.DictComp):
                    self.visit(node.key)
                    self.visit(node.value)
                else:
                    self.visit(node.elt)
                self.depth = previous_depth

            visit_SetComp = visit_ListComp
            visit_DictComp = visit_ListComp
            visit_GeneratorExp = visit_ListComp

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
        max_comp_depth = 0

        class MemoryVisitor(ast.NodeVisitor):
            """Обходчик AST для оценки пространственной сложности."""

            def __init__(self) -> None:
                self.depth = 0

            def visit_FunctionDef(self, node: ast.AST) -> None:
                return

            visit_AsyncFunctionDef = visit_FunctionDef
            visit_ClassDef = visit_FunctionDef
            visit_Lambda = visit_FunctionDef
            visit_GeneratorExp = visit_FunctionDef

            def visit_ListComp(
                self, node: Union[ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp]
            ) -> None:
                nonlocal max_comp_depth
                for generator in node.generators:
                    self.visit(generator.iter)
                    for condition in generator.ifs:
                        self.visit(condition)
                self.depth += len(node.generators)
                max_comp_depth = max(max_comp_depth, self.depth)
                if isinstance(node, ast.DictComp):
                    self.visit(node.key)
                    self.visit(node.value)
                else:
                    self.visit(node.elt)
                self.depth -= len(node.generators)

            visit_SetComp = visit_ListComp
            visit_DictComp = visit_ListComp

            def visit_Call(self, node: ast.Call) -> None:
                nonlocal max_comp_depth
                if (isinstance(node.func, ast.Name)
                        and node.func.id in ('list', 'dict', 'set', 'tuple')
                        and node.args and isinstance(node.args[0], ast.Call)
                        and isinstance(node.args[0].func, ast.Name)
                        and node.args[0].func.id == 'range'):
                    max_comp_depth = max(max_comp_depth, self.depth + 1)
                self.generic_visit(node)

        MemoryVisitor().visit(tree)
        
        # Оценка пространственной сложности
        if max_comp_depth > 3:
            return f"O(n^{max_comp_depth})"
        return ("O(1)", "O(n)", "O(n²)", "O(n³)")[max_comp_depth]
    
    @contextmanager
    def _profiling_context(self) -> Iterator[ProfileMetrics]:
        """
        Контекстный менеджер для сбора метрик.
        
        Yields:
            ProfileMetrics: Объект для накопления метрик
        """
        metrics = ProfileMetrics()
        if self._console_handler is not None:
            self._console_handler.setLevel(self.config.log_level)
        trace_gc = self.config.trace_gc
        proc = None
        gc_before = None
        tracing = False
        with ExitStack() as resources:
            try:
                if self.config.trace_memory:
                    tracing = resources.enter_context(
                        _tracing_session(self.config.force_tracemalloc)
                    )
                    if tracing:
                        metrics.peak_memory_scope = _SCOPE_SHARED
                if self.config.gc_collect_before:
                    gc.collect()
                if trace_gc:
                    gc_before = sum(gc.get_count())
                proc = psutil.Process()
                metrics.memory_before_mb = proc.memory_info().rss / 1024**2
            except Exception as exc:
                metrics.collection_error = str(exc)
                self.logger.warning("Инициализация профайлера не завершена: %s", exc)

            cpu_before = time.process_time()
            t_start = time.perf_counter()
            try:
                yield metrics
            finally:
                metrics.execution_time = time.perf_counter() - t_start
                metrics.cpu_time = time.process_time() - cpu_before
                try:
                    if tracing:
                        _, peak = tracemalloc.get_traced_memory()
                        metrics.peak_memory_mb = peak / 1024**2
                    if trace_gc and gc_before is not None:
                        metrics.gc_count_change = sum(gc.get_count()) - gc_before
                    if proc is not None:
                        metrics.memory_after_mb = proc.memory_info().rss / 1024**2
                except Exception as exc:
                    metrics.collection_error = str(exc)
                    self.logger.warning("Сбор метрик профайлера не завершён: %s", exc)
    
    def profile(self, func: Callable) -> Callable:
        """
        Декоратор для профилирования функции.
        
        Args:
            func: Функция для профилирования
            
        Returns:
            Обернутая функция с автоматическим профилированием
        """
        if not callable(func):
            raise TypeError("profile() ожидает вызываемый объект")
        if asyncio.iscoroutinefunction(func) or asyncio.iscoroutinefunction(
            getattr(func, "__call__", None)
        ):
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
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
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
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return self._run_profiled_sync(func, *args, **kwargs)
        return wrapper

    def _complete_profiling(self, func: Callable, result: Any,
                            metrics: ProfileMetrics) -> None:
        """
        Завершает цикл профилирования: дополняет метрики и пишет в лог.

        Args:
            func: Профилируемая функция
            result: Результат выполнения
            metrics: Накопленные метрики
        """
        self._finalize_metrics(func, result, metrics)
        self._log_metrics(self._get_func_name(func), metrics)

    def _finalize_metrics(self, func: Callable, result: Any, metrics: ProfileMetrics) -> None:
        """
        Дополняет метрики размером результата и анализом сложности.
        
        Args:
            func: Профилируемая функция
            result: Результат выполнения функции
            metrics: Объект метрик для дополнения
        """
        # Размер результата
        try:
            metrics.result_size_bytes = sys.getsizeof(result)
        except Exception:
            pass
        
        # Анализ сложности (если включён)
        if self.config.analyze_complexity and self.config.enable_ast_analysis:
            metrics.time_complexity, metrics.space_complexity = \
                self._analyze_complexity(func)
    
    def _log_metrics(self, func_name: str, metrics: ProfileMetrics) -> None:
        """
        Логирование метрик профилирования.
        
        Args:
            func_name: Имя функции
            metrics: Объект с метриками
        """
        if self._console_handler is not None:
            self._console_handler.setLevel(self.config.log_level)
            self._console_handler.setFormatter(logging.Formatter(
                self.config.log_format, datefmt=self.config.date_format
            ))
        # Ленивое форматирование: строка вычисляется только при реальном логировании
        result_size = (
            metrics.result_size_bytes
            if metrics.result_size_bytes is not None
            else 'н/д'
        )
        self.logger.info(
            "Функция: %s\n"
            "  Временная сложность: %s\n"
            "  Пространственная сложность: %s\n"
            "  Время выполнения: %.6f c\n"
            "  CPU time: %.6f c\n"
            "  Память (до/после): %.2f / %.2f МБ\n"
            "  Пиковая память: %.2f МБ\n"
            "  Изменение GC count: %d\n"
            "  Размер результата: %s байт\n"
            "  Область пиковой памяти: %s\n"
            "  Ошибка сбора: %s\n"
            "  Сложность: структурная оценка по AST, не доказанный Big-O\n"
            "%s",
            func_name,
            metrics.time_complexity,
            metrics.space_complexity,
            metrics.execution_time,
            metrics.cpu_time,
            metrics.memory_before_mb, metrics.memory_after_mb,
            metrics.peak_memory_mb,
            metrics.gc_count_change,
            result_size,
            metrics.peak_memory_scope,
            metrics.collection_error or 'нет',
            '=' * 50,
        )
    
    async def _run_profiled_async(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Выполнение асинхронной функции с профилированием.
        
        Args:
            func: Асинхронная функция
            *args: Позиционные аргументы
            **kwargs: Именованные аргументы
            
        Returns:
            Результат выполнения функции
        """
        if not self.config.enable_profiling:
            return await func(*args, **kwargs)
        with self._profiling_context() as metrics:
            result = await func(*args, **kwargs)
        self._complete_profiling(func, result, metrics)
        return result
    
    def _run_profiled_sync(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Выполнение синхронной функции с профилированием.
        
        Args:
            func: Синхронная функция
            *args: Позиционные аргументы
            **kwargs: Именованные аргументы
            
        Returns:
            Результат выполнения функции
        """
        if not self.config.enable_profiling:
            return func(*args, **kwargs)
        with self._profiling_context() as metrics:
            result = func(*args, **kwargs)
        self._complete_profiling(func, result, metrics)
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
