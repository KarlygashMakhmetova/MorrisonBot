import telebot
from telebot import types
from coin_rewards import rewards
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os

bot = telebot.TeleBot('7252441687:AAG_NXXHUAD7SsObvvrd3_-JShZEhld3X2c')


STUDENTS_FILE = 'students.json'
TEACHERS_FILE = 'teachers.json'
SHOP_FILE = 'shop_data.json'

session = {}
students = {}
teachers = {}
add_teacher_sessions = {}

remove_coins_sessions = {}

ADMIN_IDS = [827084249, 831628355]
def is_admin(user_id):
    return user_id in ADMIN_IDS
def is_teacher(user_id):
    return str(user_id) in teachers
def is_student(user_id):
    return str(user_id) in students
def load_teachers():
    global teachers
    if os.path.exists(TEACHERS_FILE):
        with open(TEACHERS_FILE, 'r', encoding='utf-8') as f:
            teachers = json.load(f)
    else:
        teachers = {}
def save_teachers():
    with open(TEACHERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(teachers, f, ensure_ascii=False, indent=4)
def load_students():
    global students
    if os.path.exists(STUDENTS_FILE):
        with open(STUDENTS_FILE, 'r', encoding='utf-8') as f:
            students = json.load(f)
    else:
        students = {}
def save_students():
    with open(STUDENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(students, f, ensure_ascii=False, indent=4)
def load_shop_data():
    try:
        with open(SHOP_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
def save_shop_data(data=None):
    if data is None:
        data = shop_data
    with open("shop_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
def add_student(user_id, name, username=None):
    user_id = str(user_id)
    if user_id not in students:
        students[user_id] = {
            "name": name,
            "coins": 0,
            "transactions": []
        }
        if username:
            students[user_id]["username"] = username
        save_students()
def add_coins(user_id, amount, reason="", teacher_name=""):
    user_id = str(user_id)
    if user_id in students:
        students[user_id]['coins'] += amount
        students[user_id].setdefault("transactions", [])
        students[user_id]["transactions"].append({
            "type": "reward",
            "amount": amount,
            "reason": reason,
            "teacher": teacher_name
        })
        save_students()
def remove_coins(user_id, amount, reason="", teacher_name=""):
    user_id = str(user_id)
    if user_id in students and students[user_id]['coins'] >= amount:
        students[user_id]['coins'] -= amount
        students[user_id].setdefault("transactions", [])
        students[user_id]["transactions"].append({
            "type": "withdrawal",
            "amount": amount,
            "reason": reason,
            "teacher": teacher_name
        })
        save_students()
        return True
    return False
def get_coins(user_id):
    return students.get(str(user_id), {}).get('coins', 0)
def find_students_by_name(name_query):
    name_query = name_query.lower()
    return [(uid, data['name']) for uid, data in students.items() if name_query in data['name'].lower()]
def get_main_shop_inline():
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [InlineKeyboardButton(text=cat, callback_data=f"shop_{cat}") for cat in shop_data.keys()]
    keyboard.add(*buttons)
    return keyboard
def get_category_items(category):
    items = shop_data.get(category, [])
    text = f"🛍 <b>{category}</b>\n\n"
    for i, (name, price, desc) in enumerate(items, 1):
        text += f"{i}. <b>{name}</b> - {price} 🪙\n{desc}\n\n"
    return text.strip()
def get_items_keyboard(category):
    keyboard = InlineKeyboardMarkup(row_width=3)
    items = shop_data.get(category, [])
    buttons = [
        InlineKeyboardButton(
            text=str(i + 1),
            callback_data=f"buy_{category}_{i}"
        )
        for i in range(len(items))
    ]
    keyboard.add(*buttons)
    return keyboard

load_teachers()
load_students()
shop_data = load_shop_data()

new_users = {}
add_student_sessions = {}

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    username = message.from_user.username or f"id{user_id}"
    name = message.from_user.first_name

    if not is_student(user_id) and not is_teacher(user_id) and not is_admin(user_id):
        new_users[username] = {"user_id": user_id, "name": name}
        bot.send_message(user_id, "Ожидайте, пока вас зарегистрируют.")
        wait_sticker = open('wait.webp', 'rb')
        bot.send_sticker(user_id, wait_sticker)
        return

    welcome = f"Привет, {name}! Добро пожаловать в систему монеток!"
    if is_teacher(user_id):
        welcome += "\n👩‍🏫 Чтобы узнать команды, нажми /info"
    elif is_student(user_id):
        welcome += "\n🧒 Чтобы узнать команды, нажми /info"
    elif is_admin(user_id):
        welcome += "\nТы - админ!🔥 \nЧтобы узнать команды, нажми /info"

    bot.send_message(user_id, welcome)

@bot.message_handler(commands=['addteacher'])
def add_teacher_command(message):
    if not is_admin(message.chat.id):
        return bot.send_message(message.chat.id, "❌ У вас нет доступа к этой команде.")

    bot.send_message(message.chat.id, "Введите username учителя (без @):")
    bot.register_next_step_handler(message, process_teacher_username)
def process_teacher_username(message):
    username = message.text.strip().lstrip('@')
    found_user = new_users.get(username)

    if not found_user:
        return bot.send_message(message.chat.id, "❌ Пользователь не найден. Убедитесь, что он нажал /start. "
                                                 "\nНачните заново с команды /addteacher.")

    add_teacher_sessions[message.chat.id] = {"username": username}
    bot.send_message(message.chat.id, "Введите имя учителя (как будет отображаться):")
    bot.register_next_step_handler(message, process_teacher_name)
def process_teacher_name(message):
    admin_id = message.chat.id
    session_data = add_teacher_sessions.get(admin_id)
    if not session_data:
        return bot.send_message(admin_id, "❌ Ошибка. Начните заново с команды /addteacher.")

    name = message.text.strip()
    username = session_data['username']
    user_data = new_users.get(username)

    if not user_data:
        return bot.send_message(admin_id, "❌ Пользователь не найден.")

    user_id = str(user_data['user_id'])
    teachers[user_id] = name
    save_teachers()

    bot.send_message(admin_id, f"✅ Учитель {name} (@{username}) добавлен!")
    bot.send_message(user_data['user_id'], "🎓 Вы были зарегистрированы как учитель! Используйте команду /start.")

    del add_teacher_sessions[admin_id]
    del new_users[username]

@bot.message_handler(commands=['removeteacher'])
def remove_teacher(message):
    if not is_admin(message.chat.id):
        return bot.send_message(message.chat.id, "❌ У вас нет прав для этой команды.")

    if not teachers:
        return bot.send_message(message.chat.id, "📭 Список учителей пуст.")

    keyboard = types.InlineKeyboardMarkup()
    for uid, name in teachers.items():
        keyboard.add(types.InlineKeyboardButton(f"{name} (ID: {uid})", callback_data=f"delteacher_{uid}"))

    bot.send_message(message.chat.id, "🥺Выбери куратора для удаления:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delteacher_"))
def delete_teacher(call):
    if not is_admin(call.message.chat.id):
        return bot.answer_callback_query(call.id, "❌ Нет прав")

    teacher_id = call.data.split('_')[1]
    if teacher_id in teachers:
        teacher_name = teachers[teacher_id]
        del teachers[teacher_id]
        save_teachers()
        bot.send_message(call.message.chat.id, f"✅ Учитель {teacher_name} (ID: {teacher_id}) удалён.")
    else:
        bot.send_message(call.message.chat.id, "❌ Учитель не найден.")


@bot.message_handler(commands=['info'])
def info(message):
    user_id = message.chat.id

    if is_teacher(user_id):
        buttons = [
            KeyboardButton('/addstudent'),
            KeyboardButton('/addcoins'),
            KeyboardButton('/add_custom_coins'),
            KeyboardButton('/transactions'),
            KeyboardButton('/removecoins')
        ]
    elif is_admin(user_id):
        buttons = [
            KeyboardButton('/addteacher'),
            KeyboardButton('/removeteacher'),
            KeyboardButton('/addstudent'),
            KeyboardButton('/addcoins'),
            KeyboardButton('/add_custom_coins'),
            KeyboardButton('/removecoins'),
            KeyboardButton('/transactions'),
            KeyboardButton('/shop_edit'),
            KeyboardButton('/shop_remove'),
            KeyboardButton('/shop_add'),
            KeyboardButton('/tasks_add'),
            KeyboardButton('/tasks_remove'),
            KeyboardButton('/tasks_edit')
        ]
    else:
        welcome_txt = ("Привет! 👋 Я — бот, который помогает тебе зарабатывать монетки 🪙 за хорошее поведение, активность и успехи в учебе."
                       "\n\nВот что я умею:"
                       "\n\n🛍️ <b>Магазин наград</b>"
                       "\nТы можешь тратить свои монетки в магазине на разные призы и поощрения! Просто набери команду /shop, чтобы посмотреть доступные товары."
                       "\n\n💼 <b>Баланс</b>"
                       "\nХочешь узнать, сколько у тебя монет? Напиши команду /balance, и я покажу твой текущий счёт."
                       "\n\n🪙 <b>Как получать монетки ?</b> "
                       "\nВыполняйте задания и ваш Куратор зачислит монетки на счет")
        bot.send_message(user_id, welcome_txt, parse_mode='HTML')
        return

    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(*buttons)

    bot.send_message(user_id, "👇 Выберите нужную команду из списка", reply_markup=markup)

@bot.message_handler(commands=['profile'])
def profile(message):
    user_id = message.chat.id
    if is_student(user_id):
        coins = get_coins(user_id)
        bot.send_message(user_id, f"🧾 Ваш профиль:\nМонеток: {coins}")
    else:
        bot.send_message(user_id, "❌ Вы не зарегистрированы.")


@bot.message_handler(commands=['top'])
def top(message):
    sorted_students = sorted(students.items(), key=lambda x: x[1]['coins'], reverse=True)
    rating = "🏆 ТОП по количеству монет:\n"
    for i, (uid, info) in enumerate(sorted_students, 1):
        rating += f"{i}. {info['name']} — {info['coins']} монеток\n"
    bot.send_message(message.chat.id, rating)

# ✅ Обновлённая команда /addstudent
@bot.message_handler(commands=['addstudent'])
def handle_add_student(message):
    if not (is_teacher(message.chat.id) or is_admin(message.chat.id)):
        return bot.send_message(message.chat.id, "❌ Нет доступа.")
    bot.send_message(message.chat.id, "Введите username ученика (без @):")
    bot.register_next_step_handler(message, process_username)
def process_username(message):
    username = message.text.strip().lstrip('@')
    if username not in new_users:
        return bot.send_message(message.chat.id, "❌ Пользователь не найден. Убедитесь, что он нажал /start."
                                                 "\nНачните заново с команды /addstudent.")

    # Сохраняем username в сессии для этого учителя
    add_student_sessions[message.chat.id] = {'username': username}
    bot.send_message(message.chat.id, "Введите имя ученика (как хотите, чтобы отображалось):")
    bot.register_next_step_handler(message, process_student_name)
def process_student_name(message):
    teacher_id = message.chat.id
    if teacher_id not in add_student_sessions:
        return bot.send_message(teacher_id, "❌ Что-то пошло не так, начните сначала командой /addstudent.")

    name = message.text.strip()
    username = add_student_sessions[teacher_id]['username']
    user_data = new_users.get(username)
    if not user_data:
        return bot.send_message(teacher_id, "❌ Пользователь не найден, попробуйте снова. \n/addstudent")

    user_id = str(user_data['user_id'])
    add_student(user_id, name)  # Здесь добавляем ученика с именем от учителя
    bot.send_message(teacher_id, f"✅ Ученик {name} (@{username}) добавлен!\n\nХотите продолжить?/info")
    bot.send_message(user_data['user_id'],
                     "🎉 Вы были зарегистрированы! Отправьте команду /start, чтобы воспользоваться ботом.")

    # Удаляем из сессий
    del add_student_sessions[teacher_id]
    del new_users[username]

@bot.message_handler(commands=['addcoins'])
def addcoins_cmd(message):
    if not (is_teacher(message.chat.id) or is_admin(message.chat.id)):
        return
    bot.send_message(message.chat.id, "Введите имя ученика:")
    bot.register_next_step_handler(message, search_student)
def search_student(message):
    results = find_students_by_name(message.text)
    if not results:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_info"))
        return bot.send_message(message.chat.id, "❌ Ученик не найден.", reply_markup=keyboard)
    keyboard = types.InlineKeyboardMarkup()
    for uid, name in results:
        keyboard.add(types.InlineKeyboardButton(name, callback_data=f'select_{uid}'))
    bot.send_message(message.chat.id, "Выберите ученика:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda c: c.data.startswith('select_'))
def select_student(call):
    teacher_id = call.message.chat.id
    student_id = call.data.split('_')[1]
    session[teacher_id] = student_id

    keyboard = types.InlineKeyboardMarkup()
    for k, r in rewards.items():
        keyboard.add(types.InlineKeyboardButton(f"{k}. {r['text']} - {r['coins']}🪙", callback_data=f"reward_{k}"))
    keyboard.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_info"))

    bot.send_message(teacher_id, "Выберите причину начисления:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda c: c.data.startswith('reward_'))
def give_reward(call):
    teacher_id = call.message.chat.id
    if teacher_id not in session:
        return bot.send_message(teacher_id, "❗ Сначала выберите ученика.")

    reason_id = call.data.split('_')[1]
    reward = rewards[reason_id]
    student_id = session[teacher_id]

    add_coins(student_id, reward['coins'], reward['text'], teachers.get(str(teacher_id), "Неизвестный учитель"))
    bot.send_message(teacher_id, f"✅ Начислено {reward['coins']}🪙 — {students[student_id]['name']}")
    bot.send_message(int(student_id), f"🎉 Тебе начислено {reward['coins']} монет(ы) за: {reward['text']}")

@bot.message_handler(commands=['add_custom_coins'])
def add_custom_coins_command(message):
    if not (is_teacher(message.from_user.id) or is_admin(message.from_user.id)):
        return bot.reply_to(message, "❌ У вас нет доступа к этой команде.")
    msg = bot.send_message(message.chat.id, "🔍 Введите имя ученика:")
    bot.register_next_step_handler(msg, search_student_by_name)
def search_student_by_name(message):
    search_name = message.text.lower()
    matches = {sid: data for sid, data in students.items() if search_name in data['name'].lower()}

    if not matches:
        msg = bot.send_message(message.chat.id, "⚠️ Ученик не найден. Попробуйте ещё раз:")
        return bot.register_next_step_handler(msg, search_student_by_name)

    markup = types.InlineKeyboardMarkup()
    for student_id, student in matches.items():
        markup.add(types.InlineKeyboardButton(
            text=f"{student['name']} ({student['coins']} монет)",
            callback_data=f"addcustomcoins_{student_id}"
        ))

    bot.send_message(message.chat.id, "👤 Найдены следующие ученики. Выберите нужного:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("addcustomcoins_"))
def handle_add_custom_coins_callback(call):
    student_id = call.data.split("_")[1]
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "💰 Введите количество монет:")
    bot.register_next_step_handler(msg, process_custom_coin_amount, student_id)
def process_custom_coin_amount(message, student_id):
    try:
        amount = int(message.text)
        if amount <= 0:
            raise ValueError
        msg = bot.send_message(message.chat.id, "✏️ Введите причину начисления:")
        bot.register_next_step_handler(msg, process_custom_coin_reason, student_id, amount)
    except ValueError:
        msg = bot.send_message(message.chat.id, "⚠️ Введите корректное положительное число:")
        bot.register_next_step_handler(msg, process_custom_coin_amount, student_id)
def process_custom_coin_reason(message, student_id, amount):
    reason = message.text
    teacher_id = message.from_user.id
    teacher_name = teachers.get(str(teacher_id), "Неизвестный учитель")

    add_coins(student_id, amount, reason, teacher_name)

    student_name = students[student_id]['name']
    bot.send_message(message.chat.id, f"✅ {amount} монет начислено ученику {student_name}.\n📄 Причина: {reason}")
    bot.send_message(int(student_id), f"🎉 Вам начислено {amount} монет(ы) за: {reason}")


@bot.message_handler(commands=['shop'])
def open_shop(message):
    if not is_student(message.chat.id) and not is_teacher(message.chat.id) and not is_admin(message.chat.id):
        return bot.send_message(message.chat.id, "⛔ Вы не зарегистрированы.")

    global shop_data
    shop_data = load_shop_data()

    bot.send_message(message.chat.id, "🛒 Выберите категорию:", reply_markup=get_main_shop_inline())

@bot.callback_query_handler(func=lambda call: call.data.startswith("shop_"))
def handle_shop_category(call):
    global shop_data
    shop_data = load_shop_data()

    category = call.data[5:]
    if category in shop_data:
        items_text = get_category_items(category)
        keyboard = get_items_keyboard(category)
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, items_text, parse_mode="HTML", reply_markup=keyboard)
    else:
        bot.answer_callback_query(call.id, text="Категория не найдена")

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def handle_buy_item(call):
    global students
    global shop_data

    shop_data = load_shop_data()
    load_students()

    parts = call.data.split("_")
    category = "_".join(parts[1:-1])
    item_index = int(parts[-1])
    user_id = str(call.from_user.id)

    if user_id not in students:
        bot.answer_callback_query(call.id, text="Вы не зарегистрированы.")
        return

    items = shop_data.get(category, [])
    if 0 <= item_index < len(items):
        item_name, price, desc = items[item_index]
        user_data = students[user_id]
        user_coins = user_data.get("coins", 0)

        if user_coins >= price:
            students[user_id]["coins"] -= price
            students[user_id].setdefault("transactions", []).append({
                "type": "purchase",
                "item": item_name,
                "price": price,
                "category": category
            })
            students[user_id].setdefault("purchases", []).append(item_name)

            save_students()

            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                f"✅ Вы успешно купили <b>{item_name}</b> за {price} 🪙!\n\n{desc}",
                parse_mode="HTML"
            )

            # Уведомление кураторам
            buyer_name = students[user_id]["name"]
            username = call.from_user.username

            if username:
                user_display = f"{buyer_name} - @{username}"
            else:
                user_display = f"{buyer_name} (id: {user_id})"

            notification_text = (
                f"📢 Ученик {user_display} купил товар: <b>{item_name}</b> за {price} 🪙."
            )

            for teacher_id in teachers:
                try:
                    bot.send_message(int(teacher_id), notification_text, parse_mode="HTML")
                except Exception as e:
                    print(f"Ошибка отправки учителю {teacher_id}: {e}")

            for admin_id in ADMIN_IDS:
                try:
                    bot.send_message(int(admin_id), notification_text, parse_mode="HTML")
                except Exception as e:
                    print(f"Ошибка отправки админу {admin_id}: {e}")

        else:
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                f"❌ Недостаточно монет. У вас: {user_coins} 🪙, нужно: {price} 🪙.",
                parse_mode="HTML"
            )
    else:
        bot.answer_callback_query(call.id, text="Товар не найден.")

@bot.message_handler(commands=['transactions'])
def handle_transactions(message):
    if not (is_teacher(message.from_user.id) or is_admin(message.from_user.id)):
        return bot.send_message(message.chat.id, "❌ Команда только для учителей.")

    bot.send_message(message.chat.id, "Введите имя ученика:")
    bot.register_next_step_handler(message, transaction_search_student)
def transaction_search_student(message):
    results = find_students_by_name(message.text)
    if not results:
        return bot.send_message(message.chat.id, "❌ Ученик не найден.")

    keyboard = types.InlineKeyboardMarkup()
    for uid, name in results:
        keyboard.add(types.InlineKeyboardButton(name, callback_data=f"transact_{uid}"))
    bot.send_message(message.chat.id, "Выберите ученика:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda c: c.data.startswith("transact_"))
def show_transactions(call):
    student_id = call.data.split("_")[1]
    if student_id not in students:
        return bot.answer_callback_query(call.id, "Ученик не найден.", show_alert=True)

    student = students[student_id]
    transactions = student.get('transactions', [])

    if not transactions:
        text = f"📒 У ученика {student['name']} пока нет операций."
    else:
        text = f"📒 История операций ученика {student['name']}:\n\n"
        for t in reversed(transactions[-10:]):  # последние 10, но от новой к старой
            t_type = t.get("type")
            if t_type == "reward":
                text += f"➕ Начислено: +{t['amount']} 🪙 за {t.get('reason', '')} (учитель: {t.get('teacher', '')})\n"
            elif t_type == "purchase":
                text += f"🛒 Покупка: {t.get('item', '')} за {t.get('price', 0)} 🪙 (категория: {t.get('category', '')})\n"
            elif t_type == "withdrawal" or t_type == "removal":
                text += f"➖ Изъято: {t['amount']} 🪙 за {t.get('reason', '')} (учитель: {t.get('teacher', '')})\n"
            else:
                text += f"❓ Неизвестная операция: {t}\n"

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_info"))

    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard)
    bot.answer_callback_query(call.id)

@bot.message_handler(commands=['removecoins'])
def removecoins_cmd(message):
    if not (is_teacher(message.from_user.id) or is_admin(message.from_user.id)):
        return bot.send_message(message.chat.id, "❌ Нет доступа.")
    bot.send_message(message.chat.id, "Введите имя ученика, у которого хотите изъять монетки:")
    bot.register_next_step_handler(message, removecoins_search_student)
def removecoins_search_student(message):
    results = find_students_by_name(message.text)
    if not results:
        return bot.send_message(message.chat.id, "❌ Ученик не найден. Попробуйте ещё раз.")
    keyboard = types.InlineKeyboardMarkup()
    for uid, name in results:
        keyboard.add(types.InlineKeyboardButton(name, callback_data=f'remove_select_{uid}'))
    bot.send_message(message.chat.id, "Выберите ученика для изъятия монет:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda c: c.data.startswith('remove_select_'))
def remove_select_student(call):
    teacher_id = call.message.chat.id
    student_id = call.data.split('_')[-1]
    remove_coins_sessions[teacher_id] = {'student_id': student_id}
    bot.answer_callback_query(call.id)
    bot.send_message(teacher_id, "Введите количество монет, которое нужно изъять:")
    bot.register_next_step_handler_by_chat_id(teacher_id, removecoins_input_amount)
def removecoins_input_amount(message):
    teacher_id = message.chat.id
    if teacher_id not in remove_coins_sessions:
        return bot.send_message(teacher_id, "❌ Сессия истекла, начните заново командой /removecoins.")

    try:
        amount = int(message.text.strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        return bot.send_message(teacher_id, "❌ Введите корректное положительное число.")

    remove_coins_sessions[teacher_id]['amount'] = amount
    bot.send_message(teacher_id, "Введите причину изъятия монет:")
    bot.register_next_step_handler_by_chat_id(teacher_id, removecoins_input_reason)
def removecoins_input_reason(message):
    teacher_id = message.chat.id
    if teacher_id not in remove_coins_sessions:
        return bot.send_message(teacher_id, "❌ Сессия истекла, начните заново командой /removecoins.")

    reason = message.text.strip()
    session_data = remove_coins_sessions[teacher_id]
    student_id = session_data['student_id']
    amount = session_data['amount']

    if student_id not in students:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_info"))
        bot.send_message(teacher_id, "❌ Ученик не найден.", reply_markup=keyboard)
        remove_coins_sessions.pop(teacher_id, None)
        return

    current_coins = students[student_id]['coins']
    if amount > current_coins:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_info"))
        bot.send_message(teacher_id, f"❌ У ученика всего {current_coins} монет, изъять {amount} невозможно.", reply_markup=keyboard)
        remove_coins_sessions.pop(teacher_id, None)
        return

    # Уменьшаем монеты и сохраняем транзакцию
    students[student_id]['coins'] -= amount
    students[student_id].setdefault('transactions', [])
    students[student_id]['transactions'].append({
        "type": "removal",
        "amount": -amount,
        "reason": reason,
        "teacher": teachers.get(str(teacher_id), "Неизвестный учитель")
    })
    save_students()
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_info"))
    keyboard.add(types.InlineKeyboardButton("📜 Показать транзакции", callback_data=f"transact_{student_id}"))

    bot.send_message(teacher_id, f"✅ Успешно изъято {amount}🪙 у {students[student_id]['name']}.\nПричина: {reason}", reply_markup=keyboard)
    bot.send_message(int(student_id), f"⚠️ У вас изъяли {amount} монет.\nПричина: {reason}", reply_markup=keyboard)

    # Очистка сессии
    remove_coins_sessions.pop(teacher_id, None)

@bot.callback_query_handler(func=lambda c: c.data == "back_to_info")
def back_to_info(call):
    bot.answer_callback_query(call.id)
    info(call.message)  # Повторно вызываем функцию info для возврата к командам

@bot.message_handler(func=lambda message: is_student(message.chat.id))
def restrict_student_text(message):
    # Не удаляем команды
    if message.text and message.text.startswith("/"):
        return

    # Удаляем остальное
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

@bot.message_handler(commands=['shop_edit'])
def manage_shop_edit(message):
    if not is_admin(message.chat.id):
        return
    global shop_data
    shop_data = load_shop_data()

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for category in shop_data.keys():
        markup.add(KeyboardButton(category))
    bot.send_message(message.chat.id, "Выберите категорию товара для редактирования:", reply_markup=markup)
    bot.register_next_step_handler(message, process_edit_category)
def process_edit_category(message):
    category = message.text.strip()

    if category not in shop_data:
        bot.send_message(message.chat.id, "❌ Категория не найдена. Пожалуйста, выберите категорию из списка ниже:")
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        for cat in shop_data.keys():
            markup.add(KeyboardButton(cat))
        bot.send_message(message.chat.id, "Выберите категорию товара для редактирования:", reply_markup=markup)
        bot.register_next_step_handler(message, process_edit_category)
        return

    items = shop_data[category]
    text = f"Выберите номер товара для редактирования из категории \"{category}\":\n\n"
    for idx, (name, price, desc) in enumerate(items, 1):
        text += f"{idx}. {name} — {price} коинов\n   {desc}\n"
    bot.send_message(message.chat.id, text)
    bot.register_next_step_handler(message, lambda m: process_edit_item_index(m, category))
def process_edit_item_index(message, category):
    try:
        index = int(message.text.strip()) - 1
        if index < 0 or index >= len(shop_data[category]):
            raise IndexError
    except:
        bot.send_message(message.chat.id, "❌ Неверный номер. Попробуйте снова.")

        items = shop_data[category]
        text = f"Выберите номер товара для редактирования из категории \"{category}\":\n\n"
        for idx, (name, price, desc) in enumerate(items, 1):
            text += f"{idx}. {name} — {price} коинов\n   {desc}\n"
        bot.send_message(message.chat.id, text)
        bot.register_next_step_handler(message, lambda m: process_edit_item_index(m, category))
        return

    bot.send_message(message.chat.id, "Что вы хотите изменить?\n\nВведите:\n1 — Название\n2 — Цену\n3 — Описание")
    bot.register_next_step_handler(message, lambda m: process_edit_field(m, category, index))
def process_edit_field(message, category, index):
    field = message.text.strip()
    if field not in ("1", "2", "3"):
        bot.send_message(message.chat.id, "❌ Неверный выбор. Введите:\n1 — Название\n2 — Цену\n3 — Описание")
        bot.register_next_step_handler(message, lambda m: process_edit_field(m, category, index))
        return

    field_map = {"1": "название", "2": "цена", "3": "описание"}
    bot.send_message(message.chat.id, f"Введите новое значение для пункта - {field_map[field]}:")
    bot.register_next_step_handler(message, lambda m: apply_edit(m, category, index, int(field)))
def apply_edit(message, category, index, field):
    global shop_data
    new_value = message.text.strip()
    item = list(shop_data[category][index])

    if field == 1:  # Название
        item[0] = new_value
    elif field == 2:  # Цена
        if not new_value.isdigit():
            bot.send_message(message.chat.id, "❌ Цена должна быть числом. Отмена.")
            return
        item[1] = int(new_value)
    elif field == 3:  # Описание
        item[2] = new_value

    shop_data[category][index] = item
    save_shop_data(shop_data)  # передай актуальные данные

    bot.send_message(
        message.chat.id,
        f"✅ Товар успешно обновлён:\n\nНазвание: {item[0]}\nЦена: {item[1]}\nОписание: {item[2]}"
    )


@bot.message_handler(commands=['shop_remove'])
def manage_shop_remove(message):
    if not is_admin(message.chat.id):
        return
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for category in shop_data.keys():
        markup.add(KeyboardButton(category))
    bot.send_message(message.chat.id, "🗑 Выберите категорию товара для удаления:", reply_markup=markup)
    bot.register_next_step_handler(message, process_remove_category)
def process_remove_category(message):
    category = message.text.strip()
    if category not in shop_data:
        bot.send_message(message.chat.id, "❌ Категория не найдена. Попробуйте снова.")
        bot.register_next_step_handler(message, process_remove_category)
        return

    items = shop_data[category]
    if not items:
        bot.send_message(message.chat.id, "❌ В этой категории нет товаров.")
        return

    text = f"🗑 Выберите номер товара для удаления из категории \"{category}\":\n\n"
    for idx, (name, price, desc) in enumerate(items, 1):
        text += f"{idx}. {name} — {price} коинов\n   {desc}\n"
    bot.send_message(message.chat.id, text)
    bot.register_next_step_handler(message, lambda m: process_remove_item_index(m, category))
def process_remove_item_index(message, category):
    try:
        index = int(message.text.strip()) - 1
        if index < 0 or index >= len(shop_data[category]):
            raise IndexError
    except:
        bot.send_message(message.chat.id, "❌ Неверный номер. Попробуйте снова.")
        bot.register_next_step_handler(message, lambda m: process_remove_item_index(m, category))
        return

    item = shop_data[category].pop(index)
    save_shop_data()

    bot.send_message(message.chat.id, f"✅ Товар \"{item[0]}\" успешно удалён из категории \"{category}\".")

@bot.message_handler(commands=['manageshop_add'])
def manage_shop_add(message):
    if not is_admin(message.chat.id):
        return
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for category in shop_data.keys():
        markup.add(KeyboardButton(category))
    markup.add(KeyboardButton("➕ Создать новую категорию"))
    bot.send_message(message.chat.id, "🛒 Выберите категорию для добавления товара или создайте новую:", reply_markup=markup)
    bot.register_next_step_handler(message, process_add_category_choice)
def process_add_category_choice(message):
    category = message.text.strip()
    if category == "➕ Создать новую категорию":
        bot.send_message(message.chat.id, "Введите название новой категории:")
        bot.register_next_step_handler(message, process_new_category_name)
        return

    if category not in shop_data:
        bot.send_message(message.chat.id, "❌ Категория не найдена. Попробуйте снова.")
        bot.register_next_step_handler(message, process_add_category_choice)
        return

    bot.send_message(message.chat.id, f"Введите данные нового товара для категории \"{category}\" в формате:\n\n<название> - <цена> - <описание>")
    bot.register_next_step_handler(message, process_add_item, category)
def process_new_category_name(message):
    new_category = message.text.strip()
    if new_category in shop_data:
        bot.send_message(message.chat.id, "❌ Такая категория уже существует. Попробуйте другую.")
        bot.register_next_step_handler(message, process_new_category_name)
        return

    shop_data[new_category] = []
    save_shop_data()
    bot.send_message(message.chat.id, f"✅ Категория \"{new_category}\" создана.")
    bot.send_message(message.chat.id, f"Введите данные нового товара для категории \"{new_category}\" в формате:\n\n<название> - <цена> - <описание>")
    bot.register_next_step_handler(message, process_add_item, new_category)
def process_add_item(message, category):
    text = message.text.strip()
    parts = text.split(" - ")
    if len(parts) != 3:
        bot.send_message(message.chat.id, "❌ Неверный формат. Используйте:\n<название> - <цена> - <описание>\nПопробуйте снова.")
        bot.register_next_step_handler(message, process_add_item, category)
        return

    name, price_str, desc = map(str.strip, parts)
    if not price_str.isdigit():
        bot.send_message(message.chat.id, "❌ Цена должна быть числом. Попробуйте снова.")
        bot.register_next_step_handler(message, process_add_item, category)
        return

    price = int(price_str)
    shop_data[category].append([name, price, desc])
    save_shop_data()

    bot.send_message(message.chat.id, f"✅ Товар \"{name}\" успешно добавлен в категорию \"{category}\" с ценой {price} и описанием:\n{desc}")

@bot.message_handler(commands=['tasks_add'])
def manage_tasks_add(message):
    if not is_admin(message.chat.id):
        return
    bot.send_message(message.chat.id,
                     "📝 Введите название нового задания и количество коинов в формате:\n\nзадание - коины (только количество)")
    bot.register_next_step_handler(message, process_new_task)

def process_new_task(message):
    text = message.text.strip()
    if ' - ' not in text:
        bot.send_message(message.chat.id, "❌ Неверный формат. Используйте:\nзадание - коины\nПопробуйте снова.")
        bot.register_next_step_handler(message, process_new_task)
        return

    task_name, coins_str = map(str.strip, text.split(' - ', 1))
    if not coins_str.isdigit():
        bot.send_message(message.chat.id, "❌ Количество коинов должно быть числом. Попробуйте снова.")
        bot.register_next_step_handler(message, process_new_task)
        return

    coins = int(coins_str)

    # Проверяем, чтобы такого задания по названию еще не было
    for val in rewards.values():
        if isinstance(val, dict) and val.get('text') == task_name:
            bot.send_message(message.chat.id, "❌ Задание с таким названием уже существует. Введите другое название.")
            bot.register_next_step_handler(message, process_new_task)
            return

    # Определяем новый ключ (строковый порядковый номер)
    existing_ids = [int(k) for k in rewards.keys() if k.isdigit()]
    new_id = str(max(existing_ids) + 1) if existing_ids else '1'

    rewards[new_id] = {'text': task_name, 'coins': coins}
    save_rewards()

    bot.send_message(message.chat.id, f"✅ Задание \"{task_name}\" успешно добавлено с наградой {coins} коинов.")

def save_rewards():
    import json
    with open('coin_rewards.py', 'w', encoding='utf-8') as f:
        f.write("rewards = ")
        f.write(repr(rewards))


@bot.message_handler(commands=['tasks_edit'])
def manage_tasks_edit(message):
    if not is_admin(message.chat.id):
        return

    if not rewards:
        bot.send_message(message.chat.id, "❌ Нет доступных заданий для редактирования.")
        return

    text = "📋 Список заданий для редактирования:\n\n"
    for key, val in rewards.items():
        text += f"{key}. {val['text']} — {val['coins']} 🪙\n"

    bot.send_message(message.chat.id, text + "\nВведите номер задания для редактирования:")
    bot.register_next_step_handler(message, process_edit_task_choice)
def process_edit_task_choice(message):
    task_id = message.text.strip()

    if task_id not in rewards:
        bot.send_message(message.chat.id, "❌ Неверный номер задания. Попробуйте снова.")
        bot.register_next_step_handler(message, process_edit_task_choice)
        return

    bot.send_message(
        message.chat.id,
        "Что вы хотите изменить?\n\nВведите:\n1 — Название\n2 — Коины"
    )
    bot.register_next_step_handler(message, lambda m: process_edit_task_field(m, task_id))
def process_edit_task_field(message, task_id):
    field = message.text.strip()

    if field not in ("1", "2"):
        bot.send_message(message.chat.id, "❌ Неверный выбор. Введите:\n1 — Название\n2 — Коины")
        bot.register_next_step_handler(message, lambda m: process_edit_task_field(m, task_id))
        return

    field_map = {"1": "название", "2": "коины"}
    bot.send_message(message.chat.id, f"Введите новое значение для поля — {field_map[field]}:")
    bot.register_next_step_handler(message, lambda m: apply_task_edit(m, task_id, int(field)))
def apply_task_edit(message, task_id, field):
    new_value = message.text.strip()

    if field == 1:
        rewards[task_id]['text'] = new_value
    elif field == 2:
        if not new_value.isdigit():
            bot.send_message(message.chat.id, "❌ Коины должны быть числом. Попробуйте снова.")
            bot.register_next_step_handler(message, lambda m: apply_task_edit(m, task_id, field))
            return
        rewards[task_id]['coins'] = int(new_value)

    save_rewards()

    bot.send_message(
        message.chat.id,
        f"✅ Задание успешно обновлено:\n\n"
        f"Задание: {rewards[task_id]['text']}\n"
        f"Коины: {rewards[task_id]['coins']} 🪙"
    )

@bot.message_handler(commands=['tasks_remove'])
def manage_tasks_remove(message):
    if not is_admin(message.chat.id):
        return

    if not rewards:
        bot.send_message(message.chat.id, "❌ Нет заданий для удаления.")
        return

    text = "🗑 Выберите задание для удаления:\n\n"
    for key, val in rewards.items():
        if isinstance(val, dict) and 'text' in val and 'coins' in val:
            text += f"{key}. {val['text']} — {val['coins']} 🪙\n"
        else:
            # Если элемент невалидный, можно пропустить или логировать
            continue

    bot.send_message(message.chat.id, text + "\nВведите номер задания для удаления:")
    bot.register_next_step_handler(message, process_remove_task_choice)
def process_remove_task_choice(message):
    task_id = message.text.strip()

    if task_id not in rewards or not isinstance(rewards[task_id], dict):
        bot.send_message(message.chat.id, "❌ Задание не найдено. Попробуйте снова.")
        bot.register_next_step_handler(message, process_remove_task_choice)
        return

    removed_task = rewards.pop(task_id)
    save_rewards()

    bot.send_message(message.chat.id, f"✅ Задание \"{removed_task['text']}\" успешно удалено.")

bot.infinity_polling(none_stop=True)
