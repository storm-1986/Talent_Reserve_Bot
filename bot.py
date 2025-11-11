from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# ВСТАВЬТЕ СЮДА ВАШ ТОКЕН ОТ @BotFather
BOT_TOKEN = "8085427677:AAH5HrDnsSEBpzMAfI-fJz1eqvX-A7dG6_E"

# Приветственное сообщение
WELCOME_MESSAGE = """Уважаемые коллеги! Настоящий опрос проводится среди сотрудников группы компаний ОАО «Савушкин продукт» с целью эффективного планирования карьерного развития, формирования кадрового резерва, а также выявления инициативных и целеустремлённых специалистов, готовых расти и развиваться вместе с компанией, применяя свои знания и навыки на её производственных площадках. Просим вас быть искренними — прежде всего перед самими собой. Опрос займёт всего несколько минут. 
Благодарим за ваше участие и уделённое время!"""

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

# Списки для чекбоксов
CITIES = ["Брест", "Береза", "Барановичи", "Пинск", "Столин", "Орша", "Иваново", 
          "Минск", "Витебск", "Гродно", "Гомель", "Могилёв", "ТФ Полесский"]

REASONS_NO_RESERVE = [
    "Удовлетворён текущей должностью",
    "Не готов(а) брать на себя ответственность за команду или процессы",
    "Не уверен(а) в своих силах / компетенциях", 
    "Психологически не готов(а) к дополнительной ответственности в текущих условиях",
    "Другое (укажите)"
]

EDUCATION_LEVELS = [
    "Профессионально-техническое",
    "Средне специальное", 
    "Высшее",
    "Обучаюсь"
]

AGE_GROUPS = ["18-25", "26-31", "31-35", "36-40", "Больше 41"]

# Клавиатура для Да/Нет вопросов
YES_NO_KEYBOARD = [["✅ Да", "❌ Нет"]]

# Главное меню
def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📝 Начать опрос", callback_data="start_survey")],
        [InlineKeyboardButton("ℹ️ О кадровом резерве", callback_data="reserve_info")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Кнопка возврата в главное меню
def get_back_to_menu_keyboard():
    keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]]
    return InlineKeyboardMarkup(keyboard)

# Обработчик команды /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает команду /start"""
    if update.message:
        await update.message.reply_text(
            "Добро пожаловать в бот опроса кадрового резерва ОАО «Савушкин продукт»!\n\n" + WELCOME_MESSAGE,
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await update.callback_query.message.reply_text(
            "Добро пожаловать в бот опроса кадрового резерва ОАО «Савушкин продукт»!\n\n" + WELCOME_MESSAGE,
            reply_markup=get_main_menu_keyboard()
        )

# Обработчик команды /menu
async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает команду /menu"""
    await update.message.reply_text(
        "🏠 Главное меню:",
        reply_markup=get_main_menu_keyboard()
    )

# Обработчик команды /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает команду /help"""
    await update.message.reply_text(
        HELP_TEXT,
        reply_markup=get_back_to_menu_keyboard(),
        parse_mode='Markdown'
    )

# Обработчик команды /status
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает команду /status"""
    user_data = context.user_data
    answers = user_data.get('answers', {})
    
    if not answers:
        status_text = "📊 **Статус опроса:**\n\nВы еще не начинали опрос."
    else:
        status_text = "📊 **Статус опроса:**\n\n"
        for question_num, answer in answers.items():
            if isinstance(question_num, int):
                status_text += f"Вопрос {question_num}: {answer}\n"
            else:
                status_text += f"{question_num}: {answer}\n"
        
        if 'fio' in answers:
            status_text += "\n✅ Опрос завершен!"
        else:
            status_text += "\n⏳ Опрос в процессе..."
    
    await update.message.reply_text(
        status_text,
        reply_markup=get_back_to_menu_keyboard(),
        parse_mode='Markdown'
    )

# Обработчик inline-кнопок
async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия inline-кнопок"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "main_menu":
        await query.edit_message_text(
            "🏠 Главное меню:",
            reply_markup=get_main_menu_keyboard()
        )
    
    elif query.data == "start_survey":
        # Показываем приветственное сообщение перед началом опроса
        await query.edit_message_text(
            WELCOME_MESSAGE + "\n\n*Для начала опроса ответьте на первый вопрос:*",
            parse_mode='Markdown'
        )
        await ask_first_question(query, context)
    
    elif query.data == "reserve_info":
        await query.edit_message_text(
            RESERVE_INFO,
            reply_markup=get_back_to_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    elif query.data == "help":
        await query.edit_message_text(
            HELP_TEXT,
            reply_markup=get_back_to_menu_keyboard(),
            parse_mode='Markdown'
        )

# Функция для первого вопроса опроса
async def ask_first_question(update, context: ContextTypes.DEFAULT_TYPE):
    """Задает первый вопрос: проверка сотрудника"""
    question = "Являетесь ли вы сотрудником ОАО «Савушкин продукт»?"
    
    if hasattr(update, 'callback_query'):
        # Если пришло из inline-кнопки, используем существующее сообщение
        message = update.callback_query.message
        reply_markup = ReplyKeyboardMarkup(YES_NO_KEYBOARD, resize_keyboard=True)
        await message.reply_text(question, reply_markup=reply_markup)
    else:
        # Если пришло из команды, используем update.message
        reply_markup = ReplyKeyboardMarkup(YES_NO_KEYBOARD, resize_keyboard=True)
        await update.message.reply_text(question, reply_markup=reply_markup)
    
    context.user_data['current_question'] = 1

# Функция для второго вопроса опроса
async def ask_second_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задает второй вопрос: о кадровом резерве"""
    question = "Хотели бы Вы, чтобы Ваша кандидатура была рассмотрена для включения в кадровый резерв?"
    
    reply_markup = ReplyKeyboardMarkup(YES_NO_KEYBOARD, resize_keyboard=True)
    await update.message.reply_text(question, reply_markup=reply_markup)
    context.user_data['current_question'] = 2

# ВЕТКА ДА - пользователь хочет в кадровый резерв
async def ask_position_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вопрос: Какую должность рассматриваете"""
    question = "Какую должность Вы рассматриваете для возможного назначения в рамках кадрового резерва?"
    
    await update.message.reply_text(question, reply_markup=ReplyKeyboardRemove())
    context.user_data['current_question'] = 3

async def ask_initiatives_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вопрос: Какие инициативы или программы"""
    question = "Какие инициативы или программы Вы хотели бы видеть для развития сотрудников?"
    
    await update.message.reply_text(question)
    context.user_data['current_question'] = 4

async def ask_training_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вопрос: Готовы ли пройти обучение"""
    question = "Готовы ли Вы пройти обучение или стажировку для включения в кадровый резерв?"
    
    reply_markup = ReplyKeyboardMarkup(YES_NO_KEYBOARD, resize_keyboard=True)
    await update.message.reply_text(question, reply_markup=reply_markup)
    context.user_data['current_question'] = 5

async def ask_career_obstacles_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вопрос: Что мешает карьерному росту"""
    question = "Что, по Вашему мнению, мешает карьерному росту внутри компании?"
    
    await update.message.reply_text(question, reply_markup=ReplyKeyboardRemove())
    context.user_data['current_question'] = 6

async def ask_improvements_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вопрос: Предложения по улучшению"""
    question = "Есть ли у Вас предложения по улучшению работы Вашего филиала или компании в целом?"
    
    await update.message.reply_text(question)
    context.user_data['current_question'] = 7

async def ask_rotation_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вопрос: Готовы к ротации"""
    question = "Готовы ли Вы к ротации или переводу в другое подразделение (филиал)?"
    
    reply_markup = ReplyKeyboardMarkup(YES_NO_KEYBOARD, resize_keyboard=True)
    await update.message.reply_text(question, reply_markup=reply_markup)
    context.user_data['current_question'] = 8

async def ask_cities_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вопрос: Выбор городов для ротации"""
    question = "Укажите preferred города для ротации (можно выбрать несколько):"
    
    # Создаем клавиатуру с городами (по 3 в строке для компактности)
    keyboard = []
    for i in range(0, len(CITIES), 3):
        keyboard.append(CITIES[i:i+3])
    keyboard.append(["✅ Завершить выбор"])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        question + "\n\nВыберите города по одному, затем нажмите '✅ Завершить выбор'",
        reply_markup=reply_markup
    )
    context.user_data['current_question'] = 9
    context.user_data['selected_cities'] = []  # Инициализируем список выбранных городов

async def ask_structural_unit_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вопрос: Структурное подразделение"""
    question = "Укажите структурное подразделение:"
    
    await update.message.reply_text(question, reply_markup=ReplyKeyboardRemove())
    context.user_data['current_question'] = 10

# ВЕТКА НЕТ - пользователь не хочет в кадровый резерв
async def ask_reason_no_reserve_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вопрос: Причина отказа от кадрового резерва (множественный выбор как города)"""
    question = "Пожалуйста, укажите причину, по которой Вы не готовы рассматривать включение в кадровый резерв:"
    
    # Инициализируем список выбранных причин
    context.user_data['selected_reasons'] = []
    
    # Создаем клавиатуру с причинами (по 2 в строке для компактности)
    keyboard = []
    for i in range(0, len(REASONS_NO_RESERVE), 2):
        row = REASONS_NO_RESERVE[i:i+2]
        keyboard.append(row)
    keyboard.append(["✅ Завершить выбор"])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        question + "\n\nВыберите причины по одной, затем нажмите '✅ Завершить выбор'",
        reply_markup=reply_markup
    )
    context.user_data['current_question'] = "3_alt"

async def ask_other_reason_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вопрос: Уточнение причины 'Другое'"""
    question = "Пожалуйста, укажите Вашу причину:"
    
    await update.message.reply_text(
        question,
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data['current_question'] = "other_reason"

async def ask_career_obstacles_alt_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вопрос: Что мешает карьерному росту (альтернативная ветка)"""
    question = "Что, по Вашему мнению, мешает карьерному росту внутри компании?"
    
    await update.message.reply_text(question, reply_markup=ReplyKeyboardRemove())
    context.user_data['current_question'] = "4_alt"

async def ask_improvements_alt_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вопрос: Предложения по улучшению (альтернативная ветка)"""
    question = "Есть ли у Вас предложения по улучшению работы Вашего филиала или компании в целом?"
    
    await update.message.reply_text(question)
    context.user_data['current_question'] = "5_alt"

# ОБЩИЕ ВОПРОСЫ (для обеих веток)
async def ask_current_city_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вопрос: ПП/ТФ, в котором работаете"""
    question = "ПП/ТФ, в котором вы работаете:"
    
    keyboard = []
    for i in range(0, len(CITIES), 3):
        keyboard.append(CITIES[i:i+3])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(question, reply_markup=reply_markup)
    context.user_data['current_question'] = "current_city"

async def ask_current_position_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вопрос: Текущая должность"""
    question = "Ваша профессия/должность, которую Вы сейчас занимаете (укажите):"
    
    await update.message.reply_text(question, reply_markup=ReplyKeyboardRemove())
    context.user_data['current_question'] = "current_position"

async def ask_education_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вопрос: Образование"""
    question = "Ваше образование:"
    
    # Распределяем по 2 в ряд
    keyboard = []
    for i in range(0, len(EDUCATION_LEVELS), 2):
        row = EDUCATION_LEVELS[i:i+2]
        keyboard.append(row)
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(question, reply_markup=reply_markup)
    context.user_data['current_question'] = "education"

async def ask_education_institution_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вопрос: Учебное заведение (если выбрано 'Обучаюсь')"""
    question = "Укажите учебное заведение, в котором обучаетесь:"
    
    await update.message.reply_text(question)
    context.user_data['current_question'] = "education_institution"

async def ask_age_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вопрос: Возраст"""
    question = "Ваш возраст:"
    
    # Распределяем по 2 в ряд
    keyboard = []
    for i in range(0, len(AGE_GROUPS), 2):
        row = AGE_GROUPS[i:i+2]
        keyboard.append(row)
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(question, reply_markup=reply_markup)
    context.user_data['current_question'] = "age"

async def ask_fio_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вопрос: ФИО"""
    question = "Укажите ФИО:"
    
    await update.message.reply_text(question, reply_markup=ReplyKeyboardRemove())
    context.user_data['current_question'] = "fio"

# Функция для валидации ФИО
def validate_fio(fio):
    """Проверяет корректность ФИО"""
    # Убираем лишние пробелы
    fio = ' '.join(fio.split())
    
    # Проверяем длину (минимум 5 символов, максимум 100)
    if len(fio) < 5 or len(fio) > 100:
        return False, "ФИО должно содержать от 5 до 100 символов"
    
    # Проверяем, что есть хотя бы 2 слова (Имя и Фамилия)
    parts = fio.split()
    if len(parts) < 2:
        return False, "Укажите как минимум имя и фамилию"
    
    # Проверяем, что все символы кириллические, дефисы или пробелы
    for char in fio:
        if not (char.isalpha() or char in ' -'):
            return False, "ФИО может содержать только буквы, дефисы и пробелы"
    
    return True, fio

# Функция для завершения опроса
async def finish_survey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершает опрос и благодарит пользователя"""
    
    # Сохраняем результаты
    user_id = update.message.from_user.id
    answers = context.user_data.get('answers', {})
    
    # Формируем сообщение с результатами
    result_message = "✅ Спасибо за участие в опросе!\n\nВаши ответы сохранены.\n\nОпрос завершен!"
    
    await update.message.reply_text(
        result_message,
        reply_markup=get_back_to_menu_keyboard()
    )
    
    # Выводим ответы в консоль для отладки
    print(f"Ответы пользователя {user_id}:")
    for question_num, answer in answers.items():
        print(f"Вопрос {question_num}: {answer}")
    print("---")
    
    # Очищаем данные пользователя
    context.user_data.clear()

# Обработчик текстовых сообщений (кнопок и ответов)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия кнопок и текстовые ответы"""
    user_message = update.message.text
    current_question = context.user_data.get('current_question', 0)
    
    # Инициализируем словарь ответов если его нет
    if 'answers' not in context.user_data:
        context.user_data['answers'] = {}

    # Вопрос 1: Проверка сотрудника
    if current_question == 1:
        if user_message in ["✅ Да", "❌ Нет"]:
            context.user_data['answers'][1] = user_message
            if user_message == "✅ Да":
                await ask_second_question(update, context)
            else:
                # Убираем клавиатуру и предлагаем вернуться в меню
                await update.message.reply_text(
                    "К сожалению, данный опрос только для сотрудников компании.",
                    reply_markup=ReplyKeyboardRemove()
                )
                await update.message.reply_text(
                    "Вы можете вернуться в главное меню:",
                    reply_markup=get_back_to_menu_keyboard()
                )
                context.user_data.clear()
        else:
            await update.message.reply_text("Пожалуйста, выберите вариант ответа с помощью кнопок.")

    # Вопрос 2: Хочет ли в кадровый резерв
    elif current_question == 2:
        if user_message in ["✅ Да", "❌ Нет"]:
            context.user_data['answers'][2] = user_message
            if user_message == "✅ Да":
                context.user_data['branch'] = 'yes'
                await ask_position_question(update, context)
            else:
                context.user_data['branch'] = 'no'
                await ask_reason_no_reserve_question(update, context)
        else:
            await update.message.reply_text("Пожалуйста, выберите вариант ответа с помощью кнопок.")

    # ВЕТКА ДА
    elif current_question == 3:  # Должность
        context.user_data['answers'][3] = user_message
        await ask_initiatives_question(update, context)

    elif current_question == 4:  # Инициативы
        context.user_data['answers'][4] = user_message
        await ask_training_question(update, context)

    elif current_question == 5:  # Обучение
        if user_message in ["✅ Да", "❌ Нет"]:
            context.user_data['answers'][5] = user_message
            await ask_career_obstacles_question(update, context)
        else:
            await update.message.reply_text("Пожалуйста, выберите вариант ответа с помощью кнопок.")

    elif current_question == 6:  # Препятствия карьерному росту
        context.user_data['answers'][6] = user_message
        await ask_improvements_question(update, context)

    elif current_question == 7:  # Предложения по улучшению
        context.user_data['answers'][7] = user_message
        await ask_rotation_question(update, context)

    elif current_question == 8:  # Ротация
        if user_message in ["✅ Да", "❌ Нет"]:
            context.user_data['answers'][8] = user_message
            if user_message == "✅ Да":
                await ask_cities_question(update, context)
            else:
                await ask_current_city_question(update, context)
        else:
            await update.message.reply_text("Пожалуйста, выберите вариант ответа с помощью кнопок.")

    elif current_question == 9:  # Выбор городов для ротации
        if user_message == "✅ Завершить выбор":
            if context.user_data['selected_cities']:
                context.user_data['answers'][9] = ", ".join(context.user_data['selected_cities'])
                await ask_structural_unit_question(update, context)
            else:
                await update.message.reply_text("Пожалуйста, выберите хотя бы один город.")
        elif user_message in CITIES:
            if user_message not in context.user_data['selected_cities']:
                context.user_data['selected_cities'].append(user_message)
                await update.message.reply_text(f"Добавлен: {user_message}\nВыберите еще или нажмите '✅ Завершить выбор'")
            else:
                await update.message.reply_text("Этот город уже выбран.")

    elif current_question == 10:  # Структурное подразделение
        context.user_data['answers'][10] = user_message
        await ask_current_city_question(update, context)

    # ВЕТКА НЕТ
    elif current_question == "3_alt":  # Причина отказа (множественный выбор как города)
        if user_message == "✅ Завершить выбор":
            if context.user_data['selected_reasons']:
                # Проверяем, выбрано ли "Другое"
                if "Другое (укажите)" in context.user_data['selected_reasons']:
                    # Если выбрано "Другое", спрашиваем уточнение
                    await ask_other_reason_question(update, context)
                else:
                    # Сохраняем выбранные причины и переходим дальше
                    context.user_data['answers'][3] = ", ".join(context.user_data['selected_reasons'])
                    await ask_career_obstacles_alt_question(update, context)
            else:
                await update.message.reply_text("❌ Пожалуйста, выберите хотя бы одну причину.")
        
        elif user_message in REASONS_NO_RESERVE:
            if user_message not in context.user_data['selected_reasons']:
                # Добавляем причину
                context.user_data['selected_reasons'].append(user_message)
                selected_count = len(context.user_data['selected_reasons'])
                await update.message.reply_text(f"✅ Добавлена причина: {user_message}\n\nВыбрано причин: {selected_count}\nВыберите еще или нажмите '✅ Завершить выбор'")
            else:
                # Убираем причину
                context.user_data['selected_reasons'].remove(user_message)
                selected_count = len(context.user_data['selected_reasons'])
                await update.message.reply_text(f"❌ Убрана причина: {user_message}\n\nВыбрано причин: {selected_count}\nВыберите еще или нажмите '✅ Завершить выбор'")

    elif current_question == "other_reason":  # Обработка текста для "Другое"
        if user_message.strip():
            context.user_data['other_reason'] = user_message.strip()
            # Обновляем текст "Другое" с уточнением
            if "Другое (укажите)" in context.user_data['selected_reasons']:
                context.user_data['selected_reasons'].remove("Другое (укажите)")
                context.user_data['selected_reasons'].append(f"Другое: {user_message.strip()}")
            
            # Сохраняем выбранные причины и переходим дальше
            context.user_data['answers'][3] = ", ".join(context.user_data['selected_reasons'])
            await ask_career_obstacles_alt_question(update, context)
        else:
            await update.message.reply_text("❌ Пожалуйста, укажите причину:")
    elif current_question == "4_alt":  # Препятствия карьерному росту (альт)
        context.user_data['answers'][4] = user_message
        await ask_improvements_alt_question(update, context)

    elif current_question == "5_alt":  # Предложения по улучшению (альт)
        context.user_data['answers'][5] = user_message
        await ask_current_city_question(update, context)

    # ОБЩИЕ ВОПРОСЫ
    elif current_question == "current_city":
        context.user_data['answers']['current_city'] = user_message
        await ask_current_position_question(update, context)

    elif current_question == "current_position":
        context.user_data['answers']['current_position'] = user_message
        await ask_education_question(update, context)

    elif current_question == "education":
        if user_message in EDUCATION_LEVELS:
            context.user_data['answers']['education'] = user_message
            if user_message == "Обучаюсь":
                # Убираем клавиатуру сразу после выбора "Обучаюсь"
                await update.message.reply_text(
                    "Вы выбрали: Обучаюсь",
                    reply_markup=ReplyKeyboardRemove()
                )
                await ask_education_institution_question(update, context)
            else:
                await ask_age_question(update, context)
        else:
            await update.message.reply_text("Пожалуйста, выберите вариант ответа с помощью кнопок.")

    elif current_question == "education_institution":
        context.user_data['answers']['education_institution'] = user_message
        await ask_age_question(update, context)

    elif current_question == "age":
        if user_message in AGE_GROUPS:
            context.user_data['answers']['age'] = user_message
            await ask_fio_question(update, context)
        else:
            await update.message.reply_text("Пожалуйста, выберите вариант ответа с помощью кнопок.")

    elif current_question == "fio":
        # Валидация ФИО
        is_valid, result = validate_fio(user_message)
        if is_valid:
            context.user_data['answers']['fio'] = result
            await finish_survey(update, context)
        else:
            await update.message.reply_text(
                f"❌ {result}\n\nПожалуйста, укажите корректное ФИО (например: Иванов Иван Иванович):"
            )

    else:
        # Если сообщение не обработано, показываем главное меню
        await update.message.reply_text(
            "Выберите действие:",
            reply_markup=get_main_menu_keyboard()
        )

# Обработчик ошибок
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Произошла ошибка: {context.error}")

# Главная функция
def main():
    print("Запускаю бота опроса...")
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    
    # Обработчики кнопок и сообщений
    application.add_handler(CallbackQueryHandler(handle_button_click))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.add_error_handler(error)
    
    print("Бот запущен! Нажмите Ctrl+C для остановки.")
    application.run_polling()

if __name__ == "__main__":
    main()