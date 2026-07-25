"""
Конфигурация профайлера производительности.

Модуль предоставляет централизованное управление настройками профилирования.
"""

from dataclasses import dataclass


@dataclass
class ProfilerConfig:
    """
    Конфигурация профайлера.
    
    Attributes:
        enable_profiling: Включить/выключить профилирование
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR)
        log_format: Формат сообщений лога
        max_result_length: Максимальная длина результата для вывода
        trace_memory: Отслеживать использование памяти
        trace_gc: Отслеживать сборщик мусора
        analyze_complexity: Анализировать алгоритмическую сложность
    """
    enable_profiling: bool = True
    log_level: str = "INFO"
    log_format: str = "[%(asctime)s] %(message)s"
    date_format: str = "%H:%M:%S"
    max_result_length: int = 1000
    trace_memory: bool = True
    trace_gc: bool = True
    analyze_complexity: bool = True
    
    # Продвинутые настройки
    enable_ast_analysis: bool = True
    force_tracemalloc: bool = True
    gc_collect_before: bool = True
    
    def __post_init__(self):
        """Валидация конфигурации после инициализации."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_levels:
            raise ValueError(f"log_level должен быть одним из: {valid_levels}")
        
        if self.max_result_length < 100:
            raise ValueError("max_result_length должен быть >= 100")


# Глобальная конфигурация по умолчанию
default_config = ProfilerConfig()


def get_config() -> ProfilerConfig:
    """
    Получить текущую конфигурацию.
    
    Returns:
        Текущий объект конфигурации
    """
    return default_config


def update_config(**kwargs) -> None:
    """
    Обновить конфигурацию.
    
    Args:
        **kwargs: Параметры для обновления
        
    Example:
        update_config(log_level="DEBUG", enable_profiling=False)
    """
    global default_config
    
    for key, value in kwargs.items():
        if hasattr(default_config, key):
            setattr(default_config, key, value)
        else:
            raise AttributeError(f"Неизвестный параметр конфигурации: {key}")


def reset_config() -> None:
    """Сбросить конфигурацию к значениям по умолчанию."""
    global default_config
    default_config = ProfilerConfig()
