# это парсер который сочетает все функции

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import asyncio
import os  # для удаления файла
import shutil  # для удаления папки
import sqlite3
import random # для того что бы перемешать все элементы в списке

from sqlite3 import OperationalError

from telethon import TelegramClient
from telethon.errors import  AuthKeyUnregisteredError
from telethon import errors

from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch

from opentele.td import TDesktop
from opentele.tl import TelegramClient
from opentele.api import  UseCurrentSession
from opentele.exception import TFileNotFound

from app.config import API_ID, API_HASH, ROOT_PROJECT_DIR

# channel имя канала
# gender = по какому гендеру мы будем искать
# coming_in_filter = последний заход менее чем день назад
# coming_in = время последнего захода в днях по которым будем парсить
# gender_filter = если надо отфильтровать по гендеру
# premium_filter = есть ли премиум
# photo_filter = есть ли фото
# phone_filter = открыт ли номер телефона
# use_language_rus_name = парсить только по именам написанных на русском языке
# use_language_eng_name = парсить только по именам написанных на русском языке
# filter = отображает применяются ли фильтры
# txt_fail = отображает место где мы будем сохранять txt файл

async def error_handler()->int or str:
    """Вернёт int значение, это имя папки, где хранится рабочий аккаунт или вернёт строку если аккаунты закончились"""
    # use_bot будет True если мы используем бота
    location_main_folder = ROOT_PROJECT_DIR + '/Working_file/Telegram_file'

    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute(f"SELECT name_folder_with_account FROM parsing", )
    name_folder_with_account = cursor.fetchone()  # Извлекает первую найденную строку
    connection.close()

    count_user = name_folder_with_account[0] + 1  # отображает имя паки где хранится аккаунт и + 1 для поиска нового аккаунта

    tdata_location = f'{location_main_folder}/work_accounts/{count_user}/tdata'  # указываем путь к другому аккаунту

    if os.path.isdir(tdata_location): # если аккаунт есть
        connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
        cursor = connection.cursor()
        cursor.execute(f"UPDATE parsing SET name_folder_with_account = ?", (count_user,))
        connection.commit()  # сохранение
        connection.close()

        return count_user # возвращаем int т.к. есть аккаунт
    else:
        return f"WARNING\nАккаунты закончились, скрипт прекратил работу!\n count_user = {count_user}"

async def search_by_available_chats(coming_in_filter=False, coming_in = 1, gender_filter= False, gender='None', premium_filter=False,
               photo_filter=False,phone_filter = False,use_language_rus_name = False,use_language_eng_name = False, filter=False,count_user_name = 1, txt_fail = '1'):

    connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM chat_list")
    all_chat = cursor.fetchall()  # Извлекает все строки
    random.shuffle(all_chat) # перемешиваем все элементы в списке
    connection.close()

    result = ''
    countSuccessful = 0  # счётчик успешных спаршенных участников
    countAttempt = 0  # счётчик кол-во исходных пользователей
    use_bot = False

    location_main_folder = ROOT_PROJECT_DIR + '/Working_file/Telegram_file'

    if not filter:
        error_count = 0
        try:
            client = TelegramClient(location_main_folder + '/bot_session/bot_session.session', API_ID,API_HASH)
            await client.start()
            use_bot = True
        except (RuntimeError, OperationalError):
            if error_count > 15:
                return 'WARNING'
            error_count += 1
            await asyncio.sleep(7)
    else:
        error_count = 0
        while True:  # если аккаунт с которого будем парсить будет использоваться(кто-то парсит с него) (тупо ждём)
            try:  # Обязательно блок try должен быть такой т.к. пока пользователь ждёт освобождение аккаунта, то он может заблокировать и поменяться данные для входа
                connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
                cursor = connection.cursor()
                cursor.execute(f"SELECT name_folder_with_account FROM parsing", )
                name_folder_with_account = cursor.fetchone()  # Извлекает первую найденную строку
                connection.close()

                count_user = str(name_folder_with_account[0])
                tdata_location = location_main_folder + '/work_accounts/' + count_user + '/tdata'  # место, где хранится аккаунт который будет отсылать сообщения

                try:
                    tdesk = TDesktop(tdata_location)
                except TFileNotFound:  # если папки с tdata нету
                    result = f"WARNING\nАккаунты закончились, скрипт прекратил работу!\n count_user = {count_user}"
                    return result

                client = await tdesk.ToTelethon(session=f"{ROOT_PROJECT_DIR}/Working_file/Telegram_file/work_accounts/{count_user}/script.session",
                                                flag=UseCurrentSession)
                await client.connect()  # вход в аккаунт
                break
            except (RuntimeError, OperationalError):
                print('при входе в аккаунт')
                if error_count > 10:
                    return 'WARNING'
                error_count += 1
                await asyncio.sleep(7)

    result_location = location_main_folder + f'//{txt_fail}.txt'
    file = open(result_location, 'w+')

    keep_searching = True # отображает надо ли продолжать поиск, (нет в том случае если число пользователей которых необходимо было найти достигнуто)
    result_user_list = []
    for chat in all_chat:  # проходится по всем чатам
        chat = str(chat)# chat это имя чата
        chat = chat[:-3]
        chat = chat[2:] # убираем три последних символа и два первых

        user_list = []
        user_names = []
        try:
            chat_proverca = await client.get_entity(chat)  # проверка на наличие такого чата
            if not chat_proverca.megagroup:  # если не является мегагруппой (чатом)
                connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
                cursor = connection.cursor()
                cursor.execute(f"DELETE FROM chat_list WHERE name_chat = ?", (chat,)) # удаление чата из БД
                connection.commit()
                connection.close()
                continue
            await client(GetParticipantsRequest(chat_proverca.id, ChannelParticipantsSearch(''), offset=0, limit=1,hash=0))  # выйдет ошибка если нету участников которые можно спарсить
            user_list = client.iter_participants(chat) # собираем всех участников чата
        except (errors.UsernameInvalidError, ValueError):
            connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
            cursor = connection.cursor()
            cursor.execute(f"DELETE FROM chat_list WHERE name_chat = ?", (chat,))  # удаление чата из БД
            connection.commit()
            connection.close()
            continue
        except (errors.ChatAdminRequiredError, errors.ChannelPrivateError):
            connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
            cursor = connection.cursor()
            cursor.execute(f"DELETE FROM chat_list WHERE name_chat = ?", (chat,))  # удаление чата из БД
            connection.commit()
            connection.close()
            continue
        except AttributeError:
            connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
            cursor = connection.cursor()
            cursor.execute(f"DELETE FROM chat_list WHERE name_chat = ?", (chat,))  # удаление чата из БД
            connection.commit()
            connection.close()
            continue
        except Exception:
            await client.disconnect()

            result = await error_handler()
            if isinstance(result, str):  # если вернулся str (такое будет если аккаунты закончатся)
                return result
            else:
                all_chat.append(chat)

                error_count = 0
                while True:  # если аккаунт с которого будем парсить будет использоваться(кто-то парсит с него) (тупо ждём)
                    try:  # Обязательно блок try должен быть такой т.к. пока пользователь ждёт освобождение аккаунта, то он может заблокировать и поменяться данные для входа
                        connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
                        cursor = connection.cursor()
                        cursor.execute(f"SELECT name_folder_with_account FROM parsing", )
                        name_folder_with_account = cursor.fetchone()  # Извлекает первую найденную строку
                        connection.close()

                        count_user = str(name_folder_with_account[0])
                        tdata_location = location_main_folder + '/work_accounts/' + count_user + '/tdata'  # место, где хранится аккаунт который будет отсылать сообщения

                        try:
                            tdesk = TDesktop(tdata_location)
                        except TFileNotFound:  # если папки с tdata нету
                            result = f"WARNING\nАккаунты закончились, скрипт прекратил работу!\n count_user = {count_user}"
                            return result

                        client = await tdesk.ToTelethon(
                            session=f"{ROOT_PROJECT_DIR}/Working_file/Telegram_file/work_accounts/{count_user}/script.session",
                            flag=UseCurrentSession)
                        await client.connect()  # вход в аккаунт
                        break
                    except (RuntimeError, OperationalError):
                        print('при входе в аккаунт')
                        if error_count > 10:
                            return 'WARNING'
                        error_count += 1
                        await asyncio.sleep(7)

        count_admin = 0
        count_iteration = 0
        async for user in user_list:
            count_iteration += 1
            try:
                if user.participant.admin_rights: # если нашли админа
                    count_admin += 1
            except AttributeError: # у обычных пользователей нет такой переменной, тогда выйдет эта ошибка
                pass
            if user_list.total == count_admin: # если кол-во админов совпадает с кол-во участников чата (значит закрыт список участников)
                connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
                cursor = connection.cursor()
                cursor.execute(f"DELETE FROM chat_list WHERE name_chat = ?", (chat,))  # удаление чата из БД
                connection.commit()
                connection.close()
            if count_iteration > 100: # если мы прошлись более 100 раз (не будет же в одном чате 100 админов)
                async for user in user_list:
                    if user.bot == False and not user.username == None:
                        user_names.append(user)
                break
        if filter:  # если необходимо применить фильтры
            if coming_in_filter:
                moscow_tz = ZoneInfo("Europe/Moscow")
                dat = datetime.now(moscow_tz) - timedelta(days=coming_in)

            if gender_filter:
                connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
                cursor = connection.cursor()

            for user in user_names:  # смысл цикла: проходится по каждому пользователю и проходит фильтры который накинул пользователь,
                try:  # если не удовлетворяет фильтру, то такому пользователю мы ставим add_user == False и не вписываем его в конечный текстовый файл
                    add_user = True  # отображает добавлять ли нам пользователя

                    if coming_in_filter == True and add_user == True:

                        dat2 = user.status.was_online
                        dat2 = dat2.replace(tzinfo=ZoneInfo("Europe/Moscow"))
                        # это проверить
                        if coming_in == 30:  # если применён фильтр (Заход более чем 30 дней назад)
                            if not dat > dat2:  # если заходил на аккаунт менее чем переданное значение
                                add_user = False
                        else:
                            if not dat < dat2:  # если заходил на аккаунт менее чем переданное значение
                                add_user = False
                        # это проверить
                    if gender_filter and add_user:
                        if use_language_rus_name:
                            cursor.execute(f"SELECT name FROM {gender + '_rus'} WHERE name = ?",(f"{user.first_name.lower()}",))  # % - wildcard для начала и конца строки
                            result_db = cursor.fetchall()
                        elif use_language_eng_name:
                            cursor.execute(f"SELECT name FROM {gender + '_eng'} WHERE name = ?",(f"{user.first_name.lower()}",))  # % - wildcard для начала и конца строки
                            result_db = cursor.fetchall()
                        else:
                            cursor.execute(f"SELECT name FROM {gender} WHERE name = ?",(f"{user.first_name.lower()}",))  # % - wildcard для начала и конца строки
                            result_db = cursor.fetchall()

                        if not result_db:  # если нету результата поиска
                            add_user = False

                    if premium_filter and add_user:
                        if not user.premium:
                            add_user = False

                    if photo_filter and add_user:
                        if not user.photo:
                            add_user = False

                    if phone_filter and add_user:
                        if not user.phone:
                            add_user = False

                    if add_user:
                        result_user_list.append(user.username)
                        countAttempt += 1
                        if len(result_user_list) > count_user_name - 1:
                            keep_searching = False
                            break
                except (AttributeError, TypeError):  # если нету даты захода
                    continue
            if gender_filter:
                connection.close()
        else:
            for user in user_names:
                if len(result_user_list) > count_user_name - 1:
                    keep_searching = False
                    break
                result_user_list.append(user.username)
                countAttempt += 1

        if not keep_searching:
            break

    await client.disconnect()

    users_list = list(set(result_user_list))
    for user in users_list:
        try:
            file.write('@' + str(user) + '\n')
            countSuccessful += 1
        except UnicodeEncodeError:
            continue
    file.close()

    result += f"\nСтатистика:\nУспешно найдено участников: {countSuccessful} из {countAttempt} просмотренных"
    if countAttempt > 0:
        if countSuccessful > 0:
            result = 'Парсинг прошёл успешно\n' + result
        else:
            result = 'С данными фильтрами не найдено пользователей\n' + result
    print(result + f'\nДля {txt_fail}')
    return result

async def main(all_chat: list, coming_in_filter=None, coming_in = 1, gender_filter=None, gender='None', premium_filter=None,
               photo_filter=None,phone_filter = None,use_language_rus_name = None,use_language_eng_name = None, filter = None, txt_fail = '1'):

    result = ''
    countSuccessful = 0  # счётчик успешных спарсинных участников
    countAttempt = 0  # счётчик кол-во исходных пользователей
    location_main_folder = ROOT_PROJECT_DIR + '/Working_file/Telegram_file'
    use_bot = False
    name_folder_with_account = ['0'] # [0] имя папки, где хранится аккаунт
    client = None
    count_user = 0

    if not filter:
        error_count = 0
        try:
            client = TelegramClient(location_main_folder+'/bot_session/bot_session.session', API_ID,API_HASH)
            await client.start()
            use_bot = True
        except (RuntimeError, OperationalError): # если вот уже производит парсинг будет эта ошибка
            if error_count > 15:
                return 'WARNING'
            error_count += 1
            await asyncio.sleep(7)
    else:
        error_count = 0
        while True:  # если аккаунт с которого будем парсить будет использоваться(кто-то парсит с него) (тупо ждём)
            try: # Обязательно блок try должен быть такой т.к. пока пользователь ждёт освобождение аккаунта, то он может заблокировать и поменяться данные для входа
                connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
                cursor = connection.cursor()
                cursor.execute(f"SELECT name_folder_with_account FROM parsing", )
                name_folder_with_account = cursor.fetchone()  # Извлекает первую найденную строку
                connection.close()

                count_user = str(name_folder_with_account[0])
                tdata_location = location_main_folder + '/work_accounts/' + count_user + '/tdata'  # место, где хранится аккаунт который будет отсылать сообщения

                try:
                    tdesk = TDesktop(tdata_location)
                except TFileNotFound:  # если папки с tdata нету
                    result = f"WARNING\nАккаунты закончились, скрипт прекратил работу!\n count_user = {count_user}"
                    return result

                client = await tdesk.ToTelethon(session=f"{ROOT_PROJECT_DIR}/Working_file/Telegram_file/work_accounts/{count_user}/script.session",
                                                flag=UseCurrentSession)
                await client.connect()  # вход в аккаунт
                break
            except (RuntimeError, OperationalError) as e:
                if error_count > 10:
                    return 'WARNING'
                error_count += 1
                await asyncio.sleep(7)

    result_location = location_main_folder + f'//{txt_fail}.txt'
    file = open(result_location, 'w+')

    user_names = []
    for chat in all_chat:  # проходится по всем чатам (chat это имя чата)

        user_list = []
        try:
            chat_proverca = await client.get_entity(chat)  # проверка на наличие такого чата

            if not chat_proverca.megagroup:  # если не является мегагруппой (чатом)
                result += f'"{chat}" это канал. Требуется чат.\n'
                continue

            # выйдет ошибка если нет участников которые можно спарсить
            await client(GetParticipantsRequest(chat_proverca.id, ChannelParticipantsSearch(''), offset=0, limit=1,hash=0))
            user_list = client.iter_participants(chat) # собираем всех участников чата
        except (errors.UsernameInvalidError, ValueError, AttributeError):
            result += f'Чат "{chat}" не найден.\n'
        except (errors.ChatAdminRequiredError, errors.ChannelPrivateError):
            result += f'Чат "{chat}" является приватным.\n'
        except Exception:
            await client.disconnect()

            result = await error_handler()
            if isinstance(result, str):  # если вернулся str (такое будет если аккаунты закончатся)
                return result
            else:
                all_chat.append(chat)

                error_count = 0
                while True:  # если аккаунт с которого будем парсить будет использоваться(кто-то парсит с него) (тупо ждём)
                    try:  # Обязательно блок try должен быть такой т.к. пока пользователь ждёт освобождение аккаунта, то он может заблокировать и поменяться данные для входа
                        connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
                        cursor = connection.cursor()
                        cursor.execute(f"SELECT name_folder_with_account FROM parsing", )
                        name_folder_with_account = cursor.fetchone()  # Извлекает первую найденную строку
                        connection.close()

                        count_user = str(name_folder_with_account[0])
                        tdata_location = location_main_folder + '/work_accounts/' + count_user + '/tdata'  # место, где хранится аккаунт который будет отсылать сообщения

                        try:
                            tdesk = TDesktop(tdata_location)
                        except TFileNotFound:  # если папки с tdata нету
                            result = f"WARNING\nАккаунты закончились, скрипт прекратил работу!\n count_user = {count_user}"
                            return result

                        client = await tdesk.ToTelethon(session= f"{ROOT_PROJECT_DIR}/Working_file/Telegram_file/work_accounts/{count_user}/script.session", flag=UseCurrentSession)
                        await client.connect()  # вход в аккаунт
                        break
                    except (RuntimeError, OperationalError):
                        if error_count > 10:
                            return 'WARNING'
                        error_count += 1
                        await asyncio.sleep(7)

        count_admin = 0
        count_iteration = 0
        async for user in user_list:
            count_iteration += 1
            try:
                if user.participant.admin_rights: # если нашли админа
                    count_admin += 1
            except AttributeError: # у обычных пользователей нет такой переменной, тогда выйдет эта ошибка
                pass
            if user_list.total == count_admin: # если кол-во админов совпадает с кол-во участников чата
                result += f'У чата "{chat}" закрыт список пользователей.\n'

            if count_iteration > 100: # если мы прошлись более 100 раз (не будет же в одном чате 100 админов)
                async for user in user_list:
                    countAttempt += 1
                    if user.bot == False and user.username:
                        user_names.append(user)
                break

    await client.disconnect()
    result_user_list = []

    if filter:  # если необходимо применить фильтры
        if coming_in_filter:
            moscow_tz = ZoneInfo("Europe/Moscow")
            dat = datetime.now(moscow_tz) - timedelta(days = coming_in)

        if gender_filter:
            connection = sqlite3.connect(ROOT_PROJECT_DIR + '/Working_file/data_base.sqlite3')
            cursor = connection.cursor()

        for user in user_names:  # смысл цикла: проходится по каждому пользователю и проходит фильтры который накинул пользователь,
            try:  # если не удовлетворяет фильтру, то такому пользователю мы ставим add_user == False и не вписываем его в конечный текстовый файл
                add_user = True  # отображает добавлять ли нам пользователя

                if coming_in_filter:

                    dat2 = user.status.was_online
                    dat2 = dat2.replace(tzinfo=ZoneInfo("Europe/Moscow"))

                    if coming_in == 30:  # если применён фильтр (Заход более чем 30 дней назад)
                        if not dat > dat2:  # если заходил на аккаунт менее чем переданное значение
                            add_user = False
                    else:
                        if not dat < dat2:  # если заходил на аккаунт менее чем переданное значение
                            add_user = False

                if gender_filter == True and add_user == True:

                    if use_language_rus_name:
                        cursor.execute(f"SELECT name FROM {gender + '_rus'} WHERE name = ?",(f"{user.first_name.lower()}",))  # % - wildcard для начала и конца строки
                        result_db = cursor.fetchall()
                    elif use_language_eng_name:
                        cursor.execute(f"SELECT name FROM {gender + '_eng'} WHERE name = ?",(f"{user.first_name.lower()}",))  # % - wildcard для начала и конца строки
                        result_db = cursor.fetchall()
                    else:
                        cursor.execute(f"SELECT name FROM {gender} WHERE name = ?", (f"{user.first_name.lower()}",))  # % - wildcard для начала и конца строки
                        result_db = cursor.fetchall()

                    if not result_db:  # если нету результата поиска
                        add_user = False

                if premium_filter == True and add_user == True:
                    if not user.premium:
                        add_user = False

                if photo_filter == True and add_user == True:
                    if not user.photo:
                        add_user = False

                if phone_filter == True and add_user == True:
                    if not user.phone:
                        add_user = False

                if add_user:
                    result_user_list.append(user.username)

            except (AttributeError, TypeError):  # если нету даты захода
                continue
        if gender_filter:
            connection.close()
    else:
        for user in user_names:
            result_user_list.append(user.username)

    if len(all_chat) == 1:
        for user in result_user_list:
            try:
                file.write('@' + str(user) + '\n')
                countSuccessful += 1
            except UnicodeEncodeError:
                continue
    else:
        users_list = list(set(result_user_list))
        for user in users_list:
            try:
                file.write('@' + str(user) + '\n')
                countSuccessful += 1
            except UnicodeEncodeError:
                continue
    file.close()

    result += f"\nСтатистика:\nУспешно найдено участников: {countSuccessful} из {countAttempt} возможных"
    if countAttempt > 0:
        if countSuccessful > 0:
            result = 'Парсинг прошёл успешно\n' + result
        else:
            result = 'Пользователи не найдены!\n' + result
    print(result + f'\nДля {txt_fail}')
    return result

# для теста
# all_chat = ['LSDqgTlJdlM5NDcy']
# asyncio.run(main(all_chat, filter= True,coming_in_filter= True, coming_in = 7))
# LSDqgTlJdlM5NDcy, buysellphones    с открытым списком
# stageused_market   с закрытым списком
# asyncio.run(search_by_available_chats( count_user_name = 100))