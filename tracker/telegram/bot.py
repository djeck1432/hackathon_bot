import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.types.message import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder, ReplyKeyboardMarkup
from dotenv import load_dotenv

from tracker import ISSUES_URL, PULLS_URL, get_issues_without_pull_requests
from tracker.telegram.db.crud import DBConnector

load_dotenv()

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

bot = Bot(
    token=os.environ.get("TELEGRAM_BOT_TOKEN", str()),
    default=DefaultBotProperties(parse_mode="HTML"),
)
dp = Dispatcher()
DB = DBConnector()


@dp.message(CommandStart())
async def start_message(message: Message) -> None:
    """
    A function that starts the bot.
    :param message: Message that starts the bot.
    :return: None
    """
    await message.answer(
        f"Hello {message.from_user.mention_html()}!\n"
        f"would you like to check some issues?",
        reply_markup=issue_button(),
    )


@dp.message(F.text == "📓get missed deadlines📓")
async def send_deprecated_issue_assignees(msg: Message) -> None:
    """
    Sends information about assignees that missed the deadline.
    :param msg: Message instance for communication with a user
    :return: None
    """
    all_pull_requests = DB.get_all_repositories()

    for repository in all_pull_requests:
        issues = get_issues_without_pull_requests(
            issues_url=ISSUES_URL.format(owner=repository.author, repo=repository.name),
            pull_requests_url=PULLS_URL.format(
                owner=repository.author, repo=repository.name
            ),
        )

        message = (
            "=" * 50
            + "\n"
            + f"Repository: {repository.author}/{repository.name}"
            + "\n"
            + "=" * 50
            + "\n\n"
        )

        for issue in issues:
            message += (
                "-----------------------------------\n"
                "Issue: " + issue.get("title", str()) + "\n"
                "User: " + issue.get("assignee", dict()).get("login", str()) + "\n"
                "Assigned:" + "\n"
                "\t\t\t\tDays ago: " + str(issue["days"]) + "\n"
                "-----------------------------------\n"
            )

        if not issues:
            message += "No missed deadlines."

        await msg.answer(f"<blockquote>{message}</blockquote>")


def issue_button() -> ReplyKeyboardMarkup:
    """
    A function that generates a button that allows the user to click on issues.
    :return: ReplyKeyboardMarkup
    """
    builder = ReplyKeyboardBuilder()
    builder.button(text="📓get missed deadlines📓")

    return builder.as_markup(resize_keyboard=True)


async def start_tg_bot() -> None:
    """
    A function that starts the bot.
    :return: None
    """
    try:
        await dp.start_polling(bot, polling_timeout=0)

    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(start_tg_bot())
