import time

from common.Store import store
import common.VK.Convert as Converter
from common.VK.VKWrappers import make_upload_docs, make_upload_photo, make_reply
import common.Logger as Logger


import traceback

from objdict import ObjDict
import os
import sys
import asyncio
import shlex
from utils import load_config

class Yui:

    def __init__(self):
        self.store = store
        self.ver = "0.1.5 beta"

        Logger.Ylog(f"> Привет, я Yui! Бот для социальной сети ВК.\n> На данный момент моя версия: {self.ver}")
        load_config()
        self.call_init()

    def call_init(self):
        plugin_folder_files = os.listdir("plugins")
        if not plugin_folder_files:
            Logger.Elog("Не было найдено плагинов! Создайте хоть один плагин")
            exit()

        sys.path.insert(0, "plugins")
        for file in plugin_folder_files:
            if file.endswith(".py"):
                try:
                    a  = __import__(os.path.splitext(file)[0], None, None, [''])
                    Logger.Slog(f"Юи загрузила плагин {file}")
                except Exception as err:
                    print(err)
                    traceback.print_exc()
        return True

    def say_goodbye(self):
        Logger.Ylog("Пока семпай, надеюсь ещё встретимся!")

    async def process_update(self, update):
        updated_message = await Converter.convert_to_message(update)

        await asyncio.sleep(0.1)

        command = None
        for (k, v) in store.handlers.items():
            print(k)
            print(updated_message.text)
            if updated_message.text.startswith(k):
                command = k
                break

        args = None
        if command:
            args = shlex.split(updated_message.text[len(command):].strip())

            if self.store.config.NeedLogMessage:
                Logger.Slog(
                    f"Пришла команда {command} с аргументами {args} из { f'ЛС {updated_message.peer_id}' if not updated_message.is_multichat else f'Беседы #{updated_message.chat_id}' }")

        ts = int(time.time())

        if updated_message.from_id in self.store.cd_users:
            if ts - self.store.cd_users[updated_message.from_id]['message_date'] <= self.store.config.CoolDownDelay:
                self.store.cd_users[updated_message.from_id]['message_date'] = ts
                return True

            self.store.cd_users[updated_message.from_id]['message_date'] = ts
        else:
            self.store.cd_users[updated_message.from_id] = {}
            self.store.cd_users[updated_message.from_id]['message_date'] = ts

        currentStore = ObjDict()
        currentStore.reply = make_reply(self.store, updated_message.peer_id, currentStore)
        currentStore.upload_photo = make_upload_photo(self.store, updated_message.peer_id)
        currentStore.upload_doc = make_upload_docs(self.store, updated_message.peer_id)
        currentStore.request = self.store.wrappers.request
        if command:
            currentStore.cmd = command
            currentStore.args = args

        if await self.store.call_before_events(updated_message, currentStore):
            return True

        if command:
            await self.store.call_command(updated_message, currentStore)

        if await self.store.call_after_events(updated_message, currentStore):
            return True