"""Set the owner password from backend/.env ADMIN_PASSWORD and end existing owner sessions."""
import asyncio, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / '.env', override=True)
from tejas.db import db, users
from tejas.auth import hashpw


async def main():
    email = os.environ['ADMIN_EMAIL'].lower()
    owner = await users.find_one({'email': email})
    await users.update_one({'id': owner['id']}, {'$set': {'password_hash': hashpw(os.environ['ADMIN_PASSWORD'])}})
    ended = await db.tejas_sessions.delete_many({'user_id': owner['id']})
    print('updated', email, 'sessions ended', ended.deleted_count)


asyncio.run(main())
