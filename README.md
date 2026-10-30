# Система аналитики заполненности библиотеки в реальном времени

Учебный проект на **Python + PostgreSQL + SQL + Streamlit**.

Система моделирует поток событий входа и выхода студентов из одного помещения библиотеки. Генератор данных является отдельным модулем и в перспективе заменяется реальным считывателем студенческих пропусков.

## Архитектура

Источник событий (сейчас генератор) → Python → PostgreSQL → SQL-аналитика → Streamlit Dashboard.

## Быстрый запуск

### 1. Установить Python 3.11+

Проверка:

```bash
python --version
```

### 2. Запустить PostgreSQL

Самый простой способ — Docker Desktop:

```bash
docker compose up -d
```

Проверить:

```bash
docker ps
```

Должен быть контейнер `library-postgres`.

### 3. Создать виртуальное окружение

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Установить зависимости

```bash
pip install -r requirements.txt
```

### 5. Создать `.env`

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

### 6. Инициализировать БД

```bash
python src/init_db.py
```

### 7. Заполнить БД историей

```bash
python src/seed_history.py --hours 8
```

### 8. Запустить генератор событий

В отдельном терминале из корня проекта:

```bash
python src/generator.py --interval 2
```

Генератор будет каждые 2 секунды создавать события ENTER/EXIT.

### 9. Запустить dashboard

Ещё один терминал:

```bash
streamlit run src/app.py
```

После запуска Streamlit откроет локальный адрес, обычно `http://localhost:8501`.

## Сброс БД

```bash
python src/init_db.py --reset
```

## Остановка PostgreSQL

```bash
docker compose down
```

## Тесты

```bash
pytest -q
```

## Перспективное развитие

Генератор событий заменяется модулем интеграции со считывателем студенческих пропусков. Слой PostgreSQL, аналитические запросы и dashboard при этом сохраняются.
