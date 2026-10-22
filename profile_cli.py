#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI для профилирования производительности Python функций и скриптов.

Использование:
    # Профилирование функции из модуля:
    python profile_cli.py module_name function_name [args...]
    
    # Профилирование файла:
    python profile_cli.py --file script.py
    
Примеры:
    python profile_cli.py math factorial 10
    python profile_cli.py json dumps '{"key": "value"}'
    python profile_cli.py my_module my_func arg1 --kwargs '{"param": 42}'
    python profile_cli.py --file benchmark.py
"""

import sys
import argparse
import importlib
import json
import asyncio
import reprlib
import runpy
from typing import Any, List, Optional, Dict
from pathlib import Path

# Импортируем профайлер
if __package__:
    from .performance_inspect import PerformanceProfiler
else:
    from performance_inspect import PerformanceProfiler


def parse_argument(arg: Any) -> Any:
    """
    Преобразует строковый аргумент в Python объект.
    
    Поддерживаемые типы:
    - int/float числа
    - bool (true/false)
    - JSON объекты (dict, list)
    - Строки (по умолчанию)
    
    Args:
        arg: Строка для парсинга
        
    Returns:
        Преобразованный объект Python
    """
    if not isinstance(arg, str):
        return arg
    
    # Числа
    try:
        if '.' in arg:
            return float(arg)
        return int(arg)
    except ValueError:
        pass
    
    # Булевы значения
    if arg.lower() in ('true', 'false'):
        return arg.lower() == 'true'
    
    # JSON
    try:
        return json.loads(arg)
    except (json.JSONDecodeError, TypeError):
        pass
    
    return arg


def format_result(result: Any, max_length: int = 1000) -> str:
    """
    Форматирует результат для вывода, обрезая большие объекты.
    
    Args:
        result: Объект для форматирования
        max_length: Максимальная длина строки представления
        
    Returns:
        Отформатированная строка
    """
    try:
        if isinstance(result, int):
            if result.bit_length() > max_length * 4:
                return f"<int: {result.bit_length()} бит>"
            str_result = str(result)
            if len(str_result) > max_length:
                return f"<int с {len(str_result)} цифр(ы)>"
            return str_result
        
        if isinstance(result, str) and len(result) > max_length:
            return f"<str длиной {len(result)} символов>"
        
        if isinstance(result, (list, dict, set, tuple)):
            if len(result) > max_length:
                return f"<{type(result).__name__}: {len(result)} элементов>"
            formatter = reprlib.Repr()
            formatter.maxstring = formatter.maxother = max_length
            text = formatter.repr(result)
        else:
            text = str(result)
        return text if len(text) <= max_length else text[:max_length] + "..."
    except Exception:
        return f"<объект {type(result).__name__}>"


def profile_function(
    module_name: str, 
    function_name: str, 
    args: List[str], 
    kwargs_dict: Optional[Dict[str, Any]] = None
) -> int:
    """
    Профилирование функции из указанного модуля.
    
    Args:
        module_name: Имя модуля (например, 'math', 'json', 'my_module')
        function_name: Имя функции для профилирования
        args: Позиционные аргументы функции
        kwargs_dict: Словарь именованных аргументов

    Returns:
        0 при успешном выполнении, 1 при ошибке
    """
    profiler = PerformanceProfiler()
    
    try:
        # Импорт модуля
        module = importlib.import_module(module_name)
        
        # Получение функции
        if not hasattr(module, function_name):
            print(f"❌ Ошибка: Функция '{function_name}' не найдена в модуле '{module_name}'")
            return 1

        func = getattr(module, function_name)
        if not callable(func):
            raise TypeError(f"{module_name}.{function_name} не является вызываемым")
        
        # Парсинг аргументов
        parsed_args = [parse_argument(arg) for arg in args]
        parsed_kwargs = {} if kwargs_dict is None else kwargs_dict
        if not isinstance(parsed_kwargs, dict):
            raise TypeError("Именованные аргументы должны быть JSON-объектом")
        
        # Инфо о запуске
        print(f"\n{'='*60}")
        print(f"🚀 Профилирование: {function_name} из модуля '{module_name}'")
        print(f"📋 Аргументы: {parsed_args}")
        if parsed_kwargs:
            print(f"📋 Kwargs: {parsed_kwargs}")
        print(f"{'='*60}\n")
        
        # Профилирование
        profiled_func = profiler.profile(func)
        
        if asyncio.iscoroutinefunction(profiled_func):
            print("⏳ Запуск асинхронной функции...")
            result = asyncio.run(profiled_func(*parsed_args, **parsed_kwargs))
        else:
            print("⏳ Запуск синхронной функции...")
            result = profiled_func(*parsed_args, **parsed_kwargs)
        
        print("\n✅ Успешно завершено")
        print(f"📥 Результат: {format_result(result, profiler.config.max_result_length)}\n")
        return 0

    except ImportError as e:
        print(f"\n❌ Ошибка импорта модуля '{module_name}': {e}")
        print("💡 Проверьте, что модуль установлен или находится в PYTHONPATH\n")
    except Exception as e:
        print(f"\n❌ Ошибка выполнения: {e}")
        print("💡 Stack trace:")
        import traceback
        traceback.print_exc()
        print()
    return 1


def profile_file(filename: str) -> int:
    """
    Профилирование выполнения Python файла.
    
    Args:
        filename: Путь к .py файлу (абсолютный или относительный)

    Returns:
        Код выхода: 0 при успехе, код ошибки иначе
    """
    profiler = PerformanceProfiler()
    # Сохраняем ссылки на оригинальные объекты и их копии.
    # original_path/original_argv — те же list-объекты, что и sys.path/sys.argv;
    # path_values/argv_values — их снимки для восстановления после in-place мутаций.
    original_path, path_values = sys.path, sys.path[:]
    original_argv, argv_values = sys.argv, sys.argv[:]

    try:
        abs_filename = Path(filename).resolve()
        
        if not abs_filename.is_file():
            print(f"❌ Файл не найден: '{filename}'")
            print(f"   Абсолютный путь: {abs_filename}")
            return 1
        
        # Добавляем директорию файла в sys.path
        file_dir = str(abs_filename.parent)
        sys.path = [file_dir, *sys.path]
        sys.argv = [str(abs_filename)]
        
        print(f"\n{'='*60}")
        print(f"🚀 Профилирование файла: {filename}")
        print(f"   Полный путь: {abs_filename}")
        print(f"   Директория: {file_dir}")
        print(f"{'='*60}\n")
        
        # Обертка для профилирования
        def execute_file() -> str:
            runpy.run_path(str(abs_filename), run_name="__main__")
            return f"Файл {filename} выполнен"
        
        # Профилирование
        profiled_execute = profiler.profile(execute_file)
        
        print("⏳ Выполнение файла...")
        result = profiled_execute()
        
        print("\n✅ Файл выполнен")
        print(f"📥 Результат: {format_result(result)}\n")
        return 0

    except SystemExit as exc:
        if exc.code is None:
            return 0
        if isinstance(exc.code, int):
            return exc.code
        print(exc.code, file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\n❌ Ошибка выполнения файла: {e}")
        print("💡 Stack trace:")
        import traceback
        traceback.print_exc()
        print()
        return 1
    finally:
        # Восстанавливаем in-place мутации оригинальных списков (если скрипт
        # делал sys.path.append(...) и т.п.)
        original_path[:] = path_values
        original_argv[:] = argv_values
        # Восстанавливаем ссылки на случай, если скрипт переназначил
        # sys.path / sys.argv целиком (sys.path = [...])
        sys.path, sys.argv = original_path, original_argv


def main(argv: Optional[List[str]] = None) -> int:
    """Точка входа CLI."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")
    parser = argparse.ArgumentParser(
        description="CLI для профилирования производительности Python функций и скриптов",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
╔═══════════════════════════════════════════════════════════╗
║                    ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ                  ║
╠═══════════════════════════════════════════════════════════╣
║  Профилирование функции:                                  ║
║    python profile_cli.py math factorial 5                 ║
║    python profile_cli.py json dumps '{"key": "value"}'    ║
║    python profile_cli.py my_module my_func 10 20          ║
║      --kwargs '{"param": "value"}'                        ║
║                                                           ║
║  Профилирование файла:                                    ║
║    python profile_cli.py --file script.py                 ║
║    python profile_cli.py --file /path/to/script.py        ║
╚═══════════════════════════════════════════════════════════╝
        """
    )
    
    group = parser.add_mutually_exclusive_group()
    
    group.add_argument(
        "--file", "-f",
        type=str,
        metavar="FILE",
        help="Путь к Python файлу для профилирования"
    )
    
    parser.add_argument(
        "module",
        nargs='?',
        metavar="MODULE",
        help="Имя модуля (math, json, my_module)"
    )
    
    parser.add_argument(
        "function",
        nargs='?',
        metavar="FUNCTION",
        help="Имя функции для профилирования"
    )
    
    parser.add_argument(
        "args",
        nargs="*",
        metavar="ARGS",
        help="Аргументы функции (автоматически определяются типы)"
    )
    
    parser.add_argument(
        "--kwargs", "-k",
        type=str,
        metavar="JSON",
        help="Именованные аргументы в JSON формате"
    )
    
    args = parser.parse_args(argv)
    
    # Профилирование файла
    if args.file:
        if args.module or args.function or args.args or args.kwargs is not None:
            parser.error("--file нельзя совмещать с целью-функцией или --kwargs")
        return profile_file(args.file)
    
    # Профилирование функции
    if args.module and args.function:
        kwargs_dict = None
        if args.kwargs is not None:
            try:
                kwargs_dict = json.loads(args.kwargs)
            except (ValueError, TypeError) as exc:
                parser.error(f"Некорректный JSON в --kwargs: {exc}")
            if not isinstance(kwargs_dict, dict):
                parser.error("--kwargs должен быть JSON-объектом")

        return profile_function(args.module, args.function, args.args, kwargs_dict)
    parser.error("Укажите либо --file, либо MODULE FUNCTION ARGS")


if __name__ == "__main__":
    raise SystemExit(main())
