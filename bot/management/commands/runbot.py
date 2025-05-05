from django.core.management.base import BaseCommand
from django.conf import settings
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
import json
from datetime import datetime, timedelta
from asgiref.sync import sync_to_async
from bot.models import Complaint, TelegramUser, Department, ComplaintHistory, Notification
from bot.services import ComplaintAnalyzer, DeadlineTracker
from bot.utils import analyze_complaint_text

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Определяем состояния FSM
class AppealStates(StatesGroup):
    waiting_for_description = State()
    waiting_for_location = State()
    waiting_for_photo = State()
    waiting_for_category = State()

class ComplaintStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_department = State()
    waiting_for_confirmation = State()

# Категории обращений (управления)
DEPARTMENTS = {
    "akimat": "Акимат города",
    "education": "образование",
    "health": "здравоохранение",
    "utilities": "жилищно-коммунальные хозяйства",
    "transport": "транспорт",
    "culture": "культура и спорт",
    "social": "социальная защита",
    "economy": "экономика и бюджетное планирование",
    "architecture": "архитектура и градостроительство",
    "land": "земельное отношение",
    "youth": "Молодожное дело",
    "languages": "развитие языков",
    "business": "развитие предпринимательства",
    "tourism": "развитие туризма",
    "agriculture": "развитие сельского хозяйства",
    "industry": "развитие промышленности",
    "trade": "развитие торговли",
    "investment": "развитие инвестиций",
    "innovation": "развитие инноваций",
    "digital": "развитие цифровизации"
}

class Command(BaseCommand):
    help = 'Запускает Telegram бота системы ShagymQor'

    def __init__(self):
        super().__init__()
        self.bot = None
        self.dp = None
        self.storage = MemoryStorage()

    def get_main_keyboard(self):
        """
        Создает клавиатуру главного меню
        """
        keyboard = [
            [KeyboardButton(text="📝 Оставить обращение")],
            [KeyboardButton(text="📋 Мои обращения")],
            [KeyboardButton(text="📬 Уведомления")],
            [KeyboardButton(text="📊 Статистика")]
        ]
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

    def get_departments_keyboard(self):
        """Создает клавиатуру выбора управления"""
        keyboard = []
        row = []
        
        # Словарь эмодзи для управлений
        emojis = {
            "akimat": "🏛",
            "education": "📚",
            "health": "🏥",
            "utilities": "🔧",
            "transport": "🚗",
            "culture": "🎭",
            "social": "👥",
            "economy": "💰",
            "architecture": "🏗",
            "land": "🌍",
            "youth": "👨‍🎓",
            "languages": "🌐",
            "business": "💼",
            "tourism": "✈️",
            "agriculture": "🌾",
            "industry": "🏭",
            "trade": "🛍",
            "investment": "📈",
            "innovation": "💡",
            "digital": "💻"
        }
        
        for dept_id, dept_name in DEPARTMENTS.items():
            if len(row) == 2:
                keyboard.append(row)
                row = []
            emoji = emojis.get(dept_id, "📋")
            row.append(InlineKeyboardButton(
                text=f"{emoji} {dept_name}",
                callback_data=f"dept_{dept_id}"
            ))
        if row:
            keyboard.append(row)
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    async def setup_bot(self):
        """Настройка бота"""
        self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        self.dp = Dispatcher(storage=self.storage)

        # Регистрация обработчиков команд
        self.dp.message.register(self.cmd_start, lambda msg: msg.text == "/start")
        self.dp.message.register(self.cmd_help, lambda msg: msg.text == "/help")
        
        # Регистрация обработчиков кнопок
        self.dp.message.register(self.create_appeal, lambda msg: msg.text == "📝 Оставить обращение")
        self.dp.message.register(self.list_appeals, lambda msg: msg.text == "📋 Мои обращения")
        self.dp.message.register(self.show_statistics, lambda msg: msg.text == "📊 Статистика")
        self.dp.message.register(self.show_notifications, lambda msg: msg.text == "📬 Уведомления")
        
        # Регистрация обработчиков состояний FSM
        self.dp.message.register(
            self.process_complaint_message,
            StateFilter(ComplaintStates.waiting_for_message)
        )
        self.dp.callback_query.register(
            self.process_department_confirmation,
            lambda c: c.data == "confirm_department",
            StateFilter(ComplaintStates.waiting_for_confirmation)
        )
        self.dp.callback_query.register(
            self.process_department_selection,
            lambda c: c.data.startswith("dept_"),
            StateFilter(ComplaintStates.waiting_for_department)
        )

        # Обработчик всех текстовых сообщений (должен быть последним)
        self.dp.message.register(self.handle_message)

    async def handle_message(self, message: types.Message):
        """Обработчик всех текстовых сообщений"""
        if message.text and not message.text.startswith('/'):
            logger.info(f"Получено сообщение: {message.text}")
            
            # Анализируем текст и определяем управление
            department, confidence = await analyze_complaint_text(message.text)
            logger.info(f"Результат анализа: управление={department}, уверенность={confidence}")
            
            if department and confidence >= 50:  # Если уверенность больше 50%
                logger.info(f"Автоматически определено управление {department.name} с уверенностью {confidence}%")
                # Создаем обращение
                user, _ = await sync_to_async(TelegramUser.objects.get_or_create)(
                    user_id=message.from_user.id,
                    defaults={
                        'username': message.from_user.username,
                        'first_name': message.from_user.first_name,
                        'last_name': message.from_user.last_name
                    }
                )
                
                complaint = await sync_to_async(Complaint.objects.create)(
                    user=user,
                    department=department,
                    message=message.text,
                    status='new'
                )
                
                # Создаем запись в истории
                await sync_to_async(ComplaintHistory.objects.create)(
                    complaint=complaint,
                    status='new',
                    department=department,
                    comment=f'Обращение создано через Telegram бота. Автоматически определено управление с уверенностью {confidence:.1f}%'
                )
                
                await message.answer(
                    f"✅ Ваше обращение успешно создано и направлено в {department.name}!\n\n"
                    f"Номер обращения: #{complaint.id}\n"
                    f"Уверенность определения: {confidence:.1f}%\n"
                    f"Статус: Новое\n\n"
                    f"Вы можете отслеживать статус обращения на сайте или через бота.",
                    reply_markup=self.get_main_keyboard()
                )
            else:
                logger.info("Не удалось автоматически определить управление или уверенность низкая")
                # Если не удалось определить управление или уверенность низкая
                await message.answer(
                    "К сожалению, я не смог автоматически определить подходящее управление для вашего обращения.\n"
                    "Пожалуйста, выберите управление из списка ниже:",
                    reply_markup=self.get_departments_keyboard()
                )
                
                # Сохраняем текст обращения в состояние
                state = FSMContext(self.dp.storage, message.from_user.id, message.chat.id)
                await state.update_data(message=message.text)
                await state.set_state(ComplaintStates.waiting_for_department)

    async def cmd_start(self, message: types.Message):
        """Обработчик команды /start"""
        # Создаем или получаем пользователя
        user, created = await sync_to_async(TelegramUser.objects.get_or_create)(
            user_id=message.from_user.id,
            defaults={
                'username': message.from_user.username,
                'first_name': message.from_user.first_name,
                'last_name': message.from_user.last_name
            }
        )
        
        await message.answer(
            "👋 Добро пожаловать в систему Шағым Qор!\n\n"
            "Я помогу вам отправить обращение в акимат города и отслеживать его статус.\n\n"
            "🔹 Оставить обращение - создать новое обращение\n"
            "🔹 Мои обращения - просмотр статуса ваших обращений\n"
            "🔹 Статистика - информация о работе управлений\n"
            "🔹 Помощь - справка по работе с ботом\n\n"
            "Выберите действие в меню ниже:",
            reply_markup=self.get_main_keyboard()
        )

    async def cmd_help(self, message: types.Message):
        """Обработчик команды /help"""
        await self.show_help(message)

    async def show_help(self, message: types.Message):
        """Показывает справку"""
        help_text = (
            "ℹ️ Справка по работе с ботом Шағым Qор\n\n"
            "📝 Как оставить обращение:\n"
            "1. Нажмите 'Оставить обращение'\n"
            "2. Опишите проблему\n"
            "3. Укажите местоположение\n"
            "4. Прикрепите фото (при необходимости)\n"
            "5. Выберите категорию\n\n"
            "📋 Мои обращения:\n"
            "- Просмотр всех ваших обращений\n"
            "- Статус обработки\n"
            "- История рассмотрения\n\n"
            "📊 Статистика:\n"
            "- Количество обращений по категориям\n"
            "- Среднее время рассмотрения\n"
            "- Эффективность работы управлений\n\n"
            "❗️ Сроки рассмотрения обращений:\n"
            "- Простые вопросы: до 5 рабочих дней\n"
            "- Вопросы требующие проверки: до 15 рабочих дней\n"
            "- Сложные вопросы: до 30 рабочих дней"
        )
        await message.answer(help_text, reply_markup=self.get_main_keyboard())

    async def create_appeal(self, message: types.Message, state: FSMContext = None):
        """Начинает процесс создания обращения"""
        if state is None:
            state = FSMContext(self.dp.storage, message.from_user.id, message.chat.id)
        
        # Сбрасываем предыдущее состояние
        await state.clear()
        
        await message.answer(
            "📝 Пожалуйста, опишите вашу проблему или предложение.\n\n"
            "Для эффективной обработки укажите:\n"
            "- Что конкретно случилось?\n"
            "- Когда это произошло?\n"
            "- Какое решение вы предлагаете?\n\n"
            "Чем подробнее вы опишете ситуацию, тем быстрее мы сможем помочь."
        )
        await state.set_state(ComplaintStates.waiting_for_message)

    async def process_complaint_message(self, message: types.Message, state: FSMContext):
        """Обработка текста обращения"""
        user, _ = await sync_to_async(TelegramUser.objects.get_or_create)(
            user_id=message.from_user.id,
            defaults={
                'username': message.from_user.username,
                'first_name': message.from_user.first_name,
                'last_name': message.from_user.last_name
            }
        )
        
        # Анализируем текст и определяем управление
        department, confidence = await analyze_complaint_text(message.text)
        
        if department and confidence >= 50:  # Если уверенность больше 50%
            await state.update_data(
                message=message.text,
                department_id=department.id,
                suggested_department=department.name,
                confidence=confidence
            )
            
            # Запрашиваем подтверждение
            keyboard = InlineKeyboardMarkup()
            keyboard.add(
                InlineKeyboardButton(
                    text=f"Да, отправить в {department.name}",
                    callback_data="confirm_department"
                ),
                InlineKeyboardButton(
                    text="Выбрать другое управление",
                    callback_data="choose_department"
                )
            )
            
            await message.answer(
                f"Я определил, что ваше обращение относится к управлению:\n"
                f"📋 {department.name}\n"
                f"Уверенность: {confidence:.1f}%\n\n"
                f"Вы согласны с этим выбором?",
                reply_markup=keyboard
            )
            await state.set_state(ComplaintStates.waiting_for_confirmation)
        else:
            # Если не удалось определить управление или уверенность низкая
            await state.update_data(message=message.text)
            await message.answer(
                "Пожалуйста, выберите управление, в которое хотите отправить обращение:",
                reply_markup=self.get_departments_keyboard()
            )
            await state.set_state(ComplaintStates.waiting_for_department)

    async def process_department_confirmation(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Обработка подтверждения выбора управления"""
        data = await state.get_data()
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        department = await sync_to_async(Department.objects.get)(id=data['department_id'])
        
        # Создаем обращение
        complaint = await sync_to_async(Complaint.objects.create)(
            user=user,
            department=department,
            message=data['message'],
            status='new'
        )
        
        # Создаем запись в истории
        await sync_to_async(ComplaintHistory.objects.create)(
            complaint=complaint,
            status='new',
            department=department,
            comment='Обращение создано через Telegram бота'
        )
        
        await callback_query.message.edit_text(
            f"✅ Ваше обращение успешно создано!\n\n"
            f"Номер обращения: #{complaint.id}\n"
            f"Управление: {department.name}\n"
            f"Статус: Новое\n\n"
            f"Вы можете отслеживать статус обращения на сайте или через бота."
        )
        await state.clear()

    async def process_department_selection(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Обработка выбора управления вручную"""
        dept_id = callback_query.data.replace("dept_", "")
        data = await state.get_data()
        
        # Получаем пользователя
        user, _ = await sync_to_async(TelegramUser.objects.get_or_create)(
            user_id=callback_query.from_user.id,
            defaults={
                'username': callback_query.from_user.username,
                'first_name': callback_query.from_user.first_name,
                'last_name': callback_query.from_user.last_name
            }
        )
        
        # Получаем или создаем управление
        department, _ = await sync_to_async(Department.objects.get_or_create)(
            name=DEPARTMENTS[dept_id],
            defaults={'description': f'Управление {DEPARTMENTS[dept_id]}'}
        )
        
        # Создаем обращение
        complaint = await sync_to_async(Complaint.objects.create)(
            user=user,
            department=department,
            message=data['message'],
            status='new'
        )
        
        # Создаем запись в истории
        await sync_to_async(ComplaintHistory.objects.create)(
            complaint=complaint,
            status='new',
            department=department,
            comment='Обращение создано через Telegram бота. Управление выбрано пользователем.'
        )
        
        await callback_query.message.edit_text(
            f"✅ Ваше обращение успешно создано и направлено в {department.name}!\n\n"
            f"Номер обращения: #{complaint.id}\n"
            f"Статус: Новое\n\n"
            f"Вы можете отслеживать статус обращения на сайте или через бота."
        )
        await state.clear()

    async def list_appeals(self, message: types.Message):
        """Показывает список обращений пользователя"""
        get_user = sync_to_async(TelegramUser.objects.get)
        get_complaints = sync_to_async(
            lambda u: [
                {
                    'id': c.id,
                    'department_name': c.department.name if c.department else 'Не указана',
                    'created_at': c.created_at,
                    'status': c.get_status_display() if hasattr(c, 'get_status_display') else c.status
                }
                for c in Complaint.objects.filter(user=u).select_related('department').order_by('-created_at')
            ]
        )
        
        user = await get_user(user_id=message.from_user.id)
        complaints = await get_complaints(user)
        
        if not complaints:
            await message.answer(
                "📋 Ваши обращения:\n\n"
                "На данный момент у вас нет активных обращений.\n"
                "Чтобы создать новое обращение, нажмите '📝 Оставить обращение'",
                reply_markup=self.get_main_keyboard()
            )
            return

        response = "📋 Ваши обращения:\n\n"
        for complaint in complaints:
            status_emoji = {
                "new": "🆕",
                "in_progress": "⏳",
                "completed": "✅",
                "overdue": "❌"
            }.get(complaint['status'], "❓")
            
            response += (
                f"{status_emoji} Обращение #{complaint['id']}\n"
                f"📝 Категория: {complaint['department_name']}\n"
                f"📅 Дата: {complaint['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
                f"📋 Статус: {complaint['status']}\n\n"
            )

        await message.answer(response, reply_markup=self.get_main_keyboard())

    async def show_statistics(self, message: types.Message):
        """Показывает статистику обращений"""
        # Получаем статистику из базы данных
        get_stats = sync_to_async(lambda: {
            'total': Complaint.objects.count(),
            'completed': Complaint.objects.filter(status='completed').count(),
            'in_progress': Complaint.objects.filter(status='in_progress').count(),
            'new': Complaint.objects.filter(status='new').count()
        })
        
        stats = await get_stats()
        
        stats_text = (
            "📊 Статистика работы управлений:\n\n"
            f"📈 Всего обращений: {stats['total']}\n"
            f"✅ Решено: {stats['completed']}\n"
            f"⏳ В работе: {stats['in_progress']}\n"
            f"🆕 Новых: {stats['new']}\n\n"
        )

        # Статистика по категориям
        get_dept_stats = sync_to_async(lambda dept_name: {
            'department': Department.objects.filter(name=dept_name).first(),
            'total': Complaint.objects.filter(department__name=dept_name).count(),
            'completed': Complaint.objects.filter(department__name=dept_name, status='completed').count()
        })

        for dept_id, dept_name in DEPARTMENTS.items():
            dept_stats = await get_dept_stats(dept_name)
            if dept_stats['department'] and dept_stats['total'] > 0:
                efficiency = (dept_stats['completed'] / dept_stats['total']) * 100
                stats_text += (
                    f"{dept_name}:\n"
                    f"- Всего обращений: {dept_stats['total']}\n"
                    f"- Решено: {dept_stats['completed']}\n"
                    f"- Эффективность: {efficiency:.1f}%\n\n"
                )

        await message.answer(stats_text, reply_markup=self.get_main_keyboard())

    async def show_notifications(self, message: types.Message):
        """
        Показывает список уведомлений пользователя
        """
        user = await sync_to_async(TelegramUser.objects.get)(user_id=message.from_user.id)
        notifications = await sync_to_async(list)(
            Notification.objects.filter(user=user).order_by('-created_at')[:10]
        )
        
        if not notifications:
            await message.answer("У вас пока нет уведомлений")
            return
        
        text = "📬 Ваши последние уведомления:\n\n"
        for notification in notifications:
            text += f"• {notification.message}\n"
            text += f"  {notification.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        
        await message.answer(text)

    async def run_bot(self):
        """Запуск бота"""
        try:
            await self.setup_bot()
            await self.dp.start_polling(self.bot)
        finally:
            if self.bot:
                await self.bot.session.close()

    def handle(self, *args, **options):
        """Точка входа для команды управления"""
        try:
            self.stdout.write(self.style.SUCCESS('Запуск бота...'))
            asyncio.run(self.run_bot())
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка при запуске бота: {e}')) 