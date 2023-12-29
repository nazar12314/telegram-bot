from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, filters
from telegram.ext import ApplicationBuilder, ContextTypes, ChatMemberHandler

import telegram.error
import pandas as pd

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from config import *
from constants import *

import textwrap
import datetime
import pytz
import random

import os

TOKEN = os.getenv('BOTAPIKEY')
MONGO_URI = os.getenv('MONGOURI')


client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
db = client[DB]

user_collection = db[USER_COLLECTION]
deleted_user_collection = db[DELETED_USER_COLLECTION]

df = pd.read_csv(ANNOTATIONS_PATH)
shown_images = {}

zodiac_keyboard = ReplyKeyboardMarkup(
    [
        [KeyboardButton(Buttons.ARIES.value), KeyboardButton(Buttons.TAURUS.value), KeyboardButton(Buttons.GEMINI.value), KeyboardButton(Buttons.CANCER.value)],
        [KeyboardButton(Buttons.LEO.value), KeyboardButton(Buttons.VIRGO.value), KeyboardButton(Buttons.LIBRA.value), KeyboardButton(Buttons.SCORPIO.value)],
        [KeyboardButton(Buttons.SAGITTARIUS.value), KeyboardButton(Buttons.CAPRICORN.value), KeyboardButton(Buttons.AQUARIUS.value), KeyboardButton(Buttons.PISCES.value)],
    ],
    one_time_keyboard=True,
    resize_keyboard=True,
)

eastern_zodiac_keyboard = ReplyKeyboardMarkup(
    [
        [KeyboardButton(Buttons.RAT.value), KeyboardButton(Buttons.BULL.value), KeyboardButton(Buttons.TIGER.value), KeyboardButton(Buttons.RABBIT.value)],
        [KeyboardButton(Buttons.DRAGON.value), KeyboardButton(Buttons.SNAKE.value), KeyboardButton(Buttons.HORSE.value), KeyboardButton(Buttons.GOAT.value)],
        [KeyboardButton(Buttons.MONKEY.value), KeyboardButton(Buttons.ROOSTER.value), KeyboardButton(Buttons.DOG.value), KeyboardButton(Buttons.PIG.value)],
    ],
    one_time_keyboard=True,
    resize_keyboard=True,
)


def main_page_info(user_id):
    text_message = textwrap.dedent(
        """
        Описание принципа
        Развлекательный текст
        """)

    buttons = [
        [KeyboardButton(Buttons.ASTROLOGY.value), KeyboardButton(Buttons.OWN_BOT.value)],
        [KeyboardButton(Buttons.OFFICE.value), KeyboardButton(Buttons.ABOUT.value)],
    ]

    if user_id == ADMIN_ID:
        buttons[0][1] = KeyboardButton(Buttons.ADMIN.value)

    keyboard = ReplyKeyboardMarkup(
        buttons,
        one_time_keyboard=True,
        resize_keyboard=True,
    )

    return text_message, keyboard


def generate_horoscope(zodiac, user_id):
    available_images = [image for image in df[df['title'] == zodiac]['image'] if image not in shown_images.get(user_id, [])]

    if available_images:
        chosen_image = random.choice(available_images)
        shown_images.setdefault(user_id, []).append(chosen_image)

        return chosen_image


def update_horoscope_image(user_id, get_image=False):
    user = user_collection.find_one({"user_id": user_id})

    horoscope_image = generate_horoscope(user["zodiac_sign"], user_id)

    if horoscope_image:
        user_collection.update_one({'user_id': user_id}, {'$set': {'horoscope_image': horoscope_image}}, upsert=True)

    if get_image and horoscope_image:
        return horoscope_image


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.job_queue.start()
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    logo_path = "horoscopes/horoscope.jpeg"
    # context.job_queue.run_daily(send_periodic_horoscope, datetime.time(hour=8, tzinfo=pytz.timezone('Europe/Kiev')),  chat_id=chat_id)

    context.job_queue.run_repeating(send_periodic_horoscope, interval=30, chat_id=chat_id)

    deleted_user = deleted_user_collection.find_one({"user_id": user_id})

    if deleted_user:
        user = deleted_user_collection.find_one_and_delete({"user_id": user_id})

        user_collection.insert_one(user)

    existing_user = user_collection.find_one({"user_id": user_id})

    if not existing_user:
        user_data = {
            "first_name": update.message.from_user.first_name,
            "last_name": update.message.from_user.last_name,
            "user_id": user_id,
            "username": update.message.from_user.username,
            "phone_number": update.message.contact.phone_number if update.message.contact else None
        }

        user_collection.insert_one(user_data)
    else:
        text_message, keyboard = main_page_info(user_id)

        await update.message.reply_text(text_message, reply_markup=keyboard)

        return States.MAIN_PAGE.value

    await update.message.reply_photo(photo=logo_path)

    text_message = textwrap.dedent(
        """
        Приветственное сообщение
        Короткая информация
        Выберете свой знак зодиака
        """)

    await update.message.reply_text(text_message, reply_markup=zodiac_keyboard)

    return States.ZODIAC_SIGN.value


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    context.user_data.clear()
    await context.job_queue.stop()

    user = user_collection.find_one_and_delete({"user_id": user_id})

    deleted_user_collection.insert_one(user)
    
    await update.message.reply_text("Возвращайтесь!", reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


async def save_zodiac_sign(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chosen_sign = update.message.text
    user_id = update.message.from_user.id

    user_collection.update_one({'user_id': user_id}, {'$set': {'zodiac_sign': chosen_sign}}, upsert=True)

    await update.message.reply_text(f"Ваш знак зодиака: {chosen_sign}")

    await update.message.reply_text("Выберите восточный знак зодиака", reply_markup=eastern_zodiac_keyboard)

    return States.EAST_ZODIAC_SIGN.value


async def save_east_zodiac_sign(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chosen_sign = update.message.text
    user_id = update.message.from_user.id

    user_collection.update_one({'user_id': user_id}, {'$set': {'east_zodiac_sign': chosen_sign}}, upsert=True)

    text_message, keyboard = main_page_info(update.message.from_user.id)
    await update.message.reply_text(text_message, reply_markup=keyboard)

    update_horoscope_image(user_id)

    return States.MAIN_PAGE.value


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text_message = textwrap.dedent(
        """
        Текст о проекте
        Контакты
        Ссылка на бота обратной связи
        """)

    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton(Buttons.BACK.value)]
        ],
        one_time_keyboard=True,
        resize_keyboard=True,
    )

    await update.message.reply_text(text_message, reply_markup=keyboard)

    return States.ABOUT.value


async def office(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    existing_user = user_collection.find_one({"user_id": user_id})
    zodiac_sign = existing_user["zodiac_sign"]
    east_zodiac_sign = existing_user["east_zodiac_sign"]

    text_message = textwrap.dedent(
        f"""
        Описание раздела + текущий статус
        Знак зодиака: {zodiac_sign}
        Восточный знак зодиака: {east_zodiac_sign}
        Дизайн личности
        """)

    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton(Buttons.CHANGE_ZODIAC_SIGN.value), KeyboardButton(Buttons.CHANGE_EAST_ZODIAC.value)],
            [KeyboardButton(Buttons.PERSON_DESIGN.value), KeyboardButton(Buttons.MAIN_PAGE_BACK.value)],
        ],
        one_time_keyboard=True,
        resize_keyboard=True,
    )

    await update.message.reply_text(text_message, reply_markup=keyboard)

    return States.OFFICE.value


async def astrology(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    existing_user = user_collection.find_one({"user_id": user_id})
    zodiac_sign = existing_user["zodiac_sign"]
    east_zodiac_sign = existing_user["east_zodiac_sign"]

    text_message = textwrap.dedent(
        f"""
        Описание раздела + текущий статус
        Знак зодиака: {zodiac_sign}
        Восточный знак зодиака: {east_zodiac_sign}
        Дизайн личности
        """)

    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton(Buttons.HOROSCOPE.value), KeyboardButton(Buttons.EAST_HOROSCOPE.value)],
            [KeyboardButton(Buttons.PERSON_DESIGN.value), KeyboardButton(Buttons.MAIN_PAGE_BACK.value)],
        ],
        one_time_keyboard=True,
        resize_keyboard=True,
    )

    await update.message.reply_text(text_message, reply_markup=keyboard)

    return States.ASTROLOGY.value


async def main_page(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text_message, keyboard = main_page_info(update.message.from_user.id)
    await update.message.reply_text(text_message, reply_markup=keyboard)

    return States.MAIN_PAGE.value


async def personal_design(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text_message = textwrap.dedent(
        f"""
        Упс...
        Раздел на стадии разработки
        """)

    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton(Buttons.BACK.value), KeyboardButton(Buttons.MAIN_PAGE_BACK.value)],
        ],
        one_time_keyboard=True,
        resize_keyboard=True,
    )

    await update.message.reply_text(text_message, reply_markup=keyboard)

    return States.PERSONAL_DESIGN.value


async def change_zodiac_sign(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    existing_user = user_collection.find_one({"user_id": user_id})
    zodiac_sign = existing_user["zodiac_sign"]

    text_message = textwrap.dedent(
        f"""
        Для смены знака зодиака
        Выберите один из списка ниже.
        Текущий знак: {zodiac_sign}
        """)

    await update.message.reply_text(text_message, reply_markup=zodiac_keyboard)

    return States.CHANGE_ZODIAC_SIGN.value


async def change_zodiac_sign_success(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chosen_sign = update.message.text
    user_id = update.message.from_user.id

    user_collection.update_one({'user_id': user_id}, {'$set': {'zodiac_sign': chosen_sign}}, upsert=True)
    update_horoscope_image(user_id)

    text_message = textwrap.dedent(
        f"""
        Ваш знак успешно сменен!

        Текущий знак: {chosen_sign}
        """)

    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton(Buttons.CHANGE_ZODIAC_SIGN.value), KeyboardButton(Buttons.OFFICE.value)],
        ],
        one_time_keyboard=True,
        resize_keyboard=True,
    )

    await update.message.reply_text(text_message, reply_markup=keyboard)

    return States.ZODIAC_CHANGED.value


async def change_east_zodiac_sign(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    existing_user = user_collection.find_one({"user_id": user_id})
    east_zodiac_sign = existing_user["east_zodiac_sign"]

    text_message = textwrap.dedent(
        f"""
        Для смены восточного знака зодиака
        Выберите один из списка ниже.
        Текущий знак: {east_zodiac_sign}
        """)

    await update.message.reply_text(text_message, reply_markup=eastern_zodiac_keyboard)

    return States.CHANGE_EAST_ZODIAC_SIGN.value


async def change_east_zodiac_sign_success(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chosen_sign = update.message.text
    user_id = update.message.from_user.id
    user_collection.update_one({'user_id': user_id}, {'$set': {'east_zodiac_sign': chosen_sign}}, upsert=True)

    text_message = textwrap.dedent(
        f"""
        Ваш знак успешно сменен!

        Текущий знак: {chosen_sign}
        """)

    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton(Buttons.CHANGE_EAST_ZODIAC.value), KeyboardButton(Buttons.OFFICE.value)],
        ],
        one_time_keyboard=True,
        resize_keyboard=True,
    )

    await update.message.reply_text(text_message, reply_markup=keyboard)

    return States.EAST_ZODIAC_CHANGED.value


async def send_periodic_horoscope(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    
    horoscope_image = update_horoscope_image(chat_id, get_image=True)
    
    try:
        if horoscope_image:
            await context.bot.send_photo(chat_id, photo=open(horoscope_image, 'rb'), caption=f'Гороскоп на сегодня \u2191')
        else:
            context.bot.send_message(chat_id, "Гороскопов больше нет!")
    except telegram.error.Forbidden as e:
        print("Blocked by the user!")

        await context.job_queue.stop()


async def horoscope(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chosen_sign = update.message.text
    user_id = update.message.from_user.id

    if chosen_sign in ZODIAC_SIGNS:
        user_collection.update_one({'user_id': user_id}, {'$set': {'zodiac_sign': chosen_sign}}, upsert=True)
        update_horoscope_image(user_id)

    user = user_collection.find_one({"user_id": user_id})

    await update.message.reply_photo(user["horoscope_image"])

    text_message = textwrap.dedent(
        f"""
        Текущий знак: {user["zodiac_sign"]}
        """)

    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton(Buttons.HOROSCOPE_FOR_TODAY.value), KeyboardButton(Buttons.HOROSCOPE_FOR_MONTH.value)],
            [KeyboardButton(Buttons.CHANGE_ZODIAC_SIGN.value), KeyboardButton(Buttons.ASTROLOGY.value)],
        ],
        one_time_keyboard=True,
        resize_keyboard=True,
    )

    await update.message.reply_text(text_message, reply_markup=keyboard)

    return States.HOROSCOPE.value


async def change_zodiac_sign_astrology(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    existing_user = user_collection.find_one({"user_id": user_id})
    zodiac_sign = existing_user["zodiac_sign"]

    text_message = textwrap.dedent(
        f"""
        Для смены знака зодиака
        Выберите один из списка ниже.
        Текущий знак: {zodiac_sign}
        """)

    await update.message.reply_text(text_message, reply_markup=zodiac_keyboard)

    return States.CHANGE_ZODIAC_SIGN_ASTROLOGY.value


async def change_east_sign_astrology(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    existing_user = user_collection.find_one({"user_id": user_id})
    east_zodiac_sign = existing_user["east_zodiac_sign"]

    text_message = textwrap.dedent(
        f"""
        Для смены восточного знака зодиака
        Выберите один из списка ниже.
        Текущий знак: {east_zodiac_sign}
        """)

    await update.message.reply_text(text_message, reply_markup=eastern_zodiac_keyboard)

    return States.CHANGE_EAST_ZODIAC_SIGN_ASTROLOGY.value


async def today_horoscope(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text_message = textwrap.dedent(
        f"""
        Гороскоп на сегодня \u2191
        """)

    user_id = update.message.from_user.id
    user = user_collection.find_one({"user_id": user_id})

    await update.message.reply_photo(user["horoscope_image"])

    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton(Buttons.HOROSCOPE_FOR_TODAY.value), KeyboardButton(Buttons.HOROSCOPE_FOR_MONTH.value)],
            [KeyboardButton(Buttons.CHANGE_ZODIAC_SIGN.value), KeyboardButton(Buttons.ASTROLOGY.value)],
        ],
        one_time_keyboard=True,
        resize_keyboard=True,
    )

    await update.message.reply_text(text_message, reply_markup=keyboard)

    return States.HOROSCOPE.value


async def month_horoscope(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text_message = textwrap.dedent(
        f"""
        Гороскоп на месяц \u2191
        """)

    user_id = update.message.from_user.id
    user = user_collection.find_one({"user_id": user_id})

    await update.message.reply_photo(user["horoscope_image"])

    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton(Buttons.HOROSCOPE_FOR_TODAY.value), KeyboardButton(Buttons.HOROSCOPE_FOR_MONTH.value)],
            [KeyboardButton(Buttons.CHANGE_ZODIAC_SIGN.value), KeyboardButton(Buttons.ASTROLOGY.value)],
        ],
        one_time_keyboard=True,
        resize_keyboard=True,
    )

    await update.message.reply_text(text_message, reply_markup=keyboard)

    return States.HOROSCOPE.value


async def year_east_horoscope(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text_message = textwrap.dedent(
        f"""
        Восточный гороскоп на год

        Картинка с гороскопом
        """)

    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton(Buttons.HOROSCOPE_FOR_MONTH.value), KeyboardButton(Buttons.HOROSCOPE_FOR_YEAR.value)],
            [KeyboardButton(Buttons.CHANGE_EAST_ZODIAC.value), KeyboardButton(Buttons.ASTROLOGY.value)],
        ],
        one_time_keyboard=True,
        resize_keyboard=True,
    )

    await update.message.reply_text(text_message, reply_markup=keyboard)

    return States.EAST_HOROSCOPE.value


async def month_east_horoscope(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text_message = textwrap.dedent(
        f"""
        Восточный гороскоп на месяц:

        Картинка с гороскопом
        """)

    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton(Buttons.HOROSCOPE_FOR_MONTH.value), KeyboardButton(Buttons.HOROSCOPE_FOR_YEAR.value)],
            [KeyboardButton(Buttons.CHANGE_EAST_ZODIAC.value), KeyboardButton(Buttons.ASTROLOGY.value)],
        ],
        one_time_keyboard=True,
        resize_keyboard=True,
    )

    await update.message.reply_text(text_message, reply_markup=keyboard)

    return States.EAST_HOROSCOPE.value


async def east_horoscope(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chosen_sign = update.message.text
    user_id = update.message.from_user.id

    if chosen_sign in EASTERN_ZODIAC_SIGNS:
        user_collection.update_one({'user_id': user_id}, {'$set': {'east_zodiac_sign': chosen_sign}}, upsert=True)

    user = user_collection.find_one({"user_id": user_id})

    text_message = textwrap.dedent(
        f"""
        Текущий знак: {user["east_zodiac_sign"]}
        """)

    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton(Buttons.HOROSCOPE_FOR_MONTH.value), KeyboardButton(Buttons.HOROSCOPE_FOR_YEAR.value)],
            [KeyboardButton(Buttons.CHANGE_EAST_ZODIAC.value), KeyboardButton(Buttons.ASTROLOGY.value)],
        ],
        one_time_keyboard=True,
        resize_keyboard=True,
    )

    await update.message.reply_text(text_message, reply_markup=keyboard)

    return States.EAST_HOROSCOPE.value


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text_message = textwrap.dedent(
        f"""
        Админ панель
        """)

    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton(Buttons.PRESENT_USERS.value), KeyboardButton(Buttons.LEFT_USERS.value)],
            [KeyboardButton(Buttons.ADVERT.value), KeyboardButton(Buttons.MAIN_PAGE_BACK.value)],
        ],
        one_time_keyboard=True,
        resize_keyboard=True,
    )

    await update.message.reply_text(text_message, reply_markup=keyboard)

    return States.ADMIN_PANEL.value


async def get_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_count = user_collection.count_documents({})

    text_message = textwrap.dedent(
        f"""
        Количество пользователей: {user_count}
        """)

    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton(Buttons.BACK.value)],
        ],
        one_time_keyboard=True,
        resize_keyboard=True,
    )

    await update.message.reply_text(text_message, reply_markup=keyboard)

    return States.ADMIN_PANEL.value


async def get_left_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_count = deleted_user_collection.count_documents({})

    text_message = textwrap.dedent(
        f"""
        Количество отписанных пользователей: {user_count}
        """)

    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton(Buttons.BACK.value)],
        ],
        one_time_keyboard=True,
        resize_keyboard=True,
    )

    await update.message.reply_text(text_message, reply_markup=keyboard)

    return States.ADMIN_PANEL.value


async def set_advert_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text_message = textwrap.dedent(
        f"""
        Впишите текст для объявления
        """)

    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton(Buttons.BACK.value), KeyboardButton(Buttons.CONTINUE.value)],
        ],
        one_time_keyboard=True,
        resize_keyboard=True,
    )

    await update.message.reply_text(text_message, reply_markup=keyboard)

    return States.ADVERT_TEXT.value


async def set_advert_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text != Buttons.CONTINUE:
        context.user_data["advert_text"] = update.message.text

    text_message = textwrap.dedent(
        f"""
        Приложите картинку для объявления
        """)

    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton(Buttons.BACK.value), KeyboardButton(Buttons.CONTINUE.value)],
        ],
        one_time_keyboard=True,
        resize_keyboard=True,
    )

    await update.message.reply_text(text_message, reply_markup=keyboard)

    return States.ADVERT_TEXT.value


async def send_advert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # if update.message.text != Buttons.CONTINUE:
    #     context.user_data[" = update.message.text

    # users = user_collection.find({})
    # States.ADVERT.value
    pass


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            States.ZODIAC_SIGN.value: [MessageHandler(filters.Regex('|'.join(ZODIAC_SIGNS)), save_zodiac_sign)],
            States.EAST_ZODIAC_SIGN.value: [MessageHandler(filters.Regex('|'.join(EASTERN_ZODIAC_SIGNS)), save_east_zodiac_sign)],
            States.MAIN_PAGE.value: [
                MessageHandler(filters.Text(Buttons.ABOUT.value), about),
                MessageHandler(filters.Text(Buttons.OWN_BOT.value), about),
                MessageHandler(filters.Text(Buttons.OFFICE.value), office),
                MessageHandler(filters.Text(Buttons.ASTROLOGY.value), astrology),
                MessageHandler(filters.Text(Buttons.ADMIN.value) & filters.User(user_id=ADMIN_ID), admin_panel),
                CommandHandler('start', start)
            ],
            States.OFFICE.value: [
                MessageHandler(filters.Text(Buttons.PERSON_DESIGN.value), personal_design),
                MessageHandler(filters.Text(Buttons.CHANGE_ZODIAC_SIGN.value), change_zodiac_sign),
                MessageHandler(filters.Text(Buttons.CHANGE_EAST_ZODIAC.value), change_east_zodiac_sign),
                MessageHandler(filters.Text(Buttons.MAIN_PAGE_BACK.value), main_page),
                CommandHandler('start', start)
            ],
            States.ABOUT.value: [
                MessageHandler(filters.Text(Buttons.BACK.value), main_page),
                CommandHandler('start', start)
            ],
            States.PERSONAL_DESIGN.value: [
                MessageHandler(filters.Text(Buttons.BACK.value), office),
                MessageHandler(filters.Text(Buttons.MAIN_PAGE_BACK.value), main_page),
                CommandHandler('start', start)
            ],
            States.CHANGE_ZODIAC_SIGN.value: [
                MessageHandler(filters.Regex('|'.join(ZODIAC_SIGNS)), change_zodiac_sign_success),
                CommandHandler('start', start)
            ],
            States.ZODIAC_CHANGED.value: [
                MessageHandler(filters.Text(Buttons.CHANGE_ZODIAC_SIGN.value), change_zodiac_sign),
                MessageHandler(filters.Text(Buttons.OFFICE.value), office),
                CommandHandler('start', start)
            ],
            States.CHANGE_EAST_ZODIAC_SIGN.value: [
                MessageHandler(filters.Regex('|'.join(EASTERN_ZODIAC_SIGNS)), change_east_zodiac_sign_success),
                CommandHandler('start', start)
            ],
            States.EAST_ZODIAC_CHANGED.value: [
                MessageHandler(filters.Text(Buttons.CHANGE_EAST_ZODIAC.value), change_east_zodiac_sign),
                MessageHandler(filters.Text(Buttons.OFFICE.value), office),
                CommandHandler('start', start)
            ],
            States.ASTROLOGY.value: [
                MessageHandler(filters.Text(Buttons.PERSON_DESIGN.value), personal_design),
                MessageHandler(filters.Text(Buttons.HOROSCOPE.value), horoscope),
                MessageHandler(filters.Text(Buttons.EAST_HOROSCOPE.value), east_horoscope),
                MessageHandler(filters.Text(Buttons.MAIN_PAGE_BACK.value), main_page),
                CommandHandler('start', start)
            ],
            States.HOROSCOPE.value: [
                MessageHandler(filters.Text(Buttons.HOROSCOPE_FOR_TODAY.value), today_horoscope),
                MessageHandler(filters.Text(Buttons.HOROSCOPE_FOR_MONTH.value), month_horoscope),
                MessageHandler(filters.Text(Buttons.CHANGE_ZODIAC_SIGN.value), change_zodiac_sign_astrology),
                MessageHandler(filters.Text(Buttons.ASTROLOGY.value), astrology),
                CommandHandler('start', start)
            ],
            States.CHANGE_ZODIAC_SIGN_ASTROLOGY.value: [
                MessageHandler(filters.Regex('|'.join(ZODIAC_SIGNS)), horoscope),
                CommandHandler('start', start)
            ],
            States.EAST_HOROSCOPE.value: [
                MessageHandler(filters.Text(Buttons.HOROSCOPE_FOR_MONTH.value), month_east_horoscope),
                MessageHandler(filters.Text(Buttons.HOROSCOPE_FOR_YEAR.value), year_east_horoscope),
                MessageHandler(filters.Text(Buttons.CHANGE_EAST_ZODIAC.value), change_east_sign_astrology),
                MessageHandler(filters.Text(Buttons.ASTROLOGY.value), astrology),
                CommandHandler('start', start)
            ],
            States.CHANGE_EAST_ZODIAC_SIGN_ASTROLOGY.value: [
                MessageHandler(filters.Regex('|'.join(EASTERN_ZODIAC_SIGNS)), east_horoscope),
                CommandHandler('start', start)
            ],
            States.ADMIN_PANEL.value: [
                MessageHandler(filters.Text(Buttons.MAIN_PAGE_BACK.value), main_page),
                MessageHandler(filters.Text(Buttons.ADVERT.value), set_advert_text),
                MessageHandler(filters.Text(Buttons.PRESENT_USERS.value), get_users),
                MessageHandler(filters.Text(Buttons.LEFT_USERS.value), get_left_users),
                MessageHandler(filters.Text(Buttons.BACK.value), admin_panel),
                CommandHandler('start', start)
            ], 
            # States.ADVERT_TEXT.value: [
            #     MessageHandler(filters.Text(~Buttons.BACK.value), set_advert_image),
            #     MessageHandler(filters.Text(Buttons.BACK.value), admin_panel),
            #     CommandHandler('start', start)
            # ],
            # States.ADVERT_IMAGE.value: [
            #     MessageHandler(filters.Text(~Buttons.BACK.value), send_advert),
            #     MessageHandler(filters.Text(Buttons.BACK.value), set_advert_text),
            #     CommandHandler('start', start)
            # ]
        },
        fallbacks=[],
    )

    app.add_handler(conversation_handler)

    app.add_handler(CommandHandler("stop", stop))

    app.run_polling()


if __name__ == "__main__":
    main()
