import datetime

from vkbottle.bot import Blueprint
from vkbottle.bot import Message

from utils.database import Database
from utils.bot import UserBot
from data.config import Tokens, Main


bp = Blueprint()
db = Database('data/db.db')
user = UserBot(token=Tokens.user)


@bp.on.private_message(text=['Начать', 'начать'])
async def start_handler_def(message: Message):
    result = db.get_user_or_none(message.from_id)

    print(result)

    if result is None:
        user_info = await user.api.users.get(user_ids=[message.from_id], fields=["relation", "sex", "bdate", "city"])
        user_info = user_info[0]

        bdate = True if user_info.bdate else False
        sex = True if user_info.sex else False
        city = True if user_info.city else False
        family_status = True if user_info.relation == 6 else False

        try:
            bdate_datetime = datetime.datetime.strptime(user_info.bdate, "%d.%m.%Y")
            age = (datetime.datetime.now() - bdate_datetime).days // 365

        except Exception as ex:
            bdate = False

        if bdate and sex and city and family_status:
            sex = user_info.sex
            city = user_info.city.id
            family_status = user_info.relation

            db.register(
                uid=message.from_id,
                sex=sex,
                age=age,
                city=city
            )

            await message.answer(
                message="Успешно Вас зарегистрировали. Напишите мне 'Поиск', чтобы начать подбор кандидатов"
            )

        else:
            message_text = f'''Ваш профиль не полностью заполнено

Дата рождения - {"не заполнено или не виден год" if not bdate else "заполнено"}
Пол - {"не заполнено" if not sex else "заполнено"}
Город - {"не заполнено" if not city else "заполнено"}
Семейный статус - {"не заполнено или не стоит 'В активном поиске'" if not family_status else "заполнено"}

Заполните профиль и напишите мне "Начать"'''

            await message.answer(
                message=message_text
            )
    else:
        await message.answer(
            message="Напишите мне 'Поиск', чтобы начать подбор кандидатов"
        )


@bp.on.private_message(text=['Поиск', 'поиск'])
async def search_handler_def(message: Message):
    data = db.get_user_or_none(message.from_id)

    if data is None:
        await message.answer(
            message="Вы не зарегистрированы, напишите 'Начать' и попробуйте потом снова"
        )

    else:

        await message.answer(
            message='Начинаю поиск. Ожидайте'
        )

        result = await user.find_pair(
            count=Main.count,
            offset=Main.offset,
            city=data[3],
            sex=data[1],
            age=data[2],
            uid=message.from_id
        )

        Main.offset += Main.count + 1

        while len(result) == 0:
            result = await user.find_pair(
                count=Main.count,
                offset=Main.offset,
                city=data[3],
                sex=data[1],
                age=data[2],
                uid=message.from_id
            )

            Main.offset += Main.count + 1

        for person in result:
            photos = await user.get_photo(
                uid=person.get('uid')
            )

            photo_string = ''

            for photo in photos:
                photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'

            await message.answer(
                message=f'''Имя - {person['name']}
                    
ссылка - vk.com/id{person["uid"]}''',
                    attachment=photo_string
                )

            db.add_seen(
                uid=message.from_id,
                person=person.get('uid')
            )


@bp.on.private_message()
async def default_handler_def(message: Message):
    await message.answer(
        message="Неизвестная команда, напишите мне 'Начать'"
    )