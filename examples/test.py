"""
Тестовый файл для демонстрации работы профайлера.

Запускается только при прямом вызове через python test.py
Не выполняется при импорте в другом модуле.
"""

import sys
from pathlib import Path

# Добавляем родительскую директорию в путь для импорта модулей проекта
sys.path.insert(0, str(Path(__file__).parent.parent))

from auto_profile import auto_profile


@auto_profile
def create_list():
    """
    Создание списка с 10 миллионами элементов.
    Демонстрирует O(n) пространственную сложность.
    """
    lst = [x * 2 for x in range(10_000_000)]
    return lst


@auto_profile
def create_iterator():
    """
    Создание итератора для 10 миллионов элементов.
    Демонстрирует ленивые вычисления и эффективное использование памяти.
    """
    it = map(lambda x: x * 2, range(10_000_000))
    # Преобразуем в список для измерения реального потребления памяти
    result = list(it)
    return result  # Исправлено: возвращаем result вместо it


@auto_profile
def space_complexity_test() -> None:
    """
    Тест различных уровней пространственной сложности.
    
    Проверяет:
    - O(1) - константная память
    - O(n) - линейная память (списки, словари, множества)
    - O(n²) - квадратичная память (матрицы)
    - O(n³) - кубическая память (трехмерные массивы)
    """
    print("\n=== ТЕСТ ПРОРАНСТВЕННОЙ СЛОЖНОСТИ ===\n")
    
    # O(1) - константная память
    print("1️⃣ Тест O(1) - простые переменные...")
    a = 42
    b = "hello"
    c = [1, 2, 3]
    
    # O(n) - линейная память
    print("2️⃣ Тест O(n) - список из 10000 элементов...")
    linear_list = [i for i in range(10000)]
    
    # O(n²) - квадратичная память
    print("3️⃣ Тест O(n²) - матрица 100x100...")
    quadratic_matrix = [[i * j for j in range(100)] for i in range(100)]
    
    # O(n³) - кубическая память
    print("4️⃣ Тест O(n³) - трехмерный массив 10x10x10...")
    cubic_array = [[[i + j + k for k in range(10)] 
                    for j in range(10)] 
                   for i in range(10)]
    
    # Словарь O(n)
    print("5️⃣ Тест O(n) - словарь из 5000 элементов...")
    dict_storage = {i: i ** 2 for i in range(5000)}
    
    # Множество O(n)
    print("6️⃣ Тест O(n) - множество из 3000 элементов...")
    set_storage = {i for i in range(3000)}
    
    print("\n✅ Все тесты пространственной сложности завершены\n")


if __name__ == "__main__":
    # Запускаем только при прямом вызове
    print("=" * 60)
    print("ЗАПУСК ТЕСТОВ ПРОИЗВОДИТЕЛЬНОСТИ")
    print("=" * 60)
    
    create_list()
    create_iterator()
    space_complexity_test()
    
    print("=" * 60)
    print("ТЕСТЫ ЗАВЕРШЕНЫ")
    print("=" * 60)