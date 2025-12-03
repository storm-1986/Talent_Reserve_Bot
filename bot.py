import asyncio
import os
import re
import urllib3
import json
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
API_USERNAME = os.getenv('API_USERNAME')
API_PASSWORD = os.getenv('API_PASSWORD')

# Настройка логирования - УБИРАЕМ ЛИШНИЕ ЛОГИ
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

# Настройка нашего логгера
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Создаем форматтер
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Создаем папку logs если ее нет
logs_dir = 'logs'
os.makedirs(logs_dir, exist_ok=True)

# Файловый обработчик
log_filename = f'survey_bot_{datetime.now().strftime("%Y%m%d")}.log'
log_filepath = os.path.join(logs_dir, log_filename)
file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Консольный обработчик (только для нашего логгера)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Добавляем обработчики только к нашему логгеру
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Отключаем предупреждения о небезопасном HTTPS
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Приветственное сообщение
WELCOME_MESSAGE = """Добро пожаловать в бот опроса кадрового резерва ОАО «Савушкин продукт»!

*Уважаемые коллеги!* Настоящий опрос проводится среди сотрудников группы компаний ОАО «Савушкин продукт» с целью эффективного планирования карьерного развития, формирования кадрового резерва, а также выявления инициативных и целеустремлённых специалистов, готовых расти и развиваться вместе с компанией, применяя свои знания и навыки на её производственных площадках.

Просим вас быть искренними — прежде всего перед самими собой. Опрос займёт всего несколько минут.

*Благодарим за ваше участие и уделённое время!*"""

# Информация о кадровом резерве
RESERVE_INFO = """📊 **О кадровом резерве**

Кадровый резерв — это программа развития сотрудников компании, направленная на:
• Выявление перспективных специалистов
• Подготовку к руководящим должностям  
• Профессиональное развитие и рост
• Формирование пула внутренних кандидатов

Участие в программе позволяет:
✅ Получить новые знания и навыки
✅ Рассматриваться на перспективные должности
✅ Участвовать в проектах развития компании
✅ Получить поддержку в карьерном росте"""

# Помощь
HELP_TEXT = """❓ **Помощь**

**Доступные команды:**
/start - начать работу с ботом
/menu - открыть главное меню  
/help - показать эту справку
/status - проверить статус опроса

**Основные разделы:**
📝 Начать опрос - команда на запуск опроса
ℹ️ О кадровом резерве - информация о программе
❓ Помощь - справочная информация

Для возврата в главное меню используйте кнопку 🏠 Главное меню"""

# Списки для выбора
CITIES = ["Брест", "Береза", "Барановичи", "Пинск", "Столин", "Орша", "Иваново", 
          "Минск", "Витебск", "Гродно", "Гомель", "Могилёв", "ТФ Полесский"]

REASONS_NO_RESERVE = [
    "Удовлетворён текущей должностью",
    "Не готов(а) брать на себя ответственность",
    "Не уверен(а) в своих силах", 
    "Психологически не готов(а)",
    "Другое (укажите)"
]

EDUCATION_LEVELS = [
    "Профессионально-техническое",
    "Среднее специальное", 
    "Высшее",
    "Обучаюсь"
]

AGE_GROUPS = ["18-25", "26-30", "31-35", "36-40", "Больше 40"]

# Единый словарь всех вопросов в camelCase
QUESTIONS = {
    'isAgree': {
        'text': "Продолжая, я соглашаюсь с политикой обработки персональных данных в соответствии с Законом Республики Беларусь \"О защите персональных данных\"",
        'type': 'consent'
    },
    'isEmployee': {
        'text': "Вы сотрудник ОАО «Савушкин продукт»?",
        'type': 'yes_no'
    },
    'wantReserve': {
        'text': "Хотели бы Вы, чтобы Ваша кандидатура была рассмотрена для включения в кадровый резерв?",
        'type': 'yes_no_custom'
    },
    'desiredPosition': {
        'text': "Какую должность Вы рассматриваете для возможного назначения в рамках кадрового резерва?",
        'type': 'text'
    },
    'readyTraining': {
        'text': "Готовы ли Вы пройти обучение или стажировку для включения в кадровый резерв?",
        'type': 'yes_no_custom'
    },
    'careerObstacles': {
        'text': "Что, по Вашему мнению, мешает карьерному росту внутри компании?",
        'type': 'text'
    },
    'improvementSuggestions': {
        'text': "Есть ли у Вас предложения по улучшению работы Вашего филиала или компании в целом?",
        'type': 'text'
    },
    'readyRotation': {
        'text': "Готовы ли Вы к ротации или переводу в другое подразделение или филиал?",
        'type': 'yes_no_custom'
    },
    'preferredCities': {
        'text': "Укажите предпочтительные города для ротации (можно выбрать несколько):",
        'type': 'cities'
    },
    'structuralUnit': {
        'text': "Укажите структурное подразделение для ротации (логистика, продажи, бухгалтерии, производство и т.п.):",
        'type': 'text'
    },
    'reasonsNotJoining': {
        'text': "Пожалуйста, укажите причину, по которой Вы не готовы рассматривать включение в кадровый резерв:",
        'type': 'reasons'
    },
    'currentCity': {
        'text': "Укажите ПП/ТФ, в котором вы работаете:",
        'type': 'current_city'
    },
    'currentPosition': {
        'text': "Укажите Вашу профессию/должность, которую Вы сейчас занимаете:",
        'type': 'text'
    },
    'education': {
        'text': "Укажите Ваше образование:",
        'type': 'education'
    },
    'educationInstitution': {
        'text': "Укажите учебное заведение, в котором обучаетесь:",
        'type': 'text'
    },
    'age': {
        'text': "Укажите Ваш возраст:",
        'type': 'age'
    },
    'tabNumber': {
        'text': "Укажите Ваш табельный номер:",
        'type': 'tab_number'
    },
    'fio': {
        'text': "Укажите свои имя и фамилию:",
        'type': 'text'
    },
    'otherReason': {
        'text': "Пожалуйста, укажите Вашу причину:",
        'type': 'text'
    }
}

def validate_text_length(text: str, max_length: int = 1000) -> tuple[bool, str]:
    """Проверка длины текста"""
    if len(text) > max_length:
        return False, f"❌ Сообщение слишком длинное. Максимум {max_length} символов."
    return True, ""

def sanitize_text(text: str) -> str:

    dangerous_patterns = [
        r"(\bDROP\b|\bDELETE\b|\bINSERT\b|\bUPDATE\b|\bSELECT\b|\bUNION\b)",
        r"(\-\-|\;|\/\*|\*\/)",
        r"(<script|<\/script>|javascript:)",
        r"(\\x[0-9a-fA-F]{2})",
        r"(\badmin\b|\broot\b|\btest\b)",
        r"([<>])",
    ]
    
    sanitized = text
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '[removed]', sanitized, flags=re.IGNORECASE)
    
    sanitized = sanitized[:1000]
    return sanitized.strip()

def validate_and_sanitize_text(text: str) -> tuple[bool, str, str]:
    """Полная валидация и очистка текста"""
    is_valid_length, length_error = validate_text_length(text)
    if not is_valid_length:
        return False, length_error, ""
    
    clean_text = re.sub(r'[^\w\sа-яА-ЯёЁ.,!?;:()\-]', '', text)
    if not clean_text.strip():
        return False, "❌ Текст содержит только специальные символы. Пожалуйста, введите осмысленный текст.", ""
    
    sanitized_text = sanitize_text(text)
    
    if len(sanitized_text.strip()) < 2:
        return False, "❌ Текст слишком короткий или содержит недопустимые символы.", ""
    
    return True, "", sanitized_text

# Inline-клавиатуры
def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📝 Начать опрос", callback_data="start_survey")],
        [InlineKeyboardButton("ℹ️ О кадровом резерве", callback_data="reserve_info")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_to_menu_keyboard():
    keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]]
    return InlineKeyboardMarkup(keyboard)

def get_yes_no_keyboard():
    keyboard = [
        [InlineKeyboardButton("✅ Да", callback_data="yes")],
        [InlineKeyboardButton("❌ Нет", callback_data="no")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_yes_no_custom_keyboard(question_key: str):
    """Клавиатура для кастомных Да/Нет вопросов"""
    if question_key == 'wantReserve':
        callback_yes = "yes_want_reserve"
        callback_no = "no_want_reserve"
    elif question_key == 'readyTraining':
        callback_yes = "yes_ready_training"
        callback_no = "no_ready_training"
    elif question_key == 'readyRotation':
        callback_yes = "yes_ready_rotation"
        callback_no = "no_ready_rotation"
    else:
        callback_yes = "yes"
        callback_no = "no"
    
    keyboard = [
        [InlineKeyboardButton("✅ Да", callback_data=callback_yes)],
        [InlineKeyboardButton("❌ Нет", callback_data=callback_no)]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_cities_keyboard(selected_cities=None):
    if selected_cities is None:
        selected_cities = []
    
    keyboard = []
    cities_per_row = 2
    
    for i in range(0, len(CITIES), cities_per_row):
        row = []
        for city in CITIES[i:i + cities_per_row]:
            mark = "✅" if city in selected_cities else "◻️"
            row.append(InlineKeyboardButton(f"{mark} {city}", callback_data=f"city_{city}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("✅ Завершить выбор", callback_data="finish_cities")])
    return InlineKeyboardMarkup(keyboard)

def get_reasons_keyboard(selected_reasons=None):
    if selected_reasons is None:
        selected_reasons = []
    
    keyboard = []
    for i, reason in enumerate(REASONS_NO_RESERVE):
        mark = "✅" if reason in selected_reasons else "◻️"
        callback_data = f"reason_{i}"
        keyboard.append([InlineKeyboardButton(f"{mark} {reason}", callback_data=callback_data)])
    keyboard.append([InlineKeyboardButton("✅ Завершить выбор", callback_data="finish_reasons")])
    return InlineKeyboardMarkup(keyboard)

def get_education_keyboard():
    keyboard = []
    for education in EDUCATION_LEVELS:
        keyboard.append([InlineKeyboardButton(education, callback_data=f"education_{education}")])
    return InlineKeyboardMarkup(keyboard)

def get_age_keyboard():
    keyboard = []
    ages_per_row = 3
    
    for i in range(0, len(AGE_GROUPS), ages_per_row):
        row = []
        for age in AGE_GROUPS[i:i + ages_per_row]:
            row.append(InlineKeyboardButton(age, callback_data=f"age_{age}"))
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)

def get_current_city_keyboard():
    keyboard = []
    cities_per_row = 2
    
    for i in range(0, len(CITIES), cities_per_row):
        row = []
        for city in CITIES[i:i + cities_per_row]:
            row.append(InlineKeyboardButton(city, callback_data=f"current_city_{city}"))
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)

def get_consent_keyboard():
    keyboard = [
        [InlineKeyboardButton("✅ Продолжить", callback_data="consent_continue")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Обработчики команд
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            WELCOME_MESSAGE,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏠 Главное меню:", reply_markup=get_main_menu_keyboard())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, reply_markup=get_back_to_menu_keyboard(), parse_mode='Markdown')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    answers = user_data.get('answers', {})
    
    if not answers:
        status_text = "📊 **Статус опроса:**\n\nВы еще не начинали опрос."
    else:
        status_text = "📊 **Статус опроса:**\n\n"
        for question_key, answer in answers.items():
            status_text += f"{question_key}: {answer}\n"
        
        if 'fio' in answers:
            status_text += "\n✅ Опрос завершен!"
        else:
            status_text += "\n⏳ Опрос в процессе..."
    
    await update.message.reply_text(status_text, reply_markup=get_back_to_menu_keyboard(), parse_mode='Markdown')

# Универсальная функция для задавания вопросов
async def ask_question(update, context: ContextTypes.DEFAULT_TYPE, question_key: str):
    """Универсальная функция для задавания вопроса"""
    question_data = QUESTIONS[question_key]
    question_text = question_data['text']
    question_type = question_data['type']
    
    # Определяем клавиатуру в зависимости от типа вопроса
    if question_type == 'consent':
        keyboard = get_consent_keyboard()
    elif question_type == 'yes_no':
        keyboard = get_yes_no_keyboard()
    elif question_type == 'yes_no_custom':
        keyboard = get_yes_no_custom_keyboard(question_key)
    elif question_type == 'cities':
        context.user_data['selected_cities'] = []
        keyboard = get_cities_keyboard()
    elif question_type == 'reasons':
        context.user_data['selected_reasons'] = []
        context.user_data['other_reason'] = None
        keyboard = get_reasons_keyboard()
    elif question_type == 'current_city':
        keyboard = get_current_city_keyboard()
    elif question_type == 'education':
        keyboard = get_education_keyboard()
    elif question_type == 'age':
        keyboard = get_age_keyboard()
    else:
        keyboard = None
    
    # Отправляем вопрос
    if hasattr(update, 'message') and update.message:
        if keyboard:
            await update.message.reply_text(question_text, reply_markup=keyboard)
        else:
            await update.message.reply_text(question_text)
    else:
        if keyboard:
            await update.callback_query.message.reply_text(question_text, reply_markup=keyboard)
        else:
            await update.callback_query.message.reply_text(question_text)
    
    context.user_data['current_question'] = question_key

def get_next_question(current_question: str, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Определяет следующий вопрос на основе текущего и ветки опроса"""
    user_data = context.user_data
    branch = user_data.get('branch')
    
    question_flow = {
        'desiredPosition': 'readyTraining',
        'readyTraining': 'careerObstacles',
        'careerObstacles': 'improvementSuggestions',
        'improvementSuggestions': 'readyRotation',
        'structuralUnit': 'currentCity',
        'currentCity': 'currentPosition',
        'currentPosition': 'education',
        'educationInstitution': 'age',
        'age': 'tabNumber',
        'tabNumber': 'fio',
        'fio': None
    }
    
    # Ветка "Нет" (не хочу в кадровый резерв)
    if branch == 'no':
        if current_question == 'reasonsNotJoining':
            return 'careerObstacles'
        elif current_question == 'otherReason':
            return 'careerObstacles'
        elif current_question == 'careerObstacles':
            return 'improvementSuggestions'
        elif current_question == 'improvementSuggestions':
            return 'currentCity'
    
    # Особые случаи для образования
    if current_question == 'education':
        answers = user_data.get('answers', {})
        if answers.get('education') == "Обучаюсь":
            return 'educationInstitution'
        else:
            return 'age'
    
    return question_flow.get(current_question)

# Главный обработчик inline-кнопок
async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_data = context.user_data
    
    if 'answers' not in user_data:
        user_data['answers'] = {}

    # Навигация
    if query.data == "main_menu":
        await query.edit_message_text("🏠 Главное меню:", reply_markup=get_main_menu_keyboard())
    
    elif query.data == "start_survey":
        user_data.clear()
        user_data['answers'] = {}
        
        # Сохраняем правильного пользователя
        user_data['telegram_user'] = query.from_user  # СОХРАНЯЕМ ПОЛЬЗОВАТЕЛЯ
        
        user_id = query.from_user.id
        logger.info(f"Пользователь {user_id} начал опрос")
        
        # Редактируем сообщение с главным меню, убирая кнопки
        await query.edit_message_text(WELCOME_MESSAGE, parse_mode='Markdown')
        
        # Переходим к вопросу о согласии
        await ask_question(query, context, 'isAgree')

    elif query.data == "consent_continue":
        # Сохраняем ответ о согласии
        user_data['answers']['isAgree'] = "✅ Да"

        # Логируем ответ
        logger.info(f"Пользователь {query.from_user.id}: isAgree = Да")
        
        # Оставляем текст согласия без кнопки (редактируем)
        await query.edit_message_text(QUESTIONS['isAgree']['text'])
        
        # Отправляем ответ пользователя новым сообщением
        await query.message.reply_text("✅ Да")
        
        # Переходим к первому вопросу
        await ask_question(query, context, 'isEmployee')

    elif query.data == "reserve_info":
        await query.edit_message_text(RESERVE_INFO, reply_markup=get_back_to_menu_keyboard(), parse_mode='Markdown')
    
    elif query.data == "help":
        await query.edit_message_text(HELP_TEXT, reply_markup=get_back_to_menu_keyboard(), parse_mode='Markdown')
    
    # Вопрос 1: Сотрудник компании
    elif query.data in ["yes", "no"]:
        user_data['answers']['isEmployee'] = "✅ Да" if query.data == "yes" else "❌ Нет"
        await query.edit_message_text(QUESTIONS['isEmployee']['text'])
        await query.message.reply_text("✅ Да" if query.data == "yes" else "❌ Нет")
        
        # Логируем ответ
        answer_text = "Да" if query.data == "yes" else "Нет"
        logger.info(f"Пользователь {query.from_user.id}: isEmployee = {answer_text}")
        
        if query.data == "yes":
            await ask_question(query, context, 'wantReserve')
        else:
            user_data['answers']['isEmployee'] = "❌ Нет"
            await query.message.reply_text("Данный опрос только для сотрудников компании. Спасибо за внимание!")
            await finish_survey(query, context, show_completion_message=False)
    
    # Вопрос 2: Кадровый резерв
    elif query.data in ["yes_want_reserve", "no_want_reserve"]:
        user_data['answers']['wantReserve'] = "✅ Да" if query.data == "yes_want_reserve" else "❌ Нет"
        await query.edit_message_text(QUESTIONS['wantReserve']['text'])
        await query.message.reply_text("✅ Да" if query.data == "yes_want_reserve" else "❌ Нет")
        
        # Логируем ответ
        answer_text = "Да" if query.data == "yes_want_reserve" else "Нет"
        logger.info(f"Пользователь {query.from_user.id}: wantReserve = {answer_text}")
        
        if query.data == "yes_want_reserve":
            user_data['branch'] = 'yes'
            await ask_question(query, context, 'desiredPosition')
        else:
            user_data['branch'] = 'no'
            await ask_question(query, context, 'reasonsNotJoining')
    
    # Вопрос 5: Обучение
    elif query.data in ["yes_ready_training", "no_ready_training"]:
        user_data['answers']['readyTraining'] = "✅ Да" if query.data == "yes_ready_training" else "❌ Нет"
        await query.edit_message_text(QUESTIONS['readyTraining']['text'])
        await query.message.reply_text("✅ Да" if query.data == "yes_ready_training" else "❌ Нет")
        
        # Логируем ответ
        answer_text = "Да" if query.data == "yes_ready_training" else "Нет"
        logger.info(f"Пользователь {query.from_user.id}: readyTraining = {answer_text}")
        
        await ask_question(query, context, 'careerObstacles')
    
    # Вопрос 8: Ротация
    elif query.data in ["yes_ready_rotation", "no_ready_rotation"]:
        user_data['answers']['readyRotation'] = "✅ Да" if query.data == "yes_ready_rotation" else "❌ Нет"
        await query.edit_message_text(QUESTIONS['readyRotation']['text'])
        await query.message.reply_text("✅ Да" if query.data == "yes_ready_rotation" else "❌ Нет")
        
        # Логируем ответ
        answer_text = "Да" if query.data == "yes_ready_rotation" else "Нет"
        logger.info(f"Пользователь {query.from_user.id}: readyRotation = {answer_text}")
        
        if query.data == "yes_ready_rotation":
            await ask_question(query, context, 'preferredCities')
        else:
            await ask_question(query, context, 'currentCity')
    
    # Выбор городов для ротации
    elif query.data.startswith("city_"):
        city = query.data[5:]
        selected_cities = user_data.get('selected_cities', [])
        
        if city in selected_cities:
            selected_cities.remove(city)
        else:
            selected_cities.append(city)
        
        user_data['selected_cities'] = selected_cities
        
        # Логируем выбор города
        logger.info(f"Пользователь {query.from_user.id}: выбрал город {city}, текущий выбор: {selected_cities}")
        
        await query.edit_message_text(
            QUESTIONS['preferredCities']['text'] + "\n\nВыбрано: " + ", ".join(selected_cities) if selected_cities else "Ничего не выбрано",
            reply_markup=get_cities_keyboard(selected_cities)
        )

    elif query.data == "finish_cities":
        selected_cities = user_data.get('selected_cities', [])
        if selected_cities:
            user_data['answers']['preferredCities'] = ", ".join(selected_cities)
            await query.edit_message_text(QUESTIONS['preferredCities']['text'])
            cities_text = "\n".join([f"✅ {city}" for city in selected_cities])
            await query.message.reply_text(cities_text)
            
            # Логируем финальный выбор городов
            logger.info(f"Пользователь {query.from_user.id}: preferredCities = {selected_cities}")
            
            await ask_question(query, context, 'structuralUnit')
        else:
            await query.answer("❌ Пожалуйста, выберите хотя бы один город.", show_alert=True)
    
    # Выбор причин отказа
    elif query.data.startswith("reason_"):
        try:
            reason_index = int(query.data[7:])
            reason_text = REASONS_NO_RESERVE[reason_index]
            selected_reasons = user_data.get('selected_reasons', [])
            
            if reason_text in selected_reasons:
                selected_reasons.remove(reason_text)
                if reason_text == "Другое (укажите)":
                    user_data.pop('other_reason', None)
            else:
                selected_reasons.append(reason_text)
            
            user_data['selected_reasons'] = selected_reasons
            
            # Логируем выбор причины
            logger.info(f"Пользователь {query.from_user.id}: выбрал причину '{reason_text}', текущий выбор: {selected_reasons}")
            
            await query.edit_message_text(
                QUESTIONS['reasonsNotJoining']['text'] + "\n\nВыбрано: " + ", ".join(selected_reasons) if selected_reasons else "Ничего не выбрано",
                reply_markup=get_reasons_keyboard(selected_reasons)
            )
        except (ValueError, IndexError):
            await query.answer("❌ Ошибка обработки", show_alert=True)

    elif query.data == "finish_reasons":
        selected_reasons = user_data.get('selected_reasons', [])
        if selected_reasons:
            user_data['answers']['reasonsNotJoining'] = ", ".join(selected_reasons)
            await query.edit_message_text(QUESTIONS['reasonsNotJoining']['text'])
            
            reasons_text = "\n".join([f"✅ {reason}" for reason in selected_reasons])
            
            if user_data.get('other_reason'):
                reasons_text += f"\n✅ Другое: {user_data['other_reason']}"
                user_data['answers']['reasonsNotJoining'] += f" ({user_data['other_reason']})"
            
            await query.message.reply_text(reasons_text)
            
            # Логируем финальный выбор причин
            logger.info(f"Пользователь {query.from_user.id}: reasonsNotJoining = {selected_reasons}")
            if user_data.get('other_reason'):
                logger.info(f"Пользователь {query.from_user.id}: другая причина = {user_data['other_reason']}")
            
            if "Другое (укажите)" in selected_reasons and not user_data.get('other_reason'):
                await ask_question(query, context, 'otherReason')
            else:
                await ask_question(query, context, 'careerObstacles')
        else:
            await query.answer("❌ Пожалуйста, выберите хотя бы одну причину.", show_alert=True)
    
    # Образование
    elif query.data.startswith("education_"):
        education = query.data[10:]
        user_data['answers']['education'] = education
        await query.edit_message_text(QUESTIONS['education']['text'])
        await query.message.reply_text(f"✅ {education}")
        
        # Логируем ответ
        logger.info(f"Пользователь {query.from_user.id}: education = {education}")
        
        if education == "Обучаюсь":
            await ask_question(query, context, 'educationInstitution')
        else:
            await ask_question(query, context, 'age')
    
    # Возраст
    elif query.data.startswith("age_"):
        age = query.data[4:]
        user_data['answers']['age'] = age
        await query.edit_message_text(QUESTIONS['age']['text'])
        await query.message.reply_text(f"✅ {age}")
        
        # Логируем ответ
        logger.info(f"Пользователь {query.from_user.id}: age = {age}")
        
        await ask_question(query, context, 'tabNumber')
    
    # Текущий город
    elif query.data.startswith("current_city_"):
        city = query.data[13:]
        user_data['answers']['currentCity'] = city
        await query.edit_message_text(QUESTIONS['currentCity']['text'])
        await query.message.reply_text(f"✅ {city}")
        
        # Логируем ответ
        logger.info(f"Пользователь {query.from_user.id}: currentCity = {city}")
        
        await ask_question(query, context, 'currentPosition')

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Сохраняем пользователя если еще не сохранен
    if 'telegram_user' not in context.user_data:
        context.user_data['telegram_user'] = update.message.from_user
    user_message = update.message.text
    current_question = context.user_data.get('current_question', 0)
    user_id = update.message.from_user.id
    
    if 'answers' not in context.user_data:
        context.user_data['answers'] = {}

    blocked_questions = ['isEmployee', 'wantReserve', 'readyTraining', 'readyRotation', 
                        'preferredCities', 'reasonsNotJoining', 'education', 'age', 'currentCity']
    if current_question in blocked_questions:
        await update.message.reply_text("❌ Пожалуйста, используйте кнопки для ответа на этот вопрос.")
        return

    # ОСОБАЯ ОБРАБОТКА ДЛЯ ТАБЕЛЬНОГО НОМЕРА
    if current_question == 'tabNumber':
        is_valid, error_msg = validate_tab_number(user_message)
        if not is_valid:
            await update.message.reply_text(error_msg)
            return
        
        # Сохраняем очищенный номер
        context.user_data['answers'][current_question] = error_msg  # error_msg содержит очищенный номер
        await update.message.reply_text(f"✅ {error_msg}")
        
        # Логируем ответ
        logger.info(f"Пользователь {user_id}: {current_question} = {error_msg}")
        
        # Переходим к следующему вопросу
        next_question = get_next_question(current_question, context)
        if next_question:
            await ask_question(update, context, next_question)
        else:
            await finish_survey(update, context)
        return

    # Обычная обработка для других текстовых вопросов
    is_valid, error_msg, sanitized_text = validate_and_sanitize_text(user_message)
    if not is_valid:
        await update.message.reply_text(error_msg)
        return

    # Сохраняем ответ
    context.user_data['answers'][current_question] = sanitized_text
    await update.message.reply_text(f"✅ {sanitized_text}")
    
    # Логируем текстовый ответ
    logger.info(f"Пользователь {user_id}: {current_question} = {sanitized_text}")
    
    # Определяем следующий вопрос
    next_question = get_next_question(current_question, context)
    if next_question:
        await ask_question(update, context, next_question)
    else:
        await finish_survey(update, context)

def validate_tab_number(tab_number: str) -> tuple[bool, str]:
    """Проверка табельного номера"""
    # Убираем пробелы и другие символы
    clean_number = re.sub(r'\s+', '', tab_number)
    
    # Проверяем что только цифры
    if not clean_number.isdigit():
        return False, "❌ Табельный номер должен содержать только цифры"
    
    # Проверяем длину (не более 9 цифр)
    if len(clean_number) > 9:
        return False, "❌ Табельный номер не может содержать более 9 цифр"
    
    # Проверяем что не пустой
    if len(clean_number) == 0:
        return False, "❌ Табельный номер не может быть пустым"
    
    return True, clean_number

# Функция для валидации ФИО
def validate_fio(fio):
    fio = sanitize_text(fio)
    fio = ' '.join(fio.split())
    
    if len(fio) < 5 or len(fio) > 100:
        return False, "ФИО должно содержать от 5 до 100 символов"
    
    parts = fio.split()
    if len(parts) < 2:
        return False, "Укажите как минимум имя и фамилию"
    
    for part in parts:
        if not re.match(r'^[a-zA-Zа-яА-ЯёЁ\-.]+$', part):
            return False, "ФИО может содержать только буквы, дефисы и точки"
    
    return True, fio

# Завершение опроса
async def finish_survey(update: Update, context: ContextTypes.DEFAULT_TYPE, show_completion_message: bool = True):
    user_data = context.user_data
    
    # Берем пользователя из сохраненных данных
    user = user_data.get('telegram_user')
    if not user:
        # Если по какой-то причине нет сохраненного пользователя, пробуем получить из update
        if update.message:
            user = update.message.from_user
            message = update.message
        else:
            query = update.callback_query
            user = query.from_user
            message = query.message
    else:
        # Определяем message для отправки ответа
        if update.message:
            message = update.message
        else:
            message = update.callback_query.message
    
    answers = user_data.get('answers', {})
    
    survey_data = format_survey_data(user, answers)
    
    # Логируем полные результаты в файл
    logger.info(f"Результаты опроса пользователя {user.id}:")
    logger.info(json.dumps(survey_data, ensure_ascii=False, indent=2))
    
    success = await send_survey_data(survey_data)
    
    if show_completion_message:
        if success:
            result_message = "✅ Опрос завершен!\n\nСпасибо за участие! Ваши данные направлены на рассмотрение в кадровый резерв ОАО «Савушкин продукт».\n\nУдачи в профессиональном росте! 🌱"
        else:
            result_message = "✅ Опрос завершен!\n\nСпасибо за участие!\n\nВаши ответы сохранены, но возникла ошибка при отправке."
        
        await message.reply_text(result_message)
    
    context.user_data.clear()

def format_survey_data(user, answers: dict) -> dict:
    telegram_user = {
        "id": user.id,
        "firstName": user.first_name or "",
        "lastName": user.last_name or "",
        "userName": user.username or "",
        "languageCode": user.language_code or "",
        "isBot": user.is_bot,
        "isPremium": bool(getattr(user, 'is_premium', False))
    }
    
    respondent_data = {
        "fullName": clean_answer_text(answers.get('fio', '')),
        "ageGroup": clean_answer_text(answers.get('age', '')),
        "position": clean_answer_text(answers.get('currentPosition', '')),
        "filial": clean_answer_text(answers.get('currentCity', '')),
        "isEmployee": clean_answer_text(answers.get('isEmployee', '')),
        "isAgree": clean_answer_text(answers.get('isAgree', '')),
        "phoneNumber": "",
        "tabNumber": answers.get('tabNumber', ''),  # ДОБАВЛЕНО: табельный номер
        "telegramUser": telegram_user
    }
    
    # Исключаем isAgree и tabNumber из блока response
    excluded_keys = ['fio', 'age', 'currentPosition', 'currentCity', 'education', 
                    'educationInstitution', 'isEmployee', 'isAgree', 'tabNumber']
    
    answers_array = []
    
    for answer_key, answer_value in answers.items():
        if answer_key in QUESTIONS and answer_key not in excluded_keys:
            clean_answer = clean_answer_text(str(answer_value))
            
            answers_array.append({
                "questionId": answer_key,
                "questionText": QUESTIONS[answer_key]['text'],
                "answerText": clean_answer
            })
    
    if 'education' in answers:
        answers_array.append({
            "questionId": "education",
            "questionText": QUESTIONS['education']['text'],
            "answerText": clean_answer_text(answers['education'])
        })
    
    if 'educationInstitution' in answers:
        answers_array.append({
            "questionId": "educationInstitution", 
            "questionText": QUESTIONS['educationInstitution']['text'],
            "answerText": clean_answer_text(answers['educationInstitution'])
        })
    
    question_order = [
        'wantReserve', 'desiredPosition', 'readyTraining',
        'careerObstacles', 'improvementSuggestions', 'readyRotation',
        'preferredCities', 'structuralUnit', 'reasonsNotJoining', 'education', 'educationInstitution'
    ]
    
    sorted_answers = sorted(answers_array, 
                          key=lambda x: question_order.index(x['questionId']) 
                          if x['questionId'] in question_order else len(question_order))
    
    return {
        "name": "Хочу расти!",
        "respondent": respondent_data,
        "response": {
            "answers": sorted_answers
        }
    }

def clean_answer_text(answer: str) -> str:
    cleaned = re.sub(r'^[✅❌👤\s]*', '', answer)
    return cleaned

# API функции
async def get_bearer_token() -> str:
    """Получает bearer token для авторизации"""
    auth_url = "https://edi1.savushkin.com:5050/api/authentication/authenticate"
    auth_data = {
        "username": API_USERNAME,
        "password": API_PASSWORD
    }
    
    try:
        response = requests.post(
            auth_url, 
            json=auth_data, 
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            token = result.get('uuid', '')
            if token:
                logger.info("Токен авторизации получен успешно")
                print("✅ Токен авторизации получен")
                return token
            else:
                logger.error("Токен не найден в ответе авторизации")
                print("❌ Токен не найден в ответе")
                return ""
        else:
            logger.error(f"Ошибка авторизации: {response.status_code} - {response.text}")
            print(f"❌ Ошибка авторизации: {response.status_code}")
            return ""
            
    except Exception as e:
        logger.error(f"Ошибка при получении токена: {e}")
        print(f"❌ Ошибка при получении токена: {e}")
        return ""

async def send_survey_data(survey_data: dict) -> bool:
    """Отправляет данные опроса на сервер"""
    bearer_token = await get_bearer_token()
    
    if not bearer_token:
        logger.error("Не удалось получить токен авторизации")
        print("❌ Не удалось получить токен авторизации")
        return False
    
    survey_url = "https://edi1.savushkin.com:5050/bot/xr/surveys/add"
    
    try:
        headers = {
            'Authorization': f'Bearer {bearer_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            survey_url, 
            json=survey_data, 
            headers=headers,
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            record_id = result.get('id')
            message = result.get('message')
            
            if record_id:
                logger.info(f"Данные успешно отправлены. ID записи: {record_id}, Сообщение: {message}")
                print(f"✅ Данные успешно отправлены. ID записи: {record_id}")
            else:
                logger.info(f"Данные отправлены. Сообщение: {message}")
                print(f"✅ Данные отправлены")
                
            return True
        else:
            logger.error(f"Ошибка отправки данных: {response.status_code} - {response.text}")
            print(f"❌ Ошибка отправки данных: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка при отправке данных: {e}")
        print(f"❌ Ошибка при отправке данных: {e}")
        return False

# Обработчик ошибок
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    error_msg = f"Произошла ошибка: {context.error}"
    logger.error(error_msg)
    print(error_msg)

# Главная функция
def main():
    # Создаем папку logs если ее нет
    os.makedirs('logs', exist_ok=True)

    print("Запускаю бота опроса...")
    
    # Дополнительно настраиваем логирование для библиотеки telegram
    logging.getLogger('telegram.ext.updater').setLevel(logging.WARNING)
    logging.getLogger('telegram.ext.dispatcher').setLevel(logging.WARNING)
    logging.getLogger('telegram.ext.jobqueue').setLevel(logging.WARNING)
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    
    application.add_handler(CallbackQueryHandler(handle_button_click))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.add_error_handler(error)
    
    print("Бот запущен! Нажмите Ctrl+C для остановки.")
    
    # ИСПРАВЛЕНИЕ ДЛЯ PYTHON 3.14 - вариант 2
    try:
        application.run_polling()
    except RuntimeError as e:
        if "no current event loop" in str(e):
            # Создаем новую event loop для этого потока
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(application.run_polling())
            except KeyboardInterrupt:
                print("\nБот остановлен.")
            finally:
                loop.close()
        else:
            raise e

if __name__ == "__main__":
    main()