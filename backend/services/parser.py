"""
PDF Parser Service
Extract sections, instructions, and questions from JEE Advanced PDFs
"""
from __future__ import annotations
import re
import json
import pdfplumber
from typing import Dict, List, Tuple, Any

SECTION_RE = re.compile(r"\bSECTION\s*[-–]?\s*(\d+)\b", re.IGNORECASE)
Q_RE = re.compile(r"\bQ\.\s*(\d+)\b")
Q_ALT_RE = re.compile(r"\b(\d+)\s*\.\s*(?=[A-Z])")  # Matches "1. A particle..."


def extract_text_by_page(pdf_path: str) -> List[str]:
    """Extract text from each page of PDF"""
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            txt = page.extract_text() or ""
            pages.append(txt)
    return pages


def join_pages(pages: List[str]) -> str:
    """Join pages with page break markers"""
    return "\n\n===PAGE_BREAK===\n\n".join(pages)


def split_sections(full_text: str) -> List[Dict[str, Any]]:
    """
    Split text into sections.
    Finds 'SECTION n' markers and extracts content between them.
    """
    matches = list(SECTION_RE.finditer(full_text))
    out = []
    
    if not matches:
        # If no sections found, treat entire text as one section
        return [{"section_code": "SEC1", "raw": full_text.strip()}]
    
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        sec_text = full_text[start:end].strip()
        sec_no = m.group(1)
        out.append({"section_code": f"SEC{sec_no}", "raw": sec_text})
    
    return out


def extract_instructions_and_questions(
    section_raw: str
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Extract instructions and questions from section text.
    Instructions = from section start until first 'Q.'
    Questions = segmented by 'Q. n'
    """
    # Try primary pattern first
    q_first = Q_RE.search(section_raw)
    
    if not q_first:
        # Try alternate pattern
        q_first = Q_ALT_RE.search(section_raw)
        if not q_first:
            return section_raw.strip(), []
    
    instr = section_raw[:q_first.start()].strip()
    body = section_raw[q_first.start():]

    q_blocks = []
    # Split by Q. boundaries
    parts = re.split(r"(?=\bQ\.\s*\d+\b)", body)
    
    # If primary split didn't work, try alternate
    if len(parts) <= 1:
        parts = re.split(r"(?=\b\d+\s*\.\s*(?=[A-Z]))", body)
    
    for p in parts:
        p = p.strip()
        if not p:
            continue
            
        m = Q_RE.search(p)
        if not m:
            m = Q_ALT_RE.search(p)
            if not m:
                continue
        
        q_no = int(m.group(1))
        q_blocks.append({"q_no": q_no, "raw": p})
    
    return instr, q_blocks


def detect_options(q_raw: str) -> Dict[str, str]:
    """
    Extract options (A), (B), (C), (D) from question text.
    Returns dict like {'A': 'option text', 'B': 'option text', ...}
    """
    opts = {}
    
    # Pattern for (A), (B), (C), (D)
    splits = re.split(r"\(\s*([ABCD])\s*\)", q_raw)
    
    if len(splits) >= 3:
        i = 1
        while i + 1 < len(splits):
            key = splits[i].upper()
            val = splits[i + 1].strip()
            # Clean up - remove next option start if present
            val = re.split(r"\(\s*[ABCD]\s*\)", val)[0].strip()
            opts[key] = val
            i += 2
    
    return opts


def guess_q_type(section_instr: str, options: Dict[str, str]) -> str:
    """Guess question type from instruction text and options"""
    s = section_instr.lower()
    
    if "numerical" in s or "integer" in s or "numeric" in s:
        return "INTEGER"
    if "match" in s and ("list" in s or "column" in s):
        return "MATCH"
    if "one correct" in s or "single correct" in s:
        return "SCQ"
    if "one or more" in s or "more than one" in s or "multiple correct" in s:
        return "MCQ_MULTI"
    if "paragraph" in s or "comprehension" in s:
        return "COMP_SET"
    if options:
        return "SCQ"  # Default for option questions
    
    return "OTHER"


def parse_marking_rule(section_instr: str) -> Dict[str, Any]:
    """
    Extract marking rules from instruction text.
    Returns dict with raw text and detected +/- marks.
    """
    rule = {"raw": section_instr[:2000]}  # Cap to avoid huge strings
    
    # Detect patterns like +3, -1, +4, -2
    plus = re.findall(r"\+\s*(\d+(?:\.\d+)?)", section_instr)
    minus = re.findall(r"-\s*(\d+(?:\.\d+)?)", section_instr)
    
    if plus:
        rule["plus_candidates"] = [float(x) for x in plus]
    if minus:
        rule["minus_candidates"] = [float(x) for x in minus]
    
    # Try to extract specific marking patterns
    # Pattern: "Full Marks : +3 / +4" or "Marks: +3"
    full_match = re.search(
        r"(?:full\s*)?marks?\s*[:\s]*\+?\s*(\d+(?:\.\d+)?)", 
        section_instr, 
        re.IGNORECASE
    )
    if full_match:
        rule["full_marks"] = float(full_match.group(1))
    
    # Pattern: "Negative Marks : -1" or "Zero Marks : 0"
    neg_match = re.search(
        r"negative\s*marks?\s*[:\s]*-?\s*(\d+(?:\.\d+)?)", 
        section_instr, 
        re.IGNORECASE
    )
    if neg_match:
        rule["negative_marks"] = -float(neg_match.group(1))
    
    return rule


def build_yearspec_and_questions(
    pdf_path: str, 
    year: int, 
    paper_no: int
) -> Tuple[List[Dict], List[Dict], Dict]:
    """
    Main parsing function.
    Returns: (yearspec_sections, questions, validation_report)
    """
    pages = extract_text_by_page(pdf_path)
    full = join_pages(pages)
    sections = split_sections(full)

    yearspec = []
    questions = []
    total_q_detected = 0

    for sec in sections:
        instr, q_blocks = extract_instructions_and_questions(sec["raw"])
        marking = parse_marking_rule(instr)
        
        # Try to infer expected question count
        q_count_expected = None
        rng = re.search(
            r"Questions?\s+(\d+)\s+(?:to|–|-)\s+(\d+)", 
            instr, 
            re.IGNORECASE
        )
        if rng:
            a, b = int(rng.group(1)), int(rng.group(2))
            if b >= a:
                q_count_expected = b - a + 1

        section_code = sec["section_code"]
        default_qtype = guess_q_type(instr, {})

        yearspec.append({
            "year": year,
            "paper_no": paper_no,
            "section_code": section_code,
            "subject": "UNKNOWN",
            "question_type": default_qtype,
            "q_count_expected": q_count_expected,
            "marking_rule": marking,
            "rounding_rule": None,
            "evidence_text": instr[:4000],
            "page_refs": None
        })

        for qb in q_blocks:
            opts = detect_options(qb["raw"])
            q_type = guess_q_type(instr, opts)
            stem = qb["raw"]
            
            # Remove options part from stem if options found
            if opts:
                stem = re.split(r"\(\s*A\s*\)", qb["raw"])[0].strip()

            questions.append({
                "year": year,
                "paper_no": paper_no,
                "section_code": section_code,
                "subject": "UNKNOWN",
                "q_no": qb["q_no"],
                "q_type": q_type,
                "stem_text": stem,
                "options": opts if opts else None,
                "source_page_range": None,
                "status": "DRAFT"
            })
            total_q_detected += 1

    # Validation summary
    validation = {
        "sections_found": len(sections),
        "questions_detected": total_q_detected,
        "empty_stems": sum(1 for q in questions if not q["stem_text"].strip()),
        "option_missing_count": sum(
            1 for q in questions 
            if q["q_type"] in ("SCQ", "MCQ_MULTI") 
            and (not q["options"] or len(q["options"]) < 4)
        ),
    }
    
    return yearspec, questions, validation
