import logging
import gspread
from google.oauth2.service_account import Credentials
from aiogram import executor
import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import ParseMode
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove,ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import buttons

API_TOKEN = '5751694717:AAEkmL0Os01qZgbqCJ_K8i7USDMXUgfQe5g'

# logging.basicConfig(level=logging.INFO)

scope = ['https://www.googleapis.com/auth/spreadsheets']
credentials = Credentials.from_service_account_file('project-403812-4e74a92ff835.json')
client = gspread.authorize(credentials.with_scopes(scope))
sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1U1LeBvf4Z_6vtTz2M9mKY6aeWRT9NUjo-CB8Dhk-rk8/edit?usp=sharing')

worksheet = sheet.get_worksheet(0)

def next_available_row(worksheet):
    str_list = list(filter(None, worksheet.col_values(1)))
    return str(len(str_list)+1)

gc = gspread.authorize(credentials)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

### STATES ###
class States(StatesGroup):
    waiting_for_name = State()         # ФИО
    waiting_for_phone = State()        # телефон
    waiting_for_address = State()      # адреса
    waiting_for_post_text = State()    # рассылка (админ)
    waiting_for_post_photo = State()   # рассылка (админ)
### START ###
@dp.message_handler(commands=['start'])
async def on_start(message: types.Message):
    await bot.send_video(message.chat.id, open('video.mp4', 'rb'),
                         reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Начать", callback_data="start_data_collection")))

### NAME ###
@dp.callback_query_handler(lambda callback_query: callback_query.data == "start_data_collection", state="*")
async def command(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.answer("Давайте начнем сбор данных. Введите свое ФИО:")
    await States.waiting_for_name.set()

### TEL ###
@dp.message_handler(state=States.waiting_for_name)
async def command(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text

    await message.reply("Отлично! Теперь введите свой номер телефона:", reply_markup=buttons.buttonCon)
    await States.waiting_for_phone.set()

### ADRESS ###
@dp.message_handler(content_types=types.ContentType.CONTACT,state=States.waiting_for_phone)
async def command(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        contact_data = message.contact.phone_number
        data['phone'] = contact_data

    await message.reply("Отлично! Теперь введите свой адрес проживания:", reply_markup=buttons.buttonGeo)
    await States.waiting_for_address.set()

### INFO ###
@dp.message_handler(content_types=types.ContentType.LOCATION, state=States.waiting_for_address)
async def command(message: types.Message, state: FSMContext):
    next_row = next_available_row(worksheet)
    latitude = message.location.latitude
    longitude = message.location.longitude
    id = message.from_user.id
    username = message.from_user.full_name
    chat_id = message.chat.id
    async with state.proxy() as data:
        data['id'] = id
        data['chat_id'] = chat_id
        data['username'] = username
        data['latitude'] = latitude
        data['longitude'] = longitude
        user_data = data['name'], data['phone'], data['latitude'],data['longitude'],data['id'],data['username'],data['chat_id']
        await message.reply("Спасибо за предоставленную информацию:\n"
                            f"ФИО: {user_data[0]}\n"
                            f"Номер телефона: {user_data[1]}\n", reply_markup=buttons.buttonUser)
        worksheet.update_acell("A{}".format(next_row), f'{user_data[0]}')
        worksheet.update_acell("B{}".format(next_row), f'{user_data[1]}')
        worksheet.update_acell("C{}".format(next_row), f'{user_data[2]}')
        worksheet.update_acell("D{}".format(next_row), f'{user_data[3]}')
        worksheet.update_acell("E{}".format(next_row), f'{user_data[4]}')
        worksheet.update_acell("F{}".format(next_row), f'{user_data[5]}')
        worksheet.update_acell("G{}".format(next_row), f'{user_data[6]}')

        await state.finish()

### SEARCH ###

@dp.message_handler(text="Найти")
async def command(message: types.Message):
    inline_btn1 = InlineKeyboardButton('<< Назад', callback_data='btn1')
    inline_btn2 = InlineKeyboardButton('Вперёд >>', callback_data='btn2')

    inline_kb = InlineKeyboardMarkup(row_width=2)
    inline_kb.add(inline_btn1, inline_btn2)
    fio = worksheet.acell(f'A{buttons.user}').value
    tel = worksheet.acell(f'B{buttons.user}').value
    message = f"Результат поиска🔍:\n\nФИО: {fio}\nТелефон: +{tel}"
    chat_id = 1028676957  # Замените на ID чата или пользователя, куда отправить

    await bot.send_message(chat_id, message, reply_markup=inline_kb)
@dp.callback_query_handler(lambda callback_query: callback_query.data == "btn2")
async def command(callback_query: types.CallbackQuery, state: FSMContext):
    
    buttons.user = buttons.user + 1
    inline_btn1 = InlineKeyboardButton('<< Назад', callback_data='btn1')
    inline_btn2 = InlineKeyboardButton('Вперёд >>', callback_data='btn2')

    inline_kb = InlineKeyboardMarkup(row_width=2)
    inline_kb.add(inline_btn1, inline_btn2)
    fio = worksheet.acell(f'A{buttons.user}').value
    tel = worksheet.acell(f'B{buttons.user}').value

    if fio != None and tel != None:
        message = f"Результат поиска🔍:\n\nФИО: {fio}\nТелефон: +{tel}"
        chat_id = 1028676957  # Замените на ID чата или пользователя, куда отправить
        await bot.send_message(chat_id, message, reply_markup=inline_kb)
    if fio == None or tel == None:
        inline_btn1 = InlineKeyboardButton('<< Назад', callback_data='btn1')
        inline_kb = InlineKeyboardMarkup(row_width=1)
        inline_kb.add(inline_btn1)

        message = f"Результат поиска🔍:\n\nФИО: {fio}\nТелефон: +{tel}"
        chat_id = 1028676957  # Замените на ID чата или пользователя, куда отправить
        await bot.send_message(chat_id, 'Это был последний пользователь в списке', reply_markup=inline_kb)
@dp.callback_query_handler(lambda callback_query: callback_query.data == "btn1")
async def command(callback_query: types.CallbackQuery, state: FSMContext):
    if buttons.user >= 3:
        buttons.user = buttons.user - 1
        inline_btn1 = InlineKeyboardButton('<< Назад', callback_data='btn1')
        inline_btn2 = InlineKeyboardButton('Вперёд >>', callback_data='btn2')

        inline_kb = InlineKeyboardMarkup(row_width=2)
        inline_kb.add(inline_btn1, inline_btn2)
        fio = worksheet.acell(f'A{buttons.user}').value
        tel = worksheet.acell(f'B{buttons.user}').value
        message = f"Результат поиска🔍:\n\nФИО: {fio}\nТелефон: +{tel}"
        chat_id = 1028676957  # Замените на ID чата или пользователя, куда отправить

        await bot.send_message(chat_id, message, reply_markup=inline_kb)
    if buttons.user < 2:
        buttons.user = buttons.user - 1
        inline_btn2 = InlineKeyboardButton('Вперёд >>', callback_data='btn2')

        inline_kb = InlineKeyboardMarkup(row_width=1)
        inline_kb.add(inline_btn2)
        chat_id = 1028676957
        await bot.send_message(chat_id, 'Это был первый пользователь в списке', reply_markup=inline_kb)

### LOCATION ###
@dp.message_handler(text="Выгрузка")
async def command(message: types.Message):
    user_id = message.from_user.id 
    lat = worksheet.acell(f'C{buttons.user}').value
    lon = worksheet.acell(f'D{buttons.user}').value
    await bot.send_location(user_id,float(lat),float(lon))

@dp.message_handler(text="/send_post")
async def command(message: types.Message):
    id = message.from_user.id
    if id == 1028676957 or id == 925098584:
        await message.reply('Отправьте изображение')
        await States.waiting_for_post_photo.set()
@dp.message_handler(content_types=types.ContentType.PHOTO ,state=States.waiting_for_post_photo)
async def command(message: types.Message, state: FSMContext):
    photo_id = message.photo[0].file_id
    buttons.photo_post_id = photo_id
    with open(f'postp.txt', 'w') as text_file:
        text_file.write(photo_id)
    # Отправляем пользователю сообщение об успешном сохранении фотографии
    await message.reply('Теперь нужно отправить текст')
    await States.waiting_for_post_text.set()
@dp.message_handler(state=States.waiting_for_post_text)
async def command(message: types.Message, state: FSMContext):
    text = message.text
    with open(f'postt.txt', 'w') as text_file:
        text_file.write(text)
    await message.answer('Текст сохранен. /check_post')
    await state.finish()

@dp.message_handler(text='ahelp')
async def command(message: types.Message, state: FSMContext):
    id = message.from_user.id
    if id == 1028676957 or id == 925098584:
       await message.reply('commands:\n/send_post\n/check_post')

@dp.message_handler(text='/check_post')
async def command(message: types.Message):
    textp = buttons.read_text_from_file('postt.txt')
    photo = buttons.read_text_from_file('postp.txt')
    await bot.send_photo(message.chat.id, photo, caption=f'{textp}\n\n___________________________\nЗапускать рассылку?(да/нет)')
@dp.message_handler(text='да')
async def command(message: types.Message):
    id = message.from_user.id
    if id == 1028676957 or id == 925098584:


        text_post1 = buttons.read_text_from_file('postt.txt')
        text_post2 = buttons.read_text_from_file('postp.txt')
        worksheet = sheet.get_worksheet(1)
        next_row = next_available_row(worksheet)
        worksheet.update_acell("A{}".format(next_row), f'{text_post1}')
        worksheet.update_acell("B{}".format(next_row), f'{text_post2}')
        worksheet = sheet.get_worksheet(0)


        while True:
            us_id = worksheet.acell(f'G{buttons.sender+1}').value
            textp = buttons.read_text_from_file('postt.txt')
            buttons.sender = buttons.sender + 1
            print(buttons.sender)
            try:
                if id != None:
                    await bot.send_photo(us_id,buttons.photo_post_id, caption=f'{textp}')
            except:
                buttons.sender = 1
                break       
@dp.message_handler(text='нет')
async def command(message: types.Message):
    id = message.from_user.id
    if id == 1028676957 or id == 925098584:
        await message.reply('Отправьте изображение')
        await States.waiting_for_post_photo.set()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)