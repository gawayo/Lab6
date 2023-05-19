import logging
import os
import psycopg2 as pg
import re

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext

from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    BotCommand, BotCommandScopeDefault,BotCommandScopeChat

conn=pg.connect (user='postgres', password='postgres', host='localhost', port='8888', database='lab6')
cursor=conn.cursor()

bot_token=os.getenv('TELEGRAM_BOT_TOKEN')
bot = Bot(token=bot_token)
dp=Dispatcher(bot, storage=MemoryStorage())

button_save = KeyboardButton('/save_currency')
button_delete = KeyboardButton('/delete_currency')
button_edit = KeyboardButton('/edit_currency')

buttons = ReplyKeyboardMarkup().add(button_save,button_delete, button_edit)
class Form(StatesGroup):
    name = State()
    delete_name = State()
    edit_name = State()
    edit_name1 = State()
    rate = State()
    check = State()
    num = State()
    delete = State()
    save_namer = State()
    save_rater = State()


currencies=[]
f_name=[]

#4.	Реализовать меню команд:
user_commands = [
    BotCommand(command='/start', description='start'),
    BotCommand(command='/convert', description='Конвертировать'),
    BotCommand(command='/get_currency', description='Показать валюты')
]

admin_commands = [
    BotCommand(command='/start', description='start'),
    BotCommand(command='/manage_currency', description='Менеджер валют'),
    BotCommand(command='/convert', description='Конвертировать'),
    BotCommand(command='/get_currency', description='Показать валюты'),
    BotCommand(command='/save_currency', description='Добавить валюту'),
    BotCommand(command='/edit_currency', description='Редактировать валюту'),
]

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    # Установка пользовательских команд бота с помощью метода set_my_commands и передача списка user_commands.
    await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())
    await message.reply("Привет! Я бот для подсчёта валюты.")

def check_id():
    df = cursor.execute("""Select chat_id from admins""")
    Admin_id = cursor.fetchall()
    Admin_id = re.sub(r"[^0-9]", r"", str(Admin_id))
    admins_list = []
    if Admin_id in admins_list:
        return (admins_list)
    else:
        admins_list.append(Admin_id)
        return (admins_list)

#a)	при нажатии на кнопку "Добавить валюту"
@dp.message_handler(commands=['manage_currency'])
async def manage_command(message: types.Message):
    # Получение id пользователей из чата и преобразование их в строку
    admin = str(message.chat.id)
    # Вызов функции check_id() для проверки наличия id в базе данных
    admin_id = check_id()
    if admin in admin_id:
        await bot.set_my_commands(admin_commands,scope=BotCommandScopeDefault(chat_id=admin))
        await message.reply("Вы админ",reply_markup=buttons)
    else:
        # Если id отсутствует в базе данных, установка обычных команд
        await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())
        await message.reply("Нет доступа к команде")

#бот выводит сообщение: "Введите курс к рублю";
@dp.message_handler(commands=['save_currency'])
async def save_command(message: types.Message):
    admin_id = check_id()
    admin = str(message.chat.id)
    if admin in admin_id:
        await message.reply("Введите название валюты")
        await Form.save_namer.set()
    else:
        await message.reply("Нет доступа к команде")

#бот выводит сообщение: "Введите курс к рублю";
@dp.message_handler(state=Form.save_namer)
async def process_save_name(message: types.Message, state: FSMContext):
    name = message.text
    # `%s` является маркером параметра, который будет заменен значением `currency_name`
    curr = cursor.execute("""Select currence_name from currencies where currence_name=%s""",(name,))
    curr = cursor.fetchall()
    if curr == []:
        currencies.append(name)
        await message.reply("Введите курс валюты")
        await Form.save_rater.set()
    else:
        await message.reply("Данная валюта уже существует")


#бот сохраняет курс в таблицу currencies
def save_currencies(currencies):
    cursor.execute(""" Insert into currencies (currence_name, rate) 
        values (%s,%s);""",currencies)
    conn.commit()
    currencies.clear()
@dp.message_handler(state=Form.save_rater)
async def process_save_rate(message: types.Message, state: FSMContext):
    rate =message.text
    currencies.append(rate)
    save_currencies(currencies)
    await message.reply("Сохранено")
    await state.finish()

# b)	при нажатии на кнопку "Удалить валюту":
@dp.message_handler(commands=['delete_currency'])
async def delete_command(message: types.Message):
    admin_id = check_id()
    admin = str(message.chat.id)
    if admin in admin_id:
        await Form.delete_name.set()
        await message.reply("Введите название валюты")
    else:
        await message.reply("Нет доступа к команде")

@dp.message_handler(state=Form.delete_name)
async def delete_name(message: types.Message, state: FSMContext):
    name = message.text
    cursor.execute("""delete from currencies where currence_name=%s""", (name,))
    conn.commit()
    await message.reply('Удалено')
    await state.finish()
#c)	при нажатии на кнопку "Изменить курс валюты":
@dp.message_handler(commands=['edit_currency'])
async def edit_command(message: types.Message):
    admin_id = check_id()
    admin = str(message.chat.id)
    if admin in admin_id:
        await Form.edit_name.set()
        await message.reply("Введите название валюты")
    else:
        await message.reply("Нет доступа к команде")
@dp.message_handler(state=Form.edit_name)
async def process_edit(message: types.Message, state: FSMContext):
    name = message.text
    f_name.append(name)
    await Form.edit_name1.set()
    await message.reply('Введите курс к рублю')

@dp.message_handler(state=Form.edit_name1)
async def process_rate1(message: types.Message, state: FSMContext):
    currency_rate = message.text
    cursor.execute("""UPDATE currencies SET rate=%s WHERE currence_name=%s""", (currency_rate,f_name[0],))
    conn.commit()
    await message.reply('Сохранено')
    f_name.clear()
    await state.finish()
#2.	Реализовать команду /get_currencies, которая выводит все сохраненные валюты с курсом к рублю
@dp.message_handler(commands=['get_currency'])
async def convert_command(message: types.Message):
    curr = cursor.execute("""Select currence_name, rate from currencies""")
    curr = cursor.fetchall()
    await message.reply(curr)

#3.	Реализовать команду /convert, которая конвертирует заданную сумму в валюте в сумму в рублях
@dp.message_handler(commands=['convert'])
async def convert_command(message: types.Message):
    await Form.check.set()
    await message.reply("Введите название валюты")
@dp.message_handler(state=Form.check)
async def process_check(message: types.Message, state: FSMContext):
    await state.update_data(cheack_rate=message.text)
    name = message.text
    curr = cursor.execute("""Select rate from currencies where lower (currence_name)=lower (%s)""", (name,))
    curr = str(cursor.fetchall())
    curr = re.sub(r"[^0-9,]",r"",curr)
    curr = float(re.sub(r"[,]", r".", curr))
    f_name.append(curr)
    await Form.num.set()
    await message.reply("Введите сумму перевода")
@dp.message_handler(state=Form.num)
async def process_convert(message: types.Message, state: FSMContext):
    num = message.text
    result = float(f_name[0]) * float(num)
    await message.reply(result)
    f_name.clear()
    await state.finish()

if __name__ =='__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
