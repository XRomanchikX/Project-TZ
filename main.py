import logging
import gspread
import asyncio
from google.oauth2.service_account import Credentials
from aiogram import executor
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import buttons
import os

API_TOKEN = '5751694717:AAEkmL0Os01qZgbqCJ_K8i7USDMXUgfQe5g'

logging.basicConfig(level=logging.INFO)

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
    worksheet = sheet.get_worksheet(0)
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
@dp.message_handler(text="Найти🔍")
async def command(message: types.Message):
    worksheet = sheet.get_worksheet(0)
    id = message.from_user.id
    
    inline_btn1 = InlineKeyboardButton('<< Назад', callback_data='btn1')
    inline_btn2 = InlineKeyboardButton('Вперёд >>', callback_data='btn2')

    inline_kb = InlineKeyboardMarkup(row_width=2)
    inline_kb.add(inline_btn1, inline_btn2)
    fio = worksheet.acell(f'A{buttons.user}').value
    tel = worksheet.acell(f'B{buttons.user}').value
    message = (f"Результат поиска🔍:\n\nФИО: {fio}\nТелефон: +{tel}")
    
    

    await bot.send_message(int(id), message, reply_markup=inline_kb)
    asyncio.sleep(0.5)
    lat = worksheet.acell(f'C{buttons.user}').value
    lon = worksheet.acell(f'D{buttons.user}').value
    location_message = await bot.send_location(id,float(lat),float(lon))
    buttons.location_message_id = location_message.message_id
@dp.callback_query_handler(lambda callback_query: callback_query.data == "btn2")
async def command(callback_query: types.CallbackQuery, state: FSMContext):
    worksheet = sheet.get_worksheet(0)
    chat_id = callback_query.from_user.id

    buttons.user = buttons.user + 1
    inline_btn1 = InlineKeyboardButton('<< Назад', callback_data='btn1')
    inline_btn2 = InlineKeyboardButton('Вперёд >>', callback_data='btn2')

    inline_kb = InlineKeyboardMarkup(row_width=2)
    inline_kb.add(inline_btn1, inline_btn2)
    fio = worksheet.acell(f'A{buttons.user}').value
    tel = worksheet.acell(f'B{buttons.user}').value
    
    if fio != None and tel != None:
        if buttons.location_message_id:
            await bot.delete_message(chat_id, buttons.location_message_id)
        message = f"Результат поиска🔍:\n\nФИО: {fio}\nТелефон: +{tel}"
        await callback_query.message.edit_text(message, reply_markup=inline_kb)
        lat = worksheet.acell(f'C{buttons.user}').value
        lon = worksheet.acell(f'D{buttons.user}').value

        location_message = await bot.send_location(chat_id,float(lat),float(lon))
        buttons.location_message_id = location_message.message_id
        #await bot.send_message(chat_id, message, reply_markup=inline_kb)
    if fio == None or tel == None:
        inline_btn1 = InlineKeyboardButton('<< Назад', callback_data='btn1')
        inline_kb = InlineKeyboardMarkup(row_width=1)
        inline_kb.add(inline_btn1)

        message = f"Результат поиска🔍:\n\nФИО: {fio}\nТелефон: +{tel}"
        await callback_query.message.edit_text('Это был последний пользователь в списке', reply_markup=inline_kb)
        #await bot.send_message(chat_id, 'Это был последний пользователь в списке', reply_markup=inline_kb)
@dp.callback_query_handler(lambda callback_query: callback_query.data == "btn1")
async def command(callback_query: types.CallbackQuery, state: FSMContext):
    worksheet = sheet.get_worksheet(0)
    chat_id = callback_query.from_user.id

    # buttons.user = buttons.user - 1
    if buttons.user >= 3:
        if buttons.location_message_id:
            await bot.delete_message(chat_id, buttons.location_message_id)
        buttons.user = buttons.user - 1
        inline_btn1 = InlineKeyboardButton('<< Назад', callback_data='btn1')
        inline_btn2 = InlineKeyboardButton('Вперёд >>', callback_data='btn2')

        inline_kb = InlineKeyboardMarkup(row_width=2)
        inline_kb.add(inline_btn1, inline_btn2)
        fio = worksheet.acell(f'A{buttons.user}').value
        tel = worksheet.acell(f'B{buttons.user}').value
        message = f"Результат поиска🔍:\n\nФИО: {fio}\nТелефон: +{tel}"

        await callback_query.message.edit_text(message, reply_markup=inline_kb)
        lat = worksheet.acell(f'C{buttons.user}').value
        lon = worksheet.acell(f'D{buttons.user}').value
        location_message = await bot.send_location(chat_id,float(lat),float(lon))
        buttons.location_message_id = location_message.message_id
       # await bot.send_message(chat_id, message, reply_markup=inline_kb)
   
    if buttons.user < 2:
        
        inline_btn2 = InlineKeyboardButton('Вперёд >>', callback_data='btn2')

        inline_kb = InlineKeyboardMarkup(row_width=1)
        inline_kb.add(inline_btn2)
        await callback_query.message.edit_text('Это был первый пользователь в списке', reply_markup=inline_kb)
        #await bot.send_message(chat_id, 'Это был первый пользователь в списке', reply_markup=inline_kb)


@dp.message_handler(text="/send_post")
async def command(message: types.Message):
    worksheet = sheet.get_worksheet(0)
    id = message.from_user.id
    if id == 1028676957 or id == 925098584 or id == 5225100069:
        await message.reply('Отправьте изображение')
        await States.waiting_for_post_photo.set()
@dp.message_handler(content_types=types.ContentType.PHOTO ,state=States.waiting_for_post_photo)
async def command(message: types.Message, state: FSMContext):
    photo_id = message.photo[0].file_id
    buttons.photo_post_id = photo_id
    buttons.post_photo_id = photo_id
    # Отправляем пользователю сообщение об успешном сохранении фотографии
    await message.reply('Теперь нужно отправить текст')
    await States.waiting_for_post_text.set()
@dp.message_handler(state=States.waiting_for_post_text)
async def command(message: types.Message, state: FSMContext):
    text = message.text
    buttons.post_text_id = text
    await message.answer('Текст сохранен. /check_post')
    await state.finish()

@dp.message_handler(text='/ahelp')
async def command(message: types.Message, state: FSMContext):
    worksheet = sheet.get_worksheet(0)
    id = message.from_user.id
    if id == 1028676957 or id == 925098584 or id == 5225100069:
        await message.reply('commands:\n/send_post\n/check_post\n/history')

@dp.message_handler(text='/check_post')
async def command(message: types.Message):
    worksheet = sheet.get_worksheet(0)
    id = message.from_user.id
    if id == 1028676957 or id == 925098584 or id == 5225100069:
        textp = buttons.post_text_id
        photop = buttons.post_photo_id
        if textp != None and photop != None:
            await bot.send_photo(message.chat.id, photop, caption=f'{textp}\n\n___________________________\nЗапускать рассылку?(да/нет)')
        else:
            await message.reply('Рассылка не выбрана!')
@dp.message_handler(text='да')
async def command(message: types.Message):
    print(buttons.post_text_id)
    print(buttons.post_photo_id)
    worksheet = sheet.get_worksheet(0)
    id = message.from_user.id
    if id == 1028676957 or id == 925098584 or id == 5225100069:
        if buttons.post_photo_id != None and buttons.post_text_id != None:
            text_post1 = buttons.post_text_id
            text_post2 = buttons.post_photo_id
            worksheet = sheet.get_worksheet(1)
            next_row = next_available_row(worksheet)
            worksheet.update_acell("A{}".format(next_row), f'{text_post1}')
            worksheet.update_acell("B{}".format(next_row), f'{text_post2}')
            worksheet = sheet.get_worksheet(0)
            while True:
                print(1)
                us_id = worksheet.acell(f'G{buttons.sender+1}').value
                textp = buttons.post_text_id
                photop = buttons.post_photo_id
                buttons.sender = buttons.sender + 1
                try:
                    if id != None:
                        await bot.send_photo(us_id,photop, caption=f'{textp}')
                except:
                    buttons.sender = 1
                    break     
        else:
            if buttons.post_photo_id == None and buttons.post_text_id == None:
                await message.reply('Не сделано сообщение для рассылки!')
@dp.message_handler(text='нет')
async def command(message: types.Message):
    id = message.from_user.id
    if id == 1028676957 or id == 925098584 or id == 5225100069:
        await message.reply('Отправьте изображение')
        await States.waiting_for_post_photo.set()

@dp.message_handler(text="/history")
async def command(message: types.Message):
    id = message.from_user.id
    if id == 1028676957 or id == 925098584 or id == 5225100069:
        inline_btn1 = InlineKeyboardButton('<< Назад', callback_data='btn3')
        inline_btn2 = InlineKeyboardButton('Вперёд >>', callback_data='btn4')
        inline_btn3 = InlineKeyboardButton('<< Повторить >>', callback_data='btn5')
        inline_kb = InlineKeyboardMarkup(row_width=3)
        inline_kb.add(inline_btn1, inline_btn3, inline_btn2)
        worksheet = sheet.get_worksheet(1)
        fio = worksheet.acell(f'A{buttons.history}').value
        tel = worksheet.acell(f'B{buttons.history}').value
        photo_message = await bot.send_photo(id, tel, caption=f'{buttons.history-1}\n{fio}',reply_markup=inline_kb)
        buttons.photo_message_id = photo_message.message_id
        buttons.post_photo_id = tel
        buttons.post_text_id = fio
@dp.callback_query_handler(lambda callback_query: callback_query.data == "btn4")
async def command(callback_query: types.CallbackQuery, state: FSMContext):
    id = callback_query.from_user.id
    worksheet = sheet.get_worksheet(1)
    buttons.history = buttons.history + 1
    inline_btn1 = InlineKeyboardButton('<< Назад', callback_data='btn3')
    inline_btn2 = InlineKeyboardButton('Вперёд >>', callback_data='btn4')
    inline_btn3 = InlineKeyboardButton('<< Повторить >>', callback_data='btn5')
    inline_kb = InlineKeyboardMarkup(row_width=3)
    inline_kb.add(inline_btn1, inline_btn3, inline_btn2)
    fio = worksheet.acell(f'A{buttons.history}').value
    tel = worksheet.acell(f'B{buttons.history}').value
    if fio != None and tel != None:
        if buttons.photo_message_id:
            await bot.delete_message(id, buttons.photo_message_id)
        photo_message = await bot.send_photo(id, tel, caption=f'{buttons.history-1}\n{fio}',reply_markup=inline_kb)
        buttons.photo_message_id = photo_message.message_id
        buttons.post_photo_id = tel
        buttons.post_text_id = fio
    if fio == None or tel == None:
        inline_btn1 = InlineKeyboardButton('<< Назад', callback_data='btn3')
        inline_kb = InlineKeyboardMarkup(row_width=1)
        inline_kb.add(inline_btn1)
        await callback_query.message.reply('Это был последний пост в списке', reply_markup=inline_kb)
@dp.callback_query_handler(lambda callback_query: callback_query.data == "btn3")
async def command(callback_query: types.CallbackQuery, state: FSMContext):
    id = callback_query.from_user.id
    worksheet = sheet.get_worksheet(1)
    if buttons.history >= 3:
        if buttons.photo_message_id:
            await bot.delete_message(id, buttons.photo_message_id)
        buttons.history = buttons.history - 1
        fio = worksheet.acell(f'A{buttons.history}').value
        tel = worksheet.acell(f'B{buttons.history}').value
        inline_btn1 = InlineKeyboardButton('<< Назад', callback_data='btn3')
        inline_btn2 = InlineKeyboardButton('Вперёд >>', callback_data='btn4')
        inline_btn3 = InlineKeyboardButton('<< Повторить >>', callback_data='btn5')
        inline_kb = InlineKeyboardMarkup(row_width=3)
        inline_kb.add(inline_btn1, inline_btn3, inline_btn2)
        photo_message = await bot.send_photo(id, tel, caption=f'{buttons.history-1}\n{fio}',reply_markup=inline_kb)
        buttons.post_photo_id = tel
        buttons.post_text_id = fio
        buttons.photo_message_id = photo_message.message_id
    if buttons.history < 2:
        inline_btn2 = InlineKeyboardButton('Вперёд >>', callback_data='btn4')
        inline_kb = InlineKeyboardMarkup(row_width=1)
        inline_kb.add(inline_btn2)
        await callback_query.message.reply('Это был первый пост в списке', reply_markup=inline_kb)
@dp.callback_query_handler(lambda callback_query: callback_query.data == "btn5")
async def command(callback_query: types.CallbackQuery, state: FSMContext):
    id = callback_query.from_user.id
    worksheet = sheet.get_worksheet(0)
    if id == 1028676957 or id == 925098584 or id == 5225100069:
        await bot.send_photo(id, buttons.post_photo_id, caption=f'{buttons.post_text_id}\n\n___________________________\nЗапускать рассылку?(да/нет)')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
