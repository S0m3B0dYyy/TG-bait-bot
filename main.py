import sqlite3
import string
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

bot = Bot(token=token)

dp = Dispatcher(bot, storage=MemoryStorage())

class States(StatesGroup):
	menu = State()
	pay = State()
	pay_sum = State()

#------------------------------

def profile(user_id):
	_data = db.get_info(user_id)
	return f"""*Привет*, *{_data[2]}*!

👤 *Ваш ID:* {_data[1]}
📅 *Дата регистрации:* {_data[3]}
💵 *Баланс:* {_data[5]}

🔥 *Вывод от 100₽*
*Зарабатывай по {db.get_settings()[5]}₽ за каждого приглашенного друга!*

👤 *Приглашено:* {db.get_refs(user_id)}
*t.me/{link}?start={user_id}*

*Администратор:* {admin_link} 
"""

def reply_keyboard():
	keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
	keyboard.add(KeyboardButton('🖼 Видео'), KeyboardButton('🖼 Фото'))
	keyboard.add(KeyboardButton('💼 Профиль'))
	keyboard.add(KeyboardButton('💵 Пополнить баланс'))
	return keyboard

def just_back():
	keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
	keyboard.add(KeyboardButton('↪️ Назад'))
	return keyboard

def inline_keyboard(pay_sum, comment, code):
	link = f"https://qiwi.com/payment/form/{code}?extra%5B%27account%27%5D={db.get_settings()[1]}&amountInteger={pay_sum}&amountFraction=0&extra%5B%27comment%27%5D={comment}&currency=643&blocked%5B0%5D=sum&blocked%5B1%5D=comment&blocked%5B2%5D=account"
	keyboard = InlineKeyboardMarkup()
	keyboard.add(InlineKeyboardButton(text="💵 Оплатить", url=link))
	return keyboard

def random_order():
	return f"{random.randint(44,77)}{random.choice(string.ascii_letters)}{random.choice(string.ascii_letters)}{random.randint(371,984)}{random.choice(string.ascii_letters)}{random.randint(11,24)}"

#------------------------------

# Меню
@dp.message_handler(text=["💼 Профиль", "↪️ Назад"], state="*")
@dp.message_handler(commands=["start"], state="*")
async def menu(message: types.Message, state: FSMContext):
	_user_id = message.chat.id
	_username = message.chat.username
	if not (db.get_users_exist(message.chat.id)):
		if (message.text != "💼 Профиль" and message.text.startswith("/start ")):
			_ref = message.text.replace("/start ", "")
			if (int(message.chat.id) != int(_ref)):
				db.add_user_to_db(message.chat.id, message.chat.username, _ref, db.get_settings()[4])
				db.set_balance(_ref, db.get_balance(_ref) + db.get_settings()[5])
				await bot.send_message(chat_id = admin_id, text = f"Новый пользователь: {_user_id} (@{_username})\nПригласил: {_ref}")
				await bot.send_message(chat_id=_ref, text=f"*Кто-то перешел по твоей ссылке!*\nБаланс пополнен на {db.get_settings()[5]}", parse_mode='Markdown')
			else:
				db.add_user_to_db(message.chat.id, message.chat.username, 0, db.get_settings()[4])
				await bot.send_message(chat_id = admin_id, text = f"Новый пользователь: {_user_id} (@{_username})")
		else:
			db.add_user_to_db(message.chat.id, message.chat.username, 0, db.get_settings()[4])
			await bot.send_message(chat_id = admin_id, text = f"Новый пользователь: {_user_id} (@{_username})")
	db.update_nickname(_user_id, _username)
	await message.answer(profile(_user_id), reply_markup = reply_keyboard(), parse_mode="Markdown")
	await States.menu.set()

@dp.message_handler(text=["💵 Пополнить баланс"], state=States.menu)
async def menu(message: types.Message, state: FSMContext):
	_user_id = message.chat.id
	_username = message.chat.username
	await message.answer(f"💵 *Введите сумму пополнения*", reply_markup = just_back(), parse_mode="Markdown")
	await States.pay.set()

@dp.message_handler(state=States.pay)
async def menu(message: types.Message, state: FSMContext):
	if (message.text.isdigit()):
		if (int(message.text) >= 10 and int(message.text) <= 500):
			_code = 99 if db.get_settings()[1].isdigit() else 99999
			_user_id = message.chat.id
			_username = message.chat.username
			_random = random_order()
			await message.answer(f"""
*📈 Пополнение ID{_random}*

*Для оплаты перейдите по кнопке ниже*
""", 
reply_markup = inline_keyboard(message.text, _random, _code), parse_mode="Markdown")
			await States.pay_sum.set()
			await States.menu.set()
		else:
			await message.answer(f"*Введите сумму от 10₽ до 500₽*", reply_markup = just_back(), parse_mode="Markdown")
	else:
		await message.answer(f"*Введите сумму числом*", reply_markup = just_back(), parse_mode="Markdown")

@dp.message_handler(text=["🖼 Видео"], state="*")
async def video(message: types.Message, state: FSMContext):
	_user_id = message.chat.id
	_balance = db.get_balance(_user_id)
	if (int(_balance) >= db.get_settings()[2]):
		db.set_balance(_user_id, int(_balance) - db.get_settings()[2])
		_dir = f"{os.getcwd()}/videos"
		list_videos = os.listdir(_dir)
		random_video = random.choice(list(list_videos))
		with open(f"videos/{random_video}", 'rb') as video:
			await bot.send_video(chat_id = message.chat.id, video = video, reply_markup = reply_keyboard())
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
	if (int(_balance) >= db.get_settings()[3]):
		db.set_balance(_user_id, int(_balance) - db.get_settings()[3])
		_dir = f"{os.getcwd()}/photos"
		list_photos = os.listdir(_dir)
		random_photo = random.choice(list(list_photos))
		with open(f"photos/{random_photo}", 'rb') as photo:
			await bot.send_photo(chat_id = message.chat.id, photo = photo, reply_markup = reply_keyboard())
	else:
		await message.answer(f"""*Недостаточно средств!*

Пополните баланс или пригласите друзей по ссылке:
*t.me/{link}?start={_user_id}*
"""
, reply_markup = reply_keyboard(), parse_mode="Markdown")
	await States.menu.set()

#------------------------------

@dp.message_handler(commands="admin", state="*")
async def admin_menu(message: types.Message, state: FSMContext):
	if (message.chat.id == admin_id):
		_settings = db.get_settings()
		await message.answer(f"""💼 *Меню администратора*

👥 Пользователей всего: {len(db.get_all_users())}
👤 За неделю: {len(db.get_week_users())}

📝 *Настройки*

Qiwi - {_settings[1]}
Цена видео - {_settings[2]}
Цена фото - {_settings[3]}
Начальный баланс - {_settings[4]}
Бонус рефки - {_settings[5]}

*/info* - Список команд админа
""", parse_mode="Markdown")

@dp.message_handler(commands=["qiwi", "video", "photo", "stbal", "bonus"], state="*")
async def admin_menu(message: types.Message, state: FSMContext):
	if (message.chat.id == admin_id):
		if (message.text.count(" ") > 0):
			_data = message.text.split(" ")
			_command = _data[0][1:]
			_value = _data[1]
			if (_value.isdigit() or _command == "qiwi"):
				db.update_settings(_command, _value)
				await message.answer(f"✅ Значение {_command} изменено на {_value}", parse_mode="Markdown")
			else:
				await bot.send_message(message.chat.id, f"Неверный формат команды")
		else:
			await bot.send_message(message.chat.id, f"Неверный формат команды")


@dp.message_handler(commands="info", state="*")
async def admin_menu(message: types.Message, state: FSMContext):
	if (message.chat.id == admin_id):
		await message.answer(f'''💼 *Команды админа*

*/info* - Список команд админа
*/send тест* - Рассылка
*/pay ID 123* - Пополнение по ID

📝 *Изменение настроек*

*/qiwi 89876543210* - номер Qiwi
*/video 123* - стоимость видео
*/photo 123* - стоимость фото
*/stbal 123* - начальный баланс
*/bonus 123* - бонус за приглашение
''', parse_mode="Markdown")

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
		if (message.text.startswith("/pay ")):
			_data = message.text.split(" ")
			if (len(_data) > 2):
				_ID = _data[1]
				_sum = _data[2]
				if (_ID.isdigit() and (_sum.isdigit()) or _sum.replace("-", "").isdigit()):
					if (db.get_users_exist(_ID)):
						db.set_balance(_ID, db.get_balance(_ID) + int(_sum))
						_info = db.get_info(_ID)
						await bot.send_message(message.chat.id, f"✅ Баланс {_ID} (@{_info[2]}) пополнен на {_sum}")
					else:
						await bot.send_message(message.chat.id, f"❌ Пользователь не найден")
				else:
					await bot.send_message(message.chat.id, f"Неверный формат команды")
			else:
				await bot.send_message(message.chat.id, f"Неверный формат команды")

#------------------------------

if __name__ == "__main__":
	db.check_db()
	executor.start_polling(dp, skip_updates=True)
