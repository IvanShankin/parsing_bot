import os

TOKEN = '' # токен бота
CRYPTO_TOKEN = '' # токен у крипто бота
CHANNEL_URL = '' # ссылка на канал для необходимой подписки
SUPPORT_URL = '' # ссылка на поддержку
SUPPORT_ID = 123456789 # будут приходить сообщения если аккаунты закончились
ARR_ADMIN_ID = [123456789,123456789] # список админов
CHANNEL_NAME = '@Channel_name' # канал для проверки подписки

API_ID = 123456789 # данные бота
API_HASH = '' # данные бота

# заполнять ниже не надо!
project_dir = os.path.dirname(os.path.abspath(__file__))  # Путь к каталогу файла
parent_dir = os.path.dirname(project_dir)  # Получаем родительский каталог
ROOT_PROJECT_DIR = os.path.abspath(os.path.join(parent_dir, ".."))  # Путь к корню проекта
ROOT_PROJECT_DIR = ROOT_PROJECT_DIR + '/parser_bot'