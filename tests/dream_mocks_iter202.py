# Shared Playwright route mocks for signed-in Dream/Mission UI tests (iteration 202). Paste into browser scripts.
import json
SESSION = {"user": {"id": "demo-user", "name": "Rahul", "display_name": "Rahul", "role": "student"}}
DREAMS = {
    "dreams": [
        {"id": "jee-1", "exam": "jee", "college": "NIT Trichy", "branch": "Computer Science and Engineering", "need": 235, "range": [228, 242], "note": "OPEN · Other state", "at": "2026-01-05T10:00:00Z"},
        {"id": "jee-2", "exam": "jee", "college": "NIT Warangal", "branch": "Electronics and Communication", "need": 176, "range": [170, 182], "note": "OPEN · Other state", "at": "2026-01-05T10:00:00Z"},
        {"id": "jee-3", "exam": "jee", "college": "MNIT Jaipur", "branch": "Civil Engineering", "need": 150, "range": [145, 155], "note": "OPEN · Other state", "at": "2026-01-05T10:00:00Z"},
    ],
    "mocks": [
        {"id": "m3", "exam": "jee", "score": 168, "max": 300, "raw": 168, "rawMax": 300, "title": "Full Mock 3", "at": "2026-01-12T10:00:00Z"},
        {"id": "m2", "exam": "jee", "score": 141, "max": 300, "raw": 141, "rawMax": 300, "title": "Full Mock 2", "at": "2026-01-08T10:00:00Z"},
        {"id": "m1", "exam": "jee", "score": 120, "max": 300, "raw": 120, "rawMax": 300, "title": "Full Mock 1", "at": "2026-01-04T10:00:00Z"},
    ],
    "cheered": [],
}
MISSION = {"code": "AB2CDEF", "helped": 12, "week": 3, "link": "https://jeelive-mobile.emergent.host/api/j/AB2CDEF"}
