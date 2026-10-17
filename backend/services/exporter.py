"""
Export Service
Export yearspec and questions to JSON format
"""
from __future__ import annotations
import json
import os
from typing import Dict, Any, List
from datetime import datetime, timezone

STORAGE_DIR = os.environ.get("STORAGE_DIR", "./storage")


def ensure_dirs():
    """Ensure storage directory exists"""
    os.makedirs(STORAGE_DIR, exist_ok=True)


def export_to_json(
    catalog: Dict[str, Any],
    yearspec_sections: List[Dict[str, Any]],
    questions: List[Dict[str, Any]],
    validation_report: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Export data to JSON file and return the payload.
    """
    ensure_dirs()
    
    year = catalog.get("year")
    paper_no = catalog.get("paper_no")
    language = catalog.get("language")
    
    payload = {
        "metadata": {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "version": "1.0"
        },
        "catalog": {
            "year": year,
            "paper_no": paper_no,
            "language": language,
            "status": catalog.get("status")
        },
        "yearspec": yearspec_sections,
        "questions": questions,
        "quality_report": validation_report or {}
    }
    
    # Write to file
    filename = f"export_{year}_p{paper_no}_{language}.json"
    filepath = os.path.join(STORAGE_DIR, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    
    return {
        "export_path": filepath,
        "payload": payload
    }


def generate_quality_report(
    yearspec_sections: List[Dict[str, Any]],
    questions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate a quality/validation report for the parsed data.
    """
    report = {
        "total_sections": len(yearspec_sections),
        "total_questions": len(questions),
        "issues": [],
        "warnings": [],
        "stats": {
            "by_subject": {},
            "by_q_type": {},
            "by_status": {}
        }
    }
    
    # Count by subject
    for q in questions:
        subj = q.get("subject", "UNKNOWN")
        report["stats"]["by_subject"][subj] = report["stats"]["by_subject"].get(subj, 0) + 1
        
        qtype = q.get("q_type", "OTHER")
        report["stats"]["by_q_type"][qtype] = report["stats"]["by_q_type"].get(qtype, 0) + 1
        
        status = q.get("status", "DRAFT")
        report["stats"]["by_status"][status] = report["stats"]["by_status"].get(status, 0) + 1
    
    # Check for issues
    empty_stems = [q.get("q_no") for q in questions if not q.get("stem_text", "").strip()]
    if empty_stems:
        report["issues"].append({
            "type": "EMPTY_STEM",
            "severity": "HIGH",
            "affected_questions": empty_stems[:20],
            "count": len(empty_stems)
        })
    
    # Check for missing options in SCQ/MCQ questions
    missing_opts = []
    for q in questions:
        if q.get("q_type") in ("SCQ", "MCQ_MULTI"):
            opts = q.get("options") or {}
            if len(opts) < 4:
                missing_opts.append(q.get("q_no"))
    
    if missing_opts:
        report["issues"].append({
            "type": "MISSING_OPTIONS",
            "severity": "HIGH",
            "affected_questions": missing_opts[:20],
            "count": len(missing_opts)
        })
    
    # Check for UNKNOWN subjects
    unknown_subj = [q.get("q_no") for q in questions if q.get("subject") == "UNKNOWN"]
    if unknown_subj:
        report["warnings"].append({
            "type": "UNKNOWN_SUBJECT",
            "severity": "MEDIUM",
            "affected_questions": unknown_subj[:20],
            "count": len(unknown_subj)
        })
    
    # Check yearspec for missing evidence
    for sec in yearspec_sections:
        if not sec.get("evidence_text", "").strip():
            report["issues"].append({
                "type": "MISSING_EVIDENCE",
                "severity": "HIGH",
                "section": sec.get("section_code")
            })
    
    return report
