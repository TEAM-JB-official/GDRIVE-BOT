import re
from httplib2 import Http
from bot import LOGGER, G_DRIVE_CLIENT_ID, G_DRIVE_CLIENT_SECRET
from bot.config import Messages, BotCommands
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from oauth2client.client import OAuth2WebServerFlow, FlowExchangeError
from bot.helpers.sql_helper import gDriveDB
from bot.helpers.utils import CustomFilters

OAUTH_SCOPE = "https://www.googleapis.com/auth/drive"
REDIRECT_URI = "http://localhost:8080/"

# 🔥 SAFE FLOW STORAGE (multi-user safe)
flow_store = {}


@Client.on_message(filters.private & filters.incoming & filters.command(BotCommands.Authorize))
async def _auth(client, message):

    user_id = message.from_user.id

    creds = gDriveDB.search(user_id)

    if creds is not None:
        try:
            creds.refresh(Http())
            gDriveDB._set(user_id, creds)
            await message.reply_text(Messages.ALREADY_AUTH, quote=True)
        except Exception as e:
            await message.reply_text(f"**ERROR REFRESHING:** `{e}`")
        return

    try:
        flow = OAuth2WebServerFlow(
            G_DRIVE_CLIENT_ID,
            G_DRIVE_CLIENT_SECRET,
            OAUTH_SCOPE,
            redirect_uri=REDIRECT_URI,
            response_type='code',
            access_type='offline',
            prompt='consent'
        )

        auth_url = flow.step1_get_authorize_url()

        # store flow per user
        flow_store[user_id] = flow

        LOGGER.info(f'AuthURL generated for {user_id}')

        await message.reply_text(
            text=Messages.AUTH_TEXT.format(auth_url),
            quote=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Authorize Google Drive", url=auth_url)]]
            )
        )

    except Exception as e:
        await message.reply_text(f"**ERROR:** ```{e}```", quote=True)


@Client.on_message(filters.private & filters.incoming & filters.command(BotCommands.Revoke) & CustomFilters.auth_users)
def _revoke(client, message):

    user_id = message.from_user.id

    try:
        gDriveDB._clear(user_id)
        LOGGER.info(f'Revoked: {user_id}')
        message.reply_text(Messages.REVOKED, quote=True)

    except Exception as e:
        message.reply_text(f"**ERROR:** ```{e}```", quote=True)


@Client.on_message(filters.private & filters.incoming & filters.text & ~CustomFilters.auth_users)
async def _token(client, message):

    user_id = message.from_user.id

    match = re.search(r"[?&]code=([^&]+)", message.text)

    if not match:
        return

    code = match.group(1)

    flow = flow_store.get(user_id)

    if not flow:
        await message.reply_text(Messages.FLOW_IS_NONE, quote=True)
        return

    try:
        sent_message = await message.reply_text("🕵️ Checking received code...", quote=True)

        creds = flow.step2_exchange(code)

        gDriveDB._set(user_id, creds)

        LOGGER.info(f'AuthSuccess: {user_id}')

        await sent_message.edit_text(Messages.AUTH_SUCCESSFULLY)

        # clear flow after success
        flow_store.pop(user_id, None)

    except FlowExchangeError:
        await sent_message.edit_text(Messages.INVALID_AUTH_CODE)

    except Exception as e:
        await sent_message.edit_text(f"**ERROR:** ```{e}```")
