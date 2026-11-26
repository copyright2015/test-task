# Campaign Manager

## Русский

Интерфейс для управления кампаниями через тестовый API Keitaro.

### Требования

- Python 3.10+
- Node.js 18+

Скопируйте `.env.example` в `.env` и укажите `KEITARO_API_KEY` для работы с API. Не добавляйте `.env` в репозиторий.

Запустите `run.bat` в Windows или `bash run.sh` в macOS/Linux. Скрипты создают виртуальное окружение Python, устанавливают зависимости, применяют миграции SQLite и запускают API и интерфейс.

- Интерфейс: http://127.0.0.1:5173
- Документация API: http://127.0.0.1:8000/docs

## English

Campaign management UI for the Keitaro test API.

### Requirements

- Python 3.10+
- Node.js 18+

Copy `.env.example` to `.env` and set `KEITARO_API_KEY` before using API-backed features. Do not commit `.env`.

Run `run.bat` on Windows or `bash run.sh` on macOS/Linux. The scripts create a Python virtual environment, install dependencies, apply SQLite migrations, and start the API and UI.

- UI: http://127.0.0.1:5173
- API docs: http://127.0.0.1:8000/docs
