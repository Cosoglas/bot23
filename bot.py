import asyncio
import os
import random
import json
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ========== НАСТРОЙКИ ==========
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
START_IMAGE = "https://i.postimg.cc/26JL6gM2/kot1.jpg"

IMAGES = [
    "https://i.postimg.cc/KzXy8NQt/photo-2026-04-30-21-13-18.jpg",
    "https://i.postimg.cc/tT0H45Dh/photo-2026-04-30-21-13-21.jpg",
    "https://i.postimg.cc/XJM0Y8xG/photo-2026-04-30-21-13-23.jpg",
    "https://i.postimg.cc/XJw6GCDC/photo-2026-04-30-21-13-30.jpg",
    "https://i.postimg.cc/d18ckySk/photo-2026-04-30-21-13-32.jpg",
    "https://i.postimg.cc/fLxQt9g3/photo-2026-04-30-21-13-33.jpg",
    "https://i.postimg.cc/pTDMhF1m/photo-2026-04-30-21-13-42.jpg",
    "https://i.postimg.cc/gJvbXZBn/photo-2026-04-30-21-13-44.jpg",
    "https://i.postimg.cc/DZq3JXYm/photo-2026-04-30-21-13-46.jpg",
    "https://i.postimg.cc/9M3jQp1d/photo-2026-04-30-21-13-48.jpg",
]

CAPTIONS = [
    "🎨 Вот твоя картина!",
    "✨ Специально для тебя",
    "🖼️ Наслаждайся!",
    "🌟 Красота, правда?",
    "💎 Шедевр!",
    "Красотка да",
    "ебать жестко",
    "бля кайф да?",
    "да да да да ",
    "Супер ",
    "Класс",
    "Ебать сука",
    "Выебал бы?",
    "Какая соска",
    "Кайфы",
]

# ========== ХРАНИЛИЩЕ ==========
# ИСПРАВЛЕНО: __file__ - правильная переменная для определения пути к текущему файлу
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FEED_FILE = os.path.join(SCRIPT_DIR, 'feed_posts.json')
USERS_FILE = os.path.join(SCRIPT_DIR, 'users_data.json')

print(f"📁 Файл ленты: {FEED_FILE}")
print(f"📁 Файл пользователей: {USERS_FILE}")

def load_feed():
    """Загрузка постов ленты"""
    try:
        if os.path.exists(FEED_FILE):
            with open(FEED_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"✅ Загружено постов: {len(data)}")
                return data
        else:
            print("ℹ️ Файл ленты не найден, будет создан новый.")
            return []
    except Exception as e:
        print(f"⚠️ Ошибка загрузки ленты: {e}")
        return []

def save_feed(posts):
    """Сохранение постов ленты"""
    try:
        with open(FEED_FILE, 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        print(f"💾 Лента сохранена! Постов: {len(posts)}")
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения ленты: {e}")
        return False

def load_users():
    """Загрузка данных пользователей"""
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"✅ Загружено пользователей: {len(data)}")
                return data
        else:
            print("ℹ️ Файл пользователей не найден, будет создан новый.")
            return {}
    except Exception as e:
        print(f"⚠️ Ошибка загрузки пользователей: {e}")
        return {}

def save_users(users):
    """Сохранение данных пользователей"""
    try:
        os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
        print(f"💾 Пользователи сохранены! Всего: {len(users)}")
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения пользователей: {e}")
        import traceback
        traceback.print_exc()
        return False

# Загружаем данные
feed_posts = load_feed()
users_data = load_users()

#===============================
def print_header():
    print("\n" + "=" * 70)
    print(" БОТ Он крутой")
    print("=" * 70)

def print_status(message, status="info"):
    icons = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌", "loading": "⏳"}
    icon = icons.get(status, "ℹ️")
    print(f"{icon} {message}")

def wait_for_exit():
    print("\n" + "-" * 70)
    input("Нажми ENTER для выхода...")

# Инициализация бота
try:
    print_status("Инициализация бота...", "loading")
    bot = Bot(token=API_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    print_status("Бот инициализирован успешно", "success")
except Exception as e:
    print_status(f"Ошибка инициализации: {e}", "error")
    wait_for_exit()
    exit(1)

# ========== СОСТОЯНИЯ ==========
class SuggestionState(StatesGroup):
    waiting_for_message = State()

class FeedState(StatesGroup):
    waiting_for_post = State()

# НОВОЕ: Состояния для админки
class AdminState(StatesGroup):
    waiting_for_broadcast = State()

# ========== ФУНКЦИИ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ==========
def update_user_data(user_id, username, first_name):
    """Обновление данных пользователя"""
    global users_data
    user_id_str = str(user_id)
    now_time = datetime.now().strftime('%d.%m.%Y %H:%M')
    if user_id_str not in users_data:
        users_data[user_id_str] = {
            'user_id': user_id, 'username': username, 'first_name': first_name,
            'first_seen': now_time, 'last_active': now_time, 'is_online': True, 'messages_count': 1
        }
        print(f"👤 Новый пользователь: {first_name} (ID: {user_id})")
    else:
        users_data[user_id_str]['last_active'] = now_time
        users_data[user_id_str]['is_online'] = True
        users_data[user_id_str]['username'] = username
        users_data[user_id_str]['first_name'] = first_name
        users_data[user_id_str]['messages_count'] += 1
    if not save_users(users_data):
        print(f"⚠️ Не удалось сохранить данные пользователя {user_id}")

def set_user_offline(user_id):
    """Пометить пользователя как оффлайн"""
    if str(user_id) in users_data:
        users_data[str(user_id)]['is_online'] = False
        save_users(users_data)

# ========== КЛАВИАТУРЫ ==========
def get_start_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=" Рандомное пх ", callback_data="random_pic")],
        [InlineKeyboardButton(text=" Лента постов тоже рандомных ", callback_data="feed_menu")],
        [InlineKeyboardButton(text=" Предложка ", callback_data="send_suggestion")]
    ])

def get_after_pic_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Еще картинку", callback_data="random_pic")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])

def get_cancel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить", callback_data="main_menu")]
    ])

# НОВОЕ: Клавиатура админки
def get_admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Сделать рассылку", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🏠 Выйти (в гл. меню)", callback_data="main_menu")]
    ])
    
# НОВОЕ: Клавиатура отмены для админки
def get_admin_cancel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить рассылку", callback_data="admin_panel")]
    ])

def get_feed_menu_keyboard(user_id=None):
    buttons = [
        [InlineKeyboardButton(text="👀 Смотреть рандомный пост", callback_data="view_random_post")],
        [InlineKeyboardButton(text="✍️ Добавить свой пост", callback_data="add_post")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_after_post_keyboard(user_id=None):
    buttons = [
        [InlineKeyboardButton(text="🔄 Еще пост", callback_data="view_random_post")],
        [InlineKeyboardButton(text="✍️ Добавить свой", callback_data="add_post")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ========== КОМАНДЫ ==========
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    update_user_data(message.from_user.id, message.from_user.username, message.from_user.first_name)
    caption_text = (
        "🎨 **Добро в предложку гениев 2.0**\n\n"
        "🖼️ Смотри рандомное пх\n"
        "📱 Читай ленту постов или добавляй свой\n\n"
        "Удачи и хорошо провести время\n\n"
        "Выбери действие:"
    )
    try:
        await message.answer_photo(
            photo=START_IMAGE, caption=caption_text,
            reply_markup=get_start_keyboard(), parse_mode="Markdown"
        )
        print_status(f"/start от {message.from_user.id}", "success")
    except Exception as e:
        print_status(f"Ошибка /start: {e}", "error")
        await message.answer(
            "🎨 **Добро пожаловать!**\n\nВыбери действие:",
            reply_markup=get_start_keyboard(), parse_mode="Markdown"
        )

# НОВОЕ: ОБРАБОТЧИК КОМАНДЫ /ADMIN
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message, state: FSMContext):
    """Команда /admin для администратора"""
    await state.clear()
    # Проверяем, является ли пользователь админом
    if message.from_user.id != ADMIN_ID:
        print(f"⚠️ Попытка доступа к админ-панели от пользователя {message.from_user.id}")
        return # Просто игнорируем, если не админ

    total_users = len(users_data)
    total_posts = len(feed_posts)
    admin_text = (
        f"👑 **Админ-панель**\n\n"
        f"Добро пожаловать, повелитель!\n\n"
        f"📊 **Краткая статистика:**\n"
        f"  - Пользователей: `{total_users}`\n"
        f"  - Постов в ленте: `{total_posts}`\n\n"
        f"Выберите действие:"
    )
    await message.answer(admin_text, reply_markup=get_admin_keyboard(), parse_mode="Markdown")

# ========== CALLBACK ОБРАБОТЧИКИ ==========

# НОВОЕ: Обработчики для админ-панели
@dp.callback_query(F.data == "admin_panel")
async def show_admin_panel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Это только для админа!", show_alert=True)
        return
    await callback.answer()
    total_users = len(users_data)
    total_posts = len(feed_posts)
    admin_text = (
        f"👑 **Админ-панель**\n\n"
        f"📊 **Статистика на {datetime.now().strftime('%d.%m.%Y %H:%M')}**\n"
        f"  - Пользователей: `{total_users}`\n"
        f"  - Постов в ленте: `{total_posts}`\n\n"
        f"Выберите действие:"
    )
    try:
        await callback.message.edit_text(admin_text, reply_markup=get_admin_keyboard(), parse_mode="Markdown")
    except:
        await callback.message.answer(admin_text, reply_markup=get_admin_keyboard(), parse_mode="Markdown")
        await callback.message.delete()


@dp.callback_query(F.data == "admin_stats")
async def admin_show_stats(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Это только для админа!", show_alert=True)
        return
    await callback.answer()
    total_users = len(users_data)
    total_posts = len(feed_posts)
    admin_text = (
        f"👑 **Админ-панель**\n\n"
        f"📊 **Статистика на {datetime.now().strftime('%d.%m.%Y %H:%M')}**\n"
        f"  - Пользователей: `{total_users}`\n"
        f"  - Постов в ленте: `{total_posts}`\n\n"
        f"Выберите действие:"
    )
    try:
        await callback.message.edit_text(admin_text, reply_markup=get_admin_keyboard(), parse_mode="Markdown")
    except: # Если сообщение не изменилось
        pass

@dp.callback_query(F.data == "admin_broadcast")
async def start_broadcast(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Это только для админа!", show_alert=True)
        return
    await state.set_state(AdminState.waiting_for_broadcast)
    await callback.message.edit_text(
        "📢 **Создание рассылки**\n\n"
        "Отправьте сообщение (текст, фото, видео, документ), которое будет разослано всем пользователям бота.",
        reply_markup=get_admin_cancel_keyboard()
    )

@dp.message(AdminState.waiting_for_broadcast)
async def process_broadcast(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    await state.clear()
    
    active_users = [int(user_id) for user_id in users_data]
    if not active_users:
        await message.answer("Нет пользователей для рассылки.", reply_markup=get_admin_keyboard())
        return

    await message.answer(f"🚀 Начинаю рассылку для {len(active_users)} пользователей...", reply_markup=get_admin_keyboard())
    
    success_count = 0
    fail_count = 0

    for user_id in active_users:
        try:
            # message.copy_to() - самый простой способ переслать любое сообщение
            await message.copy_to(chat_id=user_id)
            success_count += 1
            await asyncio.sleep(0.1) # небольшая задержка, чтобы не нагружать API
        except Exception as e:
            fail_count += 1
            print(f"⚠️ Не удалось отправить сообщение пользователю {user_id}: {e}")

    await message.answer(
        f"✅ **Рассылка завершена!**\n\n"
        f"- Успешно отправлено: `{success_count}`\n"
        f"- Не удалось доставить: `{fail_count}`",
        parse_mode="Markdown"
    )

# --- Основные обработчики пользователя ---

@dp.callback_query(F.data == "main_menu")
async def show_main_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    update_user_data(callback.from_user.id, callback.from_user.username, callback.from_user.first_name)
    try:
        await callback.message.edit_media(
            media=types.InputMediaPhoto(
                media=START_IMAGE, caption=" **Главное меню**\n\nВыбери действие:", parse_mode="Markdown"
            ),
            reply_markup=get_start_keyboard()
        )
    except:
        try: await callback.message.delete()
        except: pass
        await callback.message.answer_photo(
            photo=START_IMAGE, caption=" **Главное меню**\n\nВыбери действие:",
            reply_markup=get_start_keyboard(), parse_mode="Markdown"
        )

@dp.callback_query(F.data == "random_pic")
async def send_random_pic(callback: types.CallbackQuery):
    await callback.answer()
    update_user_data(callback.from_user.id, callback.from_user.username, callback.from_user.first_name)
    if not IMAGES:
        await callback.message.answer("❌ Картинки не загружены!")
        return
    random_image = random.choice(IMAGES)
    random_caption = random.choice(CAPTIONS)
    try:
        await callback.message.edit_media(
            media=types.InputMediaPhoto(media=random_image, caption=random_caption),
            reply_markup=get_after_pic_keyboard()
        )
    except Exception as e:
        try: await callback.message.delete()
        except: pass
        await callback.message.answer_photo(
            photo=random_image, caption=random_caption, reply_markup=get_after_pic_keyboard()
        )

@dp.callback_query(F.data == "feed_menu")
async def show_feed_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    update_user_data(callback.from_user.id, callback.from_user.username, callback.from_user.first_name)
    posts_count = len(feed_posts)
    caption_text = (
        f"📱 **Лента постов**\n\n"
        f"Здесь пользователи делятся своими мыслями,\nфото и всем, чем захотят!\n\n"
        f"📊 Всего постов в ленте: **{posts_count}**\n\n"
        f"Выбери действие:"
    )
    try:
        await callback.message.edit_caption(
            caption=caption_text, reply_markup=get_feed_menu_keyboard(callback.from_user.id), parse_mode="Markdown"
        )
    except:
        try: await callback.message.delete()
        except: pass
        await callback.message.answer_photo(
            photo=START_IMAGE, caption=caption_text,
            reply_markup=get_feed_menu_keyboard(callback.from_user.id), parse_mode="Markdown"
        )

@dp.callback_query(F.data == "view_random_post")
async def view_random_post(callback: types.CallbackQuery):
    await callback.answer()
    update_user_data(callback.from_user.id, callback.from_user.username, callback.from_user.first_name)
    if not feed_posts:
        await callback.message.answer(
            "📭 **Лента пока пуста!**\n\nБудь первым, кто добавит пост! ✍️",
            reply_markup=get_feed_menu_keyboard(callback.from_user.id), parse_mode="Markdown"
        )
        return
    post = random.choice(feed_posts)
    author_name = post.get('author_name', 'Аноним')
    author_username = post.get('author_username', '')
    author_info = f"👤 **От:** {author_name}"
    if author_username: author_info += f" (@{author_username})"
    full_caption = (
        f"{author_info}\n"
        f"📅 {post.get('date', 'Неизвестно')}\n"
        f"{'-'*30}\n\n"
        f"{post.get('text', '')}"
    )
    if post.get('photo'):
        try:
            await callback.message.edit_media(
                media=types.InputMediaPhoto(media=post['photo'], caption=full_caption, parse_mode="Markdown"),
                reply_markup=get_after_post_keyboard(callback.from_user.id)
            )
        except:
            try: await callback.message.delete()
            except: pass
            await callback.message.answer_photo(
                photo=post['photo'], caption=full_caption,
                reply_markup=get_after_post_keyboard(callback.from_user.id), parse_mode="Markdown"
            )
    else:
        try: await callback.message.delete()
        except: pass
        await callback.message.answer(
            text=full_caption, reply_markup=get_after_post_keyboard(callback.from_user.id), parse_mode="Markdown"
        )

@dp.callback_query(F.data == "add_post")
async def start_add_post(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(FeedState.waiting_for_post)
    update_user_data(callback.from_user.id, callback.from_user.username, callback.from_user.first_name)
    await callback.message.answer(
        "✍️ **Добавить пост в ленту**\n\nОтправь мне:\n📝 Текст\n📷 Фото (с подписью или без)\n\nТвой пост увидят другие пользователи!",
        reply_markup=get_cancel_keyboard(), parse_mode="Markdown"
    )

@dp.message(FeedState.waiting_for_post)
async def handle_new_post(message: types.Message, state: FSMContext):
    update_user_data(message.from_user.id, message.from_user.username, message.from_user.first_name)
    post_data = {
        'author_id': message.from_user.id, 'author_name': message.from_user.first_name,
        'author_username': message.from_user.username, 'date': datetime.now().strftime('%d.%m.%Y %H:%M'),
        'text': '', 'photo': None
    }
    if message.photo:
        post_data['photo'] = message.photo[-1].file_id
        post_data['text'] = message.caption if message.caption else '📷 Фото'
    elif message.text:
        post_data['text'] = message.text
    else:
        await message.answer("⚠️ Отправь текст или фото.", reply_markup=get_cancel_keyboard())
        return
    feed_posts.append(post_data)
    save_feed(feed_posts)
    await state.clear()
    try:
        await message.answer_photo(
            photo=START_IMAGE,
            caption=f"✅ **Пост добавлен в ленту!**\n\nТеперь другие пользователи смогут его увидеть.\n\n📊 Всего постов: **{len(feed_posts)}**",
            reply_markup=get_start_keyboard(), parse_mode="Markdown"
        )
    except:
        await message.answer(
            f"✅ **Пост добавлен в ленту!**\n\nТеперь другие пользователи смогут его увидеть.\n\n📊 Всего постов: **{len(feed_posts)}**",
            reply_markup=get_start_keyboard(), parse_mode="Markdown"
        )

@dp.callback_query(F.data == "send_suggestion")
async def start_suggestion(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(SuggestionState.waiting_for_message)
    update_user_data(callback.from_user.id, callback.from_user.username, callback.from_user.first_name)
    await callback.message.answer(
        "✉️ **Напиши сообщение мне**\n\nОтправить сообщение мне или можеш расказать как вам бот и про его проблемы.\n\nМожешь отправить:\n📝 Текст\n📷 Фото\n🎥 Видео",
        reply_markup=get_cancel_keyboard(), parse_mode="Markdown"
    )

@dp.message(SuggestionState.waiting_for_message)
async def handle_suggestion(message: types.Message, state: FSMContext):
    update_user_data(message.from_user.id, message.from_user.username, message.from_user.first_name)
    username = f"@{message.from_user.username}" if message.from_user.username else "скрыт"
    info_text = (
        f"📩 **Сообщение от пользователя**\n\n"
        f"👤 {message.from_user.first_name} ({username})\n"
        f"🆔 `{message.from_user.id}`"
    )
    try:
        await message.forward(chat_id=ADMIN_ID)
        await bot.send_message(chat_id=ADMIN_ID, text=info_text, parse_mode="Markdown")
        await message.answer("✅ **Сообщение отправлено!**\n\nя получил твоё сообщение.", reply_markup=get_start_keyboard(), parse_mode="Markdown")
    except Exception as e:
        await message.answer("⚠️ Ошибка отправки. Попробуй позже.", reply_markup=get_start_keyboard())
    await state.clear()

# ОБРАБОТЧИК ОСТАЛЬНЫХ СООБЩЕНИЙ - теперь он в самом конце
@dp.message()
async def handle_other(message: types.Message, state: FSMContext):
    update_user_data(message.from_user.id, message.from_user.username, message.from_user.first_name)
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Используй /start для начала работы", reply_markup=get_start_keyboard())

# ========== ЗАПУСК ==========
async def main():
    print_header()
    print_status("Инициализация файлов...", "loading")
    # Создаём файлы если не существуют
    if not os.path.exists(USERS_FILE):
        print_status("Создаю файл пользователей...", "loading")
        with open(USERS_FILE, 'w', encoding='utf-8') as f: json.dump({}, f)
        print_status("Файл пользователей создан", "success")
    if not os.path.exists(FEED_FILE):
        print_status("Создаю файл ленты...", "loading")
        with open(FEED_FILE, 'w', encoding='utf-8') as f: json.dump([], f)
        print_status("Файл ленты создан", "success")
    
    print_status("Проверка настроек...", "loading")
    print_status(f"Токен: {API_TOKEN[:10]}...", "success")
    print_status(f"Admin ID: {ADMIN_ID}", "success")
    print_status(f"Картинок: {len(IMAGES)}", "success")
    print_status(f"Постов в ленте: {len(feed_posts)}", "success")
    print_status(f"Пользователей: {len(users_data)}", "success")

    print("\n" + "=" * 70 + "\n🚀 ЗАПУСК БОТА...\n" + "=" * 70 + "\n")
    try:
        print_status("Подключение к Telegram...", "loading")
        me = await bot.get_me()
        print_status(f"Бот: @{me.username}", "success")
        print("\n" + "🟢" * 35 + "\n✅ БОТ ЗАПУЩЕН И РАБОТАЕТ!\n" + "🟢" * 35 + "\n")
        print_status("Ожидание сообщений...", "info")
        print("-" * 70 + "\n")
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        print("\n" + "🔴" * 35 + "\n❌ КРИТИЧЕСКАЯ ОШИБКА!\n" + "🔴" * 35 + "\n")
        print_status(f"Тип: {type(e).__name__}", "error")
        print_status(f"Описание: {e}", "error")
        import traceback
        traceback.print_exc()
        wait_for_exit()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n" + "=" * 70 + "\n⏸️ БОТ ОСТАНОВЛЕН\n" + "=" * 70)
        # Помечаем всех как оффлайн
        for user_id in users_data:
            set_user_offline(user_id)
        print_status("Работа завершена", "success")
    except Exception as e:
        print("\n\n" + "=" * 70 + "\n💥 ОШИБКА ПРИ ЗАПУСКЕ\n" + "=" * 70)
        print_status(f"Ошибка: {e}", "error")
        import traceback
        traceback.print_exc()
        wait_for_exit()