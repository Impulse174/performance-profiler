"""
Конфигурация профайлера производительности.

Модуль предоставляет централизованное управление настройками профилирования.
"""

from dataclasses import asdict, dataclass, fields, replace
from typing import Any


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
    
    def __post_init__(self) -> None:
        """Валидация конфигурации после инициализации."""
        for field in fields(self):
            if type(getattr(self, field.name)) is not field.type:
                raise ValueError(f"{field.name} должен быть типа {field.type.__name__}")
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


def update_config(**kwargs: Any) -> None:
    """
    Обновить конфигурацию.
    
    Args:
        **kwargs: Параметры для обновления
        
    Example:
        update_config(log_level="DEBUG", enable_profiling=False)
    """
    field_names = {field.name for field in fields(default_config)}
    for key in kwargs:
        if key not in field_names:
            raise AttributeError(f"Неизвестный параметр конфигурации: {key}")
    candidate = replace(default_config, **kwargs)
    default_config.__dict__.update(asdict(candidate))


def reset_config() -> None:
    """Сбросить конфигурацию к значениям по умолчанию."""
    default_config.__dict__.update(asdict(ProfilerConfig()))
