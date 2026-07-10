import asyncio
import logging
import time
from collections import defaultdict

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, ChatPermissions

TOKEN = "8886975015:AAE3oLLUmxmVu7F7PNYTWFz3cGSC7iPLg_A"

OWNER_ID = 1932871668

logging.basicConfig(level=logging.INFO)

bot = Bot(TOKEN)
dp = Dispatcher()

# ---------------- НАСТРОЙКИ ----------------

SPAM_LIMIT = 5
SPAM_SECONDS = 10
WARN_LIMIT = 1
MUTE_TIME = 3600

# -------------------------------------------

user_messages = defaultdict(list)
user_warns = defaultdict(int)


async def mute(chat_id, user_id):
    await bot.restrict_chat_member(
        chat_id=chat_id,
        user_id=user_id,
        permissions=ChatPermissions(can_send_messages=False),
        until_date=int(time.time()) + MUTE_TIME
    )


@dp.message()
async def anti_spam(message: Message):

    if message.chat.type == "private":
        return

    member = await bot.get_chat_member(
        message.chat.id,
        message.from_user.id
    )

    if member.status in ("administrator", "creator"):
        return

    now = time.time()

    user_messages[message.from_user.id].append(now)

    user_messages[message.from_user.id] = [
        x for x in user_messages[message.from_user.id]
        if now - x <= SPAM_SECONDS
    ]

    if len(user_messages[message.from_user.id]) >= SPAM_LIMIT:

        user_warns[message.from_user.id] += 1

        if user_warns[message.from_user.id] <= WARN_LIMIT:

            await message.reply(
                f"⚠️ {message.from_user.full_name}\n\n"
                "Перестань спамить!\n"
                "Следующее нарушение = мут на 1 час."
            )

        else:

            await mute(message.chat.id, message.from_user.id)

            await message.reply(
                f"🔇 {message.from_user.full_name} получил мут на 1 час за спам."
            )

            user_warns[message.from_user.id] = 0
            user_messages[message.from_user.id].clear()


@dp.message(Command("warn"))
async def warn(message: Message):

    if message.from_user.id != OWNER_ID:
        return

    if not message.reply_to_message:
        await message.answer("Ответь на сообщение пользователя.")
        return

    uid = message.reply_to_message.from_user.id

    user_warns[uid] += 1

    await message.answer(
        f"⚠️ Предупреждение выдано.\n"
        f"Всего предупреждений: {user_warns[uid]}"
    )


@dp.message(Command("mute"))
async def cmd_mute(message: Message):

    if message.from_user.id != OWNER_ID:
        return

    if not message.reply_to_message:
        await message.answer("Ответьте на сообщение.")
        return

    uid = message.reply_to_message.from_user.id

    await mute(message.chat.id, uid)

    await message.answer("🔇 Пользователь получил мут на 1 час.")


@dp.message(Command("unmute"))
async def unmute(message: Message):

    if message.from_user.id != OWNER_ID:
        return

    if not message.reply_to_message:
        await message.answer("Ответьте на сообщение.")
        return

    uid = message.reply_to_message.from_user.id

    await bot.restrict_chat_member(
        message.chat.id,
        uid,
        permissions=ChatPermissions(
            can_send_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
    )

    await message.answer("✅ Мут снят.")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
