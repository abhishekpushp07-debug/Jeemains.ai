"""One-time NEET bank fork. Existing NEET source files are NEVER overwritten."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "backend" / "rapidfire"
TARGET = ROOT / "content" / "cards"

DIAGRAMS = {
    "heart": ("Body Fluids and Circulation", [
        ("Right atrium", "It receives deoxygenated blood from the venae cavae."),
        ("Right ventricle", "It pumps deoxygenated blood towards the lungs through the pulmonary artery."),
        ("Left atrium", "It receives oxygenated blood from the pulmonary veins."),
        ("Left ventricle", "Its thick muscular wall pumps oxygenated blood into the aorta."),
        ("Aorta", "The aorta carries oxygenated blood from the left ventricle to the body."),
        ("Pulmonary artery", "It carries deoxygenated blood from the right ventricle towards the lungs.")]),
    "nephron": ("Excretory Products and their Elimination", [
        ("Glomerulus", "The glomerulus is the capillary tuft inside Bowman's capsule, where ultrafiltration begins."),
        ("Bowman's capsule", "This cup-shaped structure surrounds the glomerulus and receives the filtrate."),
        ("Proximal convoluted tubule", "The PCT follows Bowman's capsule and reabsorbs most filtered nutrients, electrolytes and water."),
        ("Loop of Henle", "The hairpin-shaped loop has descending and ascending limbs."),
        ("Distal convoluted tubule", "The DCT follows the ascending limb and joins the collecting duct."),
        ("Collecting duct", "The collecting duct receives fluid from several nephrons and carries it towards the renal pelvis.")]),
    "flower": ("Morphology of Flowering Plants", [
        ("Stigma", "The stigma is the pollen-receptive tip of the pistil."),
        ("Style", "The style connects the stigma to the ovary."),
        ("Ovary", "The ovary is the swollen basal part of the pistil and encloses ovules."),
        ("Anther", "The anther is the pollen-producing part of the stamen."),
        ("Filament", "The filament is the stalk that supports the anther."),
        ("Sepal", "Sepals form the calyx, the outermost floral whorl, and protect the flower bud.")]),
}


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    templates = json.loads((ROOT / "content" / "diagrams.json").read_text())
    chapter_data = json.loads((SOURCE / "chapters.json").read_text())
    chapter_data.pop("Mathematics")
    chapter_data.update(json.loads((SOURCE / "neet_chapters.json").read_text()))
    if not (ROOT / "content" / "chapters.json").exists():
        write_json(ROOT / "content" / "chapters.json", chapter_data)
    created = 0
    for source in sorted((SOURCE / "cards").glob("*.json")):
        bank = json.loads(source.read_text())
        if not bank or bank[0]["subject"] not in chapter_data:
            continue
        target = TARGET / source.name
        if target.exists():
            continue
        for card in bank:
            original = card["id"]
            card.update({"exam": "NEET", "syllabus": "NEET UG", "source_card_id": original})
            if card["subject"] != "Biology":
                card["id"] = "neet-" + original
                card["provenance"] = "Independent copy of the curated shared Physics/Chemistry pilot bank; NEET-specific syllabus review pending."
        chapter = bank[0]["chapter"]
        for kind, (diagram_chapter, parts) in DIAGRAMS.items():
            if bank[0]["subject"] != "Biology" or chapter != diagram_chapter:
                continue
            removed, bank = bank[-6:], bank[:-6]
            write_json(ROOT / "archive" / (kind + "-replaced-text-cards.json"), removed)
            for i, (answer, explain) in enumerate(parts):
                letter = "ABCDEF"[i]
                distractors = [p[0] for j, p in enumerate(parts) if j != i][:3]
                answer_index = i % 4
                options = distractors[:]
                options.insert(answer_index, answer)
                bank.append({"id": f"neet-bio-diagram-{kind}-{letter.lower()}", "exam": "NEET", "subject": "Biology",
                             "chapter": chapter, "topic": f"{kind.title()} diagram identification", "syllabus": "NEET UG",
                             "prompt": f"Which part is marked {letter} in this {kind} diagram?", "formula": "",
                             "options": options, "answer": answer_index, "explain": f"{letter} is the {answer.lower()}. {explain}",
                             "review_status": "original_schematic_owner_review_pending", "seconds": 20,
                             "diagram": {"kind": kind, "target": letter, **templates[kind]},
                             "provenance": "Original vector schematic aligned with NCERT concepts, not a scanned NCERT illustration."})
        write_json(target, bank)
        created += len(bank)
    print(f"NEET source prepared: {created} cards written; existing files preserved.")


if __name__ == "__main__":
    main()