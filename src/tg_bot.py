from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import Message
from aiogram.filters import Command
from typing import Optional

from agent import ReactAgent


class SearchBot:
    def __init__(self, token: str , agent: ReactAgent, proxy: Optional[str] = None):
        self._agent = agent
        self._proxy = proxy
        self._token = token
        self._session = None
        self._bot = None
        self._dp = Dispatcher()
        self._register_handlers()

    def _create_session(self) -> AiohttpSession:
        """Создает сессию для aiogram с поддержкой прокси"""
        if self._proxy:
            return AiohttpSession(
                proxy=self._proxy
            )
        else:
            return AiohttpSession()

    def _register_handlers(self):
        self._dp.message.register(self.cmd_start, Command("start"))
        self._dp.message.register(self.answer_message)


    async def cmd_start(self, message: Message):
        user_name = message.from_user.first_name or "пользователь"
        await message.answer(
            f"👋 Привет, {user_name}!\n"
            f"Введи свой поисковый запрос."
        )


    async def answer_message(self, message: Message):
        try:
            if message.text:
                if message.from_user.id == 1014593137:
                    answer_text = self._agent.invoke(message.text)
                    await message.answer(answer_text, parse_mode="Markdown")
                else:
                    await message.answer("Я не отвечаю на сообщения посторонних людей")
        except Exception as e:
            await message.answer("❌ Произошла ошибка при обработке сообщения")

    async def _init_bot(self):
        if self._session is None:
            self._session = self._create_session()
            self._bot = Bot(token=self._token, session=self._session)

    async def start(self, skip_updates: bool = True):
        try:
            await self._init_bot()
            if skip_updates:
                await self._bot.delete_webhook(drop_pending_updates=True)
            await self._dp.start_polling(self._bot)
        except Exception as e:
            raise

    async def stop(self):
        await self._bot.session.close()
        if self._session:
            await self._session.close()