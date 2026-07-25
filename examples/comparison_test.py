"""
Сравнение производительности двух подходов к фильтрации символов:
1. List comprehension с условием ord(s) > 127
2. filter() + lambda + map(ord, symbols)
"""

import sys
from pathlib import Path

# Добавляем родительскую директорию в путь для импорта модулей проекта
sys.path.insert(0, str(Path(__file__).parent.parent))

from auto_profile import auto_profile

# Тестовые данные - символы с разными ASCII-кодами
symbols = ['¢', '£', '¥', '€', '¤', 'a', 'b', 'c', '1', '2', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '+', '-', '=', '{', '}', '|', '[', ']', '\\', ':', ';', '"', "'", '<', '>', ',', '.', '?', '/', '`', '~']


@auto_profile
def filter_with_list_comprehension(symbols_list):
    """Фильтрация с использованием list comprehension"""
    beyond_ascii = [ord(s) for s in symbols_list if ord(s) > 127]
    return beyond_ascii


@auto_profile
def filter_with_filter_lambda(symbols_list):
    """Фильтрация с использованием filter() + lambda + map()"""
    beyond_ascii = list(filter(lambda c: c > 127, map(ord, symbols_list)))
    return beyond_ascii


if __name__ == "__main__":
    print("Запуск сравнения производительности...")
    print("="*50)
    
    # Запускаем каждую функцию несколько раз для точности
    for i in range(3):
        print(f"\n--- Итерация {i+1} ---")
        result1 = filter_with_list_comprehension(symbols)
        result2 = filter_with_filter_lambda(symbols)
        
        print(f"Результат list comprehension: {result1}")
        print(f"Результат filter+lambda+map:  {result2}")
        print(f"Результаты совпадают: {result1 == result2}")