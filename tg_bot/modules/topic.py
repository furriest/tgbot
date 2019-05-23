from typing import Optional

from telegram import Message, Update, Bot, User
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import BadRequest
from telegram.ext import CommandHandler, run_async, Filters
from telegram.utils.helpers import escape_markdown

import tg_bot.modules.sql.rules_sql as sql
from tg_bot import dispatcher
from tg_bot.modules.helper_funcs.string_handling import markdown_parser


@run_async
def get_topic(bot: Bot, update: Update):
    chat_id = update.effective_chat.id
    send_topic(update, chat_id)


# Do not async - not from a handler
def send_topic(update, chat_id):
    bot = dispatcher.bot
    user = update.effective_user  # type: Optional[User]
    try:
        chat = bot.get_chat(chat_id)
    except BadRequest as excp:
        if excp.message == "Chat not found":
            bot.send_message(user.id, "The topic shortcut for this chat hasn't been set properly! Ask admins to "
                                      "fix this.")
            return
        else:
            raise

    topic = sql.get_rules(chat_id)
    text = "*{}* topic:\n\n{}".format(escape_markdown(chat.title), topic)

    if topic:
        update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    else:
        update.effective_message.reply_text("The group haven't any topic yet.")


@run_async
def set_topic(bot: Bot, update: Update):
    chat_id = update.effective_chat.id
    msg = update.effective_message  # type: Optional[Message]
    raw_text = msg.text
    args = raw_text.split(None, 1)  # use python's maxsplit to separate cmd and args
    if len(args) == 2:
        txt = args[1]
        offset = len(txt) - len(raw_text)  # set correct offset relative to command
        markdown_topic = markdown_parser(txt, entities=msg.parse_entities(), offset=offset)

        sql.set_rules(chat_id, markdown_topic)
        update.effective_message.reply_text("Topic updated.")


@run_async
def clear_topic(bot: Bot, update: Update):
    chat_id = update.effective_chat.id
    sql.set_rules(chat_id, "")
    update.effective_message.reply_text("Successfully cleared topic!")


def __stats__():
    return "{} chats have topic set.".format(sql.num_chats())


def __import_data__(chat_id, data):
    # set chat topic
    topic = data.get('info', {}).get('topic', "")
    sql.set_rules(chat_id, topic)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return "This chat has had it's topic set: `{}`".format(bool(sql.get_topic(chat_id)))


__help__ = """
 - /topic: get the topic for this chat.
 - /settopic <your topic here>: set the topic for this chat.
 - /cleartopic: clear the topic for this chat.
"""

__mod_name__ = "topic"

GET_RULES_HANDLER = CommandHandler("topic", get_topic, filters=Filters.group)
SET_RULES_HANDLER = CommandHandler("settopic", set_topic, filters=Filters.group)
RESET_RULES_HANDLER = CommandHandler("cleartopic", clear_topic, filters=Filters.group)

dispatcher.add_handler(GET_RULES_HANDLER)
dispatcher.add_handler(SET_RULES_HANDLER)
dispatcher.add_handler(RESET_RULES_HANDLER)
