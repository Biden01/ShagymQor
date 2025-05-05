from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Инициализация бота
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

@csrf_exempt
def webhook(request):
    """Обработка вебхуков от Telegram"""
    if request.method == 'POST':
        try:
            update = Update.de_json(json.loads(request.body), bot)
            application.process_update(update)
            return HttpResponse(status=200)
        except Exception as e:
            return HttpResponse(str(e), status=500)
    return HttpResponse(status=400)

def bot_status(request):
    """Проверка статуса бота"""
    try:
        bot_info = bot.get_me()
        return JsonResponse({
            'status': 'ok',
            'bot_name': bot_info.first_name,
            'username': bot_info.username
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500) 