import asyncio
import aioschedule
from telebot.async_telebot import AsyncTeleBot, types

from data import storage

conn = storage.conn
cursor = storage.cursor

with open("secret.txt") as file:
    lines = [line.rstrip() for line in file]
    TOKEN = lines[0]

bot = AsyncTeleBot(TOKEN)

StartLocationID = 0
Radius = 10


# locations = cursor.execute(f'select LocationID, Xcoord, Ycoord from Locations').fetchall()
# for i in range(len(locations)):
#     for j in range(i + 1, len(locations)):
#         distance = ((locations[i][1] - locations[j][1])**2 + (locations[i][2] - locations[j][2])**2)**0.5
#         if distance < Radius:
#             cursor.execute(
#                 'INSERT INTO LocationsMoveOptions (ToID, FromID, Distance) VALUES (?, ?, ?)',
#                 (locations[i][0], locations[j][0], distance))
#             cursor.execute(
#                 'INSERT INTO LocationsMoveOptions (ToID, FromID, Distance) VALUES (?, ?, ?)',
#                 (locations[j][0], locations[i][0], distance))
#             conn.commit()


def db_add_person(UserID, Nickname, Level, HP, CurHP, Money, Attack, MagicAttack, XP, Armour, MagicArmour, LocationID):
    cursor.execute(
        'INSERT INTO Persons (UserID, Nickname, Level, HP, CurHP, Money, Attack, MagicAttack, XP, Armour, MagicArmour, LocationID) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (UserID, Nickname, Level, HP, CurHP, Money, Attack, MagicAttack, XP, Armour, MagicArmour, LocationID))
    conn.commit()


@bot.message_handler(commands=['start'])
async def send_start(message):
    await bot.reply_to(message, f"Хочешь... Сыграть в игру ? Жми /start_game !!")


@bot.message_handler(commands=['rules'])
async def send_rules(message):
    await bot.send_message(message.chat.id, f'''
1) Посмотреть свою статистику можно с помощью /stats
2) Посмотреть свой инвентарь можно с помощью /inventory
3) Посмотреть предметы, доступные для покупки в текущей локации /items_for_sale
4) Можно перемещаться на расстояние не больше {Radius} от текущего местоположения
5) Повысить уровень можно набрав 100XP
    ''')


@bot.message_handler(commands=['items_for_sale'])
async def send_sale(message):
    cur_loc_id = cursor.execute(
        f'select LocationID from Persons where UserID = \'{message.from_user.id}\' and NowMoving = 0').fetchone()
    if cur_loc_id is None:
        await bot.reply_to(message,
                           f"Текущее положение вашего игрока не определено, @{message.from_user.username} (либо игра с ним не инициализирована, либо он находится в пути)")
    else:
        loc_type = cursor.execute(
            f'select LocationType from Locations where LocationID = \'{cur_loc_id[0]}\'').fetchone()[0]
        if loc_type == "dungeon":
            await bot.reply_to(message, "В подземельях покупки недоступны")
        else:
            items_for_sale = cursor.execute(
                f'select ItemID from ItemsInCities where LocationID = \'{cur_loc_id[0]}\'').fetchall()
            await bot.reply_to(message, "В этом городе доступны товары с ID:" + ', '.join(
                map(lambda x: str(x[0]), items_for_sale)))


@bot.message_handler(commands=['see_possible_moves'])
async def send_possible_moves(message):
    cur_loc_id = cursor.execute(
        f'select LocationID from Persons where UserID = \'{message.from_user.id}\' and NowMoving = 0').fetchone()
    if cur_loc_id is None:
        await bot.reply_to(message,
                           f"Текущее положение вашего игрока не определено, @{message.from_user.username} (либо игра с ним не инициализирована, либо он находится в пути)")
    else:
        moves = cursor.execute(
            f'select ToID from LocationsMoveOptions where FromID = \'{cur_loc_id[0]}\'').fetchall()
        await bot.reply_to(message,
                           f"Из вашего местоположения(ID = {cur_loc_id[0]}) возможно добраться до мест с ID: {', '.join(map(lambda x: str(x[0]), moves))}")
        await bot.send_message(message.chat.id, f"Используйте комманду /move_to LocationID")


latest_finds = {}


def get_fight_markup():
    fight_markup = types.InlineKeyboardMarkup()
    magic_attack = types.InlineKeyboardButton(text="Магическая атака", callback_data="magic attack")
    attack = types.InlineKeyboardButton(text="Aтака", callback_data="regular attack")
    potion = types.InlineKeyboardButton(text="Выпить зелье", callback_data="drink potion")

    fight_markup.add(potion, attack, magic_attack)
    return fight_markup


@bot.callback_query_handler(func=lambda call: call.data.startswith('magic attack'))
async def answer_attack_type(call):
    if latest_finds[call.message.chat.id] > call.message.date:
        return

    await bot.edit_message_reply_markup(call.message.chat.id,
                                        call.message.id,
                                        reply_markup=None)
    await bot.edit_message_text('Магическая атака',
                                call.message.chat.id,
                                call.message.id)

    print(call.message.from_user.username, call.message.from_user.id)
    cur_loc_id = cursor.execute(
        f'select LocationID from Persons where UserID = \'{call.message.from_user.id}\'').fetchone()[0]
    print(cur_loc_id)

    cur_mob_id = cursor.execute(
        f'select MobIDForDungeons from Locations where LocationID = \'{cur_loc_id}\'').fetchone()[0]
    print(cur_mob_id)

    mob_hp, mob_attack_type = cursor.execute(
        f'select HP, AttackType from Mobs where MobID = \'{cur_mob_id}\'').fetchone()
    print(mob_hp, mob_attack_type)

    user_hp, user_magic_attack = cursor.execute(
        f'select HP, MagicAttack from Persons where UserID = \'{call.message.from_user.id}\'').fetchone()

    cursor.execute(
        f'UPDATE Mobs SET HP = {mob_hp - user_magic_attack} WHERE MobID = \'{cur_mob_id}\'')
    conn.commit()

    if mob_hp - user_magic_attack <= 0:
        await bot.send_message(chat_id=call.message.chat.id, text="Вы победили!!!")
        return

    if mob_attack_type == "magic":
        mob_attack = cursor.execute(
            f'select MagicAttack from Mobs where MobID = \'{cur_mob_id}\'').fetchone()[0]
    else:
        mob_attack = cursor.execute(
            f'select Attack from Mobs where MobID = \'{cur_mob_id}\'').fetchone()[0]

    cursor.execute(
        f'UPDATE Persons SET HP = {user_hp - mob_attack} WHERE UserID = \'{call.message.from_user.id}\'')
    conn.commit()
    await bot.send_message(chat_id=call.message.chat.id, text=f"Вас атаковали. HP стало {user_hp - mob_attack}")
    if mob_hp - user_magic_attack <= 0:
        await bot.send_message(chat_id=call.message.chat.id, text="Вы проиграли :(((((((")
        return

    markup = get_fight_markup()
    latest_finds[call.message.chat.id] = call.message.date
    await bot.send_message(chat_id=call.message.chat.id, text="Ваше здоровье позволяет продолжить схватку. Нападайте!",
                           reply_markup=markup)


@bot.message_handler(commands=['fight'])
async def send_fight(message):
    cur_loc_id = cursor.execute(
        f'select LocationID from Persons where UserID = \'{message.from_user.id}\' and NowMoving = 0').fetchone()
    if cur_loc_id is None:
        await bot.reply_to(message,
                           f"Текущее положение вашего игрока не определено, @{message.from_user.username} (либо игра с ним не инициализирована, либо он находится в пути)")
    else:
        loc_type = cursor.execute(
            f'select LocationType from Locations where LocationID = \'{cur_loc_id[0]}\'').fetchone()[0]
        if loc_type == "city":
            await bot.reply_to(message, "В городах не водятся монстры")
        else:
            cur_mob_id = cursor.execute(
                f'select MobIDForDungeons from Locations where LocationID = \'{cur_loc_id[0]}\'').fetchone()[0]
            mob = cursor.execute(f'select * from Mobs where MobID = \'{cur_mob_id}\'').fetchone()
            # print(mob, len(mob))
            await bot.reply_to(message,
                               f"В этом подземелье вас поджидает {mob[8]}\n(XP: {mob[2]}, HP: {mob[1]}, Attack: {mob[5]}, Armour {mob[6]})")
            level = cursor.execute(f'select Level from Persons where UserID = \'{message.from_user.id}\'').fetchone()[0]
            if level >= mob[3]:
                markup = get_fight_markup()

                latest_finds[message.chat.id] = message.date
                await bot.send_message(chat_id=message.chat.id, text="Ваш уровень позволяет начать схватку. Нападайте!",
                                       reply_markup=markup)
            else:
                await bot.send_message(message.chat.id, "Ваш уровень не позволяет начать схватку :(")


@bot.message_handler(commands=['all_items'])
async def send_items(message):
    items = cursor.execute(f'select ItemID, ItemName, ItemType, Cost from Items').fetchall()

    await bot.reply_to(message, '\n'.join(map(lambda x: f'({x[2]}) {x[1]}, ID = {x[0]}, цена: {x[3]}', items)))


@bot.message_handler(commands=['all_locations'])
async def send_locations(message):
    locations = cursor.execute(f'select LocationID, LocationName, LocationType from Locations').fetchall()

    await bot.reply_to(message, '\n'.join(map(lambda x: f'({x[2]}) {x[1]}, ID = {x[0]}', locations)))


@bot.message_handler(commands=['stats'])
async def send_stats(message):
    stats = cursor.execute(
        f'select Level, curHP, Attack, Armour from Persons where UserID = \'{message.from_user.id}\'').fetchone()
    if stats is None:
        await bot.reply_to(message,
                           f"Игра с ващим юзернеймом не инициализована @{message.from_user.username}")
    else:
        await bot.reply_to(message, f'''
Ваша статистика, @{message.from_user.username}
Уровень: {stats[0]}
Текущее здоровье: {stats[1]}
Атака: {stats[2]}
Защита: {stats[3]}
        ''')


@bot.message_handler(commands=['start_game'])
async def send_welcome(message):
    query = f'select UserID from Persons where UserID = \'{message.from_user.id}\''

    id_found = cursor.execute(query).fetchone()

    if id_found is None:
        db_add_person(UserID=message.from_user.id, Nickname=message.from_user.username, Level=0, HP=200, CurHP=200,
                      Money=1000, Attack=50, MagicAttack=70, XP=0, Armour=None, MagicArmour=None,
                      LocationID=StartLocationID)
        await bot.reply_to(message, f"Инициализирована новая игра с игроком {message.from_user.username}")
        await send_rules(message)
    else:
        await bot.reply_to(message, f"Игра с вашим юзернеймом уже инициирована, @{message.from_user.username}")


async def arrival_message(message, loc_id) -> None:
    await bot.send_message(message.chat.id, text=f'Игрок {message.from_user.username} прибыл!')
    aioschedule.clear(message.chat.id)

    cursor.execute(
        f'UPDATE Persons SET LocationID = \'{loc_id}\' WHERE UserID = \'{message.from_user.id}\'')
    cursor.execute(
        f'UPDATE Persons SET NowMoving = 0 WHERE UserID = \'{message.from_user.id}\'')
    conn.commit()


@bot.message_handler(commands=['move_to'])
async def send_move(message):
    cur_loc_id = cursor.execute(
        f'select LocationID from Persons where UserID = \'{message.from_user.id}\' and NowMoving = 0').fetchone()
    if cur_loc_id is None:
        await bot.reply_to(message,
                           f"Текущее положение вашего игрока не определено, @{message.from_user.username} (либо игра с ним не инициализирована, либо он находится в пути)")
    else:
        args = message.text.split()
        if len(args) == 2 and args[1].isdigit():
            desired_loc_id = cursor.execute(
                f'select LocationID from Locations where LocationID = \'{int(args[1])}\'').fetchone()
            if desired_loc_id is None:
                await bot.reply_to(message, f"Нет локации с таким ID")
            else:
                if desired_loc_id == cur_loc_id:
                    await bot.reply_to(message, f"Вы уже в {desired_loc_id[0]}")
                else:
                    distance = cursor.execute(
                        f'select Distance from LocationsMoveOptions where FromID = \'{cur_loc_id[0]}\' and ToID = \'{desired_loc_id[0]}\'').fetchone()
                    if distance is None:
                        await bot.reply_to(message, f"{desired_loc_id[0]} слишком далеко")
                    else:
                        await bot.reply_to(message,
                                           f"Игрок {message.from_user.username} начинает путь!")
                        sec = distance[0]
                        cursor.execute(f'UPDATE Persons SET NowMoving = 1 WHERE UserID = \'{message.from_user.id}\'')
                        conn.commit()
                        aioschedule.every(sec).seconds.do(arrival_message, message, desired_loc_id[0]).tag(
                            message.chat.id)


        else:
            await bot.reply_to(message, f"/move_to получил некорректный аргумент")


@bot.message_handler(commands=['end_game'])
async def send_goodbye(message):
    query = f'select UserID from Persons where UserID = \'{message.from_user.id}\''

    id_found = cursor.execute(query).fetchone()

    if id_found is None:
        await bot.reply_to(message, f"Игра с вашим юзернеймом еще не инициирована, @{message.from_user.username}")
    else:
        cursor.execute(f'DELETE FROM Persons WHERE UserID = \'{message.from_user.id}\'')
        conn.commit()
        await bot.reply_to(message, f"Игрок {message.from_user.username} закончил игру")


async def scheduler():
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def main():
    await bot.set_my_commands([
        types.BotCommand("/start", "starts the bot"),
        types.BotCommand("/rules", "shows game rules"),
        types.BotCommand("/start_game", "starts game with your username"),
        types.BotCommand("/all_locations", "shows all game locations"),
        types.BotCommand("/see_possible_moves", "shows IDs of locations you can move to"),
        types.BotCommand("/all_items", "shows all game items"),
        types.BotCommand("/items_for_sale", "shows IDs of items you can buy in current location"),
        types.BotCommand("/fight", "starts fight with monster in current location"),
        types.BotCommand("/end_game", "ends game with your username")
    ])
    await asyncio.gather(bot.infinity_polling(), scheduler())


if __name__ == '__main__':
    asyncio.run(main())
