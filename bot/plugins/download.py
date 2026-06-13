import os
from pyrogram import Client, filters
from bot.helpers.sql_helper import gDriveDB, idsDB
from bot.helpers.utils import CustomFilters, humanbytes
from bot.helpers.downloader import download_file, utube_dl
from bot.helpers.gdrive_utils import GoogleDrive
from bot import DOWNLOAD_DIRECTORY, LOGGER
from bot.config import Messages, BotCommands
from pyrogram.errors import RPCError


# ---------------- DOWNLOAD LINK HANDLER ---------------- #

@Client.on_message(
    filters.private &
    filters.incoming &
    filters.text &
    (filters.command(BotCommands.Download) | filters.regex(r'^(ht|f)tp')) &
    CustomFilters.auth_users
)
def _download(client, message):

    user_id = message.from_user.id

    if message.media:
        return

    sent_message = message.reply_text("🕵️ Checking link...", quote=True)

    try:
        link = message.command[1] if message.command else message.text
        link = link.strip()

        # Google Drive clone
        if "drive.google.com" in link:
            sent_message.edit(Messages.CLONING.format(link))
            LOGGER.info(f'Copy:{user_id}: {link}')

            msg = GoogleDrive(user_id).clone(link)
            sent_message.edit(msg)
            return

        # Normal download
        if "|" in link:
            link, filename = link.split("|", 1)
            link = link.strip()
            filename = filename.strip()
            dl_path = os.path.join(DOWNLOAD_DIRECTORY, filename)
        else:
            link = link.strip()
            filename = os.path.basename(link)
            dl_path = DOWNLOAD_DIRECTORY

        LOGGER.info(f'Download:{user_id}: {link}')

        sent_message.edit(Messages.DOWNLOADING.format(link))

        result, file_path = download_file(link, dl_path)

        if result:

            sent_message.edit(
                Messages.DOWNLOADED_SUCCESSFULLY.format(
                    os.path.basename(file_path),
                    humanbytes(os.path.getsize(file_path))
                )
            )

            msg = GoogleDrive(user_id).upload_file(file_path)

            sent_message.edit(msg)

            LOGGER.info(f'Deleting: {file_path}')
            os.remove(file_path)

        else:
            sent_message.edit(Messages.DOWNLOAD_ERROR.format(file_path, link))

    except Exception as e:
        sent_message.edit(f"❌ ERROR: `{e}`")


# ---------------- TELEGRAM FILE UPLOAD ---------------- #

@Client.on_message(
    filters.private &
    filters.incoming &
    (filters.document | filters.audio | filters.video | filters.photo) &
    CustomFilters.auth_users
)
def _telegram_file(client, message):

    user_id = message.from_user.id
    sent_message = message.reply_text("🕵️ Checking File...", quote=True)

    file_path = None

    try:

        if message.document:
            file = message.document

        elif message.video:
            file = message.video

        elif message.audio:
            file = message.audio

        elif message.photo:
            file = message.photo  # highest quality

            file.file_name = f"IMG-{user_id}-{message.id}.jpg"
            file.mime_type = "image/jpeg"

        else:
            sent_message.edit("❌ Unsupported file type")
            return

        sent_message.edit(
            Messages.DOWNLOAD_TG_FILE.format(
                file.file_name,
                humanbytes(file.file_size),
                file.mime_type
            )
        )

        LOGGER.info(f'Download:{user_id}: {file.file_id}')

        file_path = message.download(file_name=DOWNLOAD_DIRECTORY)

        sent_message.edit(
            Messages.DOWNLOADED_SUCCESSFULLY.format(
                os.path.basename(file_path),
                humanbytes(os.path.getsize(file_path))
            )
        )

        msg = GoogleDrive(user_id).upload_file(file_path, file.mime_type)

        sent_message.edit(msg)

        LOGGER.info(f'Deleting: {file_path}')
        os.remove(file_path)

    except RPCError:
        sent_message.edit(Messages.WENT_WRONG)

    except Exception as e:
        sent_message.edit(f"❌ ERROR: `{e}`")

        if file_path and os.path.exists(file_path):
            os.remove(file_path)


# ---------------- YOUTUBE DOWNLOADER ---------------- #

@Client.on_message(
    filters.incoming &
    filters.private &
    filters.command(BotCommands.YtDl) &
    CustomFilters.auth_users
)
def _ytdl(client, message):

    user_id = message.from_user.id

    if len(message.command) < 2:
        message.reply_text(Messages.PROVIDE_YTDL_LINK, quote=True)
        return

    try:

        sent_message = message.reply_text("🕵️ Checking Link...", quote=True)

        link = message.command[1]
        LOGGER.info(f'YTDL:{user_id}: {link}')

        sent_message.edit(Messages.DOWNLOADING.format(link))

        result, file_path = utube_dl(link)

        if result:

            sent_message.edit(
                Messages.DOWNLOADED_SUCCESSFULLY.format(
                    os.path.basename(file_path),
                    humanbytes(os.path.getsize(file_path))
                )
            )

            msg = GoogleDrive(user_id).upload_file(file_path)

            sent_message.edit(msg)

            LOGGER.info(f'Deleting: {file_path}')
            os.remove(file_path)

        else:
            sent_message.edit(Messages.DOWNLOAD_ERROR.format(file_path, link))

    except Exception as e:
        sent_message.edit(f"❌ ERROR: `{e}`")
