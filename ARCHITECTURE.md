# 🏗️ Архитектура OpenDoor

## 📊 Общее описание

OpenDoor - это полнофункциональное приложение для управления системой открытия дверей на основе распознавания жестов рук. Приложение состоит из трёх основных компонентов, работающих параллельно:

```
┌─────────────────────────────────────────────────────────────────┐
│                    OpenDoor Application                          │
│                      (run.py - главный entry point)             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │ 🎥 Video Thread  │  │ 👷 Worker Thread │  │ 🌐 Flask App   │ │
│  │ (core/analyzer)  │  │ (services/worker)│  │ (app/routes)   │ │
│  │                  │  │                  │  │                │ │
│  │ - Видеопоток     │  │ - I/O операции   │  │ - Веб-интерфейс│
│  │ - MediaPipe      │  │ - БД операции    │  │ - API endpoints│
│  │ - Распознавание  │  │ - Открытие двери │  │ - Аутентификация│
│  │   жестов         │  │ - Сохранение     │  │                │
│  │                  │  │   скриншотов     │  │                │
│  └─────────┬────────┘  └─────────┬────────┘  └────────────────┘
│            │                     │
│            └─────────┬───────────┘
│                      │ task_queue
│                      ▼
│           ┌──────────────────────┐
│           │   Queue of Tasks     │
│           │ (services/worker.py) │
│           └──────────────────────┘
│
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Поток данных

### 1. Видео обработка и распознавание (core/analyzer.py)

```
Видеопоток с интеркома
        ↓
   Получение сеанса (services/novotelecom.py)
        ↓
 Получение URL потока (services/novotelecom.py)
        ↓
  Читаем видеопоток (OpenCV)
        ↓
 Конвертируем BGR → RGB
        ↓
Обрабатываем MediaPipe Hands
        ↓
    Классифицируем жест (core/recognition.py)
        ↓
   Проверяем комбинацию жестов
   (TiDishi x5 + Rock x2)
        ↓
  Если комбинация верна → Ставим в очередь:
     ├─ open_door (запрос на открытие)
     └─ save_screenshot (сохранение кадра)
```

### 2. Обработка очереди задач (services/worker.py)

```
Task из очереди
        ↓
   Тип задачи?
   ├─ open_door        → services/novotelecom.send_post_open_door_request()
   │                   → db/database.insert_door_open()
   │
   ├─ get_session      → services/novotelecom.make_session()
   │
   ├─ get_stream_url   → services/novotelecom.get_stream_url()
   │
   ├─ save_screenshot  → cv2.imwrite() → utils/storage
   │
   └─ db_insert_gesture → db/database.insert_gesture()
```

### 3. Веб-интерфейс и API (app/routes.py)

```
HTTP Request
        ↓
Проверка сеанса (utils/auth.is_session_valid)
        ↓
   Маршрут?
   ├─ /login          → Аутентификация (utils/auth.verify_password)
   ├─ /live           → Лайв трансляция
   ├─ /calendar       → Календарь (utils/storage.get_calendar_data)
   ├─ /day/<date>     → Детали дня (db/database.get_door_opens_for_day)
   ├─ /api/stats      → Статистика (FPS, frames)
   ├─ /api/current_frame → Текущий кадр
   └─ /api/recent_opens → Последние открытия
```

---

## 📂 Модули и их ответственность

### app/ - Flask веб-приложение

**routes.py**
- Главное Flask приложение
- Маршруты (routes) для всех страниц
- API endpoints для фронтенда
- Обработчик ошибок (404, 500)

**Зависимости:**
- Flask, flask-session
- config.settings (конфигурация)
- utils.auth (аутентификация)
- utils.storage (управление файлами)
- db.database (работа с БД)

---

### core/ - Основная обработка

**analyzer.py** - Основной цикл обработки видео
- Получение видеопотока с интеркома
- Обработка каждого кадра
- Применение MediaPipe для распознавания рук
- Классификация жестов
- Проверка комбинаций жестов
- Ставит задачи в очередь

**recognition.py** - Алгоритмы распознавания жестов
- `finger_is_open()` - проверка открыта ли палец
- `open_fingers()` - количество открытых пальцев
- `classify_gesture()` - классификация жеста (TiDishi, Rock, Victory и т.д.)

**Зависимости:**
- MediaPipe, OpenCV, NumPy
- core/recognition (классификация жестов)
- config.settings (параметры распознавания)
- services/worker (постановка задач в очередь)
- utils.storage (пути скриншотов)
- utils.logger (логирование)

---

### services/ - Сервисы и асинхронные задачи

**worker.py** - Рабочие потоки
- `Task` dataclass - описание задачи
- `io_worker()` - основной рабочий цикл
- Обработка всех типов задач (open_door, save_screenshot, db_insert и т.д.)
- Потокобезопасная очередь (queue.Queue)

**novotelecom.py** - Интеграция с API интеркома
- `make_session()` - создание сеанса на сайте видео.2090000.ru
- `get_stream_url()` - получение ссылки на видеопоток
- `send_post_open_door_request()` - отправка запроса на открытие двери

**Зависимости:**
- requests (HTTP запросы)
- psycopg2 (работа с БД)
- OpenCV (сохранение скриншотов)
- db.database (вставка данных)
- utils.logger (логирование)

---

### db/ - Слой работы с БД

**database.py** - PostgreSQL операции
- `Database` class - управление подключением
  - `.execute()` - выполнение INSERT/UPDATE/DELETE
  - `.fetch_one()` - получение одной строки
  - `.fetch_all()` - получение всех строк
- Функции-помощники:
  - `insert_gesture()` - вставка найденного жеста
  - `insert_door_open()` - вставка события открытия двери
  - `get_door_opens_for_day()` - получение открытий за день
  - `get_recent_door_opens()` - последние открытия

**Логирование SQL ошибок:**
Все SQL ошибки логируются через `utils.logger.log_error()` в файл `logs/database.log`

**Зависимости:**
- psycopg2 (драйвер PostgreSQL)
- config.settings (параметры подключения)
- utils.logger (логирование ошибок)

---

### config/ - Конфигурация

**settings.py** - Централизованная конфигурация
- БД параметры (PGHOST, PGPORT, и т.д.)
- API ключи (BEARER_TOKEN, LOGIN, PASSWORD)
- Веб-параметры (WEB_HOST, WEB_PORT, SECRET_KEY)
- Параметры распознавания (GESTURE_MIN_DETECTION_CONFIDENCE и т.д.)
- Параметры хранилища (SCREENSHOT_MAX_PER_DAY и т.д.)
- Пользователи по умолчанию (USERS)

**Источник конфигурации:**
1. Переменные окружения (.env файл)
2. Значения по умолчанию в коде

---

### utils/ - Утилиты

**logger.py** - Система логирования
- `setup_logger()` - создание логгера с обработчиками
- Разделение логов по модулям (main.log, worker.log, door_open.log, database.log)
- Уровни логирования:
  - Console: WARNING и выше
  - File: DEBUG и выше (все сообщения)

**storage.py** - Управление скриншотами
- `get_screenshot_path()` - генерирует путь год/месяц/день
- `get_day_screenshots()` - получает скриншоты за день
- `get_calendar_data()` - данные для календаря
- `cleanup_old_screenshots()` - удаление старых файлов
- `get_screenshot_info()` - парсит информацию из имени файла

**auth.py** - Аутентификация и сеансы
- `verify_password()` - проверка пароля
- `login_user()` - создание сеанса
- `logout_user()` - завершение сеанса
- `is_session_valid()` - проверка валидности сеанса (24 часа)
- `require_login` - декоратор для защиты endpoints
- `get_current_user()` - получение текущего пользователя

---

## 🗄️ Структура базы данных

```sql
-- Таблица найденных жестов (для отладки/статистики)
CREATE TABLE find_gesture (
    id SERIAL PRIMARY KEY,
    gesture VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица событий открытия двери
CREATE TABLE case_of_open (
    id SERIAL PRIMARY KEY,
    img_path VARCHAR(500) NOT NULL,       -- путь к скриншоту
    response_code INTEGER,                -- HTTP статус код
    response_text TEXT,                   -- ответ от API
    gestures_used VARCHAR(500),           -- использованные жесты
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 📊 Хранилище скриншотов

```
screenshot_of_open/
├── 2026/
│   ├── 06/
│   │   ├── 11/
│   │   │   ├── 14-35-22_TiDishi+Rock.png
│   │   │   ├── 16-48-10_TiDishi+Rock.png
│   │   │   └── ...
│   │   ├── 12/
│   │   │   └── ...
│   └── ...
└── ...
```

Структура: `YYYY/MM/DD/HH-MM-SS_Gesture1+Gesture2+Gesture3.png`

---

## 🚀 Процесс запуска

```python
# run.py
main()
├─ start_io_workers(n=1)
│  └─ Запускает N рабочих потоков (обработка очереди)
│
├─ start_processing_thread()
│  └─ Запускает поток видео обработки
│
└─ Flask.run(host=WEB_HOST, port=WEB_PORT)
   └─ Запускает веб-приложение
```

**Порядок запуска важен:**
1. Рабочие потоки (должны быть готовы обрабатывать задачи)
2. Поток видео (начинает ставить задачи в очередь)
3. Flask приложение (должно быть доступно сразу)

---

## 🔐 Безопасность

### Аутентификация
- Сеансы хранятся на сервере (flask-session)
- Таймаут сеанса: 24 часа
- Все защищенные endpoints требуют валидного сеанса

### Логирование SQL ошибок
Все ошибки БД логируются с полным текстом SQL запроса в:
```
logs/database.log
```

### Пароли
- Храняются в переменных окружения (.env)
- По умолчанию: простые пароли (ДОЛЖНЫ быть изменены в production)

---

## ⚡ Производительность

### Оптимизации
- Пропускаем обработку каждого N-го кадра (FRAME_SKIP_RATE = 2)
- Используем окно жестов (GESTURE_WINDOW_SIZE = 20)
- Кэширование сеансов
- Индексы на БД для быстрого поиска по дате

### Наблюдение за производительностью
```bash
# FPS и количество кадров в окне
curl http://localhost:8000/api/stats

# Просмотр логов
tail -f logs/door_open.log
```

---


