#Структура папок:

/backtend
    python app here
/frontend
    vue.js app here
/database
    sqlLite database here    
.gitignore
*.md
run.bat
run.sh

run файлы должны уметь проверять версии Python и Node.js и сразу запускать оба сервиса- бэк и фронт.

Python запускаем в venv.

Директорию /database добавить в .gitignore

Используем vue.js и vuetify для интерфейса.

Используем i18n для всего текста в проекте. Делаем два словаря на Английском и Русском.
Кнопку можно добавить в шапку страницы.

Ипользуем vue router для роутинга.

Настроки темы и основных цветом для форнта вынести в отдельный файл.

Используем python и FastAPI + SQLAlchemy для бэка который будет обращаться на тестовый апи по ключу.

Система работает без авторизации и интрефейс будет доступен юзеру сразу.

Базовый URL API : https://keitaro-for-tests.etolegko.com/admin_api/v1
header: Api-Key

Документация официального api keitaro: https://admin-api.docs.keitaro.io

Доступные методы на keitaro-for-tests.etolegko.com:

GET /campaigns	Ваши кампании, новые сверху. Параметры offset и limit.
POST /campaigns	Создать кампанию. Обязательно name; alias, если не задан, стенд придумает сам.
GET /campaigns/{id}	Одна кампания.
PUT /campaigns/{id}	Изменить кампанию: меняются только присланные поля.
DELETE /campaigns/{id}	Удалить кампанию вместе с потоками. Архива нет.
POST /campaigns/{id}/enable, /disable	Включить, выключить.
GET /campaigns/{id}/streams	Потоки кампании по порядку position.
POST /streams	Создать поток. Обязательны campaign_id и name.
GET /streams/{id}	Один поток с фильтрами и офферами.
PUT /streams/{id}	Изменить поток. Поле offers заменяет состав целиком, поле filters — фильтры целиком.
DELETE /streams/{id}	Удалить поток.
POST /streams/{id}/enable, /disable	Включить, выключить.
GET /offers, /offers/{id}	Офферы. Только чтение.
GET /groups?type=campaigns	Группы кампаний. Только чтение.
GET /domains	Домены. Только чтение.
GET /traffic_sources	Источники. Только чтение.

В качестве БД будем ипользовать SQLite, базу создаем миграцией.
Таблицы в бд создаем миграциями.

# Структура бд:

campaigns
offers
streams



Поля в бд будут аналогичны тем что мы получаем из API.
