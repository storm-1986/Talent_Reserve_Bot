import os
import re
import html
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Приветственное сообщение
WELCOME_MESSAGE = """*Уважаемые коллеги!* Настоящий опрос проводится среди сотрудников группы компаний ОАО «Савушкин продукт» с целью эффективного планирования карьерного развития, формирования кадрового резерва, а также выявления инициативных и целеустремлённых специалистов, готовых расти и развиваться вместе с компанией, применяя свои знания и навыки на её производственных площадках.
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
    "Средне специальное", 
    "Высшее",
    "Обучаюсь"
]

AGE_GROUPS = ["18-25", "26-30", "31-35", "36-40", "Больше 41"]

def validate_text_length(text: str, max_length: int = 1000) -> tuple[bool, str]:
    """Проверка длины текста"""
    if len(text) > max_length:
        return False, f"❌ Сообщение слишком длинное. Максимум {max_length} символов."
    return True, ""

def sanitize_text(text: str) -> str:
    """Очистка текста от потенциально опасных символов и HTML"""
    # Экранируем HTML-символы
    sanitized = html.escape(text)
    
    # Удаляем потенциально опасные SQL-символы (базовая защита)
    dangerous_patterns = [
        r"(\bDROP\b|\bDELETE\b|\bINSERT\b|\bUPDATE\b|\bSELECT\b|\bUNION\b)",  # SQL keywords
        r"(\-\-|\;|\/\*|\*\/)",  # SQL комментарии и разделители
        r"(<script|<\/script>|javascript:)",  # XSS
        r"(\\x[0-9a-fA-F]{2})",  # Hex-последовательности
    ]
    
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '[removed]', sanitized, flags=re.IGNORECASE)
    
    # Ограничиваем длину (на всякий случай)
    sanitized = sanitized[:1000]
    
    return sanitized.strip()

def validate_and_sanitize_text(text: str) -> tuple[bool, str, str]:
    """
    Полная валидация и очистка текста
    Возвращает: (is_valid, error_message, sanitized_text)
    """
    # Проверяем длину
    is_valid_length, length_error = validate_text_length(text)
    if not is_valid_length:
        return False, length_error, ""
    
    # Проверяем, что текст не состоит только из спецсимволов
    clean_text = re.sub(r'[^\w\sа-яА-ЯёЁ.,!?;:()\-]', '', text)
    if not clean_text.strip():
        return False, "❌ Текст содержит только специальные символы. Пожалуйста, введите осмысленный текст.", ""
    
    # Очищаем текст
    sanitized_text = sanitize_text(text)
    
    # Проверяем, что после очистки остался осмысленный текст
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

def get_cities_keyboard(selected_cities=None):
    if selected_cities is None:
        selected_cities = []
    
    keyboard = []
    cities_per_row = 2  # 2 города в строке
    
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
    ages_per_row = 3  # 3 возраста в строке
    
    for i in range(0, len(AGE_GROUPS), ages_per_row):
        row = []
        for age in AGE_GROUPS[i:i + ages_per_row]:
            row.append(InlineKeyboardButton(age, callback_data=f"age_{age}"))
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)

def get_current_city_keyboard():
    keyboard = []
    cities_per_row = 2  # 2 города в строке
    
    for i in range(0, len(CITIES), cities_per_row):
        row = []
        for city in CITIES[i:i + cities_per_row]:
            row.append(InlineKeyboardButton(city, callback_data=f"current_city_{city}"))
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)

# Обработчики команд
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            "Добро пожаловать в бот опроса кадрового резерва ОАО «Савушкин продукт»!\n\n" + WELCOME_MESSAGE,
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
        await query.edit_message_text(
            WELCOME_MESSAGE + "\n\n*Для начала опроса ответьте на первый вопрос:*", 
            parse_mode='Markdown'
        )
        await ask_first_question(query, context)
    
    elif query.data == "reserve_info":
        await query.edit_message_text(RESERVE_INFO, reply_markup=get_back_to_menu_keyboard(), parse_mode='Markdown')
    
    elif query.data == "help":
        await query.edit_message_text(HELP_TEXT, reply_markup=get_back_to_menu_keyboard(), parse_mode='Markdown')
    
    # Вопрос 1: Сотрудник компании
    elif query.data in ["yes", "no"]:
        user_data['answers']['is_employee'] = "✅ Да" if query.data == "yes" else "❌ Нет"
        await query.edit_message_text("Являетесь ли вы сотрудником ОАО «Савушкин продукт»?")
        await query.message.reply_text("✅ Да" if query.data == "yes" else "❌ Нет")
        if query.data == "yes":
            await ask_second_question(query, context)
        else:
            await query.message.reply_text(
                "К сожалению, данный опрос только для сотрудников компании.",
                reply_markup=get_back_to_menu_keyboard()
            )
            user_data.clear()
    
    # Вопрос 2: Кадровый резерв
    elif query.data in ["yes_2", "no_2"]:
        user_data['answers']['want_reserve'] = "✅ Да" if query.data == "yes_2" else "❌ Нет"
        await query.edit_message_text("Хотели бы Вы, чтобы Ваша кандидатура была рассмотрена для включения в кадровый резерв?")
        await query.message.reply_text("✅ Да" if query.data == "yes_2" else "❌ Нет")
        if query.data == "yes_2":
            user_data['branch'] = 'yes'
            await ask_position_question(query, context)
        else:
            user_data['branch'] = 'no'
            await ask_reason_no_reserve_question(query, context)

    # Вопрос 5: Обучение
    elif query.data in ["yes_5", "no_5"]:
        user_data['answers']['ready_training'] = "✅ Да" if query.data == "yes_5" else "❌ Нет"
        await query.edit_message_text("Готовы ли Вы пройти обучение или стажировку для включения в кадровый резерв?")
        await query.message.reply_text("✅ Да" if query.data == "yes_5" else "❌ Нет")
        await ask_career_obstacles_question(query, context)

    # Вопрос 8: Ротация
    elif query.data in ["yes_8", "no_8"]:
        user_data['answers']['ready_rotation'] = "✅ Да" if query.data == "yes_8" else "❌ Нет"
        await query.edit_message_text("Готовы ли Вы к ротации или переводу в другое подразделение (филиал)?")
        await query.message.reply_text("✅ Да" if query.data == "yes_8" else "❌ Нет")
        if query.data == "yes_8":
            await ask_cities_question(query, context)
        else:
            await ask_current_city_question(query, context)
    
    # Выбор городов для ротации
    elif query.data.startswith("city_"):
        city = query.data[5:]
        selected_cities = user_data.get('selected_cities', [])
        
        if city in selected_cities:
            selected_cities.remove(city)
        else:
            selected_cities.append(city)
        
        user_data['selected_cities'] = selected_cities
        await query.edit_message_text(
            "Укажите предпочтительные города для ротации (можно выбрать несколько):\n\nВыбрано: " + ", ".join(selected_cities) if selected_cities else "Ничего не выбрано",
            reply_markup=get_cities_keyboard(selected_cities)
        )
    
    elif query.data == "finish_cities":
        selected_cities = user_data.get('selected_cities', [])
        if selected_cities:
            user_data['answers']['preferred_cities'] = ", ".join(selected_cities)
            await query.edit_message_text("Укажите предпочтительные города для ротации (можно выбрать несколько):")
            cities_text = "\n".join([f"✅ {city}" for city in selected_cities])
            await query.message.reply_text(cities_text)
            await ask_structural_unit_question(query, context)
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
            
            await query.edit_message_text(
                "Пожалуйста, укажите причину (можно выбрать несколько):\n\nВыбрано: " + ", ".join(selected_reasons) if selected_reasons else "Ничего не выбрано",
                reply_markup=get_reasons_keyboard(selected_reasons)
            )
        except (ValueError, IndexError):
            await query.answer("❌ Ошибка обработки", show_alert=True)
    
    elif query.data == "finish_reasons":
        selected_reasons = user_data.get('selected_reasons', [])
        if selected_reasons:
            user_data['answers']['reasons_not_joining'] = ", ".join(selected_reasons)
            
            await query.edit_message_text("Пожалуйста, укажите причину, по которой Вы не готовы рассматривать включение в кадровый резерв:")
            reasons_text = "\n".join([f"✅ {reason}" for reason in selected_reasons])
            
            # Если есть "другая" причина, добавляем её
            if user_data.get('other_reason'):
                reasons_text += f"\n✅ Другое: {user_data['other_reason']}"
                user_data['answers']['reasons_not_joining'] += f" ({user_data['other_reason']})"
            
            await query.message.reply_text(reasons_text)
            
            if "Другое (укажите)" in selected_reasons and not user_data.get('other_reason'):
                await ask_other_reason_question(query, context)
            else:
                await ask_career_obstacles_alt_question(query, context)
        else:
            await query.answer("❌ Пожалуйста, выберите хотя бы одну причину.", show_alert=True)
    
    # Образование
    elif query.data.startswith("education_"):
        education = query.data[10:]
        user_data['answers']['education'] = education
        
        await query.edit_message_text("Ваше образование:")
        await query.message.reply_text(f"✅ {education}")
        
        if education == "Обучаюсь":
            await ask_education_institution_question(query, context)
        else:
            await ask_age_question(query, context)
    
    # Возраст
    elif query.data.startswith("age_"):
        age = query.data[4:]
        user_data['answers']['age'] = age
        
        await query.edit_message_text("Ваш возраст:")
        await query.message.reply_text(f"✅ {age}")
        
        await ask_fio_question(query, context)
    
    # Текущий город
    elif query.data.startswith("current_city_"):
        city = query.data[13:]
        user_data['answers']['current_city'] = city
        
        await query.edit_message_text("ПП/ТФ, в котором вы работаете:")
        await query.message.reply_text(f"✅ {city}")
        
        await ask_current_position_question(query, context)

# Функции вопросов
async def ask_first_question(update, context: ContextTypes.DEFAULT_TYPE):
    question = "Вы сотрудник ОАО «Савушкин продукт»?"
    
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(question, reply_markup=get_yes_no_keyboard())
    else:
        await update.callback_query.message.reply_text(question, reply_markup=get_yes_no_keyboard())
    
    context.user_data['current_question'] = 1

async def ask_second_question(update, context: ContextTypes.DEFAULT_TYPE):
    question = "Хотели бы Вы, чтобы Ваша кандидатура была рассмотрена для включения в кадровый резерв?"
    
    keyboard = [
        [InlineKeyboardButton("✅ Да", callback_data="yes_2")],
        [InlineKeyboardButton("❌ Нет", callback_data="no_2")]
    ]
    
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(question, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.message.reply_text(question, reply_markup=InlineKeyboardMarkup(keyboard))
    
    context.user_data['current_question'] = 2

async def ask_position_question(update, context: ContextTypes.DEFAULT_TYPE):
    question = "Какую должность Вы рассматриваете для возможного назначения в рамках кадрового резерва?"
    
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(question)
    else:
        await update.callback_query.message.reply_text(question)
    
    context.user_data['current_question'] = 3

async def ask_initiatives_question(update, context: ContextTypes.DEFAULT_TYPE):
    question = "Какие инициативы или программы Вы хотели бы видеть для развития сотрудников?"
    
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(question)
    else:
        await update.callback_query.message.reply_text(question)
    
    context.user_data['current_question'] = 4

async def ask_training_question(update, context: ContextTypes.DEFAULT_TYPE):
    question = "Готовы ли Вы пройти обучение или стажировку для включения в кадровый резерв?"
    
    keyboard = [
        [InlineKeyboardButton("✅ Да", callback_data="yes_5")],
        [InlineKeyboardButton("❌ Нет", callback_data="no_5")]
    ]
    
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(question, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.message.reply_text(question, reply_markup=InlineKeyboardMarkup(keyboard))
    
    context.user_data['current_question'] = 5

async def ask_career_obstacles_question(update, context: ContextTypes.DEFAULT_TYPE):
    question = "Что, по Вашему мнению, мешает карьерному росту внутри компании?"
    
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(question)
    else:
        await update.callback_query.message.reply_text(question)
    
    context.user_data['current_question'] = 6

async def ask_improvements_question(update, context: ContextTypes.DEFAULT_TYPE):
    question = "Есть ли у Вас предложения по улучшению работы Вашего филиала или компании в целом?"
    
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(question)
    else:
        await update.callback_query.message.reply_text(question)
    
    context.user_data['current_question'] = 7

async def ask_rotation_question(update, context: ContextTypes.DEFAULT_TYPE):
    question = "Готовы ли Вы к ротации или переводу в другое подразделение (филиал)?"
    
    keyboard = [
        [InlineKeyboardButton("✅ Да", callback_data="yes_8")],
        [InlineKeyboardButton("❌ Нет", callback_data="no_8")]
    ]
    
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(question, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.message.reply_text(question, reply_markup=InlineKeyboardMarkup(keyboard))
    
    context.user_data['current_question'] = 8

async def ask_cities_question(update, context: ContextTypes.DEFAULT_TYPE):
    question = "Укажите предпочтительные города для ротации (можно выбрать несколько):"
    
    context.user_data['selected_cities'] = []
    
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(question, reply_markup=get_cities_keyboard())
    else:
        await update.callback_query.message.reply_text(question, reply_markup=get_cities_keyboard())
    
    context.user_data['current_question'] = 9

async def ask_structural_unit_question(update, context: ContextTypes.DEFAULT_TYPE):
    question = "Укажите структурное подразделение:"
    
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(question)
    else:
        await update.callback_query.message.reply_text(question)
    
    context.user_data['current_question'] = 10

async def ask_reason_no_reserve_question(update, context: ContextTypes.DEFAULT_TYPE):
    question = "Пожалуйста, укажите причину, по которой Вы не готовы рассматривать включение в кадровый резерв:"
    
    context.user_data['selected_reasons'] = []
    context.user_data['other_reason'] = None
    
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(question, reply_markup=get_reasons_keyboard())
    else:
        await update.callback_query.message.reply_text(question, reply_markup=get_reasons_keyboard())
    
    context.user_data['current_question'] = "3_alt"

async def ask_other_reason_question(update, context: ContextTypes.DEFAULT_TYPE):
    question = "Пожалуйста, укажите Вашу причину:"
    
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(question)
    else:
        await update.callback_query.message.reply_text(question)
    
    context.user_data['current_question'] = "other_reason"

async def ask_career_obstacles_alt_question(update, context: ContextTypes.DEFAULT_TYPE):
    question = "Что, по Вашему мнению, мешает карьерному росту внутри компании?"
    
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(question)
    else:
        await update.callback_query.message.reply_text(question)
    
    context.user_data['current_question'] = "4_alt"

async def ask_improvements_alt_question(update, context: ContextTypes.DEFAULT_TYPE):
    question = "Есть ли у Вас предложения по улучшению работы Вашего филиала или компании в целом?"
    
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(question)
    else:
        await update.callback_query.message.reply_text(question)
    
    context.user_data['current_question'] = "5_alt"

async def ask_current_city_question(update, context: ContextTypes.DEFAULT_TYPE):
    question = "ПП/ТФ, в котором вы работаете:"
    
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(question, reply_markup=get_current_city_keyboard())
    else:
        await update.callback_query.message.reply_text(question, reply_markup=get_current_city_keyboard())
    
    context.user_data['current_question'] = "current_city"

async def ask_current_position_question(update, context: ContextTypes.DEFAULT_TYPE):
    question = "Ваша профессия/должность, которую Вы сейчас занимаете (укажите):"
    
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(question)
    else:
        await update.callback_query.message.reply_text(question)
    
    context.user_data['current_question'] = "current_position"

async def ask_education_question(update, context: ContextTypes.DEFAULT_TYPE):
    question = "Ваше образование:"
    
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(question, reply_markup=get_education_keyboard())
    else:
        await update.callback_query.message.reply_text(question, reply_markup=get_education_keyboard())
    
    context.user_data['current_question'] = "education"

async def ask_education_institution_question(update, context: ContextTypes.DEFAULT_TYPE):
    question = "Укажите учебное заведение, в котором обучаетесь:"
    
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(question)
    else:
        await update.callback_query.message.reply_text(question)
    
    context.user_data['current_question'] = "education_institution"

async def ask_age_question(update, context: ContextTypes.DEFAULT_TYPE):
    question = "Ваш возраст:"
    
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(question, reply_markup=get_age_keyboard())
    else:
        await update.callback_query.message.reply_text(question, reply_markup=get_age_keyboard())
    
    context.user_data['current_question'] = "age"

async def ask_fio_question(update, context: ContextTypes.DEFAULT_TYPE):
    question = "Укажите ФИО:"
    
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(question)
    else:
        await update.callback_query.message.reply_text(question)
    
    context.user_data['current_question'] = "fio"

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    current_question = context.user_data.get('current_question', 0)
    
    if 'answers' not in context.user_data:
        context.user_data['answers'] = {}

    # Блокируем текстовый ввод для вопросов с inline-кнопками
    blocked_questions = [1, 2, 5, 8, 9, "3_alt", "education", "age", "current_city"]
    if current_question in blocked_questions:
        await update.message.reply_text("❌ Пожалуйста, используйте кнопки для ответа на этот вопрос.")
        return

    # Валидируем и очищаем текст
    is_valid, error_msg, sanitized_text = validate_and_sanitize_text(user_message)
    if not is_valid:
        await update.message.reply_text(error_msg)
        return

    # Текстовые вопросы - отправляем ответ пользователя
    if current_question == 3:  # Должность
        context.user_data['answers']['desired_position'] = sanitized_text
        await update.message.reply_text(f"✅ {sanitized_text}")
        await ask_initiatives_question(update, context)

    elif current_question == 4:  # Инициативы
        context.user_data['answers']['development_initiatives'] = sanitized_text
        await update.message.reply_text(f"✅ {sanitized_text}")
        await ask_training_question(update, context)

    elif current_question == 6:  # Препятствия карьерному росту
        context.user_data['answers']['career_obstacles'] = sanitized_text
        await update.message.reply_text(f"✅ {sanitized_text}")
        await ask_improvements_question(update, context)

    elif current_question == 7:  # Предложения по улучшению
        context.user_data['answers']['improvement_suggestions'] = sanitized_text
        await update.message.reply_text(f"✅ {sanitized_text}")
        await ask_rotation_question(update, context)

    elif current_question == 10:  # Структурное подразделение
        context.user_data['answers']['structural_unit'] = sanitized_text
        await update.message.reply_text(f"✅ {sanitized_text}")
        await ask_current_city_question(update, context)

    elif current_question == "4_alt":  # Препятствия карьерному росту (альт)
        context.user_data['answers']['career_obstacles_alt'] = sanitized_text
        await update.message.reply_text(f"✅ {sanitized_text}")
        await ask_improvements_alt_question(update, context)

    elif current_question == "5_alt":  # Предложения по улучшению (альт)
        context.user_data['answers']['improvement_suggestions_alt'] = sanitized_text
        await update.message.reply_text(f"✅ {sanitized_text}")
        await ask_current_city_question(update, context)

    elif current_question == "current_position":  # Текущая должность
        context.user_data['answers']['current_position'] = sanitized_text
        await update.message.reply_text(f"✅ {sanitized_text}")
        await ask_education_question(update, context)

    elif current_question == "education_institution":  # Учебное заведение
        context.user_data['answers']['education_institution'] = sanitized_text
        await update.message.reply_text(f"✅ {sanitized_text}")
        await ask_age_question(update, context)

    elif current_question == "other_reason":  # Другая причина
        if sanitized_text.strip():
            context.user_data['other_reason'] = sanitized_text
            await update.message.reply_text(f"✅ {sanitized_text}")
            if "Другое (укажите)" in context.user_data.get('selected_reasons', []):
                context.user_data['selected_reasons'].remove("Другое (укажите)")
                context.user_data['selected_reasons'].append(f"Другое: {sanitized_text}")
            
            context.user_data['answers']['reasons_not_joining'] = ", ".join(context.user_data['selected_reasons'])
            await ask_career_obstacles_alt_question(update, context)
        else:
            await update.message.reply_text("❌ Пожалуйста, укажите причину:")

    elif current_question == "fio":  # ФИО
        is_valid_fio, result = validate_fio(sanitized_text)
        if is_valid_fio:
            context.user_data['answers']['fio'] = result
            await update.message.reply_text(f"✅ {result}")
            await finish_survey(update, context)
        else:
            await update.message.reply_text(f"❌ {result}\n\nПожалуйста, укажите корректное ФИО:")

    else:
        await update.message.reply_text("Выберите действие:", reply_markup=get_main_menu_keyboard())

# Функция для валидации ФИО
def validate_fio(fio):
    """Валидация ФИО с дополнительной защитой"""
    # Сначала очищаем текст
    fio = sanitize_text(fio)
    fio = ' '.join(fio.split())
    
    if len(fio) < 5 or len(fio) > 100:
        return False, "ФИО должно содержать от 5 до 100 символов"
    
    parts = fio.split()
    if len(parts) < 2:
        return False, "Укажите как минимум имя и фамилию"
    
    # Проверяем, что каждая часть содержит только буквы, дефисы и пробелы
    for part in parts:
        if not re.match(r'^[a-zA-Zа-яА-ЯёЁ\-]+$', part):
            return False, "ФИО может содержать только буквы и дефисы"
    
    # Проверяем, что нет подозрительных последовательностей
    suspicious_patterns = [
        r".*(\badmin\b|\broot\b|\btest\b).*",
        r".*(\bselect\b|\binsert\b|\bdelete\b).*",
        r".*([<>]|javascript:).*",
    ]
    
    for pattern in suspicious_patterns:
        if re.match(pattern, fio, re.IGNORECASE):
            return False, "Указано некорректное ФИО"
    
    return True, fio

# Завершение опроса
async def finish_survey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    answers = context.user_data.get('answers', {})
    
    result_message = "✅ Спасибо за участие в опросе!\n\nВаши ответы сохранены.\n\nОпрос завершен!"
    
    # Отправляем сообщение без кнопки главного меню
    await update.message.reply_text(result_message)
    
    print(f"Ответы пользователя {user_id}:")
    for question_key, answer in answers.items():
        print(f"{question_key}: {answer}")
    print("---")
    
    context.user_data.clear()

# Обработчик ошибок
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Произошла ошибка: {context.error}")

# Главная функция
def main():
    print("Запускаю бота опроса...")
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    
    application.add_handler(CallbackQueryHandler(handle_button_click))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.add_error_handler(error)
    
    print("Бот запущен! Нажмите Ctrl+C для остановки.")
    application.run_polling()

if __name__ == "__main__":
    main()