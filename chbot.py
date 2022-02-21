from telegram import Bot

# Здесь укажите токен, 
# который вы получили от @Botfather при создании бот-аккаунта
bot = Bot(token='5288168645:AAE8HpNnM99UMyk-GVlhDGxvu7LGfqOksWQ')
# Укажите id своего аккаунта в Telegram
chat_id = 101676827
text = 'Вам телеграмма!'
# Отправка сообщения
bot.send_message(chat_id, text) 