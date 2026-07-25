"""
Автоматический декоратор для профилирования функций.

Использование:
    from auto_profile import auto_profile
    
    @auto_profile
    def my_function():
        # ваш код
        pass

При вызове функции автоматически выводится подробная статистика производительности.
"""

import functools
import inspect
import asyncio
from typing import Callable, Dict, Any, Optional
from performance_inspect import PerformanceProfiler


# Глобальный экземпляр профайлера
_profiler = PerformanceProfiler()


def auto_profile(func: Callable) -> Callable:
    """
    Декоратор для автоматического профилирования функций.
    
    Обернутая функция сохраняет свое имя, docstring и метаданные.
    При каждом вызове выводится детальная статистика:
    - Время выполнения (real/CPU)
    - Использование памяти
    - Алгоритмическая сложность
    - Размер результата
    
    Поддерживает как синхронные, так и асинхронные функции.
    
    Args:
        func: Функция для профилирования
        
    Returns:
        Обернутая функция с авто-профилированием
        
    Example:
        >>> @auto_profile
        ... def factorial(n):
        ...     return 1 if n <= 1 else n * factorial(n-1)
        >>> factorial(100)  # Выведет статистику
    """
    if asyncio.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            profiled_func = _profiler.profile(func)
            return await profiled_func(*args, **kwargs)
        return async_wrapper
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            profiled_func = _profiler.profile(func)
            return profiled_func(*args, **kwargs)
        return sync_wrapper


def apply_to_all_functions(module_globals: Optional[Dict[str, Any]] = None) -> None:
    """
    Автоматически применяет @auto_profile ко всем функциям в модуле.
    
    Внимание: Изменяет глобальную область видимости модуля!
    Используйте с осторожностью - может вызвать непредсказуемое поведение.
    
    Args:
        module_globals: Словарь globals() модуля. 
                       Если None, используется globals() вызывающего модуля.
    
    Example:
        # В начале файла my_module.py:
        from auto_profile import apply_to_all_functions
        apply_to_all_functions(globals())
        
        # Теперь все функции ниже будут профилироваться:
        def func1(): ...
        def func2(): ...
    """
    if module_globals is None:
        # Пытаемся получить globals() вызывающего фрейма
        try:
            frame = inspect.currentframe()
            if frame and frame.f_back:
                module_globals = frame.f_back.f_globals
        finally:
            del frame  # Избегаем циклических ссылок
    
    if not module_globals:
        _profiler.logger.warning("Не удалось получить globals() модуля")
        return
    
    module_name = module_globals.get('__name__', 'unknown')
    
    # Собираем функции для профилирования
    functions_to_profile = []
    
    for name, obj in module_globals.items():
        # Пропускаем служебные имена и уже завернутые функции
        if (name.startswith('_') or 
            name in ('auto_profile', 'apply_to_all_functions', '_profiler', 'profiler') or
            not inspect.isfunction(obj)):
            continue
        
        functions_to_profile.append(name)
    
    # Применяем декоратор
    for name in functions_to_profile:
        func = module_globals[name]
        module_globals[name] = auto_profile(func)
        _profiler.logger.info(
            f"[AUTO_PROFILE] Функция '{name}' из модуля '{module_name}' добавлена в профилирование"
        )
    
    if functions_to_profile:
        _profiler.logger.info(
            f"[AUTO_PROFILE] Всего профилируется функций: {len(functions_to_profile)}"
        )