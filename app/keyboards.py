from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# это для нескольких кнопок в сообщение от бота
from app.config import CHANNEL_URL
from app.config import SUPPORT_URL

main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔍 Бесплатный парсинг', callback_data='parsing')],
    [InlineKeyboardButton(text='🔥 Premium Функции', callback_data="premium_features")],
    [InlineKeyboardButton(text='💎 Оформить premium', callback_data="Apply_premium",)],
    [InlineKeyboardButton(text='⚙️ Поддержка', url= SUPPORT_URL,), InlineKeyboardButton(text='ℹ️ FAQ', callback_data="F.A.Q",)],
    [InlineKeyboardButton(text='🆕 Проверить уникальность', callback_data="checking_uniqueness")] # тут название можно поменять
])

main_admin = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔍 Бесплатный парсинг', callback_data='parsing')],
    [InlineKeyboardButton(text='🔥 Premium Функции', callback_data="premium_features")],
    [InlineKeyboardButton(text='💎 Оформить premium', callback_data="Apply_premium",)],
    [InlineKeyboardButton(text='⚙️ Поддержка', url= SUPPORT_URL,), InlineKeyboardButton(text='ℹ️ FAQ', callback_data="F.A.Q",)],
    [InlineKeyboardButton(text='🆕 Проверить уникальность', callback_data="checking_uniqueness")], # тут название можно поменять
    [InlineKeyboardButton(text='🛠️ Панель админа', callback_data="admin_panel",)],
])

admin_panel = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Добавить premium ✅', callback_data='add_premium')],
    [InlineKeyboardButton(text='❌ Убрать premium ❌', callback_data='delete_premium')],
    [InlineKeyboardButton(text='📊 Статистика', callback_data="statistics")],
    [InlineKeyboardButton(text='◀ Назад', callback_data="Back",)]
])

back_in_admin_panel = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='◀ Назад', callback_data="admin_panel")]
])

premium_fun = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='▶ Перейти к парсингу', callback_data='input_chat')],
    [InlineKeyboardButton(text='🕓 По времени захода', callback_data='coming_in_filter')],
    [InlineKeyboardButton(text='🗃️ Использовать БД', callback_data="use_db",)],
    [InlineKeyboardButton(text='📱 По наличию открытого номера', callback_data="phone_filter",)],
    [InlineKeyboardButton(text='💎 По tg premium', callback_data="Apply_premium_filter", ), InlineKeyboardButton(text='🖼️ По наличию фото', callback_data="photo_filter",)],
    [InlineKeyboardButton(text='🗑️ Очистить выбор', callback_data="clear_filter",),InlineKeyboardButton(text='◀ Назад', callback_data="Back",)]
])

coming_in_filter = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='24 часа', callback_data='timeInDays_1'),InlineKeyboardButton(text='3 дня', callback_data="timeInDays_3")],
    [InlineKeyboardButton(text='7 дней', callback_data="timeInDays_7",),InlineKeyboardButton(text='14 дней', callback_data="timeInDays_14",)],
    [InlineKeyboardButton(text='Заход более чем 30 дней назад', callback_data="timeInDays_30",)],
    [InlineKeyboardButton(text='🗑️ Очистить выбор', callback_data="clear_coming_in_filter",),InlineKeyboardButton(text='◀ Назад', callback_data="premium_features",)]
])

# это дописать
db_filter = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🧔🏻 По муж. полу', callback_data="genderFilter_man"),InlineKeyboardButton(text='👩 По жен. полу', callback_data="genderFilter_woman")],
    [InlineKeyboardButton(text='🇷🇺 На русское языке', callback_data="use_only_rus_name", )],
    [InlineKeyboardButton(text='🇬🇧 На английском языке', callback_data="use_only_eng_name", )],
    [InlineKeyboardButton(text='🗑️ Очистить выбор', callback_data="clear_db_filter",),InlineKeyboardButton(text='◀ Назад', callback_data="premium_features",)]
])

not_enough_rights = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='💎 Оформить premium', callback_data='Apply_premium')],
    [InlineKeyboardButton(text='◀ Назад', callback_data="premium_features")]
])

check_subscription = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Канал бота',url=CHANNEL_URL)],
    [InlineKeyboardButton(text='✅ Проверить подписку ✅',callback_data='check_subscription')],
    [InlineKeyboardButton(text='◀ Назад', callback_data="Back")]
])

prise = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='100 за 1 час', callback_data='pay_100')],
    [InlineKeyboardButton(text='200 за 1 день', callback_data="pay_200")],
    [InlineKeyboardButton(text='300 за 5 дней', callback_data='pay_300')],
    [InlineKeyboardButton(text='450 за 15 дней', callback_data='pay_450')],
    [InlineKeyboardButton(text='600 за 30 дней', callback_data='pay_600')],
    [InlineKeyboardButton(text='1000 навсегда', callback_data="pay_1000")],
    [InlineKeyboardButton(text='◀ Назад', callback_data='Back')]
])

pay_metod = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🤖 CryptoBot', callback_data='crypro_bot_pay')],
    [InlineKeyboardButton(text='◀ Назад', callback_data='Apply_premium')]
])

currency = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='USDT', callback_data='cryproBotPay_USDT')],
    [InlineKeyboardButton(text='BTC', callback_data='cryproBotPay_BTC')],
    [InlineKeyboardButton(text='TON', callback_data='cryproBotPay_TON')],
    [InlineKeyboardButton(text='GRAM', callback_data='cryproBotPay_GRAM')],
    [InlineKeyboardButton(text='NOT', callback_data='cryproBotPay_NOT')],
    [InlineKeyboardButton(text='LTC', callback_data='cryproBotPay_LTC')],
    [InlineKeyboardButton(text='ETH', callback_data='cryproBotPay_ETH')],
    [InlineKeyboardButton(text='◀ Назад', callback_data='Apply_premium')]
])

back_in_filter = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Спарсить по имеющимся чатам', callback_data="existing_chats")],
    [InlineKeyboardButton(text='◀ Назад', callback_data="premium_features")]
])

back_in_filter2 =InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='◀ Назад', callback_data='premium_features')]])

back = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='◀ Назад', callback_data='Back')]])

to_the_main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='◀ В главное меню', callback_data='Back')]])

pay_cryptoBot = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Проверить оплату ✅', callback_data='check_pay')],
    [InlineKeyboardButton(text='❌  Отменить оплату  ❌', callback_data='cancellation_pay')],
    [InlineKeyboardButton(text='◀ Назад', callback_data='Back')]])


