"""
Продвинутые примеры использования профайлера производительности.

Демонстрирует различные сценарии профилирования:
- Синхронные и асинхронные функции
- Анализ алгоритмической сложности
- Работа с памятью
- Кастомная конфигурация
"""

import sys
from pathlib import Path

# Добавляем родительскую директорию в путь для импорта модулей проекта
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import time
from auto_profile import auto_profile, apply_to_all_functions
from performance_inspect import PerformanceProfiler


# ============================================================================
# Пример 1: Базовое использование декоратора
# ============================================================================

@auto_profile
def fibonacci_recursive(n: int) -> int:
    """Рекурсивный Фибоначчи - экспоненциальная сложность O(2^n)."""
    if n <= 1:
        return n
    return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)


@auto_profile
def fibonacci_iterative(n: int) -> int:
    """Итеративный Фибоначчи - линейная сложность O(n)."""
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


# ============================================================================
# Пример 2: Анализ алгоритмов сортировки
# ============================================================================

@auto_profile
def bubble_sort(arr):
    """Пузырьковая сортировка - O(n²) время, O(1) память."""
    n = len(arr)
    arr = arr.copy()
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr


@auto_profile
def quick_sort(arr):
    """Быстрая сортировка - O(n log n) среднее время, O(log n) память."""
    if len(arr) <= 1:
        return arr
    
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    return quick_sort(left) + middle + quick_sort(right)


# ============================================================================
# Пример 3: Асинхронные операции
# ============================================================================

@auto_profile
async def async_sleep_task(delay: float, task_id: int):
    """Асинхронная задача с задержкой."""
    print(f"Task {task_id} starting...")
    await asyncio.sleep(delay)
    print(f"Task {task_id} completed")
    return f"Result from task {task_id}"


@auto_profile
async def async_computation(n: int):
    """Асинхронная вычислительная задача."""
    await asyncio.sleep(0.1)  # Имитация I/O
    result = sum(i ** 2 for i in range(n))
    return result


# ============================================================================
# Пример 4: Интенсивное использование памяти
# ============================================================================

@auto_profile
def memory_intensive_list(size: int):
    """Создание большого списка - O(n) память."""
    return [i ** 2 for i in range(size)]


@auto_profile
def memory_intensive_matrix(rows: int, cols: int):
    """Создание матрицы - O(n²) память."""
    return [[i * cols + j for j in range(cols)] for i in range(rows)]


@auto_profile
def memory_efficient_generator(size: int):
    """Генератор - O(1) память (ленивые вычисления)."""
    return (i ** 2 for i in range(size))


# ============================================================================
# Пример 5: Автоматическое профилирование всего модуля
# ============================================================================

def function_one():
    """Первая функция для авто-профилирования."""
    time.sleep(0.1)
    return "Function 1 done"


def function_two(x: int):
    """Вторая функция для авто-профилирования."""
    return x ** 2


def function_three(data: list):
    """Третья функция для авто-профилирования."""
    return sorted(data, reverse=True)


# Применяем профилирование ко всем функциям выше
apply_to_all_functions(globals())


# ============================================================================
# Пример 6: Сравнение производительности
# ============================================================================

def run_comparison_examples():
    """Запуск примеров сравнения алгоритмов."""
    
    profiler = PerformanceProfiler()
    
    print("\n" + "="*70)
    print("СРАВНЕНИЕ: Рекурсивный vs Итеративный Фибоначчи")
    print("="*70 + "\n")
    
    # Профилируем обе версии
    profiled_recursive = profiler.profile(fibonacci_recursive)
    profiled_iterative = profiler.profile(fibonacci_iterative)
    
    n = 25
    print(f"Вычисляем F({n}):")
    print("\n1. Рекурсивная версия:")
    result_rec = profiled_recursive(n)
    
    print("\n2. Итеративная версия:")
    result_iter = profiled_iterative(n)
    
    print(f"\nРезультаты совпали: {result_rec == result_iter}")
    
    print("\n" + "="*70)
    print("СРАВНЕНИЕ: Сортировки")
    print("="*70 + "\n")
    
    import random
    test_array = [random.randint(1, 1000) for _ in range(500)]
    
    profiled_bubble = profiler.profile(bubble_sort)
    profiled_quick = profiler.profile(quick_sort)
    
    print("Пузырьковая сортировка:")
    sorted_bubble = profiled_bubble(test_array)
    
    print("\nБыстрая сортировка:")
    sorted_quick = profiled_quick(test_array)
    
    print(f"\nРезультаты совпали: {sorted_bubble == sorted_quick}")


async def run_async_examples():
    """Запуск асинхронных примеров."""
    
    print("\n" + "="*70)
    print("АСИНХРОННЫЕ ЗАДАЧИ")
    print("="*70 + "\n")
    
    # Параллельное выполнение задач
    tasks = [
        async_sleep_task(0.5, 1),
        async_sleep_task(0.3, 2),
        async_sleep_task(0.7, 3)
    ]
    
    print("Запуск 3 асинхронных задач параллельно:\n")
    results = await asyncio.gather(*tasks)
    print(f"\nРезультаты: {results}")
    
    print("\n" + "="*70)
    print("АСИНХРОННЫЕ ВЫЧИСЛЕНИЯ")
    print("="*70 + "\n")
    
    profiled_compute = PerformanceProfiler().profile(async_computation)
    result = await profiled_compute(100000)
    print(f"Результат вычислений: {result:,}")


def run_memory_examples():
    """Запуск примеров с памятью."""
    
    print("\n" + "="*70)
    print("ИСПОЛЬЗОВАНИЕ ПАМЯТИ")
    print("="*70 + "\n")
    
    profiler = PerformanceProfiler()
    
    # Список
    profiled_list = profiler.profile(memory_intensive_list)
    lst = profiled_list(100_000)
    
    # Матрица
    profiled_matrix = profiler.profile(memory_intensive_matrix)
    matrix = profiled_matrix(100, 100)
    
    # Генератор
    profiled_gen = profiler.profile(memory_efficient_generator)
    gen = profiled_gen(100_000)
    # Преобразуем в список для измерения
    _ = list(gen)


# ============================================================================
# Главная функция запуска
# ============================================================================

def main():
    """Запуск всех примеров."""
    
    print("\n" + "="*70)
    print(" ПРОФИЛИРОВАНИЕ PYTHON: ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ ")
    print("="*70)
    
    # Синхронные примеры
    run_comparison_examples()
    
    # Асинхронные примеры
    asyncio.run(run_async_examples())
    
    # Примеры с памятью
    run_memory_examples()
    
    print("\n" + "="*70)
    print(" ВСЕ ПРИМЕРЫ ЗАВЕРШЕНЫ ")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
