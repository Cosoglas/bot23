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
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
START_IMAGE = "https://i.postimg.cc/26JL6gM2/kot1.jpg"
USERS_PER_PAGE = 8 # Количество пользователей на одной странице в админке

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
     "https://i.postimg.cc/FHjWx0XJ/thumbnail-018f07bdda6ff835b3ee30dc7572f196.jpg",
     "https://i.postimg.cc/rwSn952m/thumbnail-6b2cc498458e6de5b5ceb24c54746954.jpg",
     "https://i.postimg.cc/K8nq5thj/thumbnail-76be7666be5c714e881c440af442d38d.jpg",
     "https://i.postimg.cc/cLQ9cfGx/thumbnail-8f9cb890cba522fcc3df4c69aa5d6342.jpg",
     "https://i.postimg.cc/3xgSZ2Qv/thumbnail-8fa421c43eaccb5cb056762842a3a1c5.jpg",
     "https://i.postimg.cc/sgp6J5Cf/thumbnail-a2c3f2d6d2194dbfa2679df4d6ddcff0.jpg",
     "https://i.postimg.cc/9QG8ByHz/thumbnail-a68d0849094e7b90b456a1fdb2c183d3.jpg",
     "https://i.postimg.cc/2S4cxnNb/thumbnail-cfafd01ab72c60d164caddd7e4a01a62.jpg",
     "https://i.postimg.cc/Jzb6QjCR/thumbnail-daabf99af3f246fa753389db6186cc60.jpg",
     "https://i.postimg.cc/9QG8ByHf/thumbnail-f58379667ea072cb7c83eca53e18db17.jpg",
     "https://i.postimg.cc/Nj1JxRv5/thumbnail-fea1e9f71733a64f27f47ae77fa1edd4.jpg",






]

CAPTIONS = [
    "🎨 Вот твоя картина!", "✨ Специально для тебя", "🖼️ Наслаждайся!",
    "🌟 Красота, правда?", "💎 Шедевр!", "Красотка да", "ебать жестко"
]

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
    writing_to_user = State()

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
    users_data[user_id_str]['messages_count'] = users_data[user_id_str].get('messages_count', 0) + 1
    save_data(USERS_FILE, users_data)

def set_all_users_offline():
    """Устанавливает всем пользователям статус 'оффлайн'."""
    if not users_data: return
    for user_id in users_data:
        users_data[user_id]['is_online'] = False
    if save_data(USERS_FILE, users_data):
        print("ℹ️ Все пользователи помечены как оффлайн.")

# ========== КЛАВИАТУРЫ ==========

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

def get_admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👥 Список пользователей", callback_data="admin_users_page:0")],
        [InlineKeyboardButton(text="📢 Сделать рассылку", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🏠 Выйти", callback_data="main_menu")]
    ])

def get_admin_stats_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Просмотреть все посты", callback_data="admin_view_posts:0")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel")]
    ])

def get_users_page_keyboard(page=0):
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
    nav_buttons = []
    if post_index > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"admin_view_posts:{post_index - 1}"))
    nav_buttons.append(InlineKeyboardButton(text=f"{post_index + 1}/{total_posts}", callback_data="noop"))
    if post_index < total_posts - 1:
        nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"admin_view_posts:{post_index + 1}"))
    return InlineKeyboardMarkup(inline_keyboard=[
        nav_buttons,
        [InlineKeyboardButton(text="🗑️ Удалить этот пост", callback_data=f"admin_delete_post:{post_index}")],
        [InlineKeyboardButton(text="↩️ Назад к статистике", callback_data="admin_stats")]
    ])

def get_confirm_delete_keyboard(post_index):
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

# ========== ОБРАБОТЧИКИ ЛЕНТЫ И ПРЕДЛОЖКИ (ВОССТАНОВЛЕННЫЕ) ==========

@dp.callback_query(F.data == "feed_menu")
async def show_feed_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    update_user_data(callback.from_user.id, callback.from_user.username, callback.from_user.first_name)
    caption = f"📱 **Лента постов**\n\nВсего постов в ленте: **{len(feed_posts)}**\n\nВыбери действие:"
    await callback.message.edit_media(
        media=InputMediaPhoto(media=START_IMAGE, caption=caption, parse_mode="Markdown"),
        reply_markup=get_feed_menu_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "view_random_post")
async def view_random_post(callback: types.CallbackQuery):
    update_user_data(callback.from_user.id, callback.from_user.username, callback.from_user.first_name)
    if not feed_posts:
        await callback.answer("📭 Лента пока пуста! Будь первым!", show_alert=True)
        return
    post = random.choice(feed_posts)
    author_name = post.get('author_name', 'Аноним')
    author_username = post.get('author_username', '')
    author_info = f"👤 **От:** {author_name}" + (f" (@{author_username})" if author_username else "")
    full_caption = f"{author_info}\n📅 {post.get('date', 'Неизвестно')}\n{'-'*30}\n\n{post.get('text', '')}"
    
    try:
        if post.get('photo'):
            await callback.message.edit_media(
                media=InputMediaPhoto(media=post['photo'], caption=full_caption, parse_mode="Markdown"),
                reply_markup=get_after_post_keyboard()
            )
        else:
            await callback.message.delete()
            await callback.message.answer(text=full_caption, reply_markup=get_after_post_keyboard(), parse_mode="Markdown")
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
             # Если пост тот же самый, может возникнуть ошибка, что сообщение не изменилось. Это нормально.
            print(f"Ошибка при показе поста: {e}")
    await callback.answer()

@dp.callback_query(F.data == "add_post")
async def start_add_post(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(FeedState.waiting_for_post)
    update_user_data(callback.from_user.id, callback.from_user.username, callback.from_user.first_name)
    await callback.message.delete()
    await callback.message.answer(
        "✍️ **Добавить пост в ленту**\n\nОтправь мне текст или фото (можно с подписью).",
        reply_markup=get_cancel_keyboard(), parse_mode="Markdown"
    )
    await callback.answer()

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
        post_data['text'] = message.caption or ''
    elif message.text:
        post_data['text'] = message.text
    else:
        await message.answer("⚠️ Отправь текст или фото.", reply_markup=get_cancel_keyboard())
        return

    feed_posts.append(post_data)
    save_data(FEED_FILE, feed_posts)
    await state.clear()
    await message.answer("✅ **Пост добавлен в ленту!**", reply_markup=get_start_keyboard())


@dp.callback_query(F.data == "send_suggestion")
async def start_suggestion(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SuggestionState.waiting_for_message)
    update_user_data(callback.from_user.id, callback.from_user.username, callback.from_user.first_name)
    await callback.message.delete()
    await callback.message.answer(
        "✉️ **Отправка сообщения админу**\n\nНапиши, что хочешь передать. Можно отправить текст, фото, видео и т.д.",
        reply_markup=get_cancel_keyboard(), parse_mode="Markdown"
    )
    await callback.answer()

@dp.message(SuggestionState.waiting_for_message)
async def handle_suggestion(message: types.Message, state: FSMContext):
    update_user_data(message.from_user.id, message.from_user.username, message.from_user.first_name)
    username = f"@{message.from_user.username}" if message.from_user.username else "скрыт"
    info_text = f"📩 **Сообщение от** {message.from_user.first_name} ({username})\n🆔 `{message.from_user.id}`"
    try:
        await message.forward(chat_id=ADMIN_ID)
        await bot.send_message(chat_id=ADMIN_ID, text=info_text, parse_mode="Markdown")
        await message.answer("✅ **Сообщение отправлено!**", reply_markup=get_start_keyboard())
    except Exception as e:
        await message.answer("⚠️ Ошибка отправки. Попробуй позже.", reply_markup=get_start_keyboard())
        print(f"Ошибка при пересылке сообщения от {message.from_user.id}: {e}")
    await state.clear()


# ========== СЕКЦИЯ АДМИНИСТРИРОВАНИЯ ==========

@dp.message(Command("admin"))
@dp.callback_query(F.data == "admin_panel")
async def show_admin_panel(message: types.Message | types.CallbackQuery, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    await state.clear()
    text = f"👑 **Админ-панель**\n\nДобро пожаловать, повелитель!"
    markup = get_admin_keyboard()
    
    if isinstance(message, types.Message):
        await message.answer(text, reply_markup=markup, parse_mode="Markdown")
    else:
        try:
            await message.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")
        except TelegramBadRequest: # Если сообщение не изменилось
            pass
        await message.answer()

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

@dp.callback_query(F.data.startswith("admin_users_page:"))
async def show_users_list(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    page = int(callback.data.split(":")[1])
    await callback.message.edit_text(
        f"👥 **Список пользователей** (Страница {page + 1})",
        reply_markup=get_users_page_keyboard(page)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_user_select:"))
async def select_user_to_message(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    user_id = callback.data.split(":")[1]
    user_name = users_data.get(user_id, {}).get('first_name', f"ID: {user_id}")
    
    await state.set_state(AdminState.writing_to_user)
    await state.update_data(target_user_id=user_id)
    
    await callback.message.edit_text(
        f"✍️ Отправка сообщения пользователю **{user_name}**.\n\n"
        f"Просто отправь мне то, что хочешь ему переслать.",
        reply_markup=get_cancel_keyboard(callback_data=f"admin_users_page:0"),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.message(AdminState.writing_to_user)
async def send_message_to_user(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    state_data = await state.get_data()
    target_user_id = state_data.get("target_user_id")
    await state.clear()
    
    if not target_user_id:
        await message.answer("⚠️ Ошибка, ID пользователя не найден.", reply_markup=get_admin_keyboard())
        return

    try:
        await message.copy_to(chat_id=target_user_id)
        await message.answer(f"✅ Сообщение успешно отправлено!", reply_markup=get_admin_keyboard())
    except (TelegramBadRequest, TelegramAPIError) as e:
        await message.answer(f"❌ Не удалось отправить. Возможно, юзер заблокировал бота.\nОшибка: `{e}`", parse_mode="Markdown", reply_markup=get_admin_keyboard())

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
        f"📜 **Пост #{post_index + 1}**\n{author_info}\n"
        f"📅 {post.get('date', 'Неизвестно')}\n{'-'*30}\n\n{post.get('text', '')}"
    )
    
    markup = get_view_post_keyboard(post_index, len(feed_posts))
    
    try:
        if post.get('photo'):
            await callback.message.edit_media(
                media=InputMediaPhoto(media=post['photo'], caption=full_caption, parse_mode="Markdown"),
                reply_markup=markup
            )
        else:
            await callback.message.edit_text(full_caption, reply_markup=markup, parse_mode="Markdown")
    except TelegramBadRequest: pass
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_delete_post:"))
async def admin_delete_post_confirm(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    post_index = int(callback.data.split(":")[1])
    await callback.message.edit_text(
        f"Вы уверены, что хотите удалить пост #{post_index + 1}?",
        reply_markup=get_confirm_delete_keyboard(post_index)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_confirm_delete:"))
async def admin_confirm_delete_action(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    post_index = int(callback.data.split(":")[1])
    
    if post_index < len(feed_posts):
        feed_posts.pop(post_index)
        save_data(FEED_FILE, feed_posts)
        await callback.answer("✅ Пост удален!", show_alert=True)
    
    new_index = min(post_index, len(feed_posts) - 1)
    if new_index < 0:
        await admin_show_stats(callback)
    else:
        callback.data = f"admin_view_posts:{new_index}"
        await admin_view_post(callback)

@dp.callback_query(F.data == "noop")
async def noop_callback(callback: types.CallbackQuery):
    await callback.answer()

# ========== ЗАПУСК БОТА ==========
async def main():
    print("🚀 ЗАПУСК БОТА...")
    set_all_users_offline() 
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏸️ БОТ ОСТАНОВЛЕН")
    finally:
        set_all_users_offline()