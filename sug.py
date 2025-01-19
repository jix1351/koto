#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
from typing import List, Union

import aiogram

from aiogram.utils.markdown import hlink
from aiogram.types import PhotoSize,video
from aiogram.dispatcher.handler import CancelHandler
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import MediaGroup
from info import *

from random import choice

"""
USER_ADMIN_ID
BOT_TOKEN 
CHANNEL_ID
"""
BY_LINK = hlink('by', 'https://t.me/nsfwkotobot')
executor = aiogram.executor
bot = aiogram.Bot(token=BOT_TOKEN)
dp = aiogram.Dispatcher(bot, storage=MemoryStorage())

yes_list = ['Отправлено! Это полный топ.','Отправлено!','Уже в канале!','Это лучшее, что я видел!','Тебе правда понравилось? Хорошо',
            'Тебе правда это понравилось? Отправлено..','Отправляю!','Відправляти!','Yeees.','']

no_list = ['Согласен, дурацкая картинка.','Удалено!','Удалено.','Согласен, какой-то ужас.','Нет — так нет...','Я бы не относился к такому рода контента на столько критично...',
           'Вот это сообщение удалить потом надо оно для теста чисто','В этих сообщениях нету пасхалок. Если что. А сообщение удалено.','Удалено.','Удалено.','Удалено.','Удалено.','Удалено.',
           'Удалено.','Удалено.','Удалено.','Удалено.','Парень, тебе бы передохнуть.','1101010 1101001 1111000']

# код взятый из стековерфлоу(гениальный)
class AlbumMiddleware(BaseMiddleware):
    """This middleware is for capturing media groups."""

    album_data:dict = {}

    def __init__(self, latency: Union[int, float] = 0.01):
        """
        You can provide custom latency to make sure
        albums are handled properly in highload.
        """
        self.latency = latency
        super().__init__()

    async def on_process_message(self, message: aiogram.types.Message, data: dict):
        if not message.media_group_id:
            return

        try:
            self.album_data[message.media_group_id].append(message)
            raise CancelHandler()  # закончить для этого группового элемента хендлер
        except KeyError:
            self.album_data[message.media_group_id] = [message]
            await asyncio.sleep(self.latency)

            message.conf["is_last"] = True
            data["album"] = self.album_data[message.media_group_id]

    async def on_post_process_message(self, message: aiogram.types.Message, result: dict, data: dict):
        """Clean up after handling our album."""
        if message.media_group_id and message.conf.get("is_last"):
            del self.album_data[message.media_group_id]


def update_banlist(name: str = None, action='add'):
    if name:
        with open('banlist.txt', 'a+') as banlist:
            banlist.write(name + '\n')
            banlist.seek(0)
    with open('banlist.txt', 'r') as banlist:
        banned_users = list(map(lambda x: int(x[:-1]), banlist.readlines()))
    return banned_users

banned_users = update_banlist()

@dp.message_handler(commands=['ban'],user_id=USER_ADMIN_ID)
async def ban(message):
    try:
        abuser_id = int(message.get_args())
    except (ValueError, TypeError):
        return await message.reply("Укажи ID пользователя.")
    update_banlist(str(abuser_id))
    banned_users.append(int(abuser_id))
    await message.reply(f"Пользователь {abuser_id} заблокирован.")
    # print(banned_users)


@dp.message_handler(commands=['start','help'])
async def start(data):
    """ Первый запуск бота"""
    user = data['from']['username'] if data['from']['username'] else data['from']['first_name']

    await data.answer(f"Привет {'@' if data['from']['username'] else ''}"+user+"\n"
                      "Я <b>бот-предложка</b> для канала @nsfwkoto."+"\n"
                      "Предложи свое фото, видео или гиф-файл:",parse_mode='HTML')


content_groups = {}

@dp.message_handler(is_media_group=True,content_types=['animation','photo','video'])
async def media_group_inputer(data, album):
    """

    Функция для ввода
      групп контента

    """
    if data['from']['id'] in banned_users:
        await data.answer('Вы в бане.')
        return True

    user_first_name = data['from']['first_name']

    media_group = MediaGroup()

    for obj in album:
        if obj.photo:
            file_id = obj.photo[-1].file_id
        else:
            file_id = obj[obj.content_type].file_id

        try:
            if len(media_group.to_python()) == 1:
                media_group.attach({"media": file_id, 
                                    "type": obj.content_type,                                    
                                    "caption": data.caption + f"\n{BY_LINK}: {user_first_name}" \
                                            if data.caption else f"{BY_LINK}: {user_first_name}", "parse_mode":"HTML"})
            else:
                media_group.attach({"media": file_id, "type": obj.content_type})

        except ValueError:
            return await data.answer("This type of album is not supported by aiogram.")

    choose = aiogram.types.InlineKeyboardMarkup(row_width=2)
    choose.add(aiogram.types.InlineKeyboardButton(text='[✔]Да',callback_data='yes_group'),aiogram.types.InlineKeyboardButton(text='[❌]Нет',callback_data='false_group'))

    content = await bot.send_media_group(USER_ADMIN_ID,media=media_group)


    content_groups[content[-1].media_group_id] = []
    for obj in content:
        if obj.photo:
            content_groups[content[-1].media_group_id].append((obj.photo[-1],obj.message_id,obj.caption))
        else:
            content_groups[content[-1].media_group_id].append((obj[obj.content_type],obj.message_id,obj.caption))

    yes_no = await bot.send_message(USER_ADMIN_ID,text='Выбор:',reply_markup=choose,reply_to_message_id=content[-1].message_id,parse_mode="HTML")


@dp.callback_query_handler(text='yes_group')
async def yes_group(callback):

    media_group = MediaGroup()
    media_id = callback.message.reply_to_message.media_group_id
    await bot.answer_callback_query(callback.id, text=choice(yes_list), show_alert=False)
    for obj in content_groups[media_id]:
        file_id = obj[0].file_id
        try:
            if(type(obj[0]) == PhotoSize):
                content_type = 'photo'
            else:
                content_type = 'video'
            if len(media_group.to_python()) == 1:
                caption = f"{obj[-1]}".split("\n")
                by_row = caption[-1]
                by_row = f"{BY_LINK}: "+by_row[3:]
                caption = "\n".join(caption[:-1])+"\n"+by_row
                media_group.attach({"media": file_id, "type": content_type,
                    "caption": f"{caption}", "parse_mode":"HTML"})
            else:
                media_group.attach({"media": file_id, "type": content_type})
        except ValueError:
            return await callback.message.answer("This type of album is not supported by aiogram.")

    content = await bot.send_media_group(CHANNEL_ID,media=media_group)
    for obj in content_groups[media_id]:
        await bot.delete_message(chat_id=USER_ADMIN_ID, message_id=obj[1])
    del content_groups[media_id]
    await bot.send_message(callback['from']['id'], text='Ваш пост был опубликован!')
    await callback.message.delete()

@dp.callback_query_handler(text='false_group')
async def no_group(callback):

    await bot.answer_callback_query(callback.id, text=choice(no_list), show_alert=False)
    media_id = callback.message.reply_to_message.media_group_id

    for obj in content_groups[media_id]:
        await bot.delete_message(chat_id=USER_ADMIN_ID, message_id=obj[1])
    del content_groups[media_id]
    await callback.message.delete()

@dp.message_handler(content_types=['animation','photo','video'])
async def inputer(data):
    """
    Функция для ввода контента
            по одному
    :param data:
    :return:
    """


    if data['from']['id'] in banned_users:
        await data.answer('Вы в бане.')
        return

    user = data['from']['first_name']
    choose = aiogram.types.InlineKeyboardMarkup(row_width=2)
    choose.add(aiogram.types.InlineKeyboardButton(text='[✔]Да', callback_data='yes'),
               aiogram.types.InlineKeyboardButton(text='[❌]Нет', callback_data='false'))
    if data.photo:
        await bot.send_photo(USER_ADMIN_ID,photo=data.photo[-1].file_id,
             caption=data.caption + f"\n{BY_LINK}: " + user if data.caption else f"{BY_LINK}: " + user,reply_markup=choose,parse_mode="HTML")
    else:
        await bot.send_animation(USER_ADMIN_ID,animation=data[data.content_type]['file_id'],
             caption=data.caption + f"\n{BY_LINK}: " + user if data.caption else f"{BY_LINK}: " + user, reply_markup=choose,parse_mode="HTML")


@dp.callback_query_handler(text='yes')
async def yes(callback):
    await bot.answer_callback_query(callback.id, text=choice(yes_list), show_alert=False)
    caption = callback.message.caption
    caption = caption.replace('by:',f"{BY_LINK}:")
    if callback.message.photo:
        # await bot.send_photo(CHANNEL_ID, photo=callback.message.photo[-1].file_id,caption=f'{BY_LINK}: '+callback.message.caption, parse_mode="HTML")
        await bot.send_photo(CHANNEL_ID, photo=callback.message.photo[-1].file_id,caption=caption, parse_mode="HTML")
        await bot.send_photo(callback['from']['id'], photo=callback.message.photo[-1].file_id,
                             caption='Ваш пост был опубликован!')
    else:
        await bot.send_animation(CHANNEL_ID, animation=callback.message[callback.message.content_type]['file_id'],caption=caption, parse_mode="HTML")
        await bot.send_animation(callback['from']['id'],
                                 animation=callback.message[callback.message.content_type]['file_id'],
                                 caption='Ваш пост был опубликован!')
    await callback.message.delete()

@dp.callback_query_handler(text='false')
async def no(callback):
    await bot.answer_callback_query(callback.id, text=choice(no_list), show_alert=False)
    if callback.message.reply_to_message:
        await callback.message.reply_to_message.delete()
        await callback.message.delete()
    else:
        await callback.message.delete()
