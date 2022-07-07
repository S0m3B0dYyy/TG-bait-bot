import sqlite3
import os, time, random
from aiogram import Bot, types
from aiogram.utils import executor
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import db

token = "0000000:AAAAAAA" # Токен телеграм бота
admin_id = 123456789 # ID админа
admin_link = "@link" # Ссылка на админа с @ в начале
link = "link_bot" # Ссылка на бота без @ в начале
video_cost = 10
photo_cost = 5
start_balance = 30
bonus_ref = 30

bot = Bot(token=token)

dp = Dispatcher(bot, storage=MemoryStorage())

class States(StatesGroup):
	menu = State()
	profile = State()

#------------------------------

def profile(user_id):
	_data = db.get_info(user_id)
	return f"""*Привет*, *{_data[2]}*!

📅 *Дата регистрации:* {_data[3]}
💵 *Баланс:* {_data[5]}

🔥 *Вывод от 100₽*
*Зарабатывай по 20₽ за каждого приглашенного друга!*

👤 *Приглашено:* {db.get_refs(user_id)}
*t.me/{link}?start={user_id}*

*Администратор:* {admin_link} 
"""

def reply_keyboard():
	keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
	keyboard.add(KeyboardButton('🖼 Видео'), KeyboardButton('🖼 Фото'))
	keyboard.add(KeyboardButton('💼 Профиль'))
	return keyboard

#------------------------------

# Меню
@dp.message_handler(text=["💼 Профиль"], state="*")
@dp.message_handler(commands=["start"], state="*")
async def menu(message: types.Message, state: FSMContext):
	_user_id = message.chat.id
	_username = message.chat.username
	if not (db.get_users_exist(message.chat.id)):
		if (message.text != "💼 Профиль" and message.text.startswith("/start ")):
			_ref = message.text.replace("/start ", "")
			if (int(message.chat.id) != int(_ref)):
				db.add_user_to_db(message.chat.id, message.chat.username, _ref, start_balance)
				db.set_balance(_ref, db.get_balance(_ref) + bonus_ref)
				await bot.send_message(chat_id = admin_id, text = f"Новый пользователь: {_user_id} (@{_username})\nПригласил: {_ref}")
				await bot.send_message(chat_id=_ref, text=f"*Кто-то перешел по твоей ссылке!*\nБаланс пополнен на {bonus_ref}", parse_mode='Markdown')
			else:
				db.add_user_to_db(message.chat.id, message.chat.username, 0, start_balance)
				await bot.send_message(chat_id = admin_id, text = f"Новый пользователь: {_user_id} (@{_username})")
		else:
			db.add_user_to_db(message.chat.id, message.chat.username, 0, start_balance)
			await bot.send_message(chat_id = admin_id, text = f"Новый пользователь: {_user_id} (@{_username})")
	await message.answer(profile(_user_id), reply_markup = reply_keyboard(), parse_mode="Markdown")
	await States.menu.set()

@dp.message_handler(text=["🖼 Видео"], state="*")
async def video(message: types.Message, state: FSMContext):
	_user_id = message.chat.id
	_balance = db.get_balance(_user_id)
	if (int(_balance) >= video_cost):
		_dir = f"{os.getcwd()}/videos"
		list_videos = os.listdir(_dir)
		random_video = random.choice(list(list_videos))
		with open(f"videos/{random_video}", 'rb') as video:
			await bot.send_video(chat_id = message.chat.id, video = video, reply_markup = reply_keyboard())
		db.set_balance(_user_id, int(_balance) - video_cost)
	else:
		await message.answer(f"""*Недостаточно средств!*

Пополните баланс или пригласите друзей по ссылке:
*t.me/{link}?start={_user_id}*
"""
, reply_markup = reply_keyboard(), parse_mode="Markdown")
	await States.menu.set()

@dp.message_handler(text=["🖼 Фото"], state="*")
async def photo(message: types.Message, state: FSMContext):
	_user_id = message.chat.id
	_balance = db.get_balance(_user_id)
	if (int(_balance) >= photo_cost):
		_dir = f"{os.getcwd()}/photos"
		list_photos = os.listdir(_dir)
		random_photo = random.choice(list(list_photos))
		with open(f"photos/{random_photo}", 'rb') as photo:
			await bot.send_photo(chat_id = message.chat.id, photo = photo, reply_markup = reply_keyboard())
		db.set_balance(_user_id, int(_balance) - photo_cost)
	else:
		await message.answer(f"""*Недостаточно средств!*

Пополните баланс или пригласите друзей по ссылке:
*t.me/{link}?start={_user_id}*
"""
, reply_markup = reply_keyboard(), parse_mode="Markdown")
	await States.menu.set()

@dp.message_handler(commands="admin", state="*")
async def admin_menu(message: types.Message, state: FSMContext):
	if (message.chat.id == admin_id):
		await message.answer(f"""*Меню администратора*

Пользователей всего: {len(db.get_all_users())}
За неделю: {len(db.get_week_users())}
""", parse_mode="Markdown")

#------------------------------

@dp.message_handler(state="*")
async def admin_mail(message: types.Message, state: FSMContext):
	if (message.chat.id == admin_id):
		if (message.text.startswith("/send ")):
			text = message.text.replace("/send ", "")
			users = db.get_all_users()
			a = 0
			for user in users:
				try:
					await bot.send_message(chat_id=user[0], text=text, parse_mode="Markdown")
					a += 1
					time.sleep(0.1)
				except:
					pass
			await bot.send_message(message.chat.id, f"✅ Рассылка успешно завершена\nПолучили {a} пользователей")

#------------------------------

if __name__ == "__main__":
	db.check_db()
	executor.start_polling(dp, skip_updates=True)