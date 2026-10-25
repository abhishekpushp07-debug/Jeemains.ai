"""Owner-only content export. No HTTP endpoint; learner data requires explicit private output."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT.parent


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n")


def refresh_references():
    refs = ["backend/exam_groups.py", "backend/revision.py", "backend/exam_migration.py",
            "backend/server.py", "backend/gamify.py", "backend/duels.py",
            "backend/rapidfire/generate_neet_bio.py", "backend/rapidfire/audit_cards.py",
            "backend/rapidfire/verify_cards.py", "frontend/src/components/BiologyDiagram.tsx"]
    for name in refs:
        source = APP / name
        if source.exists():
            target = ROOT / "integration" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    # Preserve rejected Biology content for audit/provenance, never for active play.
    for source in (APP / "backend" / "rapidfire" / "rejected").glob("biology__*.json"):
        target = ROOT / "archive" / "rejected" / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copyfile(source, target)


def export_content():
    refresh_references()
    cards = [card for path in sorted((ROOT / "content" / "cards").glob("*.json")) for card in json.loads(path.read_text())]
    if not cards or any(c.get("exam") != "NEET" for c in cards):
        raise ValueError("Only a non-empty NEET content bank may be exported.")
    if len({c["id"] for c in cards}) != len(cards):
        raise ValueError("Duplicate card IDs in the NEET source bank.")
    files = [p for folder in ("content", "archive", "tools", "integration") for p in (ROOT / folder).rglob("*")
             if p.is_file() and p.suffix in (".json", ".py", ".tsx", ".md") and "__pycache__" not in p.parts]
    files += [ROOT / "README.md", ROOT / "IMPORT_GUIDE.md"]
    manifest = {"schema_version": 1, "product": "NEETLIVE.AI", "exam": "NEET", "generated_at": datetime.now(timezone.utc).isoformat(),
                "card_count": len(cards), "subjects": dict(Counter(c["subject"] for c in cards)),
                "diagram_cards": sum(bool(c.get("diagram")) for c in cards), "includes_private_learner_data": False,
                "content_status": "Curated pilot content; owner/subject-expert review pending. Physics/Chemistry copied independently from the shared conceptual bank.",
                "files": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}}
    write_json(ROOT / "manifest.json", manifest)
    out = ROOT / "exports" / "neetlive-content.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files + [ROOT / "manifest.json"]:
            archive.write(path, "neetlive/" + str(path.relative_to(ROOT)))
    print(json.dumps({"bundle": str(out), "cards": manifest["card_count"], "subjects": manifest["subjects"], "diagram_cards": manifest["diagram_cards"], "bytes": out.stat().st_size}))


def export_private(output):
    from dotenv import load_dotenv
    from pymongo import MongoClient
    load_dotenv(APP / "backend" / ".env")
    target = Path(output).resolve()
    if target == APP or APP in target.parents:
        raise ValueError("Private exports must be outside the app repository and public content bundle.")
    target.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(target, 0o700)
    db = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    for name in ("rf_cards", "rf_sessions", "rf_duels", "rf_awards", "rf_learning_events"):
        path = target / (name + ".jsonl")
        with path.open("w") as out:
            for doc in db[name].find({"exam": "NEET"}, {"_id": 0}):
                if name == "rf_duels":
                    for player in doc.get("players", []):
                        player.pop("name", None)
                out.write(json.dumps(doc, default=str) + "\n")
        os.chmod(path, 0o600)
    path = target / "neet_profiles.jsonl"
    with path.open("w") as out:
        for doc in db.rf_profiles.find({"exam_stats.NEET": {"$exists": True}}, {"_id": 0, "uid": 1, "exam_stats.NEET": 1}):
            out.write(json.dumps({"uid": doc["uid"], "exam": "NEET", "stats": doc["exam_stats"]["NEET"]}) + "\n")
    os.chmod(path, 0o600)
    write_json(target / "private-manifest.json", {"exam": "NEET", "sensitive": True, "generated_at": datetime.now(timezone.utc).isoformat(),
                                               "note": "No authentication, contact data or shared wallet entitlements. Requires authorized migration and account mapping."})
    os.chmod(target / "private-manifest.json", 0o600)
    print("Private NEET records exported to protected owner-selected directory.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-output", help="Explicit authorized private migration directory OUTSIDE this repository")
    args = parser.parse_args()
    export_content()
    if args.private_output:
        export_private(args.private_output)