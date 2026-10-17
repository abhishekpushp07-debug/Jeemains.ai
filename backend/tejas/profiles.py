"""Versioned exam profile contracts. Practice only until official-year evidence is approved."""

import hashlib, json
from fastapi import APIRouter, Depends, HTTPException
from .db import db, now
from .auth import staff

router = APIRouter(
    prefix="/api/studio/profiles", tags=["Immutable exam profile catalogue"]
)


def definition(s):
    r = s.get("rules", {})
    required = [
        "minutes",
        "correct",
        "wrong",
        "skipped",
        "navigation",
        "numeric_policy",
        "solution_release",
    ]
    if any(k not in r for k in required):
        raise HTTPException(
            400,
            "Exam profile is incomplete. Save explicit rules and navigation settings before starting.",
        )
    if (
        r["navigation"] != "free"
        or r["numeric_policy"] != "integer_exact"
        or r["solution_release"] != "after_submit"
    ):
        raise HTTPException(
            400,
            "This practice release supports free navigation, exact integers and post-submission solutions only. Official locked or bonus modes are not activated.",
        )
    if s.get("profile_mode", "practice") != "practice":
        raise HTTPException(
            400,
            "No official-year profile is approved. Use clearly labelled custom practice.",
        )
    sections = []
    for name in dict.fromkeys(
        q.get("section") or q.get("subject") for q in s.get("questions", [])
    ):
        qs = [
            q for q in s["questions"] if (q.get("section") or q.get("subject")) == name
        ]
        sections.append(
            {
                "name": name,
                "count": len(qs),
                "types": {
                    t: sum(q["type"] == t for q in qs) for t in ["mcq", "integer"]
                },
            }
        )
    return {
        "schema_version": 1,
        "exam": s["exam"],
        "year": s.get("year", ""),
        "mode": "practice",
        "release_status": "custom_practice_not_official",
        "sections": sections,
        "duration_minutes": r["minutes"],
        "scoring": {k: r[k] for k in ["correct", "wrong", "skipped"]},
        "navigation": r["navigation"],
        "numeric_policy": r["numeric_policy"],
        "solution_release": r["solution_release"],
        "question_types": sorted(set(q["type"] for q in s.get("questions", []))),
        "source_evidence": {
            "kind": "owner_supplied",
            "description": s.get("source", ""),
            "official_bulletin_url": None,
            "official_retrieved_at": None,
            "official_reviewer": None,
            "official_checksum": None,
            "disputed_fields": [],
            "approval_state": "not_an_official_profile",
        },
    }


async def seal_profile(s):
    profile = definition(s)
    raw = json.dumps(profile, sort_keys=True, separators=(",", ":")).encode()
    id = hashlib.sha256(raw).hexdigest()
    await db.tejas_profiles.update_one(
        {"_id": id},
        {"$setOnInsert": {"id": id, "definition": profile, "created_at": now()}},
        upsert=True,
    )
    return {"id": id, **profile}


@router.get("")
async def profiles(u=Depends(staff)):
    return (
        await db.tejas_profiles.find({}, {"_id": 0})
        .sort("created_at", -1)
        .limit(100)
        .to_list(100)
    )
