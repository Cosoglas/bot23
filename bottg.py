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

API_TOKEN = '8630016009:AAFCemGoNmWDjhtpA7djUIt6XgXi7lwGqm0'
ADMIN_ID = 5694956927

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
            print("ℹ️  Файл ленты не найден")
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
        print(f"❌ Ошибка сохранения: {e}")
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
            print("ℹ️  Файл пользователей не найден")
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
        
        if os.path.exists(USERS_FILE):
            file_size = os.path.getsize(USERS_FILE)
            print(f"📊 Размер файла: {file_size} байт")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка сохранения пользователей: {e}")
        import traceback
        traceback.print_exc()
        return False

# Загружаем данные
feed_posts = load_feed()
users_data = load_users()

# ===============================

def print_header():
    print("\n" + "=" * 70)
    print(" БОТ Он крутой")
    print("=" * 70)

def print_status(message, status="info"):
    icons = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
        "loading": "⏳"
    }
    icon = icons.get(status, "ℹ️")
    print(f"{icon}  {message}")

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

# ========== ФУНКЦИИ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ==========

def update_user_data(user_id, username, first_name):
    """Обновление данных пользователя"""
    global users_data
    
    user_id_str = str(user_id)
    
    if user_id_str not in users_data:
        users_data[user_id_str] = {
            'user_id': user_id,
            'username': username,
            'first_name': first_name,
            'first_seen': datetime.now().strftime('%d.%m.%Y %H:%M'),
            'last_active': datetime.now().strftime('%d.%m.%Y %H:%M'),
            'is_online': True,
            'messages_count': 1
        }
        print(f"👤 Новый пользователь: {first_name} (ID: {user_id})")
    else:
        users_data[user_id_str]['last_active'] = datetime.now().strftime('%d.%m.%Y %H:%M')
        users_data[user_id_str]['is_online'] = True
        users_data[user_id_str]['username'] = username
        users_data[user_id_str]['first_name'] = first_name
        users_data[user_id_str]['messages_count'] += 1
    
    result = save_users(users_data)
    
    if not result:
        print(f"⚠️ Не удалось сохранить данные пользователя {user_id}")

def set_user_offline(user_id):
    """Пометить пользователя как оффлайн"""
    if str(user_id) in users_data:
        users_data[str(user_id)]['is_online'] = False
        save_users(users_data)

# ========== КЛАВИАТУРЫ ==========

def get_start_keyboard():
    """Главное меню"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=" Рандомное пх  ", callback_data="random_pic")],
        [InlineKeyboardButton(text=" Лента постов тоже рандомных   ", callback_data="feed_menu")],
        [InlineKeyboardButton(text=" Предложка ", callback_data="send_suggestion")]
    ])

def get_after_pic_keyboard():
    """Кнопки после картинки"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Еще картинку", callback_data="random_pic")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])

def get_cancel_keyboard():
    """Кнопка отмены"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить", callback_data="main_menu")]
    ])

def get_feed_menu_keyboard(user_id=None):
    """Меню ленты постов"""
    buttons = [
        [InlineKeyboardButton(text="👀 Смотреть рандомный пост", callback_data="view_random_post")],
        [InlineKeyboardButton(text="✍️ Добавить свой пост", callback_data="add_post")],
    ]
    
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_after_post_keyboard(user_id=None):
    """Кнопки после просмотра поста"""
    buttons = [
        [InlineKeyboardButton(text="🔄 Еще пост", callback_data="view_random_post")],
        [InlineKeyboardButton(text="✍️ Добавить свой", callback_data="add_post")],
    ]
    
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ========== КОМАНДЫ ==========

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Команда /start"""
    await state.clear()
    
    # Обновляем данные пользователя
    update_user_data(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )
    
    caption_text = (
        "🎨 **Добро в предложку гениев 2.0**\n\n"
        "🖼️ Смотри рандомное пх\n"
        "📱 Читай ленту постов или добавляй свой\n\n"
        "Удачи и хорошо провести время\n\n"
        "Выбери действие:"
    )
    
    try:
        await message.answer_photo(
            photo=START_IMAGE,
            caption=caption_text,
            reply_markup=get_start_keyboard(),
            parse_mode="Markdown"
        )
        print_status(f"/start от {message.from_user.id}", "success")
    except Exception as e:
        print_status(f"Ошибка /start: {e}", "error")
        await message.answer(
            "🎨 **Добро пожаловать!**\n\nВыбери действие:",
            reply_markup=get_start_keyboard(),
            parse_mode="Markdown"
        )

# ========== CALLBACK ОБРАБОТЧИКИ ==========

@dp.callback_query(F.data == "main_menu")
async def show_main_menu(callback: types.CallbackQuery, state: FSMContext):
    """Главное меню"""
    await state.clear()
    await callback.answer()
    
    # Обновляем данные пользователя
    update_user_data(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name
    )
    
    try:
        await callback.message.edit_media(
            media=types.InputMediaPhoto(
                media=START_IMAGE,
                caption=" **Главное меню**\n\nВыбери действие:",
                parse_mode="Markdown"
            ),
            reply_markup=get_start_keyboard()
        )
    except:
        try:
            await callback.message.delete()
        except:
            pass
        
        await callback.message.answer_photo(
            photo=START_IMAGE,
            caption=" **Главное меню**\n\nВыбери действие:",
            reply_markup=get_start_keyboard(),
            parse_mode="Markdown"
        )

@dp.callback_query(F.data == "random_pic")
async def send_random_pic(callback: types.CallbackQuery):
    """Отправка случайной картинки"""
    await callback.answer()
    
    # Обновляем активность
    update_user_data(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name
    )
    
    if not IMAGES:
        await callback.message.answer("❌ Картинки не загружены!")
        return
    
    random_image = random.choice(IMAGES)
    random_caption = random.choice(CAPTIONS)
    
    try:
        await callback.message.edit_media(
            media=types.InputMediaPhoto(
                media=random_image,
                caption=random_caption
            ),
            reply_markup=get_after_pic_keyboard()
        )
    except Exception as e:
        try:
            await callback.message.delete()
        except:
            pass
        
        await callback.message.answer_photo(
            photo=random_image,
            caption=random_caption,
            reply_markup=get_after_pic_keyboard()
        )

@dp.callback_query(F.data == "feed_menu")
async def show_feed_menu(callback: types.CallbackQuery, state: FSMContext):
    """Меню ленты постов"""
    await state.clear()
    await callback.answer()
    
    # Обновляем активность
    update_user_data(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name
    )
    
    posts_count = len(feed_posts)
    
    caption_text = (
        f"📱 **Лента постов**\n\n"
        f"Здесь пользователи делятся своими мыслями,\n"
        f"фото и всем, чем захотят!\n\n"
        f"📊 Всего постов в ленте: **{posts_count}**\n\n"
        f"Выбери действие:"
    )
    
    try:
        await callback.message.edit_caption(
            caption=caption_text,
            reply_markup=get_feed_menu_keyboard(callback.from_user.id),
            parse_mode="Markdown"
        )
    except:
        try:
            await callback.message.delete()
        except:
            pass
        
        await callback.message.answer_photo(
            photo=START_IMAGE,
            caption=caption_text,
            reply_markup=get_feed_menu_keyboard(callback.from_user.id),
            parse_mode="Markdown"
        )

@dp.callback_query(F.data == "view_random_post")
async def view_random_post(callback: types.CallbackQuery):
    """Просмотр случайного поста"""
    await callback.answer()
    
    # Обновляем активность
    update_user_data(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name
    )
    
    if not feed_posts:
        await callback.message.answer(
            "📭 **Лента пока пуста!**\n\n"
            "Будь первым, кто добавит пост! ✍️",
            reply_markup=get_feed_menu_keyboard(callback.from_user.id),
            parse_mode="Markdown"
        )
        return
    
    post = random.choice(feed_posts)
    
    author_name = post.get('author_name', 'Аноним')
    author_username = post.get('author_username', '')
    
    author_info = f"👤 **От:** {author_name}"
    if author_username:
        author_info += f" (@{author_username})"
    
    post_date = post.get('date', 'Неизвестно')
    post_text = post.get('text', '')
    
    full_caption = (
        f"{author_info}\n"
        f"📅 {post_date}\n"
        f"{'-'*30}\n\n"
        f"{post_text}"
    )
    
    if post.get('photo'):
        try:
            await callback.message.edit_media(
                media=types.InputMediaPhoto(
                    media=post['photo'],
                    caption=full_caption,
                    parse_mode="Markdown"
                ),
                reply_markup=get_after_post_keyboard(callback.from_user.id)
            )
        except:
            try:
                await callback.message.delete()
            except:
                pass
            
            await callback.message.answer_photo(
                photo=post['photo'],
                caption=full_caption,
                reply_markup=get_after_post_keyboard(callback.from_user.id),
                parse_mode="Markdown"
            )
    else:
        try:
            await callback.message.delete()
        except:
            pass
        
        await callback.message.answer(
            text=full_caption,
            reply_markup=get_after_post_keyboard(callback.from_user.id),
            parse_mode="Markdown"
        )

@dp.callback_query(F.data == "add_post")
async def start_add_post(callback: types.CallbackQuery, state: FSMContext):
    """Начало добавления поста"""
    await callback.answer()
    await state.set_state(FeedState.waiting_for_post)
    
    # Обновляем активность
    update_user_data(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name
    )
    
    await callback.message.answer(
        "✍️ **Добавить пост в ленту**\n\n"
        "Отправь мне:\n"
        "📝 Текст\n"
        "📷 Фото (с подписью или без)\n\n"
        "Твой пост увидят другие пользователи!",
        reply_markup=get_cancel_keyboard(),
        parse_mode="Markdown"
    )

@dp.message(FeedState.waiting_for_post)
async def handle_new_post(message: types.Message, state: FSMContext):
    """Обработка нового поста"""
    
    # Обновляем активность
    update_user_data(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )
    
    post_data = {
        'author_id': message.from_user.id,
        'author_name': message.from_user.first_name,
        'author_username': message.from_user.username,
        'date': datetime.now().strftime('%d.%m.%Y %H:%M'),
        'text': '',
        'photo': None
    }
    
    if message.photo:
        post_data['photo'] = message.photo[-1].file_id
        post_data['text'] = message.caption if message.caption else '📷 Фото'
    elif message.text:
        post_data['text'] = message.text
    elif message.video:
        await message.answer(
            "⚠️ Пока поддерживаются только фото и текст.\n"
            "Отправь фото с подписью или текст.",
            reply_markup=get_cancel_keyboard()
        )
        return
    else:
        await message.answer(
            "⚠️ Отправь текст или фото.",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    feed_posts.append(post_data)
    save_feed(feed_posts)
    
    try:
        await message.answer_photo(
            photo=START_IMAGE,
            caption=(
                "✅ **Пост добавлен в ленту!**\n\n"
                f"Теперь другие пользователи смогут его увидеть.\n\n"
                f"📊 Всего постов: **{len(feed_posts)}**"
            ),
            reply_markup=get_start_keyboard(),
            parse_mode="Markdown"
        )
    except:
        await message.answer(
            "✅ **Пост добавлен в ленту!**\n\n"
            f"Теперь другие пользователи смогут его увидеть.\n\n"
            f"📊 Всего постов: **{len(feed_posts)}**",
            reply_markup=get_start_keyboard(),
            parse_mode="Markdown"
        )
    
    await state.clear()

@dp.callback_query(F.data == "send_suggestion")
async def start_suggestion(callback: types.CallbackQuery, state: FSMContext):
    """Начало отправки предложки"""
    await callback.answer()
    await state.set_state(SuggestionState.waiting_for_message)
    
    # Обновляем активность
    update_user_data(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name
    )
    
    await callback.message.answer(
        "✉️ **Напиши сообщение мне**\n\n"
        "Отправить сообщение мне или можеш расказать как вам бот и про его проблемы.\n\n"
        "Можешь отправить:\n"
        "📝 Текст\n"
        "📷 Фото\n"
        "🎥 Видео",
        reply_markup=get_cancel_keyboard(),
        parse_mode="Markdown"
    )

@dp.message(SuggestionState.waiting_for_message)
async def handle_suggestion(message: types.Message, state: FSMContext):
    """Обработка предложки"""
    
    # Обновляем активность
    update_user_data(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )
    
    username = f"@{message.from_user.username}" if message.from_user.username else "скрыт"
    first_name = message.from_user.first_name
    
    info_text = (
        f"📩 **Сообщение от пользователя**\n\n"
        f"👤 {first_name} ({username})\n"
        f"🆔 `{message.from_user.id}`"
    )

    try:
        await message.forward(chat_id=ADMIN_ID)
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=info_text,
            parse_mode="Markdown"
        )
        
        await message.answer(
            "✅ **Сообщение отправлено!**\n\n"
            "я получил твоё сообщение.",
            reply_markup=get_start_keyboard(),
            parse_mode="Markdown"
        )
        await state.clear()
    except Exception as e:
        await message.answer(
            "⚠️ Ошибка отправки. Попробуй позже.",
            reply_markup=get_start_keyboard()
        )
        await state.clear()

@dp.message()
async def handle_other(message: types.Message, state: FSMContext):
    """Обработка остальных сообщений"""
    
    # Обновляем активность
    update_user_data(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )
    
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            "Используй /start для начала работы",
            reply_markup=get_start_keyboard()
        )

# ========== ЗАПУСК ==========

async def main():
    print_header()
    
    print_status("Инициализация файлов...", "loading")
    
    # Создаём файлы если не существуют
    if not os.path.exists(USERS_FILE):
        print_status("Создаю файл пользователей...", "loading")
        try:
            with open(USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump({}, f)
            print_status("Файл пользователей создан", "success")
        except Exception as e:
            print_status(f"Ошибка создания файла: {e}", "error")
    
    if not os.path.exists(FEED_FILE):
        print_status("Создаю файл ленты...", "loading")
        try:
            with open(FEED_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f)
            print_status("Файл ленты создан", "success")
        except Exception as e:
            print_status(f"Ошибка создания файла: {e}", "error")
    
    print_status("Проверка настроек...", "loading")
    
    print_status(f"Токен: {API_TOKEN[:10]}...", "success")
    print_status(f"Admin ID: {ADMIN_ID}", "success")
    print_status(f"Картинок: {len(IMAGES)}", "success")
    print_status(f"Постов в ленте: {len(feed_posts)}", "success")
    print_status(f"Пользователей: {len(users_data)}", "success")
    
    print("\n" + "=" * 70)
    print("🚀 ЗАПУСК БОТА...")
    print("=" * 70 + "\n")
    
    try:
        print_status("Подключение к Telegram...", "loading")
        
        me = await bot.get_me()
        print_status(f"Бот: @{me.username}", "success")
        
        print("\n" + "🟢" * 35)
        print("✅ БОТ ЗАПУЩЕН И РАБОТАЕТ!")
        print("🟢" * 35 + "\n")
        
        print_status("Ожидание сообщений...", "info")
        
        print("-" * 70 + "\n")
        
        await dp.start_polling(bot, skip_updates=True)
        
    except Exception as e:
        print("\n" + "🔴" * 35)
        print("❌ КРИТИЧЕСКАЯ ОШИБКА!")
        print("🔴" * 35 + "\n")
        
        print_status(f"Тип: {type(e).__name__}", "error")
        print_status(f"Описание: {e}", "error")
        
        print("\n📋 Полная информация:")
        print("-" * 70)
        import traceback
        traceback.print_exc()
        print("-" * 70)
        
        wait_for_exit()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("⏸️  БОТ ОСТАНОВЛЕН")
        print("=" * 70)
        
        # Помечаем всех как оффлайн
        for user_id in users_data:
            set_user_offline(user_id)
        
        print_status("Работа завершена", "success")
        wait_for_exit()
    except Exception as e:
        print("\n\n" + "=" * 70)
        print("💥 ОШИБКА ПРИ ЗАПУСКЕ")
        print("=" * 70)
        print_status(f"Ошибка: {e}", "error")
        
        print("\n📋 Детали:")
        print("-" * 70)
        import traceback
        traceback.print_exc()
        print("-" * 70)
        
        wait_for_exit()