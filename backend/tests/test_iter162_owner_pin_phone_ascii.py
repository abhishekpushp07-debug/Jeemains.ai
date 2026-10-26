"""TEST-ONLY iteration 162: OwnerPinResetPayload ASCII-only phone pattern (non-ASCII digits -> 422, no mutation,
no secret echo) + ASCII 0/91/+91/space formats and legacy v0 still reset. Reuses iter161 isolated harness/fixture.
Run (foreground, own process): cd /app/backend/tests && python -m pytest test_iter162_owner_pin_phone_ascii.py -n0 -q -s
"""
import uuid
from test_iter161_owner_pin_reset_isolated import (  # noqa: F401  (isolated = autouse module fixture)
    isolated, run, student, staff_client, body, pin, prof, fresh_clock, num, OWNER, OWNER_PW, URL, TDB, J)

TR = {'devanagari': '०१२३४५६७८९', 'arabic_indic': '٠١٢٣٤٥٦٧٨٩', 'fullwidth': '０１２３４５６７８９', 'bengali': '০১২৩৪৫৬৭৮৯'}


# ---- non-ASCII phone digits rejected 422 without mutation / secret echo ----
def test_non_ascii_phone_digits_rejected():
    async def go():
        fresh_clock()
        _, ph, p, sid = await student()
        o = await staff_client(OWNER, OWNER_PW)
        np = pin(p)
        for name, digits in TR.items():
            t = str.maketrans('0123456789', digits)
            for variant in (ph.translate(t), '+91' + ph.translate(t), '+91 ' + ph[:5] + ph[5:].translate(t),
                            ph[:-1] + ph[-1].translate(t)):
                r = await o.post(URL, json=body(variant, np, 1))
                assert r.status_code == 422, (name, r.status_code, r.text)
                assert np not in r.text and '"input"' not in r.text and 'pin_hash' not in r.text, r.text
        q = await prof(sid)
        assert q['pin_version'] == 1 and 'pin_reset_by' not in q
        await o.aclose()
    run(go())


# ---- ASCII formats 0 / 91 / +91 / spaced all still reset sequentially ----
def test_ascii_formats_still_reset():
    async def go():
        fresh_clock()
        _, ph, p, sid = await student()
        o = await staff_client(OWNER, OWNER_PW)
        v = 1
        for fmt in ('0' + ph, '91' + ph, '+91' + ph, '+91 ' + ph[:5] + ' ' + ph[5:], ph):
            np = pin()
            r = await o.post(URL, json=body(fmt, np, v))
            assert r.status_code == 200, (fmt, r.text)
            assert J(r)['pin_version'] == v + 1 and J(r)['student_id'] == sid
            v += 1
        assert (await prof(sid))['pin_version'] == v
        await o.aclose()
    run(go())


# ---- legacy v0 profile (no pin) still resettable with expected version 0 ----
def test_legacy_v0_reset():
    async def go():
        fresh_clock()
        sid, ph = str(uuid.uuid4()), num()
        await TDB.tejas_phone_profiles.insert_one({'_id': sid, 'id': sid, 'phone': '+91' + ph, 'name': 'TEST legacy', 'created_at': 1.0})
        o = await staff_client(OWNER, OWNER_PW)
        r = await o.post(URL, json=body(ph, pin(), 0))
        assert r.status_code == 200, r.text
        assert J(r)['pin_version'] == 1 and J(r)['student_id'] == sid
        await o.aclose()
    run(go())
