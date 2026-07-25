# 🎯 Performance Profiler v2.0 - Краткий обзор

## Что это?

Профессиональный инструмент для комплексного анализа производительности Python кода с детальными метриками и автоматическим определением алгоритмической сложности.

---

## 🚀 Быстрый старт

### 1. Установка

```bash
cd performance
pip install -r requirements.txt
```

### 2. Первое профилирование

```bash
# CLI способом
python profile_cli.py math factorial 100

# Или в коде
python test.py
```

### 3. Результат

```
============================================================
🚀 Профилирование: factorial из модуля 'math'
📋 Аргументы: [100]
============================================================

⏳ Запуск синхронной функции...
[01:18:24] Функция: factorial
  Временная сложность: O(?)
  Пространственная сложность: O(?)
  Время выполнения: 0.000014 c
  CPU time: 0.000000 c
  Память (до/после): 24.56 / 24.57 МБ
  Пиковая память: 0.00 МБ
  Изменение GC count: -1
  Размер результата: 96 байт
==================================================

✅ Успешно завершено
```

---

## 📦 Структура проекта

```
performance/
├── 🔧 Ядро
│   ├── performance_inspect.py    # Профайлер + AST анализ
│   ├── auto_profile.py           # Декораторы
│   └── config.py                 # Конфигурация
│
├── 💻 Интерфейсы
│   ├── profile_cli.py            # CLI для профилирования
│   └── examples.py               # Примеры использования
│
├── 🧪 Тестирование
│   ├── test.py                   # Демонстрационные тесты
│   └── tests/
│       └── test_profiler.py      # 17 модульных тестов
│
├── 📚 Документация
│   ├── README.md                 # Быстрый старт
│   ├── DOCUMENTATION.md          # Полное руководство
│   ├── CHANGELOG.md              # История изменений
│   └── REFACTORING_REPORT.md     # Отчет о рефакторинге
│
└── ⚙️ Конфигурация
    ├── requirements.txt          # Зависимости
    └── __init__.py               # Экспорт API
```

---

## 🎨 Основные возможности

### 1. Профилирование функций

```python
from auto_profile import auto_profile

@auto_profile
def my_function(n):
    return sum(range(n))

my_function(1_000_000)
```

**Метрики:**
- 🕐 Время выполнения (real/CPU)
- 💾 Использование памяти (до/после/пик)
- 🗑️ GC статистика
- 📦 Размер результата
- 📈 Алгоритмическая сложность

### 2. CLI интерфейс

```bash
# Профилирование функции
python profile_cli.py json dumps '{"key": "value"}'

# Профилирование скрипта
python profile_cli.py --file benchmark.py

# С именованными аргументами
python profile_cli.py my_module func 10 --kwargs '{"x": 5}'
```

### 3. Автоматическое профилирование модуля

```python
# В начале файла
from auto_profile import apply_to_all_functions
apply_to_all_functions(globals())

# Все функции ниже будут профилироваться
def func1(): ...
def func2(): ...
```

### 4. Конфигурация

```python
from config import update_config

update_config(
    log_level="DEBUG",
    max_result_length=2000,
    analyze_complexity=True
)
```

---

## 📊 Измеряемые метрики

| Метрика | Описание | Пример |
|---------|----------|--------|
| **Время выполнения** | Реальное время от начала до конца | `0.215818 c` |
| **CPU time** | Время процессора (без I/O) | `0.218750 c` |
| **Память до/после** | Потребление памяти процессом | `23.00 / 23.55 МБ` |
| **Пиковая память** | Максимальное потребление | `1.11 МБ` |
| **GC count** | Изменение счетчиков GC | `14` |
| **Размер результата** | Память возвращаемого значения | `202252 байт` |
| **Временная сложность** | O-нотация по времени | `O(n²)` |
| **Пространственная сложность** | O-нотация по памяти | `O(n)` |

---

## 🔍 Анализ алгоритмической сложности

Автоматическое определение через AST:

### Примеры

```python
@auto_profile
def constant_func(n):
    return n * 2
# Определяется как O(1)

@auto_profile  
def linear_func(n):
    total = 0
    for i in range(n):
        total += i
    return total
# Определяется как O(n)

@auto_profile
def quadratic_func(n):
    for i in range(n):
        for j in range(n):
            pass
# Определяется как O(n²)
```

---

## 📚 Документы

### Для быстрого старта
- **[README.md](README.md)** - установка и базовое использование

### Для изучения
- **[DOCUMENTATION.md](DOCUMENTATION.md)** - полное руководство
  - Архитектура
  - API Reference
  - Продвинутые примеры
  - Best practices
  - Troubleshooting

### Для понимания изменений
- **[CHANGELOG.md](CHANGELOG.md)** - история версий
- **[REFACTORING_REPORT.md](REFACTORING_REPORT.md)** - детальный отчет о рефакторинге

---

## 🧪 Запуск тестов

```bash
# Модульные тесты
python -m pytest tests/test_profiler.py -v

# Демонстрационные тесты
python test.py
```

**Покрытие:**
- ✅ 17 passing тестов
- ✅ Sync/async функции
- ✅ Анализ сложности
- ✅ Edge cases

---

## 💡 Примеры использования

### 1. Сравнение алгоритмов

```python
from performance_inspect import PerformanceProfiler

profiler = PerformanceProfiler()

@profiler.profile
def bubble_sort(arr):
    # O(n²)
    ...

@profiler.profile
def quick_sort(arr):
    # O(n log n)
    ...

bubble_sort(test_data)
quick_sort(test_data)
```

### 2. Асинхронные операции

```python
@auto_profile
async def fetch_data(url):
    await asyncio.sleep(1)
    return f"Data from {url}"

asyncio.run(fetch_data("api.example.com"))
```

### 3. Интенсивное использование памяти

```python
@auto_profile
def create_matrix(n):
    return [[i*j for j in range(n)] for i in range(n)]

create_matrix(1000)  # O(n²) память
```

Больше примеров в **[examples.py](examples.py)**

---

## ⚙️ Конфигурация

### Параметры

| Параметр | По умолчанию | Описание |
|----------|--------------|----------|
| `enable_profiling` | `True` | Включить/выключить |
| `log_level` | `INFO` | Уровень логов |
| `max_result_length` | `1000` | Макс. длина вывода |
| `analyze_complexity` | `True` | Анализ O-нотации |
| `trace_memory` | `True` | Трек памяти |
| `trace_gc` | `True` | Трек GC |

### Пример настройки

```python
from config import update_config

# Production режим
update_config(
    enable_profiling=False,
    log_level="WARNING"
)

# Debug режим
update_config(
    log_level="DEBUG",
    max_result_length=5000
)
```

---

## 🎯 Best Practices

### ✅ DO

1. Используйте декоратор для критичных функций
2. Профилируйте на реалистичных данных
3. Сравнивайте альтернативные реализации
4. Настраивайте логирование для production

### ❌ DON'T

1. Не профилируйте всё подряд (замедляет код)
2. Не игнорируйте накладные расходы профайлера
3. Не используйте в hot path без необходимости

---

## 🔄 Migration с v1.x на v2.0

### Изменения

1. **Импорт:**
   ```python
   # Было:
   from performance_inspect import profiler
   
   # Стало:
   from performance import auto_profile
   ```

2. **Метрики:**
   ```python
   # Было: словарь
   metrics['execution_time']
   
   # Стало: dataclass
   metrics.execution_time
   ```

3. **Конфигурация:**
   ```python
   # Новая централизованная система
   from config import update_config
   update_config(log_level="DEBUG")
   ```

См. **[CHANGELOG.md](CHANGELOG.md)** для деталей.

---

## 📞 Поддержка

- 📖 Документация: [DOCUMENTATION.md](DOCUMENTATION.md)
- 🐛 Баги: открывайте issues
- 💡 Ideas: PR welcome!

---

## 📊 Статистика проекта

| Метрика | Значение |
|---------|----------|
| Версия | 2.0.0 |
| Файлов | 13 |
| Строк кода | ~1500 |
| Тестов | 17 |
| Документации | 655 строк |
| Зависимости | psutil |
| Python | 3.7+ |

---

## 🎓 Ключевые улучшения v2.0

- ✅ Устранено дублирование кода (90%)
- ✅ Полная типизация всех API
- ✅ Контекстные менеджеры для ресурсов
- ✅ Централизованная конфигурация
- ✅ 17 модульных тестов
- ✅ Расширенная документация
- ✅ Улучшенный AST анализ
- ✅ Исправлены все известные баги

---

## 🚀 Готово к использованию!

```bash
# Просто запустите
python profile_cli.py math factorial 1000

# Или импортируйте в коде
from performance import auto_profile

@auto_profile
def your_function():
    # ваш код
    pass
```

**Статус:** ✅ Production Ready  
**Версия:** 2.0.0  
**Дата:** 2026-03-30
