import asyncio
import os
import random
import json
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError

# ========== НАСТРОЙКИ ==========
API_TOKEN = '8630016009:AAFCemGoNmWDjhtpA7djUIt6XgXi7lwGqm0' # Твой токен
ADMIN_ID = 5694956927  # Твой ID

START_IMAGE = "https://i.postimg.cc/26JL6gM2/kot1.jpg"
USERS_PER_PAGE = 8 # Количество пользователей на одной странице в админке

IMAGES = [ "https://i.postimg.cc/KzXy8NQt/photo-2026-04-30-21-13-18.jpg", "https://i.postimg.cc/tT0H45Dh/photo-2026-04-30-21-13-21.jpg", "https://i.postimg.cc/XJM0Y8xG/photo-2026-04-30-21-13-23.jpg" ]
CAPTIONS = [ "🎨 Вот твоя картина!", "✨ Специально для тебя", "🖼️ Наслаждайся!", "🌟 Красота, правда?", "💎 Шедевр!", "Красотка да", "ебать жестко" ]

# ========== ХРАНИЛИЩЕ ==========
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FEED_FILE = os.path.join(SCRIPT_DIR, 'feed_posts.json')
USERS_FILE = os.path.join(SCRIPT_DIR, 'users_data.json')

def load_data(file_path, default_data):
    """Универсальная функция для загрузки JSON данных."""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default_data
    except (json.JSONDecodeError, IOError) as e:
        print(f"⚠️ Ошибка загрузки {file_path}: {e}. Будут использованы данные по умолчанию.")
        return default_data

def save_data(file_path, data):
    """Универсальная функция для сохранения JSON данных."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except IOError as e:
        print(f"❌ Ошибка сохранения {file_path}: {e}")
        return False

feed_posts = load_data(FEED_FILE, [])
users_data = load_data(USERS_FILE, {})

# ========== ИНИЦИАЛИЗАЦИЯ БОТА ==========
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ========== СОСТОЯНИЯ ==========
class SuggestionState(StatesGroup):
    waiting_for_message = State()

class FeedState(StatesGroup):
    waiting_for_post = State()

class AdminState(StatesGroup):
    waiting_for_broadcast = State()
    writing_to_user = State() # НОВОЕ: для отправки сообщения конкретному юзеру

# ========== ФУНКЦИИ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ==========
def update_user_data(user_id, username, first_name):
    """Обновление данных пользователя и установка статуса 'онлайн'."""
    user_id_str = str(user_id)
    now_time = datetime.now().strftime('%d.%m.%Y %H:%M')
    if user_id_str not in users_data:
        users_data[user_id_str] = { 'first_seen': now_time, 'messages_count': 0 }
        print(f"👤 Новый пользователь: {first_name} (ID: {user_id})")

    users_data[user_id_str].update({
        'user_id': user_id, 'username': username, 'first_name': first_name,
        'last_active': now_time, 'is_online': True
    })
    users_data[user_id_str]['messages_count'] += 1
    save_data(USERS_FILE, users_data)

def set_all_users_offline():
    """Устанавливает всем пользователям статус 'оффлайн'."""
    if not users_data: return
    for user_id in users_data:
        users_data[user_id]['is_online'] = False
    save_data(USERS_FILE, users_data)
    print("ℹ️ Все пользователи помечены как оффлайн.")


# ========== КЛАВИАТУРЫ ==========

# --- Пользовательские клавиатуры ---
def get_start_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🖼️ Рандомное пх", callback_data="random_pic")],
        [InlineKeyboardButton(text="📰 Лента постов", callback_data="feed_menu")],
        [InlineKeyboardButton(text="✉️ Предложка", callback_data="send_suggestion")]
    ])

def get_after_pic_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Еще", callback_data="random_pic")],
        [InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu")]
    ])

def get_cancel_keyboard(callback_data="main_menu"):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отменить", callback_data=callback_data)]])

def get_feed_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👀 Смотреть пост", callback_data="view_random_post")],
        [InlineKeyboardButton(text="✍️ Добавить свой", callback_data="add_post")],
        [InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu")]
    ])

def get_after_post_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Еще пост", callback_data="view_random_post")],
        [InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu")]
    ])

# --- Админские клавиатуры (НОВОЕ и ОБНОВЛЕННОЕ) ---
def get_admin_keyboard():
    """Главная админ-клавиатура."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👥 Список пользователей", callback_data="admin_users_page:0")],
        [InlineKeyboardButton(text="📢 Сделать рассылку", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🏠 Выйти", callback_data="main_menu")]
    ])

def get_admin_stats_keyboard():
    """Клавиатура для меню статистики."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Просмотреть все посты", callback_data="admin_view_posts:0")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel")]
    ])

def get_users_page_keyboard(page=0):
    """Клавиатура для постраничного вывода пользователей."""
    buttons = []
    user_ids = list(users_data.keys())
    start = page * USERS_PER_PAGE
    end = start + USERS_PER_PAGE
    
    for user_id in user_ids[start:end]:
        user = users_data[user_id]
        status_icon = "🟢" if user.get('is_online', False) else "⚫"
        btn_text = f"{status_icon} {user.get('first_name', 'N/A')}"
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"admin_user_select:{user_id}")])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin_users_page:{page - 1}"))
    if end < len(user_ids):
        nav_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"admin_users_page:{page + 1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
        
    buttons.append([InlineKeyboardButton(text="↩️ В админ-панель", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_view_post_keyboard(post_index, total_posts):
    """Клавиатура для просмотра постов в админке."""
    buttons = []
    nav_buttons = []
    if post_index > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"admin_view_posts:{post_index - 1}"))
    
    nav_buttons.append(InlineKeyboardButton(text=f"{post_index + 1}/{total_posts}", callback_data="noop")) # noop - no operation

    if post_index < total_posts - 1:
        nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"admin_view_posts:{post_index + 1}"))
    
    buttons.append(nav_buttons)
    buttons.append([InlineKeyboardButton(text="🗑️ Удалить этот пост", callback_data=f"admin_delete_post:{post_index}")])
    buttons.append([InlineKeyboardButton(text="↩️ Назад к статистике", callback_data="admin_stats")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirm_delete_keyboard(post_index):
    """Клавиатура подтверждения удаления поста."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Да, удалить", callback_data=f"admin_confirm_delete:{post_index}"),
            InlineKeyboardButton(text="Нет, отмена", callback_data=f"admin_view_posts:{post_index}")
        ]
    ])


# ========== ГЛАВНЫЕ КОМАНДЫ И ОБРАБОТЧИКИ ==========

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    update_user_data(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await message.answer_photo(
        photo=START_IMAGE,
        caption="🎨 **Добро пожаловать!**\n\nВыбери, что хочешь сделать:",
        reply_markup=get_start_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "main_menu")
async def show_main_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    update_user_data(callback.from_user.id, callback.from_user.username, callback.from_user.first_name)
    await callback.message.edit_media(
        media=InputMediaPhoto(media=START_IMAGE, caption="🎨 **Главное меню**\n\nВыбери действие:", parse_mode="Markdown"),
        reply_markup=get_start_keyboard()
    )
    await callback.answer()

# ... (остальные пользовательские обработчики остаются почти без изменений) ...

@dp.callback_query(F.data == "random_pic")
async def send_random_pic(callback: types.CallbackQuery):
    update_user_data(callback.from_user.id, callback.from_user.username, callback.from_user.first_name)
    random_image = random.choice(IMAGES)
    random_caption = random.choice(CAPTIONS)
    await callback.message.edit_media(
        media=InputMediaPhoto(media=random_image, caption=random_caption),
        reply_markup=get_after_pic_keyboard()
    )
    await callback.answer()

# ========== СЕКЦИЯ АДМИНИСТРИРОВАНИЯ (ВСЕ НОВОЕ И ОБНОВЛЕННОЕ) ==========

# Вход в админ-панель
@dp.message(Command("admin"))
@dp.callback_query(F.data == "admin_panel")
async def show_admin_panel(message: types.Message | types.CallbackQuery, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    await state.clear()

    text = f"👑 **Админ-панель**\n\nДобро пожаловать, повелитель!"
    
    if isinstance(message, types.Message):
        await message.answer(text, reply_markup=get_admin_keyboard(), parse_mode="Markdown")
    else:
        await message.message.edit_text(text, reply_markup=get_admin_keyboard(), parse_mode="Markdown")
        await message.answer()

# Показ статистики
@dp.callback_query(F.data == "admin_stats")
async def admin_show_stats(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    stats_text = (
        f"📊 **Статистика**\n\n"
        f"👥 Всего пользователей: `{len(users_data)}`\n"
        f"📰 Постов в ленте: `{len(feed_posts)}`"
    )
    await callback.message.edit_text(stats_text, reply_markup=get_admin_stats_keyboard(), parse_mode="Markdown")
    await callback.answer()

# Постраничный просмотр пользователей
@dp.callback_query(F.data.startswith("admin_users_page:"))
async def show_users_list(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    page = int(callback.data.split(":")[1])
    total_users = len(users_data)
    
    await callback.message.edit_text(
        f"👥 **Список пользователей** (Страница {page + 1})",
        reply_markup=get_users_page_keyboard(page)
    )
    await callback.answer()

# Выбор пользователя для отправки сообщения
@dp.callback_query(F.data.startswith("admin_user_select:"))
async def select_user_to_message(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    user_id = callback.data.split(":")[1]
    user_info = users_data.get(user_id, {})
    user_name = user_info.get('first_name', f"ID: {user_id}")
    
    await state.set_state(AdminState.writing_to_user)
    await state.update_data(target_user_id=user_id)
    
    await callback.message.edit_text(
        f"✍️ Отправка сообщения пользователю **{user_name}**.\n\n"
        f"Просто отправь мне то, что хочешь ему переслать (текст, фото, видео и т.д.).",
        reply_markup=get_cancel_keyboard(callback_data=f"admin_users_page:0"), # Вернуться к списку
        parse_mode="Markdown"
    )
    await callback.answer()

# Обработка и отправка сообщения конкретному пользователю
@dp.message(AdminState.writing_to_user)
async def send_message_to_user(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    state_data = await state.get_data()
    target_user_id = state_data.get("target_user_id")
    
    if not target_user_id:
        await message.answer("⚠️ Произошла ошибка, ID пользователя не найден.", reply_markup=get_admin_keyboard())
        await state.clear()
        return

    try:
        await message.copy_to(chat_id=target_user_id)
        await message.answer(f"✅ Сообщение успешно отправлено!", reply_markup=get_admin_keyboard())
    except (TelegramBadRequest, TelegramAPIError) as e:
        await message.answer(f"❌ Не удалось отправить сообщение. Возможно, пользователь заблокировал бота.\nОшибка: `{e}`", parse_mode="Markdown")
    
    await state.clear()

# Постраничный просмотр постов ленты в админке
@dp.callback_query(F.data.startswith("admin_view_posts:"))
async def admin_view_post(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    
    if not feed_posts:
        await callback.answer("Лента пуста!", show_alert=True)
        return

    post_index = int(callback.data.split(":")[1])
    post = feed_posts[post_index]

    author_name = post.get('author_name', 'Аноним')
    author_username = post.get('author_username', '')
    author_info = f"👤 **От:** {author_name}" + (f" (@{author_username})" if author_username else "")
    full_caption = (
        f"📜 **Пост #{post_index + 1}**\n"
        f"{author_info}\n"
        f"📅 {post.get('date', 'Неизвестно')}\n"
        f"{'-'*30}\n\n"
        f"{post.get('text', '')}"
    )
    
    reply_markup = get_view_post_keyboard(post_index, len(feed_posts))

    try:
        if post.get('photo'):
            await callback.message.edit_media(
                media=InputMediaPhoto(media=post['photo'], caption=full_caption, parse_mode="Markdown"),
                reply_markup=reply_markup
            )
        else: # Если в посте только текст
            await callback.message.edit_text(full_caption, reply_markup=reply_markup, parse_mode="Markdown")
    except TelegramBadRequest: # Если сообщение не изменилось (например, при нажатии на 1/N)
        pass
    except Exception as e:
        await callback.answer(f"Ошибка при показе поста: {e}", show_alert=True)
        
    await callback.answer()

# Шаг 1: Запрос на подтверждение удаления
@dp.callback_query(F.data.startswith("admin_delete_post:"))
async def admin_delete_post_confirm(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    post_index = int(callback.data.split(":")[1])
    
    await callback.message.edit_text(
        f"Вы уверены, что хотите удалить пост #{post_index + 1}?",
        reply_markup=get_confirm_delete_keyboard(post_index)
    )
    await callback.answer()

# Шаг 2: Фактическое удаление после подтверждения
@dp.callback_query(F.data.startswith("admin_confirm_delete:"))
async def admin_confirm_delete_action(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    post_index = int(callback.data.split(":")[1])
    
    if post_index < len(feed_posts):
        deleted_post = feed_posts.pop(post_index)
        save_data(FEED_FILE, feed_posts)
        await callback.answer("✅ Пост удален!", show_alert=True)
    else:
        await callback.answer("⚠️ Пост уже был удален.", show_alert=True)

    # После удаления возвращаемся к просмотру постов (к первому, если список пуст)
    new_index = min(post_index, len(feed_posts) - 1)
    if new_index < 0:
        await admin_show_stats(callback) # Если постов не осталось, вернуться в статистику
    else:
        # "Эмулируем" нажатие на кнопку просмотра поста, чтобы обновить сообщение
        callback.data = f"admin_view_posts:{new_index}"
        await admin_view_post(callback)

# Обработчик для "пустых" кнопок, например "1/10"
@dp.callback_query(F.data == "noop")
async def noop_callback(callback: types.CallbackQuery):
    await callback.answer()

# ... (тут можно разместить остальные ваши обработчики: feed_menu, add_post, suggestion и т.д.) ...
# В целях краткости я их сюда не дублирую, они должны работать как и раньше.

async def main():
    print("🚀 ЗАПУСК БОТА...")
    # При запуске убедимся, что старые 'online' статусы сброшены, если бот упал
    set_all_users_offline() 
    
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏸️ БОТ ОСТАНОВЛЕН")
    finally:
        # При корректной остановке все помечаются как оффлайн
        set_all_users_offline()