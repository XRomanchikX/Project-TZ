from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
photo_post_id = 0
user = 2
admin_id = 1028676957
sender = 1

button1 = KeyboardButton('Найти')
button2 = KeyboardButton('Выгрузка')
button3 = KeyboardButton('Поделиться Контактом📞', request_contact=True)
button4 = KeyboardButton('Поделиться Геолокацией🌍', request_location=True)

buttonUser = ReplyKeyboardMarkup(resize_keyboard=True).row(button1, button2)

buttonCon = ReplyKeyboardMarkup(resize_keyboard=True).add(button3)
buttonGeo = ReplyKeyboardMarkup(resize_keyboard=True).add(button4)

def read_text_from_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

