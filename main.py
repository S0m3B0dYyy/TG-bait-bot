import sqlite3
import string
import os, time, random, configparser
from aiogram import Bot, types
from aiogram.utils import executor
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import db

config = configparser.ConfigParser()
config.read("settings.ini")
token = config["bot"]["token"]
admin_id = int(config["bot"]["admin_id"])
admin_link = config["bot"]["admin_link"]
link = config["bot"]["link"]

bot = Bot(token=token)

dp = Dispatcher(bot, storage=MemoryStorage())

class States(StatesGroup):
	menu = State()
	pay = State()
	pay_sum = State()
	admin_mail = State()
	admin_mail_accept = State()

#------------------------------

def profile(user_id):
	_data = db.get_info(user_id)
	return f"""<b>Привет, {_data[2]}!</b>

👤 <b>Ваш ID:</b> {_data[1]}
📅 <b>Дата регистрации:</b> {_data[3]}
💵 <b>Баланс:</b> {_data[5]}

🔥 <b>Вывод от 100₽
Зарабатывай по {db.get_settings()[5]}₽ за каждого приглашенного друга!</b>

👤 <b>Приглашено:</b> {db.get_refs(user_id)}
<b>t.me/{link}?start={user_id}</b>

<b>Администратор:</b> {admin_link} 
"""

def get_user_info(user_id):
	_data = db.get_info(user_id)
	_pre_ref = db.get_pre_ref(user_id)
	_pre_ref_str = f"""{_pre_ref} (@{db.get_info(_pre_ref)[2]})""" if int(_pre_ref) != 0 else "Нет"
	return f"""INFO *@{_data[2]}*

👤 *ID:* {_data[1]}
📅 *Дата регистрации:* {_data[3]}
💵 *Баланс:* {_data[5]}

👤 *Реферал:* {_pre_ref_str}

👤 *Приглашено:* {db.get_refs(user_id)}
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

@dp.message_handler(content_types=types.ContentTypes.PHOTO, state=States.menu)
async def admin_add_photo(message: types.Message, state: FSMContext):
	file_id = message.photo[-1].file_id
	if (message.chat.id == admin_id):
		db_photo_id = db.add_file(file_id, 'photo', message.chat.id)
		await States.menu.set()
		await message.answer(f"Фото {db_photo_id} добавлено")
	else:
		await bot.send_message(admin_id, f"Новое фото от {message.chat.id}")
		await bot.send_photo(admin_id, file_id)
		await message.answer("Готово! Как только модераторы проверят ваше фото, вы получите бонус")

@dp.message_handler(content_types=types.ContentTypes.VIDEO, state=States.menu)
async def admin_add_video(message: types.Message, state: FSMContext):
	file_id = message.video.file_id
	if (message.chat.id == admin_id):
		db_video_id = db.add_file(file_id, 'video', message.chat.id)
		await States.menu.set()
		await message.answer(f"Видео {db_video_id} добавлено")
	else:
		await bot.send_message(admin_id, f"Новое видео от {message.chat.id}")
		await bot.send_video(admin_id, file_id)
		await message.answer("Готово! Как только модераторы проверят ваше видео, вы получите бонус")

@dp.message_handler(commands="del", state="*")
async def admin_get_file(message: types.Message, state: FSMContext):
	if (message.chat.id == admin_id):
		if message.text.startswith("/del "):
			file_id = message.text.replace("/del ", "")
			db.delete_file(file_id)
			await States.menu.set()
			await message.answer(f"Файл {file_id} удален")

@dp.message_handler(commands="get", state="*")
async def admin_get_file(message: types.Message, state: FSMContext):
	if (message.chat.id == admin_id):
		if (message.text.startswith("/get ")):
			file_id = message.text.replace("/get ", "")
			file = db.get_file(file_id)
			if (file[2] == 'photo'):
				await bot.send_photo(message.chat.id, file[1])
			elif (file[2] == 'video'):
				await bot.send_video(message.chat.id, file[1])

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
	await message.answer(profile(_user_id), reply_markup = reply_keyboard(), parse_mode="HTML")
	await States.menu.set()

@dp.message_handler(text=["✅ Загрузить"], state="*")
async def menu(message: types.Message, state: FSMContext):
	await message.answer(f"""Отправьте мне фото или видео. Как только они пройдут администратор их одобрит, вы получите бонус
Разрешено загружать только ЦП, изнасилования, инцест""")

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
		random_video = random.choice(db.get_all_files('video'))
		await bot.send_video(chat_id = message.chat.id, video = random_video[1], reply_markup = reply_keyboard())
	else:
		await message.answer(f"""<b>Недостаточно средств!</b>

Пополните баланс или пригласите друзей по ссылке:
<b>t.me/{link}?start={_user_id}</b>
"""
, reply_markup = reply_keyboard(), parse_mode="HTML")
	await States.menu.set()

@dp.message_handler(text=["🖼 Фото"], state="*")
async def photo(message: types.Message, state: FSMContext):
	_user_id = message.chat.id
	_balance = db.get_balance(_user_id)
	if (int(_balance) >= db.get_settings()[3]):
		db.set_balance(_user_id, int(_balance) - db.get_settings()[3])
		random_photo = random.choice(db.get_all_files('photo'))
		await bot.send_photo(chat_id = message.chat.id, photo = random_photo[1], reply_markup = reply_keyboard())
	else:
		await message.answer(f"""<b>Недостаточно средств!</b>

Пополните баланс или пригласите друзей по ссылке:
<b>t.me/{link}?start={_user_id}</b>
"""
, reply_markup = reply_keyboard(), parse_mode="HTML")
	await States.menu.set()

#------------------------------

@dp.message_handler(commands="admin", state="*")
async def admin_menu(message: types.Message, state: FSMContext):
	if (message.chat.id == admin_id):
		keyboard = InlineKeyboardMarkup()
		keyboard.add(InlineKeyboardButton(text="📬 Рассылка", callback_data=f"admin_mail"))
		_settings = db.get_settings()
		await message.answer(f"""💼 *Меню администратора*

👥 Пользователей всего: {len(db.get_all_users())}
👤 За неделю: {len(db.get_old_users(7))}
👤 За день: {len(db.get_old_users(1))}

🖼 Видео: {len(db.get_all_files('video'))}
🖼 Фото: {len(db.get_all_files('photo'))}

📝 *Настройки*

Qiwi - {_settings[1]}
Цена видео - {_settings[2]}
Цена фото - {_settings[3]}
Начальный баланс - {_settings[4]}
Бонус рефки - {_settings[5]}

*/help* - Список команд админа
""", parse_mode="Markdown", reply_markup=keyboard)

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


@dp.message_handler(commands="help", state="*")
async def admin_help(message: types.Message, state: FSMContext):
	if (message.chat.id == admin_id):
		await message.answer(f'''💼 *Команды админа*

*/help* - Список команд админа
*/send тест* - Рассылка
*/top* - Рейтинг пользователей
*/pay 123 999* - Пополнение пользователю с ID 123 на 999
*/pay all 100* - Пополнение всем
*/info 123* - Информация о пользователе с ID 123

*/get 123* - Получить файл с ID 123
*/del 123* - Удалить файл с ID 123
*/dump* - Получить все файлы

*Чтобы загрузить новые файлы, отправьте их боту по одному*

📝 *Изменение настроек*

*/qiwi 89876543210* - номер Qiwi
*/video 123* - стоимость видео
*/photo 123* - стоимость фото
*/stbal 123* - начальный баланс
*/bonus 123* - бонус за приглашение
''', parse_mode="Markdown")

#------------------------------

@dp.message_handler(commands="dump", state="*")
async def admin_get_all_files(message: types.Message, state: FSMContext):
	if (message.chat.id == admin_id):
		if message.text.startswith("/dump "):
			_type = message.text.replace("/dump ", "")
			files = db.get_all_files(_type)
		else: files = db.get_all_files()
		for file in files:
			if file[2] == 'photo':
				await bot.send_photo(message.chat.id, file[1], f"{file[2]} {file[0]}\nАвтор: {file[3]}")
			elif file[2] == 'video':
				await bot.send_video(message.chat.id, file[1], f"{file[2]} {file[0]}\nАвтор: {file[3]}")

@dp.callback_query_handler(state=States.admin_mail_accept)
async def admin_mail(call: types.CallbackQuery, state: FSMContext):
	if (call.data == "admin_back_2"):
		for i in range(4):
			await bot.delete_message(call.from_user.id, call.message.message_id - i)
		await States.menu.set()
		await bot.send_message(call.from_user.id, "Отменено")
	elif (call.from_user.id == admin_id):
		if (call.data == "admin_mail_accept"):
			_data = await state.get_data()
			text = _data['text']
			_type = _data['type']
			photo = _data['photo']
			users = db.get_all_users()
			a = 0
			for user in users:
				try:
					if (_type == 'text_only'):
						await bot.send_message(user[0], text, parse_mode="HTML")
					elif (_type == 'photo'):
						await bot.send_photo(user[0], photo, text, parse_mode="HTML")
					a += 1
					time.sleep(0.1)
				except:
					pass
			for i in range(4):
				await bot.delete_message(call.from_user.id, call.message.message_id - i)
			await States.menu.set()
			await bot.send_message(call.from_user.id, f"✅ Рассылка успешно завершена\nПолучили {a} пользователей")

@dp.callback_query_handler(state="*")
async def admin_calls(call: types.CallbackQuery, state: FSMContext):
	if (call.from_user.id == admin_id):
		if (call.data == "admin_back"):
			await bot.delete_message(call.from_user.id, call.message.message_id)
			await States.menu.set()
			await bot.send_message(call.from_user.id, "Отменено")
		elif (call.data == "admin_mail"):
			keyboard = InlineKeyboardMarkup()
			keyboard.add(InlineKeyboardButton(text="❌ Назад", callback_data=f"admin_back"))
			await bot.send_message(call.from_user.id, "Введите текст рассылки: ", reply_markup=keyboard)
			await States.admin_mail.set()
		await call.answer()

@dp.message_handler(state=States.admin_mail)
async def admin_mail(message: types.Message, state: FSMContext):
	if (message.chat.id == admin_id):
		try:
			text = message.text
			keyboard = InlineKeyboardMarkup()
			keyboard.add(InlineKeyboardButton(text="✅ Начать", callback_data=f"admin_mail_accept"))
			keyboard.add(InlineKeyboardButton(text="❌ Назад", callback_data=f"admin_back_2"))
			await state.update_data(text=text)
			await state.update_data(photo=-1)
			await States.admin_mail_accept.set()
			await bot.send_message(message.chat.id, text, parse_mode="HTML")
			await bot.send_message(message.chat.id, f"Начать рассылку для {len(db.get_all_users())} пользователей?", reply_markup=keyboard)
			await state.update_data(type='text_only')
		except:
			await bot.send_message(message.chat.id, f"❌ Неверный текст")

@dp.message_handler(content_types=types.ContentTypes.PHOTO, state=States.admin_mail)
async def admin_mail_photo(message: types.Message, state: FSMContext):
	if (message.chat.id == admin_id):
		try:
			text = message.caption
			keyboard = InlineKeyboardMarkup()
			keyboard.add(InlineKeyboardButton(text="✅ Начать", callback_data=f"admin_mail_accept"))
			keyboard.add(InlineKeyboardButton(text="❌ Назад", callback_data=f"admin_back_2"))
			await state.update_data(text=text)
			await state.update_data(photo=message.photo[-1].file_id)
			await States.admin_mail_accept.set()
			await bot.send_photo(message.chat.id, message.photo[-1].file_id, text, parse_mode="HTML")
			await bot.send_message(message.chat.id, f"Начать рассылку для {len(db.get_all_users())} пользователей?", reply_markup=keyboard)
			await state.update_data(type='photo')
		except:
			await bot.send_message(message.chat.id, f"❌ Неверный текст")

@dp.message_handler(commands="info", state="*")
async def admin_info(message: types.Message, state: FSMContext):
	if (message.chat.id == admin_id):
		_ID = message.text.replace("/info ", "")
		_data = db.get_info(_ID)
		if not (_ID.isdigit()):
			await bot.send_message(message.chat.id, f"Неверный формат команды")
		elif (_data == None):
			await bot.send_message(message.chat.id, f"❌ Пользователь не найден")
		else:
			await message.answer(get_user_info(_ID), reply_markup = reply_keyboard(), parse_mode="Markdown")

@dp.message_handler(commands="top", state="*")
async def admin_top(message: types.Message, state: FSMContext):
	if (message.chat.id == admin_id):
		_text = "<b>💵 Топ по балансу</b>"
		for i in db.get_top_balance(5):
			_text = _text + f"\n{i[5]} | {i[1]} (@{i[2]})"
		_text = _text + "\n\n"
		_text = _text + "<b>👥 Топ по рефералам</b>"
		top_refs = db.get_top_ref(5)
		if top_refs:
			for i in top_refs:
				_temp_name = db.get_info(i[2])[2]
				_text = _text + f"\n{i[0]} | {i[2]} (@{_temp_name})"
		else:
			_text = _text + f"\nНикто никого не пригласил"
		await message.answer(_text, reply_markup=reply_keyboard(), parse_mode="HTML")

@dp.message_handler(commands="pay", state="*")
async def admin_pay(message: types.Message, state: FSMContext):		
	if (message.chat.id == admin_id):
		_data = message.text.split(" ")
		if (len(_data) > 2):
			_ID = _data[1]
			_sum = _data[2]
			if (_sum.isdigit()) or _sum.replace("-", "").isdigit():
				if (_ID.isdigit()):
					if (db.get_users_exist(_ID)):
						db.set_balance(_ID, db.get_balance(_ID) + int(_sum))
						_info = db.get_info(_ID)
						await bot.send_message(message.chat.id, f"✅ Баланс {_ID} (@{_info[2]}) пополнен на {_sum}")
						await bot.send_message(_ID, f"Ваш баланс пополнен на {_sum}")
					else:
						await bot.send_message(message.chat.id, f"❌ Пользователь не найден")
				elif (_ID == "all"):
					users = db.get_all_users()
					a = 0
					for user in users:
						try:
							db.set_balance(user[0], int(db.get_balance(user[0])) + int(_sum))
							await bot.send_message(user[0], f"Ваш баланс пополнен на {_sum}")
							a += 1
						except:
							pass
					await bot.send_message(message.chat.id, f"✅ Баланс {a} пользователей пополнен на {_sum}")
				else:
					await bot.send_message(message.chat.id, f"Неверный формат команды")
			else:
				await bot.send_message(message.chat.id, f"Неверный формат команды")
		else:
			await bot.send_message(message.chat.id, f"Неверный формат команды")

#------------------------------

if __name__ == "__main__":
	db.check_db()
	executor.start_polling(dp)
