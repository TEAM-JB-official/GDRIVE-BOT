import pickle
import threading
from sqlalchemy import Column, BigInteger, LargeBinary
from bot.helpers.sql_helper import BASE, SESSION


class gDriveCreds(BASE):
    __tablename__ = "gDrive"

    chat_id = Column(BigInteger, primary_key=True)
    credential_string = Column(LargeBinary)

    def __init__(self, chat_id):
        self.chat_id = chat_id


gDriveCreds.__table__.create(checkfirst=True)

INSERTION_LOCK = threading.RLock()


def _set(chat_id, credential_string):
    with INSERTION_LOCK:
        saved = SESSION.query(gDriveCreds).get(chat_id)

        if not saved:
            saved = gDriveCreds(chat_id)

        saved.credential_string = pickle.dumps(credential_string)

        SESSION.add(saved)
        SESSION.commit()


def search(chat_id):
    with INSERTION_LOCK:
        saved = SESSION.query(gDriveCreds).get(chat_id)

        if not saved:
            return None

        try:
            return pickle.loads(saved.credential_string)
        except Exception:
            return None


def _clear(chat_id):
    with INSERTION_LOCK:
        saved = SESSION.query(gDriveCreds).get(chat_id)

        if saved:
            SESSION.delete(saved)
            SESSION.commit()
