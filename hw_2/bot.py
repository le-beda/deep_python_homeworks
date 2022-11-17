import telebot
from telebot import types

TOKEN = '5441659286:AAEr-pvZ3PFaxH8tWsT07ewMzIZBtzkl8HQ'
bot = telebot.TeleBot(TOKEN)
banned = {}


@bot.message_handler(commands=['leave'])
def admins_message(message):
    if not (bot.get_chat_member(message.chat.id,
                                message.from_user.id).status in ['creator',
                                                                 'administrator']):
        bot.send_message(message.chat.id, "Не админы не могут прогонять бота")
    else:
        bot.send_message(message.chat.id, "Я ухожу")
        bot.leave_chat(message.chat.id)


@bot.message_handler(commands=['stats'])
def stats_message(message):
    admins = bot.get_chat_administrators(message.chat.id)
    members = bot.get_chat_members_count(message.chat.id)
    bot.send_message(message.chat.id, "Участников")
    bot.send_message(message.chat.id, "всего: " + str(members))
    bot.send_message(message.chat.id, "админов: " + str(len(admins)))


@bot.message_handler(content_types=["sticker"])
def ban_message(message):
    bot.send_message(message.chat.id, "СТИКЕРЫ ЗАПРЕЩЕНЫ!!!")
    if (bot.get_chat_member(message.chat.id, message.from_user.id).status in [
        'creator', 'administrator']):
        bot.send_message(message.chat.id, "Но админов не наказываем")
    else:
        if "@" + message.from_user.username in banned.keys():
            banned["@" + message.from_user.username][1] += 1
            bot.send_message(message.chat.id, "Еще *" + str(
                3 - banned["@" + message.from_user.username][
                    1]) + "* 🤔 и *бан*", parse_mode="markdown")
            if banned["@" + message.from_user.username][1] == 3:
                bot.send_message(message.chat.id,
                                 "Так что прощай навечно, @" + str(
                                     message.from_user.username))
                bot.ban_chat_member(message.chat.id, message.from_user.id)
        else:
            bot.send_message(message.chat.id, "Еще *2* 🤔 и *бан*",
                             parse_mode="markdown")
            banned["@" + message.from_user.username] = [message.from_user.id,
                                                        1]


@bot.message_handler(commands=['my_warnings'])
def warnings_message(message):
    if not ("@" + message.from_user.username in banned.keys()):
        bot.send_message(message.chat.id, "Нет предупреждений 🎉")
    else:
        bot.send_message(message.chat.id, "Предупреждений: " + str(
            banned["@" + message.from_user.username][1]))


from ast import arguments


@bot.message_handler(commands=['unban'])
def unban_message(message):
    to_be_unbanned = telebot.util.extract_arguments(message.text)
    if not (bot.get_chat_member(message.chat.id,
                                message.from_user.id).status in ['creator',
                                                                 'administrator']):
        bot.send_message(message.chat.id, "Не админы не могут снять бан")
    else:
        if to_be_unbanned and to_be_unbanned in banned.keys():
            bot.unban_chat_member(message.chat.id, banned[to_be_unbanned][0])
            bot.send_message(message.chat.id, "Вы прощены, " + to_be_unbanned)
            del banned[to_be_unbanned]
        else:
            bot.send_message(message.chat.id, "Пользователь не найден")


@bot.message_handler(content_types=["new_chat_members"])
def hello_question(message):
    bot.send_message(message.chat.id, "Новичкам привет!")
    bot.send_message(message.chat.id, "Как вам домашка по питону?")
    bot.send_message(message.chat.id,
                     "Узнать про функционал бота вы сможете с помощью команды */help*",
                     parse_mode="markdown")


@bot.message_handler(commands=['help'])
def help_message(message):
    bot.send_message(message.chat.id, "Для всех")
    bot.send_message(message.chat.id, '''Функционал бота: */help*
Статистика чата: */stats*
Попытаться стать админом: */can_i_be_admin*
Словить бан можно за посылку стикеров 😔
Посмотреть свои предупреждения: */my_warnings*''', parse_mode="markdown")
    bot.send_message(message.chat.id, "Для админов")
    bot.send_message(message.chat.id, '''Заставить бота уйти: */leave*
Разбанить пользователя: */unban @никнейм*''', parse_mode="markdown")


@bot.message_handler(commands=['can_i_be_admin'])
def can_i_be_admin_message(message):
    if bot.get_chat_member(message.chat.id, message.from_user.id).status in [
        'creator', 'administrator']:
        bot.send_message(message.chat.id,
                         "@" + str(message.from_user.username) + " уже админ")
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        item_1 = types.KeyboardButton("! Бот, разреши !")
        item_2 = types.KeyboardButton("! Бот, откажи !")
        markup.add(item_1, item_2)
        bot.send_message(message.chat.id, "Добавить @" + str(
            message.from_user.username) + " в админы?", reply_markup=markup)

        @bot.message_handler(content_types=["text"])
        def can_i_be_admin_answer(answer, tmp_id=message.from_user.id,
                                  tmp_name=message.from_user.username):
            if not (bot.get_chat_member(answer.chat.id,
                                        answer.from_user.id).status in [
                        'creator', 'administrator']):
                bot.send_message(answer.chat.id, "У @" + str(
                    answer.from_user.username) + " нет прав делать админом")
            else:
                if answer.text == "! Бот, разреши !":
                    bot.promote_chat_member(answer.chat.id, tmp_id, True)
                    bot.send_message(answer.chat.id, "@" + str(
                        tmp_name) + " теперь в команде админов!")
                elif answer.text == "! Бот, откажи !":
                    bot.send_message(answer.chat.id, "Отказано")

bot.polling(none_stop=True, interval=0)
