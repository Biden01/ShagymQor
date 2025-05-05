# Система обработки жалоб ShagymQor

Система автоматизации обработки жалоб граждан, полученных через Instagram.

## Функциональность

- Прием и обработка жалоб через Instagram
- Автоматическое распределение жалоб по управлениям
- Отслеживание статуса обработки жалоб
- Аналитика и отчетность
- Многоязычный интерфейс (казахский, русский)

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/ShagymQor.git
cd ShagymQor
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
# или
venv\Scripts\activate  # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл .env в корневой директории проекта:
```bash
cp .env.example .env
```

5. Отредактируйте файл .env, указав необходимые настройки:
```
SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
INSTAGRAM_USERNAME=your_instagram_username
INSTAGRAM_PASSWORD=your_instagram_password
```

6. Примените миграции:
```bash
python manage.py migrate
```

7. Создайте суперпользователя:
```bash
python manage.py createsuperuser
```

8. Запустите Redis (для Celery):
```bash
redis-server
```

9. Запустите Celery worker:
```bash
celery -A ShagymQor worker -l info
```

10. Запустите сервер разработки:
```bash
python manage.py runserver
```

## Использование

1. Откройте браузер и перейдите по адресу http://localhost:8000
2. Войдите в систему с учетными данными суперпользователя
3. Настройте управления и ответственных сотрудников
4. Система автоматически начнет получать сообщения из Instagram

## Структура проекта

```
ShagymQor/
├── manage.py
├── requirements.txt
├── README.md
├── .env.example
└── ShagymQor/
    ├── __init__.py
    ├── settings.py
    ├── urls.py
    ├── wsgi.py
    ├── asgi.py
    ├── celery.py
    └── apps/
        └── complaints/
            ├── __init__.py
            ├── models.py
            ├── forms.py
            ├── views.py
            ├── urls.py
            ├── admin.py
            ├── tasks.py
            └── templates/
                ├── base.html
                ├── complaint_list.html
                ├── complaint_detail.html
                ├── analytics.html
                └── department_list.html
```
