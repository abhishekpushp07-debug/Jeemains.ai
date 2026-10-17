"""Faithful paginated report composition; equations are rendered, never flattened or guessed."""

import html, re, io, threading
from functools import lru_cache
from datetime import datetime, timezone
import fitz
from matplotlib.mathtext import math_to_image
from matplotlib.font_manager import FontProperties
from tejas_core import crop_png, score_attempt

_math_lock = threading.Lock()
PATTERN = r"(\$\$[\s\S]+?\$\$|\$[^$\n]+?\$)"


@lru_cache(maxsize=128)
def math_png(formula):
    expression = formula.strip("$")
    out = io.BytesIO()
    try:
        with _math_lock:
            math_to_image(
                "$" + expression + "$",
                out,
                prop=FontProperties(size=14),
                dpi=180,
                format="png",
                color="#0B1F2A",
            )
    except Exception:
        raise ValueError(
            "This typed equation cannot be exported faithfully. Use a verified source region for complex notation instead."
        )
    return out.getvalue()


def validate_typed_math(q):
    for text in [
        q.get("text", ""),
        q.get("solution", ""),
        *q.get("options", {}).values(),
    ]:
        for part in re.split(PATTERN, str(text)):
            if part.startswith("$"):
                math_png(part)


class Report:
    def __init__(self, answer_key_only=False):
        self.header = 'JEEMAINS.AI / RESULTS & ANSWER KEYS' if answer_key_only else 'JEEMAINS.AI / RESULTS & SOLUTIONS'
        self.doc = fitz.open()
        self.page = None
        self.y = 0
        self.context = ""

    def page_for(self, title):
        self.context = title
        self.page = self.doc.new_page(width=595, height=842)
        self.y = 108
        self.page.draw_rect(
            fitz.Rect(0, 0, 595, 7),
            color=(0.059, 0.463, 0.431),
            fill=(0.059, 0.463, 0.431),
        )
        self.page.insert_text(
            (40, 36),
            self.header,
            fontsize=10,
            color=(0.059, 0.463, 0.431),
        )
        self.page.insert_htmlbox(
            fitz.Rect(40, 49, 555, 95),
            '<div style="font-size:16pt;color:#071A2B">'
            + html.escape(title)
            + "</div>",
        )

    def ensure(self, h):
        if self.y + h > 780:
            self.page_for(self.context + " · continued")

    def text(self, text, size=11, color="#294739", need=125):
        # Conservative chunks avoid forcing a long paragraph into unreadable tiny type.
        for chunk in [str(text)[i : i + 1300] for i in range(0, len(str(text)), 1300)]:
            self.ensure(need)
            box = fitz.Rect(40, self.y, 555, 780)
            content = (
                f'<div style="font-size:{size}pt;line-height:1.5;color:{color};overflow-wrap:anywhere">'
                + html.escape(chunk).replace("\n", "<br>")
                + "</div>"
            )
            spare, scale = self.page.insert_htmlbox(box, content, scale_low=0.95)
            if spare < 0:
                # Break unusually long tokens (formulas, URLs) so they can wrap.
                content = re.sub(r'(\S{40})', '\\1\u200b', content)
                spare, scale = self.page.insert_htmlbox(box, content, scale_low=0.95)
            if spare < 0:
                self.page_for(self.context + " · continued")
                box = fitz.Rect(40, self.y, 555, 780)
                spare, scale = self.page.insert_htmlbox(box, content, scale_low=0.95)
                if spare < 0:
                    raise ValueError(
                        "Report text could not fit legibly; shorten unusually long unbroken content or select source regions."
                    )
            self.y = 780 - spare + 13

    def image(self, png, width=None, height=None):
        pix = fitz.Pixmap(png)
        w = width or min(515, pix.width * 72 / 180)
        h = height or pix.height * (w / pix.width)
        if h > 650:
            w *= 650 / h
            h = 650
        self.ensure(h + 14)
        self.page.insert_image(fitz.Rect(40, self.y, 40 + w, self.y + h), stream=png)
        self.y += h + 14

    def rich(self, text, lenient=False):
        for part in re.split(PATTERN, str(text)):
            if not part:
                continue
            if part.startswith("$") and lenient:
                # Untrusted AI LaTeX: render what mathtext supports, otherwise keep the formula as text.
                try:
                    self.image(math_png(mathtext_safe(part)))
                except ValueError:
                    self.text(part.strip("$"), 10)
            elif part.startswith("$"):
                self.image(math_png(part))
            else:
                self.text(part)


def mathtext_safe(formula):
    f = formula.strip("$")
    f = re.sub(r"\\[dt]frac", r"\\frac", f)
    f = re.sub(r"\\frac\s*(\w)\s*(\w)", r"\\frac{\1}{\2}", f)
    f = re.sub(r"\\(?:text|textrm|operatorname)\s*\{", r"\\mathrm{", f)
    f = re.sub(r"\\(?:boxed|displaystyle)", "", f)
    f = re.sub(r"\\(?:left|right|big|Big|bigg|Bigg)(?![a-zA-Z])", "", f)
    f = re.sub(r"\\q?quad", r"\\ ", f)
    return "$" + f.strip() + "$"


GREEK = {'alpha': 'α', 'beta': 'β', 'gamma': 'γ', 'delta': 'δ', 'Delta': 'Δ', 'theta': 'θ', 'lambda': 'λ', 'mu': 'μ',
         'pi': 'π', 'rho': 'ρ', 'sigma': 'σ', 'omega': 'ω', 'Omega': 'Ω', 'phi': 'φ', 'epsilon': 'ε', 'varepsilon': 'ε',
         'times': '×', 'cdot': '·', 'pm': '±', 'le': '≤', 'leq': '≤', 'ge': '≥', 'geq': '≥', 'neq': '≠', 'approx': '≈',
         'propto': '∝', 'infty': '∞', 'Rightarrow': '⇒', 'rightarrow': '→', 'to': '→', 'implies': '⇒', 'degree': '°', 'circ': '°',
         'sum': 'Σ', 'int': '∫', 'partial': '∂', 'nabla': '∇', 'therefore': '∴', 'quad': ' ', 'qquad': ' ', 'ldots': '…', 'dots': '…',
         'longrightarrow': '⟶', 'xrightarrow': '→', 'rightleftharpoons': '⇌', 'leftarrow': '←', 'Leftrightarrow': '⇔', 'sim': '~',
         'eta': 'η', 'tau': 'τ', 'nu': 'ν', 'chi': 'χ', 'psi': 'ψ', 'kappa': 'κ', 'zeta': 'ζ', 'xi': 'ξ',
         'in': '∈', 'subset': '⊂', 'cup': '∪', 'cap': '∩', 'perp': '⊥', 'parallel': '∥', 'angle': '∠', 'equiv': '≡', 'gg': '≫', 'll': '≪',
         'sin': 'sin', 'cos': 'cos', 'tan': 'tan', 'cot': 'cot', 'sec': 'sec', 'log': 'log', 'ln': 'ln', 'lim': 'lim', 'max': 'max', 'min': 'min', 'det': 'det', 'exp': 'exp'}


def latex_plain(text):
    """Readable plain-text form of AI LaTeX for compact PDFs (the web app renders the full math)."""
    t = str(text).replace('$$', '').replace('$', '')
    t = re.sub(r'\\[dt]?frac\s*(\w)\s*(\w)', r'(\1)/(\2)', t)
    for _ in range(4):
        t = re.sub(r'\\[dt]?frac\{([^{}]*)\}\{([^{}]*)\}', r'(\1)/(\2)', t)
        t = re.sub(r'\\sqrt\{([^{}]*)\}', '√(\\1)', t)
        t = re.sub(r'\\(?:text|mathrm|mathbf|boxed|operatorname|vec|hat|bar|overline)\{([^{}]*)\}', r'\1', t)
    t = re.sub(r'\\([A-Za-z]+)', lambda m: GREEK.get(m.group(1), ''), t)
    t = t.replace('\\,', ' ').replace('\\;', ' ').replace('\\ ', ' ').replace('{', '').replace('}', '')
    return re.sub(r'[ \t]{2,}', ' ', t)


def render_report(a, loader):
    result = score_attempt(a)
    s = result["summary"]
    r = a["rules"]
    answer_key_only = bool(result['questions']) and all(q.get('solution_kind')=='answer_key_only' for q in result['questions'])
    review_notice = 'Skipped questions and supplied answer keys are included. No worked solutions were supplied.' if answer_key_only else 'Skipped questions and correctly matched solutions are included.'
    report = Report(answer_key_only)
    report.page_for(a["title"])
    percent = s.get("percentage")
    percentage = "Not applicable" if percent is None else str(percent) + "%"
    summary = f"{a['exam']} · Nonofficial practice\nAttempt: {a['id']}\nStarted: {datetime.fromtimestamp(a['started_at'],timezone.utc).isoformat()}\nContent version: {a.get('version',1)} · Key version: {a.get('key_version',a.get('version',1))}\nScore version: {a.get('score_version','original')}\n\nScore: {s['score']} / {s['maximum']} · Percentage: {percentage} (not a percentile)\nCorrect: {s['correct']} · Incorrect: {s['incorrect']} · Skipped: {s['skipped']}\nDropped: {s.get('dropped',0)} · Bonus-to-all: {s.get('bonus',0)}\nAttempt rate: {s['attempt_rate']}% · Accuracy: {str(s['accuracy'])+'%' if s['accuracy'] is not None else 'Not applicable (no attempts)'}\nAccuracy = correct / attempted; dropped and bonus items excluded.\nPenalty marks: {s['penalties']} · Elapsed: {s['total_seconds']} seconds\nRules: +{r['correct']} correct, {r['wrong']} wrong, {r['skipped']} unanswered\nNumerical: {r['numeric_rule']}\n\nComplete record: all {len(result['questions'])} questions in original delivery order.\n{review_notice}\nDownloaded copies are outside jeemains.ai access controls.\nAttribution: {a.get('attribution','Owner-supplied content')}"
    if a.get("mode") == "preview":
        report.text(
            "UNAPPROVED PRIVATE REVIEW PROOF — author keys and solutions still require human verification.",
            11,
            "#8C5D18",
        )
    report.text(summary)
    if s.get("sections"):
        m, b = s["main_block"], s["bonus_block"]
        lines = [f"Main ({m['count']} questions): {m['score']} / {m['maximum']} · Correct {m['correct']} · Wrong {m['incorrect']} · Unanswered {m['skipped']}"]
        lines += [f"  {x['name']}: {x['score']} / {x['maximum']} · Correct {x['correct']} · Wrong {x['incorrect']} · Unanswered {x['skipped']}" for x in s["sections"]]
        lines.append(f"Bonus ({b['count']} questions): {b['score']} / {b['maximum']} · Correct {b['correct']} · Wrong {b['incorrect']} · Unanswered {b['skipped']}" if b["entered"] else "Bonus section: not entered (opens only after all main questions are answered).")
        report.text("Section-wise scores\n" + "\n".join(lines), 10)
    if a.get("change_note"):
        report.text("Correction note: " + a["change_note"])
    report.text(
        "Frozen profile: " + a.get("profile", {}).get("id", "Legacy custom practice"), 9
    )
    for q in result["questions"]:
        report.page_for(f"Question {q['number']} · {q.get('section') or q['subject']}")
        accepted = ", ".join(q.get("accepted_answers") or [q["answer"]])
        report.text(
            f"Your response: {q['response'] if str(q['response']).strip() else 'Unanswered'} | Accepted answer(s): {accepted}\nMarks: {q['marks']} | {q['outcome'].title()} | Reason: {q.get('reason_code','standard_scoring')}",
            10,
        )
        if q.get("review_note"):
            report.text("Review note: " + q["review_note"], 9)
        for label, key, plain in [
            ("Question", "q_refs", q["text"]),
            ("Supplied answer key (no worked solution)" if q.get('solution_kind')=='answer_key_only' else "Matched solution", "s_refs", q["solution"]),
        ]:
            report.context = f"Question {q['number']} · {label}"
            report.ensure(70)
            report.text(label, 12, "#0F766E")
            if q.get("render_mode") == "source" and q.get(key):
                for ref in q[key]:
                    rect = fitz.Rect(ref["rect"])
                    w = min(515, rect.width)
                    h = rect.height * w / rect.width
                    raw = loader(ref['file_id'])
                    report.image(raw if ref.get('prerendered') else crop_png(raw, ref, 2), w, h)
                    report.text(
                        f"Source {ref['file_id']} · page {ref['page']}", 8, "#6C8278"
                    )
            else:
                if label == "Question" and q["type"] == "mcq":
                    plain += "\n\n" + "\n".join(
                        f"({k}) {v}" for k, v in q["options"].items()
                    )
                report.rich(plain)
        ai = (a.get("ai_solutions") or {}).get(q["id"])
        if ai:
            report.context = f"Question {q['number']} · AI generated solution"
            report.ensure(70)
            report.text("AI generated step-by-step solution (gpt-6-astra) · " + ai["difficulty"], 12, "#5C0025")
            parts = ["Concept: " + ai["concept"]]
            if ai["given"]:
                parts.append("Given: " + "; ".join(ai["given"]))
            parts += ["Step %d. %s: %s" % (i, re.sub(r'^\d+[.)]\s*', '', s['title']), s['explanation']) for i, s in enumerate(ai["steps"], 1)]
            parts.append(f"Answer: ({ai['final_answer']})" + ("" if ai["key_agrees"] else " — AI differs from the supplied key; the key and score are unchanged."))
            parts.append("Insight: " + ai["insight"])
            if ai["shortcut"]:
                parts.append("Shortcut: " + ai["shortcut"])
            if ai["common_mistakes"]:
                parts.append("Common mistakes: " + "; ".join(ai["common_mistakes"]))
            parts.append("Time tip: " + ai["time_tip"])
            for part in parts:
                report.text(re.sub(r'\n\s*\n+', '\n', latex_plain(part)), 9.5, "#2B2B2B", 48)
    total = len(report.doc)
    for i, p in enumerate(report.doc):
        p.insert_text(
            (40, 819),
            f"Personal study report | {i+1} / {total}",
            fontsize=8,
            color=(0.3, 0.4, 0.35),
        )
    return report.doc.tobytes(garbage=4, deflate=True)
