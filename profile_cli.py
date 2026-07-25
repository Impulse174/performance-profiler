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
from typing import Any, List, Optional, Dict
from pathlib import Path

# Импортируем профайлер
from performance_inspect import PerformanceProfiler

# Конфигурация
sys.set_int_max_str_digits(100000)  # Лимит для больших int
CURRENT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(CURRENT_DIR))

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
            str_result = str(result)
            if len(str_result) > max_length:
                return f"<int с {len(str_result)} цифр(ы)>"
            return str_result
        
        if isinstance(result, str) and len(result) > max_length:
            return f"<str длиной {len(result)} символов>"
        
        if isinstance(result, (list, dict, set, tuple)):
            str_result = str(result)
            if len(str_result) > max_length:
                size_info = {
                    list: f"список из {len(result)} элементов",
                    dict: f"словарь из {len(result)} элементов",
                    set: f"множество из {len(result)} элементов",
                    tuple: f"кортеж из {len(result)} элементов"
                }
                return f"<{size_info.get(type(result), 'коллекция')}>"
            return str_result
        
        return str(result)
    except Exception:
        return f"<объект {type(result).__name__}>"


def profile_function(
    module_name: str, 
    function_name: str, 
    args: List[str], 
    kwargs_dict: Optional[Dict[str, Any]] = None
):
    """
    Профилирование функции из указанного модуля.
    
    Args:
        module_name: Имя модуля (например, 'math', 'json', 'my_module')
        function_name: Имя функции для профилирования
        args: Позиционные аргументы функции
        kwargs_dict: Словарь именованных аргументов
    """
    profiler = PerformanceProfiler()
    
    try:
        # Импорт модуля
        module = importlib.import_module(module_name)
        
        # Получение функции
        if not hasattr(module, function_name):
            print(f"❌ Ошибка: Функция '{function_name}' не найдена в модуле '{module_name}'")
            return
        
        func = getattr(module, function_name)
        
        # Парсинг аргументов
        parsed_args = [parse_argument(arg) for arg in args]
        parsed_kwargs = {}
        if kwargs_dict:
            for key, value in kwargs_dict.items():
                parsed_kwargs[key] = parse_argument(value)
        
        # Инфо о запуске
        print(f"\n{'='*60}")
        print(f"🚀 Профилирование: {function_name} из модуля '{module_name}'")
        print(f"📋 Аргументы: {parsed_args}")
        if parsed_kwargs:
            print(f"📋 Kwargs: {parsed_kwargs}")
        print(f"{'='*60}\n")
        
        # Профилирование
        profiled_func = profiler.profile(func)
        
        if asyncio.iscoroutinefunction(func):
            print("⏳ Запуск асинхронной функции...")
            result = asyncio.run(profiled_func(*parsed_args, **parsed_kwargs))
        else:
            print("⏳ Запуск синхронной функции...")
            result = profiled_func(*parsed_args, **parsed_kwargs)
        
        print(f"\n✅ Успешно завершено")
        print(f"📥 Результат: {format_result(result)}\n")
        
    except ImportError as e:
        print(f"\n❌ Ошибка импорта модуля '{module_name}': {e}")
        print(f"💡 Проверьте, что модуль установлен или находится в PYTHONPATH\n")
    except Exception as e:
        print(f"\n❌ Ошибка выполнения: {e}")
        print(f"💡 Stack trace:")
        import traceback
        traceback.print_exc()
        print()


def profile_file(filename: str):
    """
    Профилирование выполнения Python файла.
    
    Args:
        filename: Путь к .py файлу (абсолютный или относительный)
    """
    profiler = PerformanceProfiler()
    
    try:
        abs_filename = Path(filename).resolve()
        
        if not abs_filename.exists():
            print(f"❌ Файл не найден: '{filename}'")
            print(f"   Абсолютный путь: {abs_filename}")
            return
        
        # Добавляем директорию файла в sys.path
        file_dir = str(abs_filename.parent)
        if file_dir not in sys.path:
            sys.path.insert(0, file_dir)
        
        print(f"\n{'='*60}")
        print(f"🚀 Профилирование файла: {filename}")
        print(f"   Полный путь: {abs_filename}")
        print(f"   Директория: {file_dir}")
        print(f"{'='*60}\n")
        
        # Чтение файла
        with open(abs_filename, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Обертка для профилирования
        def execute_file():
            exec_globals = {}
            exec(code, exec_globals)
            return f"Файл {filename} выполнен"
        
        # Профилирование
        profiled_execute = profiler.profile(execute_file)
        
        print("⏳ Выполнение файла...")
        result = profiled_execute()
        
        print(f"\n✅ Файл выполнен")
        print(f"📥 Результат: {format_result(result)}\n")
        
    except Exception as e:
        print(f"\n❌ Ошибка выполнения файла: {e}")
        print(f"💡 Stack trace:")
        import traceback
        traceback.print_exc()
        print()


def main():
    """Точка входа CLI."""
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
    
    args = parser.parse_args()
    
    # Профилирование файла
    if args.file:
        profile_file(args.file)
        return
    
    # Профилирование функции
    if args.module and args.function:
        kwargs_dict = None
        if args.kwargs:
            try:
                kwargs_dict = json.loads(args.kwargs)
            except json.JSONDecodeError as e:
                print(f"\n❌ Ошибка JSON в --kwargs: {e}\n")
                return
        
        profile_function(args.module, args.function, args.args, kwargs_dict)
    else:
        print("\n⚠️  Укажите либо --file, либо MODULE FUNCTION ARGS\n")
        parser.print_help()


if __name__ == "__main__":
    main()