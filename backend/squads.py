"""Cheer Squads: the dancers who cheer for a champion in their Trophy Cabinet.
Every level opens with more Knockout Cup wins; any level can also be bought early with streak diamonds. A champion's
squad is the one they picked, else the best one they have, so more wins bring a more glamorous squad."""
import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import FileResponse
from pymongo import ReturnDocument

from gamify import vault_of

SQUADS = [
    {"id": "squad_rookie", "level": 1, "title": "Rookie Squad", "body": "Crimson, royal blue and white-gold. They dance for your first crown.", "wins": 1, "gems": None},
    {"id": "squad_gold", "level": 2, "title": "Golden Glam", "body": "Gold sequins, rhinestones and a sky full of fireworks.", "wins": 3, "gems": {"red": 8, "blue": 2}},
    {"id": "squad_royal", "level": 3, "title": "Royal Sapphire", "body": "Crystal-studded purple and silver, capes and tiaras.", "wins": 8, "gems": {"blue": 6, "emerald": 2}},
    {"id": "squad_legend", "level": 4, "title": "Kohinoor Legends", "body": "Diamond-studded white and rose-gold with crystal crowns. The whole stage sparkles.", "wins": 15, "gems": {"emerald": 3, "gold": 2}},
]
BY_ID = {s["id"]: s for s in SQUADS}
ART = Path(__file__).parent / "rf_art" / "squad"
ART_NAME = re.compile(r"^squad[2-4]_[abc][1-4]\.webp$")


def unlocked(p: dict) -> list:
    won, owned = p.get("cups_won", 0), set(p.get("owned") or [])
    return [s for s in SQUADS if won >= s["wins"] or s["id"] in owned]


def squad_of(p: dict) -> dict:
    """The squad that dances for this player: the one they picked if they still have it, else their best."""
    have = unlocked(p)
    pick = next((s for s in have if s["id"] == p.get("squad")), None) or (have[-1] if have else SQUADS[0])
    return {"id": pick["id"], "level": pick["level"], "title": pick["title"]}


def make_router(db, rf_user):
    r = APIRouter(prefix="/rf")

    async def state(uid):
        p = await db.rf_profiles.find_one({"uid": uid}) or {}
        have, owned, won = {s["id"] for s in unlocked(p)}, set(p.get("owned") or []), p.get("cups_won", 0)
        return {"items": [{**s, "unlocked": s["id"] in have, "bought": s["id"] in owned, "need": max(0, s["wins"] - won)} for s in SQUADS],
                "equipped": squad_of(p)["id"], "cups_won": won, "diamonds": vault_of(p)}

    @r.get("/squads")
    async def squads(x_rf_user: Optional[str] = Header(None)):
        return await state(rf_user(x_rf_user))

    @r.post("/squads/buy")
    async def buy(data: dict, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        s = BY_ID.get(str(data.get("id")))
        if not s or not s["gems"]:
            raise HTTPException(404, "This squad is not for sale.")
        gems = s["gems"]
        got = await db.rf_profiles.find_one_and_update(
            {"uid": uid, "owned": {"$ne": s["id"]}, "cups_won": {"$not": {"$gte": s["wins"]}}, **{f"diamonds.{c}": {"$gte": n} for c, n in gems.items()}},
            {"$inc": {k: v for c, n in gems.items() for k, v in ((f"diamonds.{c}", -n), (f"diamonds_spent.{c}", n))}, "$addToSet": {"owned": s["id"]}, "$set": {"squad": s["id"]}},
            return_document=ReturnDocument.AFTER)
        if not got:
            have = await db.rf_profiles.find_one({"uid": uid}) or {}
            if s["id"] in (have.get("owned") or []):
                raise HTTPException(409, "You already have this squad.")
            if have.get("cups_won", 0) >= s["wins"]:  # opened by cup wins: never charge diamonds for it
                raise HTTPException(409, "Your cup wins already opened this squad. Tap USE to pick it.")
            wallet = vault_of(have)
            short = ", ".join(f"{n - wallet.get(c, 0)} more {c.title()}" for c, n in gems.items() if wallet.get(c, 0) < n)
            raise HTTPException(409, f"Not enough diamonds. You need {short}. Win them in cups and Phoenix streaks.")
        return await state(uid)

    @r.post("/squads/equip")
    async def equip(data: dict, x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        s = BY_ID.get(str(data.get("id")))
        p = await db.rf_profiles.find_one({"uid": uid}) or {}
        if not s or s not in unlocked(p):
            raise HTTPException(409, "Win more cups or buy this squad with diamonds first.")
        await db.rf_profiles.update_one({"uid": uid}, {"$set": {"squad": s["id"]}})
        return await state(uid)

    @r.get("/art/{name}")
    async def art(name: str):
        """Squad levels 2-4 are downloaded when first needed, so they never add to the app's size. So is the 30-second
        "Dream Unlocked" cheer track the Kohinoor Legends dance to (made by rapidfire/make_dream_cheer.py)."""
        if name == "dream_cheer.m4a":
            return FileResponse(ART.parent / "sound" / name, media_type="audio/mp4", headers={"Cache-Control": "public, max-age=31536000, immutable"})
        if not ART_NAME.match(name) or not (ART / name).is_file():
            raise HTTPException(404, "Not found.")
        return FileResponse(ART / name, media_type="image/webp", headers={"Cache-Control": "public, max-age=31536000, immutable"})

    return r
