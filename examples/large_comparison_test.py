"""
Сравнение производительности двух подходов к фильтрации символов на большем объеме данных
"""

import sys
from pathlib import Path

# Добавляем родительскую директорию в путь для импорта модулей проекта
sys.path.insert(0, str(Path(__file__).parent.parent))

from auto_profile import auto_profile
import random
import string

# Генерация большого набора тестовых данных
def generate_large_dataset(size=100000):
    """Генерируем большой набор символов, включая Unicode"""
    # Смешиваем ASCII и Unicode символы
    ascii_chars = string.ascii_letters + string.digits + string.punctuation
    unicode_chars = ['¢', '£', '¥', '€', '¤', '©', '®', '™', '±', 'µ', '¶', '·', 'º', '»', '¼', '½', '¾', '¿', 'À', 'Á', 'Â', 'Ã', 'Ä', 'Å', 'Æ']
    
    chars = list(ascii_chars) + unicode_chars
    return [random.choice(chars) for _ in range(size)]


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
    print("Генерация большого набора данных...")
    large_symbols = generate_large_dataset(100000)  # 100K символов
    print(f"Размер набора данных: {len(large_symbols)} символов")
    print("="*60)
    
    print("\n--- Тест на большом объеме данных ---")
    result1 = filter_with_list_comprehension(large_symbols)
    result2 = filter_with_filter_lambda(large_symbols)
    
    print(f"\nРезультат list comprehension: найдено {len(result1)} символов > 127")
    print(f"Результат filter+lambda+map:  найдено {len(result2)} символов > 127")
    print(f"Результаты совпадают: {result1 == result2}")
    
    # Проверим первые несколько элементов
    print(f"\nПервые 10 элементов list comprehension: {result1[:10]}")
    print(f"Первые 10 элементов filter+lambda+map:  {result2[:10]}")