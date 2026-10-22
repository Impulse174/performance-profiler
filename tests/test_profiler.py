"""
Модульные тесты для профайлера производительности.

Запуск:
    python -m pytest performance/tests/test_profiler.py -v
    или
    python -m unittest discover -s performance/tests -t . -p test_profiler.py
"""

import unittest
import asyncio
import importlib
import json
import logging
import os
import subprocess
import sys
import tempfile
import textwrap
import tracemalloc
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from dataclasses import asdict
from io import StringIO
from pathlib import Path
from threading import Barrier, Lock
from types import SimpleNamespace
from unittest.mock import Mock, patch

from performance import config as config_module
from performance import performance_inspect as profiler_module
from performance.performance_inspect import PerformanceProfiler, ProfileMetrics
from performance.auto_profile import auto_profile, apply_to_all_functions
from performance.config import ProfilerConfig

PERFORMANCE_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PERFORMANCE_ROOT.parent


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
            return list(range(4096))
        
        result = large_list_func()
        self.assertEqual(len(result), 4096)
    
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


def run_python(*args, clean_path=False):
    """Запускает дочерний Python-процесс без байткода и с явным окружением."""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    if clean_path:
        env["PYTHONPATH"] = str(WORKSPACE_ROOT)
    return subprocess.run(
        [sys.executable, *map(str, args)], cwd=WORKSPACE_ROOT, env=env,
        capture_output=True, text=True, encoding="utf-8", timeout=5,
    )


class TestPackageIsolation(unittest.TestCase):
    def test_package_import_from_workspace_without_legacy_path(self):
        result = run_python("-c", textwrap.dedent("""
            from performance import PerformanceProfiler, auto_profile
            from performance import ProfilerConfig, get_config
            from performance import profile_cli
            assert PerformanceProfiler.__module__ == 'performance.performance_inspect'
            assert PerformanceProfiler(logger=__import__('logging').getLogger('test')).config is get_config()
        """), clean_path=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_package_import_and_profiler_leave_root_logging_unchanged(self):
        # Разделяющий сабтест: НЕ полагается на legacy-обход через PYTHONPATH.
        result = run_python("-c", textwrap.dedent("""
            import logging
            root = logging.getLogger()
            handler = logging.StreamHandler()
            root.handlers[:] = [handler]
            root.setLevel(logging.ERROR)
            from performance import PerformanceProfiler
            assert root.handlers == [handler], 'import подменил root-хендлеры'
            assert root.level == logging.ERROR, 'import изменил root-уровень'
            PerformanceProfiler()
            assert root.handlers == [handler], 'конструктор подменил root-хендлеры'
            assert root.level == logging.ERROR, 'конструктор изменил root-уровень'
        """))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class ProfilerRegressionCase(unittest.TestCase):
    def setUp(self):
        # Каждый кейс владения стартует из простоя и возвращает состояние вызывающего.
        frames = tracemalloc.get_traceback_limit() if tracemalloc.is_tracing() else None
        tracemalloc.stop()
        if frames is not None:
            self.addCleanup(tracemalloc.start, frames)
        self.addCleanup(tracemalloc.stop)
        self.config = ProfilerConfig(gc_collect_before=False, analyze_complexity=False)
        self.logger = Mock(spec=logging.Logger)
        self.profiler = PerformanceProfiler(config=self.config, logger=self.logger)
        process = Mock()
        process.memory_info.return_value = SimpleNamespace(rss=4096)
        self.enterContext(patch.object(profiler_module.psutil, "Process", return_value=process))


class TestProfilerLifecycle(ProfilerRegressionCase):
    def _assert_disabled(self, asynchronous, raises):
        self.config.enable_profiling = False
        token, error = object(), ValueError("ошибка пользователя")
        calls = []

        def body():
            calls.append("body")
            if raises:
                raise error
            return token

        async def async_body():
            return body()

        with ExitStack() as stack:
            probes = [stack.enter_context(patch.object(owner, name)) for owner, name in (
                (profiler_module.psutil, "Process"), (profiler_module.gc, "collect"),
                (profiler_module.gc, "get_count"), (profiler_module.time, "perf_counter"),
                (profiler_module.time, "process_time"), (tracemalloc, "start"),
                (tracemalloc, "stop"), (tracemalloc, "get_traced_memory"),
                (self.profiler, "_analyze_complexity"), (self.profiler, "_finalize_metrics"),
                (self.profiler, "_log_metrics"),
            )]
            wrapped = self.profiler.profile(async_body if asynchronous else body)
            if raises:
                with self.assertRaises(ValueError) as caught:
                    asyncio.run(wrapped()) if asynchronous else wrapped()
                self.assertIs(caught.exception, error)
            else:
                result = asyncio.run(wrapped()) if asynchronous else wrapped()
                self.assertIs(result, token)
            self.assertEqual(calls, ["body"])
            self.assertEqual(self.logger.mock_calls, [])
            for probe in probes:
                probe.assert_not_called()

    def test_disabled_sync_returns_without_instrumentation_or_logging(self):
        self._assert_disabled(False, False)

    def test_disabled_async_returns_without_instrumentation_or_logging(self):
        self._assert_disabled(True, False)

    def test_disabled_sync_exception_is_unchanged_and_not_logged(self):
        self._assert_disabled(False, True)

    def test_disabled_async_exception_is_unchanged_and_not_logged(self):
        self._assert_disabled(True, True)

    def _assert_nested_tracing(self, other):
        observed = []

        @other.profile
        def inner():
            observed.append(tracemalloc.is_tracing())
            return 7

        @self.profiler.profile
        def outer():
            observed.append(tracemalloc.is_tracing())
            result = inner()
            observed.append(tracemalloc.is_tracing())
            return result

        result = outer()
        self.assertEqual((result, observed, tracemalloc.is_tracing()), (7, [True] * 3, False))

    def test_nested_same_profiler_preserves_outer_tracing(self):
        self._assert_nested_tracing(self.profiler)

    def test_nested_different_profilers_preserve_outer_tracing(self):
        other = PerformanceProfiler(config=self.config, logger=self.logger)
        self._assert_nested_tracing(other)

    def test_borrowed_external_tracer_remains_running_on_success_and_error(self):
        for raises in (False, True):
            with self.subTest(raises=raises):
                tracemalloc.start(3)
                error = ValueError("ошибка пользователя")

                @self.profiler.profile
                def body():
                    if raises:
                        raise error
                    return 7

                if raises:
                    with self.assertRaises(ValueError) as caught:
                        body()
                    self.assertIs(caught.exception, error)
                else:
                    self.assertEqual(body(), 7)
                self.assertTrue(tracemalloc.is_tracing())
                self.assertEqual(tracemalloc.get_traceback_limit(), 3)

    def test_force_tracemalloc_false_does_not_start_idle_tracer(self):
        self.config.force_tracemalloc = False
        with patch.object(tracemalloc, "start", wraps=tracemalloc.start) as start:
            observed = self.profiler.profile(tracemalloc.is_tracing)()
        self.assertEqual((observed, tracemalloc.is_tracing(), start.call_count), (False, False, 0))

    def test_trace_memory_mutation_during_body_does_not_leak(self):
        @self.profiler.profile
        def body():
            active = tracemalloc.is_tracing()
            self.config.trace_memory = False
            return active

        observed = body()
        self.assertEqual((observed, tracemalloc.is_tracing()), (True, False))

    def _assert_probe_failures(self, asynchronous, raises):
        for phase in ("constructor", "setup", "teardown"):
            with self.subTest(phase=phase):
                process = Mock()
                memory = SimpleNamespace(rss=4096)
                failure = profiler_module.psutil.AccessDenied(pid=1)
                process.memory_info.side_effect = [failure, memory] if phase == "setup" else [memory, failure]
                kwargs = {"side_effect": failure} if phase == "constructor" else {"return_value": process}
                token, error, calls = object(), ValueError("ошибка пользователя"), []

                def body():
                    calls.append("body")
                    if raises:
                        raise error
                    return token

                async def async_body():
                    return body()

                wrapped = self.profiler.profile(async_body if asynchronous else body)
                result = caught = None
                try:
                    with patch.object(profiler_module.psutil, "Process", **kwargs):
                        try:
                            result = asyncio.run(wrapped()) if asynchronous else wrapped()
                        except BaseException as exc:
                            caught = exc
                    self.assertEqual(
                        (result, caught, calls, tracemalloc.is_tracing()),
                        (None if raises else token, error if raises else None, ["body"], False),
                    )
                finally:
                    tracemalloc.stop()

    def test_psutil_failures_preserve_sync_result_and_release_tracing(self):
        self._assert_probe_failures(False, False)

    def test_psutil_failures_preserve_sync_exception_and_release_tracing(self):
        self._assert_probe_failures(False, True)

    def test_psutil_failures_preserve_async_result_and_release_tracing(self):
        self._assert_probe_failures(True, False)

    def test_psutil_failures_preserve_async_exception_and_release_tracing(self):
        self._assert_probe_failures(True, True)


class TestProfilerConcurrency(ProfilerRegressionCase):
    def _assert_async_overlap(self, cancel_first, different):
        other = PerformanceProfiler(config=self.config, logger=self.logger) if different else self.profiler

        async def scenario():
            entered = [asyncio.Event(), asyncio.Event()]
            release = [asyncio.Event(), asyncio.Event()]

            async def body(index):
                entered[index].set()
                await release[index].wait()
                return index

            tasks = []
            try:
                tasks.append(asyncio.create_task(self.profiler.profile(body)(0)))
                await asyncio.wait_for(entered[0].wait(), 1)
                tasks.append(asyncio.create_task(other.profile(body)(1)))
                await asyncio.wait_for(entered[1].wait(), 1)
                both_active = tracemalloc.is_tracing()
                if cancel_first:
                    tasks[0].cancel()
                    with self.assertRaises(asyncio.CancelledError):
                        await asyncio.wait_for(tasks[0], 1)
                else:
                    release[0].set()
                    self.assertEqual(await asyncio.wait_for(tasks[0], 1), 0)
                survivor_active = tracemalloc.is_tracing()
                release[1].set()
                self.assertEqual(await asyncio.wait_for(tasks[1], 1), 1)
                return both_active, survivor_active, tracemalloc.is_tracing()
            finally:
                for task in tasks:
                    if not task.done():
                        task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)

        observed = asyncio.run(asyncio.wait_for(scenario(), 3))
        self.assertEqual(observed, (True, True, False))

    def test_overlapping_async_calls_preserve_surviving_tracer(self):
        for different in (False, True):
            with self.subTest(different_profilers=different):
                self._assert_async_overlap(False, different)

    def test_cancelled_async_call_preserves_survivor_and_releases_last_owner(self):
        for different in (False, True):
            with self.subTest(different_profilers=different):
                self._assert_async_overlap(True, different)

    def test_cancelled_only_task_releases_owned_tracing(self):
        async def scenario():
            entered = asyncio.Event()

            @self.profiler.profile
            async def body():
                entered.set()
                await asyncio.Event().wait()

            task = asyncio.create_task(body())
            try:
                await asyncio.wait_for(entered.wait(), 1)
                self.assertTrue(tracemalloc.is_tracing())
                task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await asyncio.wait_for(task, 1)
            finally:
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)

        asyncio.run(scenario())
        self.assertFalse(tracemalloc.is_tracing())

    def test_threaded_overlap_logs_distinct_per_call_metrics(self):
        self.config.trace_memory = False
        barrier, lock, captured = Barrier(2), Lock(), {}
        finalize = PerformanceProfiler._finalize_metrics

        def gated_finalize(profiler, func, result, metrics):
            # Обе копии контекста должны завершиться до финализации метрик.
            barrier.wait(timeout=1)
            return finalize(profiler, func, result, metrics)

        def capture(name, metrics):
            with lock:
                captured[name] = metrics

        def small():
            return b"x"

        def larger():
            return b"x" * 64

        with patch.object(PerformanceProfiler, "_finalize_metrics", new=gated_finalize):
            with patch.object(self.profiler, "_log_metrics", side_effect=capture):
                with ThreadPoolExecutor(max_workers=2) as executor:
                    first = executor.submit(self.profiler.profile(small))
                    second = executor.submit(self.profiler.profile(larger))
                    self.assertEqual((first.result(timeout=2), second.result(timeout=2)), (small(), larger()))
        self.assertEqual(set(captured), {"small", "larger"})
        self.assertIsNot(captured["small"], captured["larger"])
        self.assertEqual(
            {name: metrics.result_size_bytes for name, metrics in captured.items()},
            {"small": sys.getsizeof(small()), "larger": sys.getsizeof(larger())},
        )


class TestConfigRegression(unittest.TestCase):
    def setUp(self):
        self.config = ProfilerConfig()
        self.enterContext(patch.object(config_module, "default_config", self.config))

    def test_invalid_config_updates_are_atomic(self):
        for invalid in ({"log_level": "INVALID"}, {"max_result_length": 99}):
            with self.subTest(invalid=invalid):
                before = asdict(self.config)
                with self.assertRaises(ValueError):
                    config_module.update_config(enable_profiling=False, **invalid)
                self.assertEqual(asdict(self.config), before)

    def test_unknown_config_update_is_atomic(self):
        before = asdict(self.config)
        with self.assertRaises(AttributeError):
            config_module.update_config(enable_profiling=False, unknown_option=True)
        self.assertEqual(asdict(self.config), before)

    def test_reset_config_preserves_singleton_and_existing_profiler_identity(self):
        profiler = PerformanceProfiler(logger=Mock(spec=logging.Logger))
        explicit = PerformanceProfiler(config=self.config, logger=Mock(spec=logging.Logger))
        config_module.update_config(enable_profiling=False, log_level="ERROR")
        config_module.reset_config()
        self.assertIs(config_module.get_config(), self.config)
        self.assertIs(profiler.config, self.config)
        self.assertIs(explicit.config, self.config)
        self.assertEqual(asdict(self.config), asdict(ProfilerConfig()))


class TestComplexityRegression(ProfilerRegressionCase):
    def test_simple_function_has_constant_time_and_space(self):
        def body(n):
            return n + 1

        self.assertEqual(self.profiler._analyze_complexity(body), ("O(1)", "O(1)"))

    def test_simple_loop_has_linear_time_and_constant_space(self):
        def body(n):
            total = 0
            for i in range(n):
                total += i
            return total

        self.assertEqual(self.profiler._analyze_complexity(body), ("O(n)", "O(1)"))

    def test_nested_loops_have_quadratic_time_and_constant_space(self):
        def body(n):
            total = 0
            for i in range(n):
                for j in range(n):
                    total += i * j
            return total

        self.assertEqual(self.profiler._analyze_complexity(body), ("O(n²)", "O(1)"))

    def test_list_comprehension_has_linear_time_and_space(self):
        def body(n):
            return [i for i in range(n)]

        self.assertEqual(self.profiler._analyze_complexity(body), ("O(n)", "O(n)"))

    def test_cartesian_comprehension_counts_all_generators(self):
        def body(n):
            return [(i, j) for i in range(n) for j in range(n)]

        self.assertEqual(self.profiler._analyze_complexity(body), ("O(n²)", "O(n²)"))

    def test_nested_comprehension_has_quadratic_time_and_space(self):
        def body(n):
            return [[j for j in range(n)] for i in range(n)]

        self.assertEqual(self.profiler._analyze_complexity(body), ("O(n²)", "O(n²)"))

    def test_sibling_comprehensions_do_not_multiply_depth(self):
        def body(n):
            return [i for i in range(n)], [j for j in range(n)]

        self.assertEqual(self.profiler._analyze_complexity(body), ("O(n)", "O(n)"))

    def test_nested_sibling_comprehensions_use_maximum_not_sum_of_depths(self):
        def body(n):
            return [([j for j in range(n)], [k for k in range(n)]) for i in range(n)]

        self.assertEqual(self.profiler._analyze_complexity(body), ("O(n²)", "O(n²)"))

    def test_unused_nested_function_does_not_contribute_time_or_space(self):
        def body(n):
            def unused():
                for i in range(n):
                    for j in range(n):
                        pass
                return [[j for j in range(n)] for i in range(n)]
            return 1

        self.assertEqual(self.profiler._analyze_complexity(body), ("O(1)", "O(1)"))


class TestApplyToAllFunctions(ProfilerRegressionCase):
    def setUp(self):
        super().setUp()
        module = importlib.import_module("performance.auto_profile")
        self.enterContext(patch.object(module, "_profiler", self.profiler))

        def local(value=3):
            return value * 2

        self.local = local
        self.namespace = {"__name__": __name__, "local": local, "imported": json.dumps}

    def test_apply_skips_imported_functions(self):
        apply_to_all_functions(self.namespace)
        self.assertIs(self.namespace["imported"], json.dumps)

    def test_apply_wraps_and_profiles_existing_local_functions(self):
        with patch.object(self.profiler, "_log_metrics") as log:
            apply_to_all_functions(self.namespace)
            result = self.namespace["local"](4)
        self.assertEqual(result, 8)
        self.assertIsNot(self.namespace["local"], self.local)
        self.assertEqual(log.call_count, 1)

    def test_apply_is_idempotent(self):
        apply_to_all_functions(self.namespace)
        wrapped = self.namespace["local"]
        apply_to_all_functions(self.namespace)
        self.assertIs(self.namespace["local"], wrapped)

    def test_apply_does_not_rewrap_explicitly_decorated_local_function(self):
        wrapped = auto_profile(self.local)
        self.namespace["local"] = wrapped
        apply_to_all_functions(self.namespace)
        self.assertIs(self.namespace["local"], wrapped)


class TestCLIProcesses(unittest.TestCase):
    def _run_cli(self, mode, *args):
        prefix = [PERFORMANCE_ROOT / "profile_cli.py"] if mode == "direct" else ["-m", "performance.profile_cli"]
        return run_python(*prefix, *args)

    def _assert_statuses(self, cases):
        for mode in ("direct", "module"):
            for args, expected in cases:
                with self.subTest(mode=mode, args=args):
                    result = self._run_cli(mode, *args)
                    self.assertEqual(result.returncode, expected, result.stdout + result.stderr)

    def test_direct_and_module_success_exit_zero(self):
        self._assert_statuses([(["math", "factorial", "5"], 0)])

    def test_direct_and_module_runtime_errors_exit_one(self):
        self._assert_statuses([
            (["math", "factorial", "-1"], 1),
            (["profiler_nonexistent_module_xyz", "missing"], 1),
            (["math", "nonexistent_function_xyz"], 1),
        ])

    def test_direct_and_module_usage_errors_exit_two(self):
        self._assert_statuses([([], 2), (["math"], 2), (["--unknown-option"], 2)])

    def test_direct_and_module_kwargs_require_valid_json_object(self):
        self._assert_statuses([
            (["json", "dumps", "{}", "--kwargs", value], 2)
            for value in ("{", "[]", "null", '"text"', "1", "true")
        ])

    def test_direct_and_module_preserve_json_keyword_strings(self):
        for mode in ("direct", "module"):
            with self.subTest(mode=mode):
                result = self._run_cli(mode, "json", "dumps", '{"x":1}', "--kwargs", '{"indent":"true"}')
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('{\ntrue"x": 1\n}', result.stdout)

    def test_file_executes_main_with_filename_argv_and_sibling_import(self):
        with tempfile.TemporaryDirectory(dir=PERFORMANCE_ROOT) as directory:
            script = Path(directory) / "entry.py"
            (Path(directory) / "profiler_regression_sibling.py").write_text("VALUE = 37\n", encoding="utf-8")
            script.write_text(textwrap.dedent("""
                import json
                import sys
                from pathlib import Path
                from profiler_regression_sibling import VALUE
                if __name__ == '__main__':
                    print('SCRIPT_CONTEXT=' + json.dumps([
                        __name__, str(Path(__file__).resolve()),
                        str(Path(sys.argv[0]).resolve()), VALUE]))
            """), encoding="utf-8")
            for mode in ("direct", "module"):
                with self.subTest(mode=mode):
                    result = self._run_cli(mode, "--file", str(script))
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    markers = [line for line in result.stdout.splitlines() if line.startswith("SCRIPT_CONTEXT=")]
                    self.assertEqual(len(markers), 1, result.stdout + result.stderr)
                    self.assertEqual(json.loads(markers[0].split("=", 1)[1]), ["__main__", str(script), str(script), 37])

    def test_direct_and_module_file_runtime_error_exit_one(self):
        with tempfile.TemporaryDirectory(dir=PERFORMANCE_ROOT) as directory:
            script = Path(directory) / "broken.py"
            script.write_text("raise RuntimeError('скрипт упал')\n", encoding="utf-8")
            self._assert_statuses([(["--file", str(script)], 1)])


class TestCLIInProcess(unittest.TestCase):
    def setUp(self):
        # Импортируем лениво; откатываем даже import-побочки legacy CLI.
        original_path, path_values = sys.path, sys.path[:]
        original_argv, argv_values = sys.argv, sys.argv[:]
        digits = sys.get_int_max_str_digits()

        def restore():
            original_path[:] = path_values
            original_argv[:] = argv_values
            sys.path, sys.argv = original_path, original_argv
            sys.set_int_max_str_digits(digits)

        self.addCleanup(restore)
        with patch.object(logging, "basicConfig"):
            from performance import profile_cli
        self.cli = profile_cli
        profiler = Mock()
        profiler.config = ProfilerConfig()
        profiler.profile.side_effect = lambda func: func
        self.enterContext(patch.object(self.cli, "PerformanceProfiler", return_value=profiler))
        self.output = self.enterContext(redirect_stdout(StringIO()))
        self.enterContext(redirect_stderr(StringIO()))

    def test_profile_function_does_not_reparse_json_keyword_strings(self):
        for value in ("2", "true", "null", "[]"):
            with self.subTest(value=value):
                dumps = Mock(wraps=json.dumps)
                with patch.object(self.cli.importlib, "import_module", return_value=SimpleNamespace(dumps=dumps)):
                    self.cli.profile_function("json", "dumps", ['{"x":1}'], {"indent": value})
                dumps.assert_called_once_with({"x": 1}, indent=value)

    def _assert_file_restores_process_state(self, raises):
        with tempfile.TemporaryDirectory(dir=PERFORMANCE_ROOT) as directory:
            script = Path(directory) / "state.py"
            script.write_text(
                "import sys\nprint('BODY_EXECUTED')\n"
                "sys.path.append('script-path-mutation')\n"
                "sys.argv.append('script-argv-mutation')\n"
                + ("raise RuntimeError('скрипт упал')\n" if raises else ""),
                encoding="utf-8",
            )
            for path_already_present in (False, True):
                with self.subTest(path_already_present=path_already_present):
                    with patch.object(sys, "path", sys.path[:] + ([directory] if path_already_present else [])):
                        with patch.object(sys, "argv", ["host-program", "keep-me"]):
                            before = (sys.path[:], sys.argv[:])
                            try:
                                self.cli.profile_file(str(script))
                            except RuntimeError:
                                if not raises:
                                    raise
                            self.assertIn("BODY_EXECUTED", self.output.getvalue())
                            self.assertEqual((sys.path, sys.argv), before)

    def test_profile_file_success_restores_sys_path_and_argv(self):
        self._assert_file_restores_process_state(False)

    def test_profile_file_failure_restores_sys_path_and_argv(self):
        self._assert_file_restores_process_state(True)


class TestAdditionalMetricsRegression(ProfilerRegressionCase):
    def test_metrics_include_actual_allocations_and_result_size(self):
        with patch.object(self.profiler, "_log_metrics") as log:
            result = self.profiler.profile(lambda: bytearray(4096))()
        metrics = log.call_args.args[1]
        self.assertGreaterEqual(metrics.execution_time, 0)
        self.assertGreaterEqual(metrics.cpu_time, 0)
        self.assertEqual(metrics.result_size_bytes, sys.getsizeof(result))
        self.assertGreaterEqual(metrics.peak_memory_mb * 1024**2, 4096)
        self.assertEqual(metrics.peak_memory_scope, "общий сеанс трассировки процесса")
        self.assertIsNone(metrics.collection_error)

    def test_collection_failure_is_exposed_in_metrics(self):
        with patch.object(profiler_module.psutil, "Process", side_effect=RuntimeError("сбой пробы")):
            with patch.object(self.profiler, "_log_metrics") as log:
                self.assertEqual(self.profiler.profile(lambda: 7)(), 7)
        self.assertEqual(log.call_args.args[1].collection_error, "сбой пробы")

    def test_force_disabled_borrows_existing_tracer(self):
        self.config.force_tracemalloc = False
        tracemalloc.start(2)
        self.assertTrue(self.profiler.profile(tracemalloc.is_tracing)())
        self.assertTrue(tracemalloc.is_tracing())
        self.assertEqual(tracemalloc.get_traceback_limit(), 2)

    def test_disabled_gc_tracking_does_not_query_gc(self):
        self.config.trace_gc = False
        with patch.object(profiler_module.gc, "get_count") as get_count:
            self.assertEqual(self.profiler.profile(lambda: 7)(), 7)
        get_count.assert_not_called()

    def test_async_callable_object_is_awaited(self):
        class AsyncCallable:
            async def __call__(self, value):
                await asyncio.sleep(0)
                return value

        wrapped = self.profiler.profile(AsyncCallable())
        self.assertTrue(asyncio.iscoroutinefunction(wrapped))
        self.assertEqual(asyncio.run(wrapped(7)), 7)

    def test_noncallable_target_is_rejected(self):
        with self.assertRaises(TypeError):
            self.profiler.profile(42)

    def test_result_size_failure_preserves_result(self):
        class BadSize:
            def __sizeof__(self):
                raise ValueError("размер недоступен")

        result = BadSize()
        with patch.object(self.profiler, "_log_metrics") as log:
            self.assertIs(self.profiler.profile(lambda: result)(), result)
        self.assertIsNone(log.call_args.args[1].result_size_bytes)

    def test_default_logger_observes_updated_config_without_touching_root(self):
        with redirect_stderr(StringIO()) as output:
            profiler = PerformanceProfiler(config=self.config)
            self.config.log_level = "ERROR"
            profiler.profile(lambda: 1)()
            self.assertEqual(output.getvalue(), "")
            self.config.log_level = "INFO"
            self.config.log_format = "ОБНОВЛЕНО %(message)s"
            profiler.profile(lambda: 1)()
            self.assertIn("ОБНОВЛЕНО", output.getvalue())


class TestAdditionalCLIRegression(unittest.TestCase):
    def test_cli_import_preserves_sys_path_and_integer_safety_limit(self):
        result = run_python("-c", textwrap.dedent("""
            import sys
            before = (sys.path[:], sys.get_int_max_str_digits())
            from performance import profile_cli
            assert (sys.path, sys.get_int_max_str_digits()) == before
        """), clean_path=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_cli_supports_legacy_windows_output_encoding(self):
        for prefix in ([str(PERFORMANCE_ROOT / "profile_cli.py")], ["-m", "performance.profile_cli"]):
            with self.subTest(prefix=prefix):
                result = subprocess.run(
                    [sys.executable, *prefix, "math", "factorial", "5"],
                    cwd=WORKSPACE_ROOT, capture_output=True, text=True, encoding="cp1251",
                    env=dict(os.environ, PYTHONIOENCODING="cp1251"), timeout=5,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("120", result.stdout)
                self.assertNotIn("UnicodeEncodeError", result.stderr)

    def test_file_mode_rejects_conflicting_function_arguments(self):
        for args in (["math", "factorial"], ["--kwargs", "{}"]):
            with self.subTest(args=args):
                result = run_python("-m", "performance.profile_cli", "--file", "unused.py", *args)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_missing_file_and_noncallable_target_fail(self):
        for args in (["--file", "profiler_missing_script_xyz.py"], ["math", "pi"]):
            with self.subTest(args=args):
                result = run_python("-m", "performance.profile_cli", *args)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_script_system_exit_status_is_preserved(self):
        with tempfile.TemporaryDirectory(dir=PERFORMANCE_ROOT) as directory:
            script = Path(directory) / "exit.py"
            for code, expected in ((None, 0), (7, 7), ("упал", 1)):
                with self.subTest(code=code):
                    script.write_text(f"raise SystemExit({code!r})\n", encoding="utf-8")
                    result = run_python("-m", "performance.profile_cli", "--file", str(script))
                    self.assertEqual(result.returncode, expected, result.stdout + result.stderr)

    def test_large_results_are_bounded_without_traversing_items(self):
        from performance.profile_cli import format_result

        class NoRepresentation:
            def __repr__(self):
                raise AssertionError("большие коллекции нельзя обходить по элементам")

        self.assertEqual(format_result([NoRepresentation()] * 2000), "<list: 2000 элементов>")
        self.assertLess(len(format_result(10**10000)), 100)
        recursive = []
        recursive.append(recursive)
        self.assertLess(len(format_result(recursive)), 100)

    def test_config_rejects_incorrect_field_types(self):
        for kwargs in ({"enable_profiling": "false"}, {"max_result_length": 100.0}, {"trace_gc": 1}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                ProfilerConfig(**kwargs)


def run_tests():
    """Запуск всех тестов."""
    loader = unittest.TestLoader()
    # Добавляем все тесты
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    
    # Запускаем с verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
