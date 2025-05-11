from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup
import requests
import sys
import requests
import random
import sqlite3


from cities import european_capitals, russian_big_cities, russian_small_cities


async def start(update, context):
    reply_keyboard = [['Ура']]
    await update.message.reply_text('Начало бота',
                                    reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return 0

async def stop(update, context):
    await update.message.reply_text("Спасибо за игру")
    return ConversationHandler.END

async def menu(update, context):
    con = sqlite3.connect("db\stats")
    cur = con.cursor()
    result1 = cur.execute(f"""SELECT * from stats WHERE username = \"{update.message.chat.username}\"""").fetchall()
    if not result1:
        cur.execute(f"""INSERT INTO stats(username) VALUES(\"{update.message.chat.username}\")""").fetchall()
    con.commit()
    con.close()
    reply_keyboard = [['Играть'], ["Посмотреть мои баллы"], ["Настройки сложности"]]
    await update.message.reply_text('Главное меню',
                                    reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return 4


async def fourth_response(update, context):
    global mode
    if update.message.text == 'Играть':
        reply_keyboard = [['Все города'], ["Столицы Европы"], ["Большие города России"], ["Маленькие города России"]]
        await update.message.reply_text('Выберите режим', reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return 1
    if update.message.text == 'Посмотреть мои баллы':
        con = sqlite3.connect("db\stats")
        cur = con.cursor()
        result = cur.execute(
            f"""SELECT points from stats WHERE username = \"{update.message.chat.username}\"""").fetchall()
        con.close()
        await update.message.reply_text(f'Вот ваши баллы: {result[0][0]}')
        await menu(update, context)
        return 4
    if update.message.text == 'Настройки сложности':
        reply_keyboard = [['1 (2 варианта ответа)'], ["2 (3 варианта ответа)"], ["3 (4 варианта ответа)"], ["4 (6 вариантов ответа)"], ["5 (8 вариантов ответа)"]]
        con = sqlite3.connect("db\stats")
        cur = con.cursor()
        result = cur.execute(
            f"""SELECT difficulty from stats WHERE username = \"{update.message.chat.username}\"""").fetchall()
        con.close()
        await update.message.reply_text(f'Выберите новую сложность, ваша сложность - {result[0][0]}', reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return 5

async def fifth_response(update, context):
    diff = int(update.message.text[0])
    con = sqlite3.connect("db\stats")
    cur = con.cursor()
    result = cur.execute(
        f"""UPDATE stats
            SET difficulty = {diff}
            WHERE username = \"{update.message.chat.username}\"""").fetchall()
    con.commit()
    con.close()
    await update.message.reply_text(f'Вам поставлена сложность {diff}')
    await menu(update, context)
    return 4

async def first_response(update, context):
    global mode
    if update.message.text == 'Все города':
        mode = 1
        await cities_command(update, context)
    if update.message.text == 'Столицы Европы':
        mode = 2
        await cities_command(update, context)
    if update.message.text == 'Россия':
        mode = 3
        await cities_command(update, context)
    if update.message.text == 'Маленькие города России':
        mode = 4
        await cities_command(update, context)
    if update.message.text == 'Большие города России':
        mode = 5
        await cities_command(update, context)

    return 2

async def second_response(update, context):
    global mode
    reply_keyboard = [['Играть дальше'], ['Конец игры'], ['В меню']]
    con = sqlite3.connect("db\stats")
    cur = con.cursor()
    result1 = cur.execute(
        f"""SELECT difficulty from stats WHERE username = \"{update.message.chat.username}\"""").fetchall()
    result2 = cur.execute(
        f"""SELECT points from stats WHERE username = \"{update.message.chat.username}\"""").fetchall()
    diff = result1[0][0]
    points = result2[0][0]
    mode_c = {1: 3,
              2: 2,
              3: 2.5,
              4: 2.5,
              5: 2}
    diff_c = {1: 0.25,
              2: 0.5625,
              3: 1,
              4: 1.5,
              5: 2}
    if update.message.text == city:
        dp = mode_c[mode] * diff_c[diff] * (0.95 ** points)
        result = cur.execute(
            f"""UPDATE stats
                SET points = {points + dp}
                WHERE username = \"{update.message.chat.username}\"""").fetchall()
        con.commit()
        await update.message.reply_text(f'Вы угадали. Вам было выдано {round(dp, 2)} баллов\nТеперь у вас {round(points + dp, 2)} баллов')
    else:
        dp = 1
        result = cur.execute(
            f"""UPDATE stats
                SET points = {points - dp}
                WHERE username = \"{update.message.chat.username}\"""").fetchall()
        con.commit()
        await update.message.reply_text(f"Вы не угадали. это был город {city}. У вас забрали {round(dp, 2)} баллов.\nТеперь у вас {round(points - dp, 2)} баллов")
    con.close()
    await update.message.reply_text('Что', reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return 3

async def third_response(update, context):
    if update.message.text == 'Играть дальше':
        await cities_command(update, context)
        return 2
    elif update.message.text == 'В меню':
        await menu(update, context)
        return 4
    elif update.message.text == 'Конец игры':
        await stop(update, context)

async def cities_command(update, context):
    global city
    global mode
    if mode == 1:
        cities = russian_big_cities + russian_small_cities + european_capitals
    if mode == 2:
        cities = european_capitals
    if mode == 3:
        cities = russian_big_cities + russian_small_cities
    if mode == 4:
        cities = russian_small_cities
    if mode == 5:
        cities = russian_big_cities
    city = random.choice(cities)

    text = city + random.choice(places)
    number = random.randint(1, 100)
    if number == 17:
        text = "Десантный мотобот"
        city = "Десантный мотобот 🎈"
    search_api_server = "https://search-maps.yandex.ru/v1/"
    api_key = ""
    search_params = {
        "apikey": api_key,
        "text": text,
        "lang": "ru_RU",
        "type": "biz"
    }

    response = requests.get(search_api_server, params=search_params)
    if not response:
        pass
    json_response = response.json()
    organization = json_response["features"][0]
    org_name = organization["properties"]["CompanyMetaData"]["name"]
    org_address = organization["properties"]["CompanyMetaData"]["address"]
    point = organization["geometry"]["coordinates"]
    org_point = f"{point[0]},{point[1]}"
    delta = "0.0017"
    apikey = "f3a0fe3a-b07e-4840-a1da-06f18b2ddf13"

    map_params = {
        "spn": ",".join([delta, delta]),
        "apikey": apikey,
        "pt": "{0},pm2dgl".format(org_point)
    }

    map_api_server = "https://static-maps.yandex.ru/v1"
    response = requests.get(map_api_server, params=map_params)

    con = sqlite3.connect("db\stats")
    cur = con.cursor()
    result = cur.execute(
        f"""SELECT difficulty from stats WHERE username = \"{update.message.chat.username}\"""").fetchall()
    con.close()
    diff = result[0][0]

    if diff == 1:
        reply_keyboard = [[city], [random.choice(cities)]]
    if diff == 2:
        reply_keyboard = [[city], [random.choice(cities)], [random.choice(cities)]]
    if diff == 3:
        reply_keyboard = [[city], [random.choice(cities)], [random.choice(cities)], [random.choice(cities)]]
    if diff == 4:
        reply_keyboard = [[city], [random.choice(cities)], [random.choice(cities)], [random.choice(cities)], [random.choice(cities)], [random.choice(cities)]]
    if diff == 5:
        reply_keyboard = [[city], [random.choice(cities)], [random.choice(cities)], [random.choice(cities)], [random.choice(cities)], [random.choice(cities)], [random.choice(cities)], [random.choice(cities)]]

    random.shuffle(reply_keyboard)
    await context.bot.send_photo(
        update.message.chat_id,
        response.content,
        caption="Угадайте город на карте", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )

places = [
        "Ресторан",  # Заведение для полноценного питания
        "Магазин",  # Общий термин для магазинов различного профиля
        "Больница",  # Учреждение для оказания медицинской помощи
        "Гостиница"
    ]
city = ''
mode = -1
application = Application.builder().token('').build()
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        0: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu)],
        1: [MessageHandler(filters.TEXT & ~filters.COMMAND, first_response)],
        2: [MessageHandler(filters.TEXT & ~filters.COMMAND, second_response)],
        3: [MessageHandler(filters.TEXT & ~filters.COMMAND, third_response)],
        4: [MessageHandler(filters.TEXT & ~filters.COMMAND, fourth_response)],
        5: [MessageHandler(filters.TEXT & ~filters.COMMAND, fifth_response)]
    },

    fallbacks=[CommandHandler('stop', stop)]
)
application.add_handler(conv_handler)
application.run_polling()
