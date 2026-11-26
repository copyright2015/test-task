# Campaign Manager

## Русский

Интерфейс для управления кампаниями через тестовый API Keitaro.

### Требования

- Python 3.10+
- Node.js 18+

## Запуск

Скопируйте `.env.example` в `.env` и укажите `KEITARO_API_KEY` для работы с API. Не добавляйте `.env` в репозиторий.

Запустите `run.bat` в Windows или `bash run.sh` в macOS/Linux. Скрипты создают виртуальное окружение Python, устанавливают зависимости, применяют миграции SQLite и запускают API и интерфейс.

- Интерфейс: http://127.0.0.1:5173
- Документация API: http://127.0.0.1:8000/docs


## Ручной запуск

Перед запуском настройте `.env`, как описано выше. Выполняйте команды из корня проекта в двух отдельных терминалах: первый для API, второй для интерфейса. Для остановки каждого сервиса нажмите `Ctrl+C` в соответствующем терминале.


### Windows (PowerShell)

Терминал 1 — подготовка и запуск API / Terminal 1 — set up and start the API:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
New-Item -ItemType Directory -Force -Path database | Out-Null
.\.venv\Scripts\python.exe -m alembic -c backend\alembic.ini upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload
```

Терминал 2 — подготовка и запуск интерфейса / Terminal 2 — set up and start the UI:

```powershell
Set-Location frontend
npm install
npm run dev
```

### macOS / Linux (Bash)

Терминал 1 — подготовка и запуск API / Terminal 1 — set up and start the API:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
mkdir -p database
.venv/bin/python -m alembic -c backend/alembic.ini upgrade head
.venv/bin/python -m uvicorn app.main:app --app-dir backend --reload
```

Терминал 2 — подготовка и запуск интерфейса / Terminal 2 — set up and start the UI:

```bash
cd frontend
npm install
npm run dev
```
