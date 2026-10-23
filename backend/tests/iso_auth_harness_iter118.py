"""TEST-ONLY iteration 118: REAL auth (no dependency override) on an ISOLATED DB.
Reuses iso_harness (handle re-bind to tejas_isolated_iter105_test, env untouched), then clears the X-Test-User
override so tejas.auth.current/staff/owner run for real. Synthetic staff users only (bcrypt hash of a random
test-only password generated per process; never written to the customer DB). No lifespan -> no seed_owner.
FRONTEND_URL / CORS_ORIGINS for variants are provided ONLY via the subprocess environment (load_dotenv does not override).
"""
import asyncio, secrets
import iso_harness as H
from tejas import auth

H.app.dependency_overrides.clear()
assert H.TEST_DB != H.REAL_DB and not H.leftover_real_handles(), H.leftover_real_handles()

OWNER_EMAIL = 'abhishekpushp07@gmail.com'
REVIEWER_EMAIL = 'test-reviewer-118@example.com'
OWNER_PW = 'T118-' + secrets.token_urlsafe(12)
REVIEWER_PW = 'T118-' + secrets.token_urlsafe(12)
OWNER_ID = '11800000-0000-4000-8000-000000000001'
REVIEWER_ID = '11800000-0000-4000-8000-000000000002'


async def seed():
    await H.tdbmod.client.drop_database(H.TEST_DB)
    await H.tdbmod.indexes()
    for uid_, email, pw, role in [(OWNER_ID, OWNER_EMAIL, OWNER_PW, 'owner'), (REVIEWER_ID, REVIEWER_EMAIL, REVIEWER_PW, 'reviewer')]:
        await H.TDB.tejas_users.insert_one({'id': uid_, 'email': email, 'name': 'TEST ' + role, 'role': role, 'exam': 'JEE Main',
                                            'access_type': 'staff_password', 'password_hash': auth.hashpw(pw), 'created_at': 0})


async def drop():
    await H.tdbmod.client.drop_database(H.TEST_DB)
