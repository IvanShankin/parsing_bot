import os
import sqlite3
import datetime as dt
import random

from aiogram import F,Bot, Router # F добавляет обработчик на сообщения от пользователя (он будет принимать всё (картинки, стикеры, контакты))
from aiogram.filters import CommandStart  # CommandStart добавляет команду '/start'   Command добавляет команду которую мы сами можем придумать (ниже есть пример)
from aiogram.types import Message, CallbackQuery
from aiogram import types
from aiogram.exceptions import TelegramBadRequest

from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext # для управления состояниями

import app.keyboards as kb # импортируем клавиатуру и сокращаем её на 'kb'
from app import parser as parser

from crypto_pay_api_sdk import Crypto

from app.config import TOKEN, CRYPTO_TOKEN, SUPPORT_ID, CHANNEL_URL, ARR_ADMIN_ID,CHANNEL_NAME, ROOT_PROJECT_DIR

bot = Bot(token = TOKEN)

crypto = Crypto(CRYPTO_TOKEN,testnet = False)

router = Router() # это почти как диспетчер только для handlers


class Form(StatesGroup): # этот класс хранит в себе ответ пользователя на запрос ввести канал дял парсинга
    waiting_for_answer = State()
    waiting_for_answer_premium = State()
    waiting_for_answer_list_of_available_chats = State()
    captcha = State()
    waiting_for_id_user_for_add = State()
    waiting_days_for_add_premium = State()
    waiting_for_id_user_for_delete = State()
    waiting_for_check_chat = State()

def generate_captcha(user_id):
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    op = random.choice(['+', '-','*'])
    question = f"{a} {op} {b} = ?"
    answer = eval(str(a) + op + str(b)) # Используем eval для вычисления ответа
    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM captcha WHERE user_id = ?", (user_id,))
    result_from_db = cursor.fetchone() # берём первую найденную строку
    if result_from_db:
        cursor.execute(f"UPDATE captcha SET answer = ? WHERE user_id = ?", (int(answer), user_id))
    else:
        cursor.execute(f"INSERT INTO captcha (user_id,answer) VALUES (?, ?)", (user_id,int(answer)))
    connection.commit()  # сохранение
    connection.close()
    return question

async def premium_filter_def(id):
    messages_result = ''
    show_filters = ''
    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM active_filters WHERE user_id = ?", (id,))
    result = cursor.fetchone()  # Извлекает первую найденную строку
    connection.close()
    if result[1] == 1:
        if result[2] == 1:
            show_filters += f'По последнему заходу не менее чем 24 часа\n'
        elif result[2] == 3 or result[2] == 7 or result[2] == 14:
            show_filters += f'По последнему заходу не менее чем {result[2]} дней\n'
        elif result[2] == 30:
            show_filters += f'Заход более чем {result[2]} дней назад\n'
    if result[3] == 1:
        if result[4] == 'man':
            show_filters += f'По мужскому полу'
            if result[8] == 1:
                show_filters += ', а так же по имени которое записано на русском языке\n'
            elif result[9] == 1:
                show_filters += ', а так же по имени которое записано на английском языке\n'
            else:
                show_filters += '\n'
        else:
            show_filters += f'По женскому полу'
            if result[8] == 1:
                show_filters += ', а так же по имени которое записано на русском языке\n'
            elif result[9] == 1:
                show_filters += ', а так же по имени которое записано на английском языке\n'
            else:
                show_filters += '\n'
    if result[5] == 1:
        show_filters += f'По наличию telegram premium\n'
    if result[6] == 1:
        show_filters += f'По наличию фото\n'
    if result[7] == 1:
        show_filters += f'По наличию открытого номера\n'
    messages_result = f'Выберите фильтры по которым будет проходить парсинг\n\nПрименённые фильтры:\n{show_filters}'
    return messages_result

async def coming_in_filter_def(id):
    messages_result =''
    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute(f"SELECT coming_in_filter,coming_in FROM active_filters WHERE user_id = ?", (id,))
    result_search = cursor.fetchone()  # Извлекает первую найденную строку
    connection.close()
    if result_search[0] == 0:
        messages_result +='нету'
    else:
        if result_search[1] == 1:
            messages_result += 'за последние 24 часа'
        elif result_search[1] == 3:
            messages_result += f'за последние {result_search[1]} дня'
        elif result_search[1] == 7 or result_search[1] == 14:
            messages_result += f'за последние {result_search[1]} дней'
        elif result_search[1] == 30:
            messages_result += f'Заход более чем {result_search[1]} дней назад'
    messages_result = f'Выберите не менее чем за какое время захода\nбудет проходить парсинг\n\nПрименённый фильтр: {messages_result}'
    return messages_result

async  def use_db_filter_def(id):
    messages_result = ''
    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute(f"SELECT gender_filter,gender,use_language_rus_name,use_language_eng_name FROM active_filters WHERE user_id = ?",
                   (id,))
    result_search = cursor.fetchone()  # Извлекает первую найденную строку
    connection.close()
    if result_search[0] == 0:
        messages_result += 'нету'
    else:
        if result_search[1] == 'man':
            messages_result += 'по мужскому полу'
            if result_search[2] == 1:
                messages_result += ', а так же по имени которое записано на русском языке'
            if result_search[3] == 1:
                messages_result += ', а так же по имени которое записано на английском языке'
        else:
            messages_result += 'по женскому полу'
            if result_search[2] == 1:
                messages_result += ', а так же по имени которое записано на русском языке'
            if result_search[3] == 1:
                messages_result += ', а так же по имени которое записано на английском языке'
    messages_result = (f'Выберите по какому полу будет проходить парсинг\n'
                       f'Так же можно выбрать на каком языке должно быть написано имя у пользователя\n\n'
                       f'Применённый фильтр: {messages_result}')
    return messages_result

async def premium_parsing(list_chat: str,user_id: int):
    my_set_0 = {line.strip().replace(" ", "") for line in list_chat.splitlines()} # это множество в котором хранится чаты по которым необходимо провести парсинг
    my_list = list(my_set_0)
    message_before_result = ''
    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    for line in my_list: # запись в БД чаты по которым парсят
        line_before = line
        if 'http://t.me/' in line:
            line = line.replace('http://t.me/', '')  # удаление
        elif 'https://t.me/' in line:
            line = line.replace('https://t.me/', '')  # удаление
        elif '@' in line:
            line = line.replace('@', '')  # удаление
        elif '/' in line:
            line = line.split('/')[1]
        try:
            await bot.get_chat('@' + line)
        except TelegramBadRequest:
            continue
        cursor.execute(f"SELECT id FROM checking_uniqueness WHERE chat = ?", (line,))
        result_db = cursor.fetchone()
        if not result_db:
            cursor.execute(f"INSERT INTO checking_uniqueness (chat) VALUES (?)",(line,))
            connection.commit()
    connection.close()

    coming_in_filter = False
    coming_in = 0
    gender_filter = False
    gender = 'None'
    premium_filter = False
    photo_filter = False
    phone_filter = False
    use_language_rus_name= False
    use_language_eng_name= False
    filter = True

    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM active_filters WHERE user_id = ?", (user_id,))
    result_search = cursor.fetchone()  # Извлекает первую найденную строку
    connection.close()
    if result_search[1] == 1:
        coming_in_filter = True
        coming_in = int(result_search[1])
    if result_search[3] == 1:
        gender_filter = True
        gender = result_search[4]
    if result_search[5] == 1:
        premium_filter = True
    if result_search[6] == 1:
        photo_filter = True
    if result_search[7] == 1:
        phone_filter = True
    if result_search[8] == 1:
        use_language_rus_name = True
    if result_search[9] == 1:
        use_language_eng_name = True
    if result_search [1] == 0 and result_search [3] == 0 and result_search [5] == 0 and result_search [6] == 0 and result_search [7] == 0 and result_search [8] == 0:
        filter = False
    result = ''
    if not len(my_list) == 0:
        result = await parser.main(all_chat = my_list, coming_in_filter = coming_in_filter, coming_in = coming_in,
                                   gender_filter = gender_filter, gender = gender, premium_filter = premium_filter,
                                   photo_filter = photo_filter, phone_filter = phone_filter, use_language_rus_name = use_language_rus_name,
                                   use_language_eng_name = use_language_eng_name, filter = filter, txt_fail=user_id)
    return result

async def premium_parsing_available_chats(count_user: int,user_id: int):
    coming_in_filter = False
    coming_in = 0
    gender_filter = False
    gender = 'None'
    premium_filter = False
    photo_filter = False
    phone_filter = False
    use_language_rus_name = False
    use_language_eng_name= False
    filter = True

    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM active_filters WHERE user_id = ?", (user_id,))
    result_search = cursor.fetchone()  # Извлекает первую найденную строку
    connection.close()
    if result_search[1] == 1:
        coming_in_filter = True
        coming_in = int(result_search[1])
    if result_search[3] == 1:
        gender_filter = True
        gender = result_search[4]
    if result_search[5] == 1:
        premium_filter = True
    if result_search[6] == 1:
        photo_filter = True
    if result_search[7] == 1:
        phone_filter = True
    if result_search[8] == 1:
        use_language_rus_name = True
    if result_search[9] == 1:
        use_language_eng_name = True
    if result_search[1] == 0 and result_search[3] == 0 and result_search[5] == 0 and result_search[6] == 0 and \
            result_search[7] == 0 and result_search [8] == 0:
        filter = False

    result = await parser.search_by_available_chats(coming_in_filter=coming_in_filter, coming_in=coming_in,
                                                    gender_filter=gender_filter,
                                                    gender=gender, premium_filter=premium_filter,
                                                    photo_filter=photo_filter, phone_filter=phone_filter,
                                                    use_language_rus_name = use_language_rus_name,
                                                    use_language_eng_name=use_language_eng_name,
                                                    filter=filter, count_user_name=count_user,
                                                    txt_fail=user_id)
    return result

@router.message(CommandStart()) # этот hendler выполняется только при отправки команды старт (/start), ниже действия которые произойдут после вхождения в этот hendler
async  def cmd_start(message: Message, state: FSMContext): # принимает сообщение от пользователя это асинхронная функция будет выполнена как только мы войдём в этот hendler
    status = ""
    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute(f"SELECT valid_until FROM premium WHERE user_id = ?", (message.from_user.id,))
    result = cursor.fetchone() # Извлекает первую найденную строку
    if result: # если такой id есть
        if result[0] == 'Free':
            status = "Free"
        elif result[0] == 'premium':
            status = "premium навсегда"
        else:
            dt_from_db = dt.datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S') # первый принимаемый параметр это входная строка с датой, второй это формат даты
            if dt_from_db < dt.datetime.now():
                status = "Free"
                cursor.execute(f"UPDATE premium SET valid_until = ? WHERE user_id = ?",('Free', message.from_user.id))
                connection.commit()  # сохранение
            else:
                status = f'premium до {result[0]}'
    else:
        connection.close()
        captcha = generate_captcha(message.from_user.id)
        await  message.answer(f'Привет <b>{message.from_user.username}</b>!\nЯ бот который может спарсить любой открытый чат\n'
                              f'Перед началом использования бота необходимо пройти капчу\n\n<b>{captcha}</b>',
            parse_mode="HTML")
        await state.set_state(Form.captcha)  # устанавливаем состояние ожидания ответа
        return

    connection.close()
    if message.from_user.id in ARR_ADMIN_ID: # если пользователь является админом
        await  message.answer(f'Привет <b>{message.from_user.username}</b>!\nВаш id: <b>'
                              f'{message.from_user.id}</b>\nСтатус: <b>Админ</b>\n\nЯ могу спарсить любой открытый чат\n'
                              f'Выбери необходимый пункт ниже 👇',
                              parse_mode="HTML", reply_markup=kb.main_admin)
    else:
        await  message.answer(f'Привет <b>{message.from_user.username}</b>!\nВаш id: <b>'
                              f'{message.from_user.id}</b>\nСтатус: <b>{status}</b>\n\nЯ могу спарсить любой открытый чат\n'
                              f'Выбери необходимый пункт ниже 👇',
                              parse_mode="HTML", reply_markup=kb.main)  # так отсылаем ответ пользователю

@router.message(Form.captcha)
async def captcha(message: types.Message, state: FSMContext):
    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute(f"SELECT answer FROM captcha WHERE user_id = ?", (message.from_user.id,))
    answer = cursor.fetchone()  # Извлекает первую найденную строку
    otvet = 0
    try:
        otvet = int(message.text)
    except ValueError:
        connection.close()
        captcha = generate_captcha(message.from_user.id)
        await message.answer(f'Введено некорректное значение, попытайтесь ещё раз\n\n<b>{captcha}</b>',parse_mode= 'HTML')
        await state.set_state(Form.captcha)
        return
    if otvet == answer[0]:
        cursor.execute(f'DELETE FROM captcha WHERE user_id = ?', (message.from_user.id,))
        cursor.execute(f"INSERT INTO premium (user_id, valid_until) VALUES (?, ?)", (message.from_user.id, "Free"))
        cursor.execute(f"INSERT INTO active_filters (user_id) VALUES (?)", (message.from_user.id,))
        cursor.execute(f"INSERT INTO pay (user_id) VALUES (?)", (message.from_user.id,))
        status = "Free"
        connection.commit()  # сохранение
        await  message.answer(f'Привет <b>{message.from_user.username}</b>!\nВаш id: <b>{message.from_user.id}</b>'
                              f'\nСтатус: <b>{status}</b>\n\nЯ могу спарсить любой открытый чат\nВыбери необходимый пункт ниже 👇',
            parse_mode="HTML", reply_markup=kb.main) # тут дописать капчу
    else:
        captcha = generate_captcha(message.from_user.id)
        await message.answer(f'Введено неверное значение, попытайтесь ещё раз\n\n<b>{captcha}</b>',parse_mode='HTML')
        await state.set_state(Form.captcha)
    connection.close()

@router.callback_query(F.data == 'Back')
async def back(callback: CallbackQuery,state: FSMContext):
    await state.clear()
    status = ""
    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute(f"SELECT valid_until FROM premium WHERE user_id = ?", (callback.from_user.id,))
    result = cursor.fetchone()  # Извлекает первую найденную строку

    if result[0] == 'Free':
        status = "Free"
    elif result[0] == 'premium':
        status = "premium навсегда"
    else:
        dt_from_db = dt.datetime.strptime(result[0],'%Y-%m-%d %H:%M:%S')  # первый принимаемый параметр это входная строка с датой, второй это формат даты
        if dt_from_db < dt.datetime.now():
            status = "Free"
            cursor.execute(f"UPDATE premium SET valid_until = ? WHERE user_id = ?",('Free', callback.from_user.id))
            connection.commit()  # сохранение
        else:
            status = f'premium до {result[0]}'

    connection.close()
    if callback.from_user.id in ARR_ADMIN_ID: # если пользователь является админом
        await  callback.message.answer(f'Привет <b>{callback.from_user.username}</b>!\n'
                                       f'Ваш id: <b>{callback.from_user.id}</b>\nСтатус: <b>Админ</b>\n\n'
                                       f'Я могу спарсить любой открытый чат\nВыбери необходимый пункт ниже 👇',
                                       parse_mode="HTML", reply_markup=kb.main_admin)
    else:
        await  callback.message.answer(f'Привет <b>{callback.from_user.username}</b>!\n'
                                       f'Ваш id: <b>{callback.from_user.id}</b>\nСтатус: <b>{status}</b>\n\n'
                                       f'Я могу спарсить любой открытый чат\nВыбери необходимый пункт ниже 👇',
                                       parse_mode="HTML", reply_markup=kb.main)

@router.callback_query(F.data == 'admin_panel')
async def admin_panel(callback: CallbackQuery, state: FSMContext):
    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM admins WHERE admin_id = ?", (callback.from_user.id,))
    result_from_db = cursor.fetchone()
    if result_from_db == None: # если админа нет в БД
        cursor.execute(f"INSERT INTO admins (admin_id) VALUES (?)", (callback.from_user.id,))
        connection.commit()  # сохранение
    connection.close()
    await state.clear()
    await callback.message.edit_text('Выберите действие:', reply_markup=kb.admin_panel)

@router.callback_query(F.data == 'add_premium')
async def add_premium(callback: CallbackQuery,state: FSMContext):
    await state.set_state(Form.waiting_for_id_user_for_add) # устанавливаем состояние ожидания ответа
    await callback.message.edit_text('Введите id пользователя:', reply_markup=kb.back_in_admin_panel)

@router.message(Form.waiting_for_id_user_for_add)
async def waiting_for_id_user_for_add(message: types.Message, state: FSMContext): # принимаем сообщение от пользователя
    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM premium WHERE user_id = ?",(message.text,))
    result_from_db = cursor.fetchone()
    if result_from_db == None: # если такого пользователя нету
        await message.answer('Пользователя по такому id нет', reply_markup=kb.back_in_admin_panel)
    else: # если такой пользователь есть
        if result_from_db[1] == 'premium':
            await message.answer('Внимание!\n\nУ данного пользователя уже оформлен премиум навсегда" ',
                                 reply_markup=kb.back_in_admin_panel)
        elif result_from_db[1] == 'Free':
            await state.set_state(Form.waiting_days_for_add_premium)
            cursor.execute(f"UPDATE admins SET user_id = ?  WHERE admin_id = ?", (message.text, message.from_user.id))
            connection.commit()  # сохранение
            await message.answer('Укажите на какое количество дней предоставить premium\n или введите "навсегда" ',
                                 reply_markup=kb.back_in_admin_panel)
        else:
            valid_until = dt.datetime.strptime(result_from_db[1], '%Y-%m-%d %H:%M:%S')
            if valid_until>dt.datetime.now():
                await state.set_state(Form.waiting_days_for_add_premium)
                cursor.execute(f"UPDATE admins SET user_id = ?  WHERE admin_id = ?", (message.text, message.from_user.id))
                connection.commit()  # сохранение
                await message.answer(f'Внимание!\nУ данного пользователя уже имеется премиум статус до:{result_from_db[1]}\n\n'
                                     f'Укажите на какое количество дней продлить premium\n или введите "навсегда" ',
                                     reply_markup=kb.back_in_admin_panel)
            else:
                await state.set_state(Form.waiting_days_for_add_premium)
                cursor.execute(f"UPDATE admins SET user_id = ?  WHERE admin_id = ?",(message.text, message.from_user.id))
                connection.commit()  # сохранение
                await message.answer(f'Укажите на какое количество дней предоставить premium\n или введите "навсегда" ',
                                     reply_markup=kb.back_in_admin_panel)

    connection.close()

@router.message(Form.waiting_days_for_add_premium)
async def waiting_days_for_add_premium(message: types.Message, state: FSMContext): # принимаем сообщение от пользователя
    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute(f"SELECT user_id FROM admins WHERE admin_id = ?", (message.from_user.id,))
    user_id_from_db = cursor.fetchone()
    if message.text == 'навсегда':
        cursor.execute(f"UPDATE premium SET valid_until = ?  WHERE user_id = ?",('premium', user_id_from_db[0]))
        connection.commit()  # сохранение
        await message.answer(f'Пользователю "{user_id_from_db[0]}" успешно присвоен premium навсегда!',reply_markup=kb.back_in_admin_panel)
    else:
        days = 0
        try:
            days = int(message.text)
        except Exception:
            await state.set_state(Form.waiting_days_for_add_premium)
            await message.answer(f'Введено некорректное значение!\nПопробуйте ещё раз или вернитесь назад',reply_markup=kb.back_in_admin_panel)
            connection.close()
            return

        cursor.execute(f"SELECT valid_until FROM premium WHERE user_id = ?",(user_id_from_db[0],))
        valid_until_from_db = cursor.fetchone()
        valid_until = dt.datetime.now()
        if valid_until_from_db[0] == 'Free':
            valid_until_for_db = valid_until + dt.timedelta(days=days)
            valid_until_for_db = valid_until_for_db.strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(f"UPDATE premium SET valid_until = ?  WHERE user_id = ?", (str(valid_until_for_db), user_id_from_db[0]))
            connection.commit()  # сохранение
            await message.answer(f'Пользователю "{user_id_from_db[0]}" успешно установлен premium статус до {valid_until_for_db}',reply_markup=kb.back_in_admin_panel)
        else:
            valid_until = dt.datetime.strptime(valid_until_from_db[0], '%Y-%m-%d %H:%M:%S')
            valid_until_for_db = valid_until + dt.timedelta(days=days)
            valid_until_for_db = valid_until_for_db.strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(f"UPDATE premium SET valid_until = ?  WHERE user_id = ?", (str(valid_until_for_db), user_id_from_db[0]))
            connection.commit()  # сохранение
            await message.answer(f'Пользователю "{user_id_from_db[0]}" успешно продлён premium статус до {valid_until_for_db}',reply_markup=kb.back_in_admin_panel)

    connection.close()

@router.callback_query(F.data == 'delete_premium')
async def delete_premium(callback: CallbackQuery,state: FSMContext):
    await state.set_state(Form.waiting_for_id_user_for_delete) # устанавливаем состояние ожидания ответа
    await callback.message.edit_text('Введите id пользователя:', reply_markup=kb.back_in_admin_panel)

@router.message(Form.waiting_for_id_user_for_delete)
async def waiting_for_id_user_for_delete(message: types.Message, state: FSMContext): # принимаем сообщение от пользователя
    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM premium WHERE user_id = ?",(message.text,))
    result_from_db = cursor.fetchone()
    if result_from_db == None: # если такого пользователя нету
        await message.answer('Пользователя по такому id нет', reply_markup=kb.back_in_admin_panel)
    else:
        cursor.execute(f"UPDATE premium SET valid_until = ?  WHERE user_id = ?",('Free', result_from_db[0]))
        connection.commit()  # сохранение
        await message.answer(f'Пользователю "{message.text}" был обновлён premium статус\nС "{result_from_db[1]}"\nна "Free"', reply_markup=kb.back_in_admin_panel)
    connection.close()

@router.callback_query(F.data == 'statistics') # ловим callback_query
async def statistics(callback: CallbackQuery): # выводим все товары которые относятся к этой категории
    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM premium")
    count_all_string = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM premium WHERE valid_until != ?", ('Free',))
    count_arrange_premium = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM premium WHERE valid_until == ?", ('premium',))
    count_premium = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(summ_purchase) FROM table_buy")
    total_summ = cursor.fetchone()[0]
    await callback.message.edit_text(f'Всего пользователей: <b>{count_all_string}</b>\n\n'
                                     f'Количество пользователей оформивших premium: <b>{count_arrange_premium}</b>\n\n'
                                     f'Количество пользователей оформивших premium навсегда: <b>{count_premium}</b>\n\n'
                                     f'Всего заработано в рублях: <b>{total_summ}</b>',
                                     parse_mode='HTML', reply_markup=kb.back_in_admin_panel)
    connection.close()


@router.callback_query(F.data == 'Apply_premium') # ловим callback_query
async def apply_premium(callback: CallbackQuery,state: FSMContext): # выводим все товары которые относятся к этой категории
    await callback.message.edit_text('Выберите подходящий тариф:', reply_markup=kb.prise)

@router.callback_query(F.data.startswith('pay_')) # ловим callback_query
async def pay_(callback: CallbackQuery):
    pay_data = callback.data.split('_')[1]
    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute(f"UPDATE pay SET summ = ? WHERE user_id = ?",(pay_data, callback.from_user.id))
    connection.commit()
    connection.close()
    await callback.message.edit_text('Выберите способ оплаты:', reply_markup=kb.pay_metod)

@router.callback_query(F.data == 'crypro_bot_pay')
async def crypro_bot_pay(callback: CallbackQuery):
    await callback.message.edit_text(f'Выберите валюту для оплаты:', reply_markup = kb.currency)

@router.callback_query(F.data.startswith('cryproBotPay_'))
async def crypro_bot_pay(callback: CallbackQuery):
    pay_data = callback.data.split('_')[1] # хранит монету которой будет происходить оплата
    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute(f"SELECT valid_until FROM premium WHERE user_id = ?", (callback.from_user.id,))
    valid_until_from_db = cursor.fetchone()
    if valid_until_from_db[0] == 'premium':
        await callback.message.edit_text('У вас уже имеется premium статус <b>навсегда</b>',
                                         parse_mode= 'HTML',reply_markup= kb.to_the_main_menu)
        return

    cursor.execute(f"SELECT summ,invoice_id,valid_until FROM pay WHERE user_id = ?", (callback.from_user.id,))
    from_db = cursor.fetchone()

    if not from_db[2] == '0': # если есть значение в этом столбце
        valid_until = dt.datetime.strptime(from_db[2], '%Y-%m-%d %H:%M:%S')  # тоже что и выше только в формате даты и времени
        if valid_until > dt.datetime.now():  # если платёж активен
            crypto.deleteInvoice(from_db[0])

    course = crypto.getExchangeRates()
    position = 0 # позиция на которой находится эта монета
    arr_moneta =course['result'] # массив который хранит все монеты

    for i in range(0,len(arr_moneta),1):
        if arr_moneta[i]['target'] == 'RUB' and arr_moneta[i]['source'] == pay_data:
            position = i

    moneta_summ = course['result'][position]['rate'] # хранит сумму в рублях одной выбранной монеты
    result_summ = int(from_db[0]) / float(moneta_summ) # конечная сумма монеты для оплаты
    pay = crypto.createInvoice(pay_data, str(result_summ), params={"description": f"Оплата premium статуса у bot_parser на "
                                                                                  f"{from_db[0]} рублей","expires_in": 3600})
    url = pay['result']['pay_url']

    valid_until = dt.datetime.now() + dt.timedelta(hours = 1)
    valid_until = valid_until.strftime("%Y-%m-%d %H:%M:%S") # преобразовываем в норм формат
    cursor.execute(f"UPDATE pay SET invoice_id = ?, valid_until = ? WHERE user_id = ?", (pay['result']['invoice_id'],valid_until, callback.from_user.id))
    connection.commit()  # сохранение
    connection.close()
    await callback.message.edit_text(f'Оплата\n\n<b>Внимание!</b>\nЕсли вы произвели оплату и при нажатии кнопки '
                                     f'<b>"проверить оплату"</b> платёж не засчитался, то просто подождите. платёж может '
                                     f'засчитываться до 5 минут.\n<b>Не в коем случае не создавайте новый,</b> иначе '
                                     f'данные о этом платеже будут утеряны и тогда оплата не будет проведена\n\n'
                                     f'Срок действия ссылки 1 час: \n\n{url}',
                                     parse_mode="HTML",reply_markup = kb.pay_cryptoBot)


@router.callback_query(F.data == 'check_pay')
async def back_in_filter(callback: CallbackQuery):
    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute(f"SELECT invoice_id FROM pay WHERE user_id = ?", (callback.from_user.id,))
    from_db = cursor.fetchone()
    connection.close()
    get_result = crypto.getInvoices(params={'invoice_ids': from_db[0]})
    if get_result['result']['items'][0]['status'] == 'active': # если не оплачен
        await callback.answer('Статус платежа: Не оплачен',show_alert = True)
    elif get_result['result']['items'][0]['status'] == 'expired': # если просрочен
        await callback.answer('Статус платежа: просрочен', show_alert=True)
    elif get_result['result']['items'][0]['status'] == 'paid': # если прошла оплата
        summ = get_result['result']['items'][0]['description'].split('на ')[1].split(' ')[0] # сумма оплаты

        connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
        cursor = connection.cursor()
        cursor.execute(f"SELECT valid_until FROM premium WHERE user_id = ?", (callback.from_user.id,))
        from_db = cursor.fetchone()
        cursor.execute(f"INSERT INTO table_buy (user_id,date_of_purchase,summ_purchase) VALUES (?, ?, ?)",
                       (callback.from_user.id, str(dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),int(summ[:-2])))
        connection.commit()  # сохранение данных об успешной покупке

        valid_until= None
        if from_db[0] == 'Free':
            valid_until = dt.datetime.now()
        else:
            valid_until = dt.datetime.strptime(from_db[0], '%Y-%m-%d %H:%M:%S')

        premium = False # True если оформлен премиум
        if summ == '100.0':
            valid_until = valid_until + dt.timedelta(hours=1)
        elif summ == '200.0':
            valid_until = valid_until + dt.timedelta(days=1)
        elif summ == '300.0':
            valid_until = valid_until + dt.timedelta(days=5)
        elif summ == '450.0':
            valid_until = valid_until + dt.timedelta(days=15)
        elif summ == '600.0':
            valid_until = valid_until + dt.timedelta(days=30)
        elif summ == '1000.0':
            premium = True

        message = ''
        if premium == False: # если пользователь оформил не премиум
            valid_until = valid_until.strftime("%Y-%m-%d %H:%M:%S")  # Форматируем дату и время в нужный формат
            message = valid_until
            cursor.execute(f"UPDATE premium SET valid_until = ? WHERE user_id = ?",(valid_until, callback.from_user.id))
        else:
            message = 'навсегда'
            cursor.execute(f"UPDATE premium SET valid_until = ? WHERE user_id = ?",('premium', callback.from_user.id))
        connection.commit()
        connection.close()
        await callback.message.edit_text(f'<b>💎 Premium</b> статус успешно приобретён\nДействителен до: <b>{message}</b>',
                                         parse_mode="HTML", reply_markup=kb.to_the_main_menu)

@router.callback_query(F.data == 'cancellation_pay')
async def back_in_filter(callback: CallbackQuery):
    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute(f"SELECT invoice_id,valid_until FROM pay WHERE user_id = ?", (callback.from_user.id,))
    from_db = cursor.fetchone()
    connection.close()
    dt_from_db = dt.datetime.strptime(from_db[1], '%Y-%m-%d %H:%M:%S') # тоже что и выше только в формате даты и времени
    if dt_from_db > dt.datetime.now(): # если платёж активен
        crypto.deleteInvoice(from_db[0])
    await callback.message.edit_text('Платёж успешно удалён', reply_markup=kb.to_the_main_menu)

@router.callback_query(F.data == 'parsing') # ловим callback_query
async def parsing(callback: CallbackQuery,state: FSMContext):
    await state.set_state(Form.waiting_for_answer) # устанавливаем состояние ожидания ответа
    await callback.message.edit_text('Отправьте ссылку на чат в формате:\n<b>t.mе/durоv</b> или <b>@durоv</b>',
                                     parse_mode="HTML",reply_markup= kb.back)

@router.callback_query(F.data == 'premium_features')  # ловим callback_query который начинается с category_   (startswith это использовании метода который вернёт True если значение начинается с переданной строки)
async def premium_features(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    messages_show = await premium_filter_def(callback.from_user.id)
    await callback.message.edit_text(messages_show,reply_markup= kb.premium_fun)

@router.callback_query(F.data == 'input_chat')  # ловим callback_query который начинается с category_   (startswith это использовании метода который вернёт True если значение начинается с переданной строки)
async def input_chat(callback: CallbackQuery,state: FSMContext):
    await state.set_state(Form.waiting_for_answer_premium)  # устанавливаем состояние ожидания ответа
    await callback.message.edit_text(
        'Введите чат или список чатов\nили выберите пункт "Спарсить по имеющимся чатам",\nтогда парсинг произойдёт '
        'по чатам которые имеет бот\n\nДля ввода списка чата необходимо ввести один чат на одной строке\n\n'
        'Если вы используете пк, то для перехода на новую строку используйте'
        '\n<b>Shift + Enter</b>\n\nПример:\n<b>t.mе/durоv\nt.mе/durоv</b>',
        parse_mode="HTML",reply_markup=kb.back_in_filter)

@router.callback_query(F.data == 'phone_filter')
async def coming_in_filter(callback: CallbackQuery):
    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute(f"SELECT phone_filter FROM active_filters WHERE user_id = ?",
                   (callback.from_user.id,))
    result_search = cursor.fetchone()  # Извлекает первую найденную строку
    if result_search[0] == 0:
        cursor.execute(f"UPDATE active_filters SET phone_filter = ? WHERE user_id = ?",
                       (1, callback.from_user.id))
    else:
        cursor.execute(f"UPDATE active_filters SET phone_filter = ? WHERE user_id = ?",
                       (0, callback.from_user.id))
    connection.commit()
    connection.close()
    messages_show = await premium_filter_def(callback.from_user.id)
    await callback.message.edit_text(messages_show, reply_markup=kb.premium_fun)

@router.callback_query(F.data == 'coming_in_filter')
async def coming_in_filter(callback: CallbackQuery):
    messages_show = await coming_in_filter_def(callback.from_user.id)
    await callback.message.edit_text(messages_show,reply_markup= kb.coming_in_filter)

@router.callback_query(F.data.startswith('timeInDays_') )
async def coming_in_filter_day(callback: CallbackQuery):
    day_data = callback.data.split('_')[1]
    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute(f"SELECT coming_in_filter, coming_in FROM active_filters WHERE user_id = ?",
                   (callback.from_user.id,))
    result_from_db = cursor.fetchone()
    if int(result_from_db[1]) == int(day_data) or result_from_db[1] == 0:
        if result_from_db[0] == 0:
            cursor.execute(f"UPDATE active_filters SET coming_in_filter = ?, coming_in = ? WHERE user_id = ?",
                           (1, day_data, callback.from_user.id))
        else:
            cursor.execute(f"UPDATE active_filters SET coming_in_filter = ? WHERE user_id = ?",
                           (0, callback.from_user.id))
    else:
        cursor.execute(f"UPDATE active_filters SET coming_in_filter = ?, coming_in = ? WHERE user_id = ?",
                       (1,day_data,callback.from_user.id))
    connection.commit()
    connection.close()
    messages_show = await coming_in_filter_def(callback.from_user.id)
    try:
        await callback.message.edit_text(messages_show, reply_markup= kb.coming_in_filter)
    except TelegramBadRequest: # если нажали на ту кнопку которая была нажата раньше
        pass

@router.callback_query(F.data.startswith('use_db') )
async def use_db(callback: CallbackQuery):
    messages_show = await use_db_filter_def(callback.from_user.id)
    await callback.message.edit_text(messages_show, reply_markup=kb.db_filter)

@router.callback_query(F.data.startswith('use_only_') )
async def gender_filter(callback: CallbackQuery):
    filter_data = callback.data.split('_')[2] # здесь будет eng или rus
    if filter_data == 'eng':
        opposite = 'rus'
    else:
        opposite = 'eng'
    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute(f"SELECT use_language_{filter_data}_name,use_language_{opposite}_name  FROM active_filters WHERE user_id = ?",
                   (callback.from_user.id,))
    result_from_db = cursor.fetchone()
    if result_from_db[0] == 1:
        cursor.execute(f"UPDATE active_filters SET use_language_{filter_data}_name = ? WHERE user_id = ?",
                       (0, callback.from_user.id))
    else:
        cursor.execute(f"UPDATE active_filters SET use_language_{filter_data}_name = ? WHERE user_id = ?",
                       (1, callback.from_user.id))
        cursor.execute(f"UPDATE active_filters SET use_language_{opposite}_name = ? WHERE user_id = ?",
                       (0, callback.from_user.id))
    connection.commit()
    connection.close()
    messages_show = await use_db_filter_def(callback.from_user.id)
    try:
        await callback.message.edit_text(messages_show, reply_markup=kb.db_filter)
    except TelegramBadRequest:
        await callback.answer('Сперва выберите пол!')

@router.callback_query(F.data.startswith('clear_db_filter') )
async def clear_db_filter(callback: CallbackQuery):
    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute(f"UPDATE active_filters SET gender_filter = ?, gender = ?, use_language_rus_name = ? WHERE user_id = ?",
                   (0,'None',0, callback.from_user.id))
    connection.commit()
    connection.close()
    messages_show = await use_db_filter_def(callback.from_user.id)
    try:
        await callback.message.edit_text(messages_show, reply_markup=kb.db_filter)
    except TelegramBadRequest:
        await callback.answer('У вас уже очищены фильтры!')

@router.callback_query(F.data.startswith('genderFilter_') )
async def gender_filter(callback: CallbackQuery):
    gender_data = callback.data.split('_')[1]
    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute(f"SELECT gender_filter, gender FROM active_filters WHERE user_id = ?", (callback.from_user.id,))
    result_from_db = cursor.fetchone()
    if result_from_db[1] == gender_data or gender_data[1] == 'None':
        if result_from_db[0] == 0:
            cursor.execute(f"UPDATE active_filters SET gender_filter = ?, gender = ? WHERE user_id = ?",
                           (1,gender_data, callback.from_user.id))
        else:
            cursor.execute(f"UPDATE active_filters SET gender_filter = ? WHERE user_id = ?",
                           (0, callback.from_user.id))
    else:
        cursor.execute(f"UPDATE active_filters SET gender_filter = ?, gender = ? WHERE user_id = ?",
                       (1,gender_data, callback.from_user.id))
    connection.commit()
    connection.close()
    messages_show = await use_db_filter_def(callback.from_user.id)
    try:
        await callback.message.edit_text(messages_show, reply_markup= kb.db_filter)
    except TelegramBadRequest:  # если нажали на ту кнопку которая была нажата раньше
        pass

@router.callback_query(F.data == 'clear_coming_in_filter')  # ловим callback_query
async def clear_coming_in_filter(callback: CallbackQuery):
    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute(f"UPDATE active_filters SET coming_in_filter = ?,coming_in = ? WHERE user_id = ?",
                   (0,1, callback.from_user.id))
    connection.commit()
    connection.close()
    messages_show = await coming_in_filter_def(callback.from_user.id)
    try:
        await callback.message.edit_text(messages_show, reply_markup=kb.coming_in_filter)
    except TelegramBadRequest:  # если нажали на ту кнопку которая была нажата раньше
        await callback.answer('У вас уже очищены все фильтры на время')

@router.callback_query(F.data == 'Apply_premium_filter')  # ловим callback_query
async def apply_premium_filter(callback: CallbackQuery):
    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute(f"SELECT premium_filter FROM active_filters WHERE user_id = ?", (callback.from_user.id,))
    result_search = cursor.fetchone()  # Извлекает первую найденную строку
    if result_search[0] == 0:
        cursor.execute(f"UPDATE active_filters SET premium_filter = ? WHERE user_id = ?", (1,callback.from_user.id))
    else:
        cursor.execute(f"UPDATE active_filters SET premium_filter = ? WHERE user_id = ?", (0, callback.from_user.id))
    connection.commit()
    connection.close()
    messages_show = await premium_filter_def(callback.from_user.id)
    await callback.message.edit_text(messages_show, reply_markup=kb.premium_fun)

@router.callback_query(F.data == 'photo_filter')  # ловим callback_query
async def photo_filter(callback: CallbackQuery):
    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute(f"SELECT photo_filter FROM active_filters WHERE user_id = ?", (callback.from_user.id,))
    result_search = cursor.fetchone()  # Извлекает первую найденную строку
    if result_search[0] == 0:
        cursor.execute(f"UPDATE active_filters SET photo_filter = ? WHERE user_id = ?", (1,callback.from_user.id))
    else:
        cursor.execute(f"UPDATE active_filters SET photo_filter = ? WHERE user_id = ?", (0, callback.from_user.id))
    connection.commit()
    connection.close()
    messages_show = await premium_filter_def(callback.from_user.id)
    await callback.message.edit_text(messages_show, reply_markup=kb.premium_fun)

@router.callback_query(F.data == 'clear_filter')  # ловим callback_query
async def clear_filter(callback: CallbackQuery):
    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute(f"UPDATE active_filters SET coming_in_filter = ?,coming_in = ?,gender_filter = ?,"
                   f" gender = ?, premium_filter = ?, photo_filter = ? WHERE user_id = ?",
                   (0,0,0,'None',0,0, callback.from_user.id))
    connection.commit()
    connection.close()
    messages_show = await premium_filter_def(callback.from_user.id)
    try:
        await callback.message.edit_text(messages_show, reply_markup=kb.premium_fun)
    except TelegramBadRequest:
        await callback.answer('У вас уже очищены все фильтры')

@router.callback_query(F.data == 'F.A.Q')  # ловим callback_query
async def faq(callback: CallbackQuery):
    await callback.message.edit_text("""Наши возможности. (Функционал парсера)\n\n\n
    ─  Стандартный статус парсера без Premium.\n\n
    • Парсинг открытого чата - получение списка всех участников открытого чата с установленным username в виде текстового файла.\n\n
    • Доступен постоянно, без ограничений и 24/7.\n\n\n\n
    ─ Для Premium пользователей:\n\n
    Парсинг открытых чатов с возможностью парсинга по критериям:\n\n
    • Собрать всех.\n\n
    • Произвести сбор user_name пользователей по имеющимся чатам в боте (в базе данных хранится более 200к user_names)\n\n
    • По дате последнего посещения (1 день назад, 3 дня, 7 дней, 14 дней и более чем 30 дней назад)\n\n
    • Только пользователей определенного пола\n\n
    • Только имена написанные на русском языке/ только имена написанные на английском языке.\n\n
    • Пользователей с номерами телефона в профиле.\n\n
    • Только пользователей с премиум статусом.\n\n
    • По наличию установленной фотографии.\n\n\n
    Проверка на уникальность чатов\n\n
    Эта функция проверяет уникальность чата,\n
    то есть, если бот работал с этим чатом, то такой чат будет считаться не уникальным\n\n\n
    ─ Если при пополнении нет удобного для Вас метода оплаты, пожалуйста, напишите администратору: @BlackSMM_Admin""",
                                     parse_mode = 'HTML', reply_markup=kb.to_the_main_menu)

@router.callback_query(F.data == 'existing_chats')
async def existing_chats(callback: CallbackQuery,state: FSMContext):
    await callback.message.edit_text('Парсинг будет происходить по списку чатов который находятся в боте\n'
                                     'и будет идти до тех пока не будет найдено необходимое количество участников с данными фильтрами.\n\n'
                                     'Введите количество участников которых необходимо найти <b>(лимит 1000)</b>\n\n'
                                     'Пример ввода: <b>100</b>',parse_mode="HTML",reply_markup=kb.back_in_filter2)
    await state.set_state(Form.waiting_for_answer_list_of_available_chats)  # устанавливаем состояние ожидания ответа

@router.callback_query(F.data == 'check_subscription')
async def existing_chats(callback: CallbackQuery):
    member = await bot.get_chat_member(chat_id=CHANNEL_NAME, user_id=callback.from_user.id)
    if member.status in ["left", "kicked"]:  # если пользователь не подписан на канал
        await callback.answer(f'Внимание!\nВы не подписаны на канал:\n\n{CHANNEL_URL}',show_alert = True)
    else:
        status = ""
        connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
        cursor = connection.cursor()
        cursor.execute(f"SELECT valid_until FROM premium WHERE user_id = ?", (callback.from_user.id,))
        result = cursor.fetchone()  # Извлекает первую найденную строку
        if result[0] == 'Free':
            status = "Free"
        elif result[0] == 'premium':
            status = "premium навсегда"
        else:
            dt_from_db = dt.datetime.strptime(result[0],'%Y-%m-%d %H:%M:%S')  # первый принимаемый параметр это входная строка с датой, второй это формат даты
            if dt_from_db < dt.datetime.now():
                status = "Free"
                cursor.execute(f"UPDATE premium SET valid_until = ? WHERE user_id = ?",
                               ('Free', callback.from_user.id))
                connection.commit()  # сохранение
            else:
                status = f'premium до {result[0]}'
        connection.close()
        await callback.answer('Спасибо за подписку)\nТеперь вы можете пользоваться бесплатным парсингом',show_alert = True)
        await callback.message.edit_text(
            f'Привет <b>{callback.from_user.username}</b>!\nВаш id: <b>{callback.from_user.id}</b>\nСтатус: '
            f'<b>{status}</b>\n\nЯ могу спарсить любой открытый чат\nВыбери необходимый пункт ниже 👇',
            parse_mode="HTML", reply_markup=kb.main)  # так отсылаем ответ пользователю

@router.callback_query(F.data == 'checking_uniqueness')
async def existing_chats(callback: CallbackQuery,state: FSMContext):
    await state.set_state(Form.waiting_for_check_chat)
    await callback.message.edit_text(f'Введите один или несколько чатов:\n\nОдин чат - одна строка\nПример:\n<b>t.mе/durоv</b>\n<b>t.mе/durоv</b>\n'
                                     f'(Что бы писать на новой строке используйте Shift + Enter)\n\nЭта функция проверяет уникальность чата,'
                                     f'\nто есть, если бот работал с этим чатом, то такой чат будет считаться не уникальным\n\nЛимит 25 чатов',
                                     parse_mode="HTML",reply_markup = kb.to_the_main_menu)

@router.message(Form.waiting_for_check_chat)
async def check_chat(message: types.Message, state: FSMContext):
    await state.clear()
    lines = message.text.split('\n')
    lines = list(set(lines))
    if len(lines) > 25:
        await state.set_state(Form.waiting_for_check_chat)
        await message.answer(f'⚠️ <b>Внимание!</b> вы превысили лимит в 25 чатов! ⚠️\n\nВведите один или несколько чатов:\n\n'
                             f'Один чат - одна строка\nПример:\n<b>t.mе/durоv</b>\n<b>t.mе/durоv</b>\n'
                             f'(Что бы писать на новой строке используйте Shift + Enter)\n\n'
                             f'Эта функция проверяет уникальность чата,'
                             f'\nто есть, если бот работал с этим чатом, то такой чат будет считаться не уникальным\n\n'
                             f'Лимит 25 чатов',
                                     parse_mode="HTML",reply_markup = kb.to_the_main_menu)
        return
    arr_parsing = []  # массив с теми чатами которые парсились
    arr_not_parsing = []  # массив с теми чатами которые не парсились
    arr_not_found = []  # массив с теми чатами которые не были найдены
    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    for line in lines:
        if 'http://t.me/' in line:
            line = line.replace('http://t.me/', '') # удаление
        elif 'https://t.me/' in line:
            line = line.replace('https://t.me/', '')  # удаление
        elif '@' in line:
            line = line.replace('@', '')  # удаление
        elif '/' in line:
            line = line.split('/')[1]
        try:
            await bot.get_chat('@' + line)
        except TelegramBadRequest:
            arr_not_found.append('http://t.me/'+ line)
            continue
        cursor.execute(f"SELECT id FROM checking_uniqueness WHERE chat = ?", (line,))
        result_db = cursor.fetchone()
        if  result_db:
            arr_parsing.append('http://t.me/'+ line)
        else:
            arr_not_parsing.append('http://t.me/' + line)
            cursor.execute(f"INSERT INTO checking_uniqueness (chat) VALUES (?)", (line,))  # если необходимо несколько значений, то пишим их через запятую в скобочках
            connection.commit()
    connection.close()
    result_message = f'Уникальные чаты (кол-во = {len(arr_not_parsing)}):\n'
    for line in arr_not_parsing:
        result_message += line + '\n'
    result_message += f'\nНе уникальные чаты (кол-во = {len(arr_parsing)}):\n'
    for line in arr_parsing:
        result_message += line + '\n'
    result_message += f'\nНе найденные чаты (кол-во = {len(arr_not_found)}):\n'
    for line in arr_not_found:
        result_message += line + '\n'
    await message.answer(f'Результат: \n\n{result_message}')
    await state.set_state(Form.waiting_for_check_chat)
    await message.answer(f'Введите один или несколько чатов:\n\nОдин чат - одна строка\nПример:\n<b>t.mе/durоv</b>\n<b>t.mе/durоv</b>\n'
                                     f'(Что бы писать на новой строке используйте Shift + Enter)\n\nЭта функция проверяет уникальность чата,'
                                     f'\nто есть, если бот работал с этим чатом, то такой чат будет считаться не уникальным\n\nЛимит 25 чатов',
                                     parse_mode="HTML",reply_markup = kb.to_the_main_menu)

@router.message(Form.waiting_for_answer)  # бесплатный парсинг
async def parsing_free(message: types.Message, state: FSMContext): # принимаем сообщение от пользователя
    await state.clear()

    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    line = message.text
    if 'http://t.me/' in line:
        line = line.replace('http://t.me/', '')  # удаление
    elif 'https://t.me/' in line:
        line = line.replace('https://t.me/', '')  # удаление
    elif '@' in line:
        line = line.replace('@', '')  # удаление
    elif '/' in line:
        line = line.split('/')[1]
    try:
        await bot.get_chat('@' + line)
        cursor.execute(f"SELECT id FROM checking_uniqueness WHERE chat = ?", (line,))
        result_db = cursor.fetchone()
        if not result_db:
            cursor.execute(f"INSERT INTO checking_uniqueness (chat) VALUES (?)", (line,))
            connection.commit()
    except TelegramBadRequest:
        await message.answer(f'<b>Внимание!</b>\nчат не найден: "{message.text}"\n\nДля парсинга чата введите '
                             f'ссылку на чат в формате <b>t.mе/durоv</b> или <b>@durоv</b>',
                             parse_mode='HTML', reply_markup=kb.back)
        await state.set_state(Form.waiting_for_answer)
        return
    connection.close()
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_NAME, user_id=message.from_user.id)
    except TelegramBadRequest:
        await message.answer(
            f'<b>Внимание!</b>\nчат не найден: "{message.text}"\n\nДля парсинга чата введите ссылку на чат в формате <b>t.mе/durоv</b> или <b>@durоv</b>',
            parse_mode='HTML', reply_markup=kb.back)
        await state.set_state(Form.waiting_for_answer)
        return

    if member.status in ["left", "kicked"]: # если пользователь не подписан на канал
        await message.answer(f'Внимание!\nДля использования бота необходимо быть подписанным на канал:\n{CHANNEL_URL}',
                             parse_mode= 'HTML',reply_markup=kb.check_subscription)
        return

    sent_message = await message.answer('Парсинг запущен...\n\nЭто может занять до 3 минут')
    last_message_id = sent_message.message_id
    result = await parser.main([line], txt_fail = message.from_user.id)

    if result.startswith('WARNING'):
        await message.answer('⚠️ Бот временно недоступен. ⚠️\nАдминистрация уже работает над этим',reply_markup= kb.to_the_main_menu)
        await message.bot.send_message(SUPPORT_ID, result) # сообщение будет отосланно мне
        return

    if result.startswith('Парсинг прошёл успешно'):
        await message.reply_document(document=types.FSInputFile(path=f'{ROOT_PROJECT_DIR}/Working_file/Telegram_file/{message.from_user.id}.txt'),
                                     caption='\n👆 Файл c результатом парсинга')

    os.remove(f'{ROOT_PROJECT_DIR}/Working_file/Telegram_file/{message.from_user.id}.txt')
    await message.bot.delete_message(message.chat.id, last_message_id)
    await message.answer(result +'\nДля парсинга следующего чата введите ссылку на чат в формате <b>t.mе/durоv</b> или <b>@durоv</b>',
                         parse_mode="HTML", reply_markup = kb.back)
    await state.set_state(Form.waiting_for_answer)  # устанавливаем состояние ожидания ответа

@router.message(Form.waiting_for_answer_premium) # событие при поступлении состояния Form.waiting_for_answer
async def parsing_premium(message: types.Message, state: FSMContext): # принимаем сообщение от пользователя
    await state.clear()
    lines = message.text.split('\n')
    lines = list(set(lines))
    if len(lines) > 15:
        await state.set_state(Form.waiting_for_check_chat)
        await message.answer(f'⚠️ <b>Внимание!</b> вы превысили лимит в 15 чатов! ⚠️',parse_mode="HTML")
        await message.answer('Для парсинга чата Введите чат или список чатов\nили выберите пункт "Спарсить по имеющимся чатам",\n'
                             'тогда парсинг произойдёт по чатам которые имеет бот\n\n'
                             'Для ввода списка чата необходимо ввести один чат на одной строке (лимит 15 чатов)\n\n'
                             'Пример:\n<b>t.mе/durоv\nt.mе/durоv</b>',
            parse_mode="HTML", reply_markup=kb.back_in_filter)
        await state.set_state(Form.waiting_for_answer_premium)  # устанавливаем состояние ожидания ответа
        return

    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute(f"SELECT valid_until FROM premium WHERE user_id = ?", (message.from_user.id,))
    result = cursor.fetchone()  # Извлекает первую найденную строку
    connection.close()
    sent_message = await message.answer('Парсинг запущен...\n\nЭто может занять до 3 минут')
    last_message_id = sent_message.message_id
    if result[0] == 'Free':
        await message.bot.delete_message(message.chat.id, last_message_id)
        await message.answer('Для этого действия необходим <b>premium</b> статус',parse_mode="HTML",
                             reply_markup=kb.not_enough_rights)
    elif result[0] == 'premium':
        result = await premium_parsing(message.text, message.from_user.id)
        if result.startswith('WARNING'):
            await message.answer('⚠️ Бот временно недоступен. ⚠️\nАдминистрация уже работает над этим',
                                 reply_markup= kb.to_the_main_menu)
            await message.bot.send_message(SUPPORT_ID, result)  # сообщение будет отосланно мне
            return
        if result.startswith('Парсинг прошёл успешно'):

            await message.reply_document(document=types.FSInputFile(path=f'{ROOT_PROJECT_DIR}/Working_file/Telegram_file/{message.from_user.id}.txt'),
                                         caption='\n👆 Файл c результатом парсинга')
        try:
            os.remove(f'{ROOT_PROJECT_DIR}/Working_file/Telegram_file/{message.from_user.id}.txt')
        except FileNotFoundError:
            pass
        await message.bot.delete_message(message.chat.id, last_message_id)
        try:
            await message.answer(result + '\n\nДля парсинга следующего чата Введите чат или список чатов\nили выберите пункт '
                                          '"Спарсить по имеющимся чатам",\nтогда парсинг произойдёт по чатам которые имеет бот\n\n'
                                          'Для ввода списка чата необходимо ввести один чат на одной строке (лимит 15 чатов)\n\n'
                                          'Пример:\n<b>t.mе/durоv\nt.mе/durоv</b>',
                parse_mode="HTML", reply_markup=kb.back_in_filter)
        except TelegramBadRequest:
            await message.answer('Внимание!\nНевозможно отобразить список с неудачным парсингом, ошибка чтения чата/чатов у серверов телеграмма' 
                                 '\n\nДля парсинга следующего чата Введите чат или список чатов\nили выберите пункт "Спарсить по имеющимся чатам",'
                                 '\nтогда парсинг произойдёт по чатам которые имеет бот\n\nДля ввода списка чата необходимо ввести один чат на одной строке '
                                 '(лимит 15 чатов)\n\nПример:\n<b>t.mе/durоv\nt.mе/durоv</b>',
                parse_mode="HTML", reply_markup=kb.back_in_filter)
        await state.set_state(Form.waiting_for_answer_premium)  # устанавливаем состояние ожидания ответа

    else:
        dt_from_db = dt.datetime.strptime(result[0],'%Y-%m-%d %H:%M:%S')  # первый принимаемый параметр это входная строка с датой, второй это формат даты
        if dt_from_db < dt.datetime.now():
            await message.bot.delete_message(message.chat.id, last_message_id)
            await message.answer('Для этого действия необходим <b>premium</b> статус',parse_mode="HTML", reply_markup=kb.not_enough_rights)
        else:
            result = await premium_parsing(message.text,message.from_user.id)
            if result.startswith('WARNING'):
                await message.answer('⚠️ Бот временно недоступен. ⚠️\nАдминистрация уже работает над этим')
                await message.bot.send_message(SUPPORT_ID, result)  # сообщение будет отосланно мне
                return
            if result.startswith('Парсинг прошёл успешно'):
                await message.reply_document(document=types.FSInputFile(path=f'{ROOT_PROJECT_DIR}/Working_file/Telegram_file/{message.from_user.id}.txt'),
                                             caption='\n👆 Файл c результатом парсинга')
            os.remove(f'{ROOT_PROJECT_DIR}/Working_file/Telegram_file/{message.from_user.id}.txt')
            await message.bot.delete_message(message.chat.id, last_message_id)
            await message.answer(result + '\n\nДля парсинга следующего чата Введите чат или список чатов\nили выберите пункт '
                                          '"Спарсить по имеющимся чатам",\nтогда парсинг произойдёт по чатам которые имеет бот\n\n'
                                          'Для ввода списка чата необходимо ввести один чат на одной строке(лимит 15 чатов)\n\n'
                                          'Пример:\n<b>t.mе/durоv\nt.mе/durоv</b>',
                parse_mode="HTML",reply_markup=kb.back_in_filter)
            await state.set_state(Form.waiting_for_answer_premium)  # устанавливаем состояние ожидания ответа


@router.message(Form.waiting_for_answer_list_of_available_chats) # событие при поступлении состояния
async def parsing_premium(message: types.Message, state: FSMContext): # принимаем сообщение от пользователя
    await state.clear()
    count_user = 1
    try:
        count_user = int(message.text)
        if count_user > 1000 or count_user < 1:
            await message.answer('⚠️ Введено значение больше 1000 или меньше одного!\n\n<b>Внимание!</b>\n'
                                 'Введите количество участников которых необходимо найти <b>(лимит 1000)</b>\n'
                                 'Пример ввода: <b>100</b>',parse_mode="HTML",reply_markup=kb.back_in_filter2)
            await state.set_state(Form.waiting_for_answer_list_of_available_chats)  # устанавливаем состояние ожидания ответа
            return
    except ValueError:
        await message.answer('⚠️ Введено некорректное значение!\n\n<b>Внимание!</b>\n'
                             'Введите количество участников которых необходимо найти <b>(лимит 1000)</b>\n'
                             'Пример ввода: <b>100</b>',
            parse_mode="HTML", reply_markup=kb.back_in_filter2)
        await state.set_state(Form.waiting_for_answer_list_of_available_chats)  # устанавливаем состояние ожидания ответа
        return

    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute(f"SELECT valid_until FROM premium WHERE user_id = ?", (message.from_user.id,))
    result = cursor.fetchone()  # Извлекает первую найденную строку
    connection.close()

    sent_message = await message.answer('Парсинг запущен...\n\nЭто может занять до 3 минут')
    last_message_id = sent_message.message_id
    if result[0] == 'Free':
        await message.bot.delete_message(message.chat.id, last_message_id)
        await message.answer('Для этого действия необходим <b>premium</b> статус', parse_mode="HTML",
                             reply_markup=kb.not_enough_rights)
    elif result[0] == 'premium':
        result = await premium_parsing_available_chats(count_user, message.from_user.id)
        if result.startswith('WARNING'):
            await message.answer('⚠️ Бот временно недоступен. ⚠️\nАдминистрация уже работает над этим',reply_markup= kb.to_the_main_menu)
            await message.bot.send_message(SUPPORT_ID, result)  # сообщение будет отосланно мне
            return
        if result.startswith('Парсинг прошёл успешно'):
            await message.reply_document(document=types.FSInputFile(
                path=f'{ROOT_PROJECT_DIR}/Working_file/Telegram_file/{message.from_user.id}.txt'),caption='\n👆 Файл c результатом парсинга')
        os.remove(f'{ROOT_PROJECT_DIR}/Working_file/Telegram_file/{message.from_user.id}.txt')
        await message.bot.delete_message(message.chat.id, last_message_id)
        await message.answer(result + '\n\nДля того что бы продолжить парсинг с такими же фильтрами введите необходимое количество участников <b>(лимит 1000)</b>',
                             parse_mode="HTML", reply_markup=kb.back_in_filter2)
        await state.set_state(Form.waiting_for_answer_list_of_available_chats)
    else:
        dt_from_db = dt.datetime.strptime(result[0],'%Y-%m-%d %H:%M:%S')  # первый принимаемый параметр это входная строка с датой, второй это формат даты
        if dt_from_db < dt.datetime.now():
            await message.bot.delete_message(message.chat.id, last_message_id)
            await message.answer('Для этого действия необходим <b>premium</b> статус', parse_mode="HTML",reply_markup=kb.not_enough_rights)
        else:
            result = await premium_parsing_available_chats(count_user, message.from_user.id)
            if result.startswith('WARNING'):
                await message.answer('⚠️ Бот временно недоступен. ⚠️\nАдминистрация уже работает над этим',reply_markup= kb.to_the_main_menu)
                await message.bot.send_message(SUPPORT_ID, result)  # сообщение будет отосланно мне
                return
            if result.startswith('Парсинг прошёл успешно'):
                await message.reply_document(document=types.FSInputFile(
                    path=f'{ROOT_PROJECT_DIR}/Working_file/Telegram_file/{message.from_user.id}.txt'),caption='\n👆 Файл c результатом парсинга')
            os.remove(f'{ROOT_PROJECT_DIR}/Working_file/Telegram_file/{message.from_user.id}.txt')
            await message.bot.delete_message(message.chat.id, last_message_id)
            await message.answer(result + '\n\nДля того что бы продолжить парсинг с такими же фильтрами введите необходимое '
                                          'количество участников <b>(лимит 1000)</b>',parse_mode="HTML", reply_markup=kb.back_in_filter2)
            await state.set_state(Form.waiting_for_answer_list_of_available_chats)



