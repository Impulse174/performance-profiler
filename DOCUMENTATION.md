# 📚 Полная документация Performance Profiler

## Оглавление

1. [Архитектура](#архитектура)
2. [API Reference](#api-reference)
3. [Продвинутые примеры](#продвинутые-примеры)
4. [Конфигурация](#конфигурация)
5. [Лучшие практики](#лучшие-практики)
6. [Troubleshooting](#troubleshooting)

---

## Архитектура

### Структура проекта

```
performance/
├── performance_inspect.py    # Ядро профилирования
├── auto_profile.py           # Декораторы
├── profile_cli.py            # CLI интерфейс
├── config.py                 # Конфигурация
├── examples.py               # Примеры использования
├── tests/
│   └── test_profiler.py      # Модульные тесты
├── requirements.txt          # Зависимости
└── README.md                 # Документация
```

### Компоненты

#### 1. PerformanceProfiler (performance_inspect.py)

Основной класс профайлера:

```python
class PerformanceProfiler:
    """
    Профилирование производительности:
    - Время выполнения (real/CPU)
    - Использование памяти
    - GC статистика
    - Анализ сложности через AST
    """
    
    def profile(func: Callable) -> Callable:
        """Декоратор для профилирования функции"""
    
    def _log_metrics(func_name: str, metrics: ProfileMetrics):
        """Логирование метрик"""
```

#### 2. ProfileMetrics (dataclass)

Структура для хранения метрик:

```python
@dataclass
class ProfileMetrics:
    execution_time: float       # Реальное время
    cpu_time: float             # CPU время
    memory_before_mb: float     # Память до
    memory_after_mb: float      # Память после
    peak_memory_mb: float       # Пик памяти
    gc_count_change: int        # Изменение GC
    result_size_bytes: int      # Размер результата
    time_complexity: str        # Временная сложность
    space_complexity: str       # Пространственная сложность
```

#### 3. Декораторы (auto_profile.py)

```python
def auto_profile(func: Callable) -> Callable:
    """Автоматическое профилирование функции"""

def apply_to_all_functions(module_globals: dict) -> None:
    """Применить ко всем функциям модуля"""
```

---

## API Reference

### Базовое использование

#### Вариант 1: Декорирование отдельных функций

```python
from auto_profile import auto_profile

@auto_profile
def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = fibonacci(30)
# Выведет детальную статистику
```

#### Вариант 2: Автоматическое профилирование модуля

```python
from performance import apply_to_all_functions

def func1(): ...
def func2(): ...

# Применять после определения всех функций и до их вызова; импортированные функции пропускаются.
apply_to_all_functions(globals())
```

#### Вариант 3: Программное создание профайлера

```python
from performance_inspect import PerformanceProfiler

profiler = PerformanceProfiler()

@profiler.profile
def my_function(x):
    return x ** 2

result = my_function(10)
```

### Конфигурация

#### Глобальные настройки

```python
from config import update_config, get_config, reset_config

# Получить текущую конфигурацию
config = get_config()
print(config.log_level)  # "INFO"

# Обновить настройки
update_config(
    log_level="DEBUG",
    enable_profiling=True,
    max_result_length=2000
)

# Сбросить к дефолтным
reset_config()
```

#### Доступные параметры

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `enable_profiling` | bool | `True` | Включить/выключить профилирование |
| `log_level` | str | `"INFO"` | Уровень логирования |
| `log_format` | str | `"[%(asctime)s] %(message)s"` | Формат логов |
| `max_result_length` | int | `1000` | Макс. длина вывода результата |
| `trace_memory` | bool | `True` | Отслеживать память |
| `trace_gc` | bool | `True` | Отслеживать GC |
| `analyze_complexity` | bool | `True` | Анализировать сложность |

---

## Продвинутые примеры

### 1. Сравнение алгоритмов

```python
from performance_inspect import PerformanceProfiler

profiler = PerformanceProfiler()

# Алгоритм 1: Пузырьковая сортировка O(n²)
@profiler.profile
def bubble_sort(arr):
    n = len(arr)
    arr = arr.copy()
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr

# Алгоритм 2: Быстрая сортировка O(n log n)
@profiler.profile
def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr)//2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)

import random
test_data = [random.randint(1, 1000) for _ in range(1000)]

bubble_sort(test_data)
quick_sort(test_data)
```

### 2. Асинхронные операции

```python
import asyncio
from auto_profile import auto_profile

@auto_profile
async def fetch_data(url, delay=1.0):
    """Имитация асинхронного запроса."""
    await asyncio.sleep(delay)
    return f"Data from {url}"

@auto_profile
async def process_batch(urls):
    """Параллельная обработка нескольких URL."""
    tasks = [fetch_data(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return results

# Запуск
urls = ["api.example.com/1", "api.example.com/2", "api.example.com/3"]
asyncio.run(process_batch(urls))
```

### 3. Анализ использования памяти

```python
from auto_profile import auto_profile

@auto_profile
def create_large_list(size):
    """Создание большого списка - O(n) память."""
    return [i**2 for i in range(size)]

@auto_profile
def create_matrix(rows, cols):
    """Матрица - O(n²) память."""
    return [[i*j for j in range(cols)] for i in range(rows)]

@auto_profile
def efficient_generator(size):
    """Генератор - O(1) память."""
    return (i**2 for i in range(size))

# Тесты
create_large_list(1_000_000)      # ~8MB памяти
create_matrix(1000, 1000)         # ~8MB памяти
list(efficient_generator(1_000_000))  # Преобразование в список
```

### 4. Кастомный логгер

```python
import logging
from performance_inspect import PerformanceProfiler

# Создаем свой логгер
custom_logger = logging.getLogger("my_profiler")
custom_logger.setLevel(logging.DEBUG)

handler = logging.FileHandler("profile.log", encoding='utf-8')
handler.setFormatter(logging.Formatter(
    '[%(levelname)s] %(message)s'
))
custom_logger.addHandler(handler)

# Используем с профайлером
profiler = PerformanceProfiler(logger=custom_logger)

@profiler.profile
def my_func(x):
    return x * 2

my_func(100)  # Запишется в profile.log
```

---

## Лучшие практики

### ✅ DO

1. **Используйте декораторы для важных функций**
   ```python
   @auto_profile
   def critical_algorithm(data):
       # Критичный по производительности код
       pass
   ```

2. **Профилируйте на реальных данных**
   ```python
   # Плохо: синтетические маленькие данные
   profile_function(my_module, my_func, [1, 2, 3])
   
   # Хорошо: данные близкие к production
   profile_function(my_module, my_func, real_dataset)
   ```

3. **Сравнивайте альтернативные реализации**
   ```python
   profiler.profile(algorithm_v1)(data)
   profiler.profile(algorithm_v2)(data)
   ```

4. **Настройте логирование для production**
   ```python
   update_config(log_level="WARNING", enable_profiling=False)
   ```

### ❌ DON'T

1. **Не профилируйте всё подряд**
   ```python
   # Плохо: замедляет всю программу
   apply_to_all_functions(globals())
   
   # Хорошо: только важные функции
   @auto_profile
   def slow_function(...): ...
   ```

2. **Не игнорируйте накладные расходы**
   - Сам профайлер потребляет ресурсы
   - Для точных бенчмарков используйте `timeit`

3. **Не используйте в hot path без необходимости**
   ```python
   # Избегайте профилирования в циклах
   for item in large_dataset:
       profiled_func(item)  # Плохо!
   ```

---

## Troubleshooting

### Проблема: Функция не профилируется

**Решение:**
1. Проверьте что функция импортирована корректно
2. Убедитесь что `enable_profiling=True` в конфиге
3. Проверьте уровень логирования (`log_level`)

### Проблема: Неправильная сложность

AST анализ эвристический и может ошибаться:

```python
# Может определить как O(n), хотя внутри сложный алгоритм
@auto_profile
def complex_function(n):
    for i in range(n):
        # Какая-то сложная логика
        pass
```

**Решение:** Используйте как ориентир, а не абсолютную истину.

### Проблема: Утечки tracemalloc

Вложенные и перекрывающиеся вызовы разделяют один сеанс трассировки,
управляемый счётчиком ссылок. Сеанс, запущенный этим профайлером, останавливает
только последний вызывающий. Трассировка, запущенная извне, никогда не
останавливается и не сбрасывается. Не останавливайте и не перезапускайте
трассировщик вручную, пока активны профилируемые вызовы.

Сообщаемый пик относится к общему сеансу трассировки процесса, а не к отдельно
взятой функции. `force_tracemalloc=False` разрешает заимствовать уже активную
трассировку, не запуская её. Сбои зонда системной памяти попадают в
`collection_error` и не подменяют результат или исключение функции.

### Проблема: Большие результаты обрезаются

**Решение:** Увеличьте лимит в конфиге:

```python
update_config(max_result_length=10000)
```

---

## Дополнительные ресурсы

- [examples.py](examples.py) - Расширенные примеры использования
- [tests/test_profiler.py](tests/test_profiler.py) - Модульные тесты
- [profile_cli.py --help](profile_cli.py) - Справка CLI

## Лицензия

MIT License - свободное использование с указанием автора.
