"""Source-aware, review-only PDF segmentation, deterministic scoring and complete reports."""

import re, uuid, math
import fitz
import numpy as np

RULES = {
    "minutes": 180,
    "correct": 4,
    "wrong": -1,
    "skipped": 0,
    "navigation": "free",
    "numeric_policy": "integer_exact",
    "solution_release": "after_submit",
    "numeric_rule": "Exact integer value; signs and leading zeros accepted; up to 20 digits. No rounding.",
}


def validate_pdf(data):
    if len(data) > 50 * 1024 * 1024:
        raise ValueError("PDF exceeds 50 MB. Split it into smaller documents.")
    if not data.startswith(b"%PDF-"):
        raise ValueError("Upload a valid PDF file, not a renamed document.")
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception:
        raise ValueError(
            "This PDF is damaged or cannot be read. Export a new unlocked PDF."
        )
    if doc.is_encrypted:
        raise ValueError(
            "Password-protected PDFs are not supported. Supply an unlocked copy."
        )
    if not 1 <= len(doc) <= 300:
        raise ValueError("PDF must contain 1–300 pages. Split larger documents.")
    if any(p.rect.width > 3000 or p.rect.height > 3000 for p in doc):
        raise ValueError(
            "PDF page dimensions are too large. Export standard-size pages."
        )
    return doc


def segment_pdf(data, solution=False):
    doc = validate_pdf(data)
    anchors, sections, barriers = [], [], []
    current_subject = ""
    for pi, page in enumerate(doc):
        pix = page.get_pixmap(colorspace=fitz.csGRAY)
        pixels = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width
        )
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                text = "".join(s["text"] for s in line["spans"]).strip()
                if re.search(r"(SECTION|SOLUTIONS)", text) and re.match(
                    r"(MATHEMATICS|PHYSICS|CHEMISTRY)", text
                ):
                    current_subject = text.split(" ")[0].title()
                    sections.append((pi, line["bbox"][1]))
                if line["bbox"][1] >= 40 and (
                    ("ANSWER KEY" in text.upper() and len(text) < 100)
                    or text.upper()
                    in ["DETAILED SOLUTIONS", "KEY AND SOLUTIONS", "SOLUTIONS"]
                ):
                    barriers.append(
                        {
                            "page": pi,
                            "top": 48 if line["bbox"][1] < 200 else line["bbox"][1] - 4,
                        }
                    )
                m = re.match(r"^Q\s*(\d+)\.\s*(.*)", text)
                if not m:
                    continue
                is_solution = bool(re.match(r"Answer\s*:", m[2], re.I))
                y = line["bbox"][1]
                # Find full-width whitespace above the stem; preserves elevated integrals and determinants.
                top = max(40, int(y) - 2)
                for row in range(int(y), max(39, int(y) - 36), -1):
                    if np.min(pixels[row, 40 : min(pix.width - 35, 560)]) > 245:
                        top = max(40, row - 2)
                        break
                barriers.append({"page": pi, "top": top})
                if solution != is_solution:
                    continue
                anchors.append(
                    {
                        "number": int(m[1]),
                        "page": pi,
                        "top": top,
                        "header": text,
                        "subject": current_subject,
                    }
                )
    records = []
    for idx, a in enumerate(anchors):
        end = (
            anchors[idx + 1]
            if idx + 1 < len(anchors)
            else {"page": len(doc) - 1, "top": doc[-1].rect.height - 48}
        )
        cutoffs = [
            b
            for b in barriers + [{"page": p, "top": y - 8} for p, y in sections]
            if (a["page"], a["top"])
            < (b["page"], b["top"])
            <= (end["page"], end["top"])
        ]
        if cutoffs:
            end = min(cutoffs, key=lambda b: (b["page"], b["top"]))
        refs = []
        texts = []
        for pi in range(a["page"], end["page"] + 1):
            page = doc[pi]
            top = a["top"] if pi == a["page"] else 48
            bottom = end["top"] - 1 if pi == end["page"] else page.rect.height - 48
            for sp, sy in sections:
                if sp == pi and top < sy < bottom:
                    bottom = sy - 8
            if bottom <= top + 2:
                continue
            clip = fitz.Rect(40, top, page.rect.width - 38, bottom)
            pix = page.get_pixmap(clip=clip, colorspace=fitz.csGRAY)
            ar = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.height, pix.width
            )
            rows = np.where(np.min(ar, axis=1) < 230)[0]
            if len(rows) == 0:
                continue
            clip.y1 = min(clip.y1, top + int(rows[-1]) + 5)
            refs.append({"page": pi + 1, "rect": [round(v, 2) for v in clip]})
            texts.append(page.get_text(clip=clip))
        text = "\n".join(texts).strip()
        key = (
            re.search(r"Answer:\s*\(?([\-+]?\d+)\)?", a["header"]) if solution else None
        )
        records.append(
            {**a, "refs": refs, "text": text, "answer": key[1] if key else ""}
        )
    return records


def build_questions(
    qdata, sdata, qfile="questions", sfile="solutions", known_tejas=False
):
    qs = segment_pdf(qdata)
    ss = segment_pdf(sdata, True)
    by_number = {}
    for s in ss:
        by_number.setdefault(s["number"], []).append(s)
    counts = {n: sum(q["number"] == n for q in qs) for n in {q["number"] for q in qs}}
    out = []
    for q in qs:
        matches = by_number.get(q["number"], [])
        # Require compatible sections if labels exist. No positional pairing.
        matches = [
            s
            for s in matches
            if not (q["subject"] and s["subject"]) or q["subject"] == s["subject"]
        ]
        s = matches[0] if len(matches) == 1 else {}
        number = q["number"]
        labels = set(re.findall(r"\(([1-4A-D])\)", q["text"]))
        family = (
            "1234" if set("1234") <= labels else "ABCD" if set("ABCD") <= labels else ""
        )
        kind = "mcq" if family else "integer"
        if known_tejas:
            kind = "mcq" if (number - 1) % 25 < 20 else "integer"
        subject = q["subject"] or (
            ["Mathematics", "Physics", "Chemistry"][min((number - 1) // 25, 2)]
            if known_tejas
            else ""
        )
        lines = s.get("text", "").splitlines()
        label = lines[1] if len(lines) > 1 else ""
        opts = {}
        if kind == "mcq":
            chosen = family or "1234"
            chunks = re.split(r"\(([" + chosen + r"])\)", q["text"])
            # Choose one complete option family. A–D figure labels are not extra options
            # when the actual response choices are numbered 1–4.
            for j in range(1, len(chunks) - 1, 2):
                opts[chunks[j]] = (
                    chunks[j + 1].strip()
                    or f"Source option {chunks[j]} (see original figure; description needs review)"
                )
        issues = []
        if len(matches) != 1:
            issues.append("Missing or ambiguous solution match")
        if counts[number] > 1:
            issues.append("Duplicate question number; resolve section identity")
        if not s.get("answer"):
            issues.append("Answer key requires review")
        out.append(
            {
                "id": str(uuid.uuid4()),
                "number": number,
                "solution_number": s.get("number"),
                "section": subject,
                "subject": subject,
                "type": kind,
                "text": q["text"],
                "options": opts,
                "answer": s.get("answer", ""),
                "solution": s.get("text", ""),
                "topic": label.split(" — ")[0],
                "difficulty": label.split(" — ")[-1] if " — " in label else "",
                "render_mode": "source",
                "q_refs": [{**r, "file_id": qfile} for r in q["refs"]],
                "s_refs": [{**r, "file_id": sfile} for r in s.get("refs", [])],
                "approved": False,
                "issues": issues,
                "accessible_text": "",
                "solution_accessible_text": "",
                "review_note": "",
            }
        )
    return out


def public_question(q):
    return {
        k: q.get(k)
        for k in [
            "id",
            "number",
            "subject",
            "section",
            "type",
            "text",
            "options",
            "topic",
            "render_mode",
            "solution_kind",
            "accessible_text",
            "q_refs",
            "bonus",
        ]
    }


def normalize_answer(value, kind):
    from tejas.scoring import canonical

    return canonical(value, kind)


def score_attempt(attempt):
    from tejas.scoring import score

    ledger = attempt.get("ledger")
    if ledger:
        rows = {r["id"]: r for r in ledger["rows"]}
        return {
            "summary": ledger["summary"],
            "questions": [{**q, **rows[q["id"]]} for q in attempt["questions"]],
        }
    return score(attempt)


def _render_crop_png(data, ref, scale=2):
    doc = validate_pdf(data)
    p = ref["page"] - 1
    if p < 0 or p >= len(doc):
        raise ValueError("Source page is out of range.")
    rect = fitz.Rect(ref["rect"])
    if rect.is_empty or not doc[p].rect.contains(rect):
        raise ValueError("Source region is outside the page.")
    pix = doc[p].get_pixmap(matrix=fitz.Matrix(scale, scale), clip=rect, alpha=False)
    if ref.get('omit_rects'):
        pixels = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n).copy()
        for coordinates in ref['omit_rects']:
            omitted = fitz.Rect(coordinates)
            if omitted.is_empty or not rect.contains(omitted):
                raise ValueError('Omitted source region must be within its crop.')
            left, top = max(0, math.floor(omitted.x0 * scale) - pix.x), max(0, math.floor(omitted.y0 * scale) - pix.y)
            right, bottom = math.ceil(omitted.x1 * scale) - pix.x, math.ceil(omitted.y1 * scale) - pix.y
            pixels[top:bottom, left:right] = 255
        pix = fitz.Pixmap(fitz.csRGB, pix.width, pix.height, pixels.tobytes(), False)
    return pix.tobytes('png')


from tejas.cache import ByteCache

_crop_cache = ByteCache(32 * 1024 * 1024)


def crop_png(data, ref, scale=2):
    import hashlib

    key = (hashlib.sha256(data).digest(), ref["page"], tuple(ref["rect"]), scale, tuple(tuple(r) for r in ref.get('omit_rects', [])))
    cached = _crop_cache.get(key)
    if cached is not None:
        return cached
    return _crop_cache.put(key, _render_crop_png(data, ref, scale))


def generate_report(attempt, file_loader):
    from tejas.reports import render_report

    return render_report(attempt, file_loader)
