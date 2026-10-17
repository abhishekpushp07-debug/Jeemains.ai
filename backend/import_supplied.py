"""Idempotent private ingestion of owner's supplied fixtures. NEVER grants rights or approval."""

from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
import asyncio, hashlib
from tejas.db import sets, files, uid, now, audit
from tejas_storage import put_object
from tejas_core import build_questions, RULES


async def main():
    id = "tejas-paper-01"
    if await sets.find_one({"id": id}):
        print("Supplied paper already imported; preserving all reviewer work.")
        return
    refs = {}
    data = {}
    for kind in ["questions", "solutions"]:
        data[kind] = Path("/app/sources/" + kind + ".pdf").read_bytes()
        fid = uid()
        path = put_object(f"tejas/sources/{id}/{fid}.pdf", data[kind])
        f = {
            "id": fid,
            "set_id": id,
            "kind": kind,
            "path": path,
            "name": "Tejas200_Paper01_"
            + ("Questions" if kind == "questions" else "Key_Solutions")
            + ".pdf",
            "sha256": hashlib.sha256(data[kind]).hexdigest(),
            "pages": 11 if kind == "questions" else 32,
            "size": len(data[kind]),
            "created_at": now(),
        }
        await files.insert_one(f)
        refs[kind] = fid
    questions = build_questions(
        data["questions"], data["solutions"], refs["questions"], refs["solutions"], True
    )
    await sets.insert_one(
        {
            "id": id,
            "title": "Tejas 200 — Predicted Paper 01",
            "exam": "JEE Main",
            "year": "2027",
            "source": "Owner-supplied, nonofficial JEE Main practice mock for 2027. Not an official paper or prediction guarantee.",
            "attribution": "Tejas — owner-supplied paper; attribution subject to rights review",
            "status": "review",
            "version": 1,
            "revision": 1,
            "created_at": now(),
            "rules": RULES,
            "questions": questions,
            "file_ids": list(refs.values()),
            "rights_upload": False,
            "rights_publish": False,
            "rights_report": False,
            "audience": "all",
            "allowed_emails": [],
            "expires": "",
            "change_reason": "",
        }
    )
    await audit(
        "system",
        "Supplied sources privately ingested",
        id,
        "75 draft questions. Rights, answer correctness, source rendering, accessible descriptions and pairings require human approval.",
    )
    print(
        f"Imported {len(questions)} questions privately as unapproved drafts. No public release."
    )


if __name__ == "__main__":
    asyncio.run(main())
