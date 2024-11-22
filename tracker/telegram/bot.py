import asyncio
import logging
import os
import sys
from string import Template

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandObject, CommandStart
from aiogram.types.message import Message
from aiogram.utils.deep_linking import create_start_link
from aiogram.utils.keyboard import ReplyKeyboardBuilder, ReplyKeyboardMarkup
from dotenv import load_dotenv

from tracker import ISSUES_URL, PULLS_URL, get_issues_without_pull_requests
from tracker.utils import (
    create_telegram_user,
    get_all_repostitories,
    get_user,
    get_all_available_issues,
)

load_dotenv()

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

bot = Bot(
    token=os.environ.get("TELEGRAM_BOT_TOKEN", str()),
    default=DefaultBotProperties(parse_mode="HTML"),
)
dp = Dispatcher()


@dp.message(CommandStart(deep_link=True, deep_link_encoded=True))
async def auth_link_handler(message: Message, command: CommandObject) -> None:
    """
    deep link handler saving the uuid and tracked repos by this user into db
    :param message: aiogram.types.Message object
    :param command: aiogram.filters.CommandObject object
    :return: None
    """
    uuid = command.args
    user = await get_user(uuid)

    await create_telegram_user(
        user=next(iter(user)), telegram_id=str(message.from_user.id)
    )
    await message.answer(
        f"Hello {message.from_user.mention_html()}!\n"
        f"Would you like to check some issues?",
        reply_markup=main_button_markup(),
    )


@dp.message(CommandStart())
async def start_message(message: Message) -> None:
    """
    A function that starts the bot.
    :param message: Message that starts the bot.
    :return: None
    """
    await message.answer(
        f"Hello {message.from_user.mention_html()}!\n"
        f"Would you like to check some issues?",
        reply_markup=main_button_markup(),
    )


@dp.message(F.text == "📓get missed deadlines📓")
async def send_deprecated_issue_assignees(msg: Message) -> None:
    """
    Sends information about assignees that missed the deadline.
    :param msg: Message instance for communication with a user
    :return: None
    """
    all_repositories = await get_all_repostitories(msg.from_user.id)

    for repository in all_repositories:
        issues = get_issues_without_pull_requests(
            issues_url=ISSUES_URL.format(
                owner=repository.get("author", str()),
                repo=repository.get("name", str()),
            ),
            pull_requests_url=PULLS_URL.format(
                owner=repository.get("author", str()),
                repo=repository.get("name", str()),
            ),
        )
 
        for issue in issues:
            message_data = {
               "repo_author": repository.get("author", str()),
                "repo_name": repository.get("name", str()),
                "issue_title": issue.get("title", "No title provided."),
                "assignee_login": issue.get("assignee", {}).get("login", "Unknown"),
                "days_ago": str(issue.get("days", "Unknown"))
            }
        message_template= Template(
            """<b>Repository: ${repo_author}/${repo_name}</b>
            -----------------------------------
            Issue: ${issue_title}
            User: ${assignee_login}
            Assigned:
                        Days ago: ${days_ago} 
            -----------------------------------
            """
        )
        message = message_template.safe_substitute(message_data)

        if not issues:
            message += "No missed deadlines.\n"

        await msg.reply(f"<blockquote>{message}</blockquote>")


def escape_html(text: str) -> str:
    """
    Escapes HTML symbols in the text to ensure proper rendering in Telegram messages.

    :param text: The input string that may contain HTML symbols.
    :return: A string with HTML symbols escaped, replacing '&' with '&amp;', '<' with '&lt;',
             and '>' with '&gt;'.
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


@dp.message(F.text == "📖get available issues📖")
async def send_available_issues(msg: Message) -> None:
    """
    Sends all the available issues
    :param msg: Message instance for communication with a user
    :return: None
    """
    all_repositories = await get_all_repostitories(msg.from_user.id)

    for repository in all_repositories:
        issues = get_all_available_issues(
            ISSUES_URL.format(
                owner=repository.get("author", str()),
                repo=repository.get("name", str()),
            ),
        )

        for issue in issues:
            description = issue.get("body", "No description provided.")
            escaped_description = escape_html(description)

            message_data = {
                "repo_author": repository.get("author", str()),
                "repo_name": repository.get("name", str()),
                "issue_title": issue.get("title", "No title provided."),
                "assignee_login": issue.get("user", {}).get("login", "Unknown"),
                "description": description
            }
            issue_message_template = Template(
                """<b>Repository: ${repo_author}/${repo_name}</b>
                -----------------------------------
                Issue #${issue_title}
                Author: ${assignee_login}
                Description: <blockquote>${description}</blockquote>
                -----------------------------------"""
            )
        message = issue_message_template.safe_substitute(message_data)

        if not issues:
            message += "No available issues.\n"

        await msg.reply(message, parse_mode="HTML")


def main_button_markup() -> ReplyKeyboardMarkup:
    """
    A function that generates a button
    :return: ReplyKeyboardMarkup
    """
    builder = ReplyKeyboardBuilder()
    builder.button(text="📓get missed deadlines📓")
    builder.button(text="📖get available issues📖")

    return builder.as_markup(resize_keyboard=True)


async def create_tg_link(uuid) -> str:
    return await create_start_link(bot=bot, payload=uuid, encode=True)


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
