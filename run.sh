#!/bin/bash

# Создаем необходимые директории
echo "Создание директорий..."
mkdir -p static media staticfiles

# Проверяем, запущен ли Redis
if ! pgrep redis-server > /dev/null; then
    echo "Запуск Redis..."
    redis-server &
    sleep 2
fi

# Применяем миграции
echo "Применение миграций..."
./venv/bin/python manage.py migrate

# Собираем статические файлы
echo "Сбор статических файлов..."
./venv/bin/python manage.py collectstatic --noinput

# Запускаем Celery worker
echo "Запуск Celery worker..."
./venv/bin/celery -A ShagymQor worker -l info &

# Запускаем Celery beat
echo "Запуск Celery beat..."
./venv/bin/celery -A ShagymQor beat -l info &

# Запускаем Django сервер
echo "Запуск Django сервера..."
./venv/bin/python manage.py runserver 0.0.0.0:8000 &

# Запускаем Telegram бота
echo "Запуск Telegram бота..."
./venv/bin/python manage.py runbot &

echo "Все компоненты запущены!"
echo "Для остановки всех процессов используйте: pkill -f 'celery|runserver|runbot'"

# Ждем завершения всех процессов
wait 