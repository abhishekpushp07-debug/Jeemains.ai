"""Builds the website hand-off pack for Rank + Mission (no Rapid Fire, no copy of the Rank data).

The website reads every college, branch and cut-off from the app server's API, so this pack ships the documentation,
the connector, read-only server code, the app's screen code, real API answers, sample PDFs and fresh screenshots,
then checks the result (no Rapid Fire code, no data files) and zips it.

Run:  cd /app/backend && python ../handoff/build_pack.py
Hand-written parts live next to this script: pack_root/*.md, docs/*.md, connect/, shots/.
"""
import hashlib, json, re, shutil, sys, urllib.error, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/app")
HERE = ROOT / "handoff"
BACK, FRONT = ROOT / "backend", ROOT / "frontend"
PACK = HERE / "JEELIVE_Rank_Mission_Website_Handoff"
ZIP = HERE / "JEELIVE_Rank_Mission_Website_Handoff.zip"
API = "http://localhost:8001/api"
LIVE = "https://jeelive-mobile.emergent.host/api"

# The one Rapid Fire helper the share code uses, given its own neutral home in the pack.
WHATSAPP_TS = '''// Opens WhatsApp with a ready message (the app keeps this helper in a shared module; copied here on its own).
import { Linking, Platform, Share } from "react-native";

export async function sendWhatsApp(text: string) {
  // api.whatsapp.com directly: the wa.me redirect breaks some emoji in the message.
  const web = "https://api.whatsapp.com/send?text=" + encodeURIComponent(text);
  if (Platform.OS === "web") { await Linking.openURL(web).catch(() => {}); return; } // a computer may have no WhatsApp app
  try { await Linking.openURL("whatsapp://send?text=" + encodeURIComponent(text)); }
  catch {
    try { await Linking.openURL(web); }
    catch { Share.share({ message: text }).catch(() => {}); }
  }
}
'''
REWRITE = {'@/src/rapid/social': '@/src/shared/whatsapp', "the Rapid Fire grant": "the 15-minute pass"}
# Dream files left out: the "Dream Unlocked" celebration and the Home card that starts it use the game's art.
DREAM_SKIP = {"DreamCheer.tsx", "routine.ts", "HomeDream.tsx"}
# Product copy that names Rapid Fire as one of the four promises (kept word for word, see docs/07 §10).
COPY_OK = {"copy.ts", "jeeliveApp.ts"}
TEXT = {".md", ".py", ".ts", ".tsx", ".json", ".sh", ".example", ".txt"}


def fresh(p: Path):
    if p.exists():
        shutil.rmtree(p)
    p.mkdir(parents=True)
    return p


def copy(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix in TEXT:
        text = src.read_text(encoding="utf-8")
        for a, b in REWRITE.items():
            text = text.replace(a, b)
        dst.write_text(text, encoding="utf-8")
    else:
        shutil.copy2(src, dst)


def dump(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def call(path, body=None, raw=False, base=API):
    req = urllib.request.Request(base + path, method="GET" if body is None else "POST",
                                 data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
        return (data, dict(r.headers)) if raw else json.loads(data)


def theme_without_game(src: Path) -> str:
    """theme.ts minus the game's palette block and the comments that point at it."""
    text = src.read_text(encoding="utf-8")
    start, end = text.index("// Rapid Fire is its own world"), text.index("export const fonts")
    text = text[:start] + text[end:]
    lines = [ln for ln in text.splitlines() if not (ln.strip().startswith("//") and "Rapid Fire" in ln)]
    text = "\n".join(lines) + "\n"
    assert "rapid" not in text.lower() and "arena" not in text, "theme.ts still mentions the game"
    return text


# ------------------------------------------------------------------ hand-written parts
def copy_docs():
    for f in (HERE / "pack_root").glob("*.md"):
        copy(f, PACK / f.name)
    for f in sorted((HERE / "docs").glob("*.md")):
        copy(f, PACK / "docs" / f.name)
    for src, name in (("WEBSITE_AGENT_BRIEF.md", "13_APP_UPDATE_AITS_AND_WHO_BUILDS_WHAT.md"), ("CEO_DASHBOARD.md", "14_CEO_DASHBOARD.md")):
        copy(ROOT / "memory" / src, PACK / "docs" / name)
    for f in (HERE / "connect").rglob("*"):
        if f.is_file() and "__pycache__" not in f.parts:
            copy(f, PACK / "CONNECT" / f.relative_to(HERE / "connect"))
    for kind, where in (("rank", "RANK"), ("mission", "MISSION")):
        for f in sorted((HERE / "shots" / kind).glob("*.jpg")):
            copy(f, PACK / where / "screenshots" / f.name)


# ------------------------------------------------------------------ code (read-only reference)
def shared(ui: Path):
    for f in ("shareCard.ts", "whatsappFile.ts"):
        copy(FRONT / "src" / f, ui / "shared" / f)
    (ui / "shared" / "theme.ts").write_text(theme_without_game(FRONT / "src" / "theme.ts"), encoding="utf-8")
    (ui / "shared" / "whatsapp.ts").write_text(WHATSAPP_TS, encoding="utf-8")


def copy_code():
    rank = PACK / "RANK" / "code"
    for f in ("rank_predictor.py", "rank_comedk.py", "rank_bitsat.py", "rank_tools.py", "rank_cutoff.py", "rank_pdf.py", "dream.py"):
        copy(BACK / f, rank / "server_reference" / f)
    # The server's own checks that Cut off agrees with Target marks and the College predictor (docs/11 section 9).
    copy(BACK / "tests" / "test_rank_cutoff.py", rank / "server_reference" / "tests" / "test_rank_cutoff.py")
    ui = rank / "app_reference_ui"
    copy(FRONT / "app" / "(tabs)" / "rank.tsx", ui / "app_tabs_rank.tsx")
    for f in sorted((FRONT / "src" / "rank").iterdir()):
        copy(f, ui / "src_rank" / f.name)
    for f in sorted((FRONT / "src" / "dream").iterdir()):
        if f.name not in DREAM_SKIP:
            copy(f, ui / "src_dream" / f.name)
    shared(ui)

    mission = PACK / "MISSION" / "code"
    for f in ("mission_links.py", "client_ip.py"):
        copy(BACK / f, mission / "server_reference" / f)
    mui = mission / "app_reference_ui"
    copy(FRONT / "app" / "(tabs)" / "mission.tsx", mui / "app_tabs_mission.tsx")
    for f in sorted((FRONT / "src" / "mission").iterdir()):
        copy(f, mui / "src_mission" / f.name)
    shared(mui)


# ------------------------------------------------------------------ OpenAPI (only the paths of this pack)
def openapi():
    spec = json.loads(urllib.request.urlopen(API.rsplit("/api", 1)[0] + "/openapi.json", timeout=30).read())
    keep = ("/api/rank/", "/api/rf/access", "/api/rf/mission/me", "/api/rf/dream")
    paths = {p: v for p, v in spec["paths"].items() if p.startswith(keep)}
    schemas, todo = {}, list(re.findall(r'#/components/schemas/([A-Za-z0-9_.-]+)', json.dumps(paths)))
    while todo:
        name = todo.pop()
        if name in schemas:
            continue
        schemas[name] = spec["components"]["schemas"][name]
        todo += re.findall(r'#/components/schemas/([A-Za-z0-9_.-]+)', json.dumps(schemas[name]))
    out = {"openapi": spec["openapi"],
           "info": {"title": "JEELIVE.AI app server: Rank, Mission, Dream college", "version": "2026.11",
                    "description": "Paths as served by the app server. Through the website connector the browser calls /api/rank/*, "
                                   "/api/mission/me and /api/dream* instead (docs/02_CONNECT_GUIDE.md). GET /api/j/{code} is a plain 302 redirect."},
           "servers": [{"url": LIVE.rsplit("/api", 1)[0]}], "paths": paths, "components": {"schemas": dict(sorted(schemas.items()))}}
    dump(PACK / "CONNECT" / "openapi_rank_mission.json", out)
    return len(paths)


# ------------------------------------------------------------------ real API answers (frozen samples)
def api_examples():
    out = PACK / "RANK" / "api_examples"
    pdfs = PACK / "RANK" / "sample_pdfs"
    note = "Frozen sample captured when this pack was built. Shows the shape only: never use these numbers on a page; call the server."
    done = []

    def save(name, method, path, body=None):
        res = call(path, body)
        dump(out / f"{name}.json", {"note": note, "request": {"method": method, "url": f"/api{path}", "body": body}, "response": res})
        done.append(name)
        return res

    save("01_meta", "GET", "/rank/meta")
    save("02_estimate_jee", "POST", "/rank/estimate", {"exam": "jee", "marks": 180, "level": "normal", "category": "OBC-NCL", "pwd": False})
    save("03_estimate_comedk", "POST", "/rank/estimate", {"exam": "comedk", "marks": 110, "level": "normal", "category": "GEN", "pwd": False})
    save("04_percentile", "POST", "/rank/percentile", {"percentile": 97.4567, "category": "GEN", "pwd": False})
    form = {"marks": 180, "level": "normal", "category": "GEN", "female": False, "pwd": False, "state": "Bihar", "branches": []}
    p1 = save("05_predict_marks_all_page1", "POST", "/rank/predict", {**form, "segment": "all", "page": 1})
    save("06_predict_marks_all_page2", "POST", "/rank/predict", {**form, "segment": "all", "page": 2})
    form2 = {"percentile": 96.5, "level": "normal", "category": "OBC-NCL", "female": True, "pwd": False, "state": "Delhi", "branches": ["Computer Science", "AI & Data Science"]}
    save("07_predict_percentile_obc_female_delhi_cs_NIT", "POST", "/rank/predict", {**form2, "segment": "NIT", "page": 1})
    p3 = save("08_predict_percentile_obc_female_delhi_cs_DELHI", "POST", "/rank/predict", {**form2, "segment": "DELHI", "page": 1})
    save("09_predict_chart_line_page_size_20", "POST", "/rank/predict", {"percentile": 99.0, "level": "normal", "category": "GEN", "female": False, "pwd": False, "state": None, "branches": [], "segment": "all", "page": 1, "page_size": 20})
    s = p1["items"][0]
    save("10_college_sheet_josaa", "POST", "/rank/college", {**form, "inst": s["inst"], "prog": s["prog"], "quota": s["quota"], "gender": s["gender"], "seat": s["seat"]})
    if p3["items"]:
        d = p3["items"][0]
        save("11_college_sheet_jac_delhi", "POST", "/rank/college", {**form2, "inst": d["inst"], "prog": d["prog"], "quota": d["quota"], "gender": d["gender"], "seat": d["seat"]})
    save("12_college_sheet_blocked_path", "POST", "/rank/college", {**form, "inst": s["inst"], "prog": s["prog"], "quota": "HS", "gender": "F", "seat": "open"})
    save("13_bitsat", "POST", "/rank/bitsat", {"score": 280, "campus": "all", "degree": "all"})
    c1 = save("14_comedk_marks", "POST", "/rank/comedk", {"marks": 110, "branches": [], "area": "all", "page": 1})
    save("15_comedk_rank_blr_cs", "POST", "/rank/comedk", {"rank": 4500, "branches": ["Computer Science"], "area": "blr", "page": 1})
    k = c1["items"][0]
    save("16_comedk_college_sheet", "POST", "/rank/comedk/college", {"marks": 110, "branches": [], "code": k["code"], "course": k["cc"]})
    save("17_target_jee", "POST", "/rank/target/jee", {"inst": s["inst"], "category": "GEN", "female": False, "pwd": False, "state": "Bihar"})
    save("18_target_comedk", "POST", "/rank/target/comedk", {"code": k["code"]})
    save("19_target_bitsat", "GET", "/rank/target/bitsat")
    save("20_colleges_search_lists", "GET", "/rank/colleges")
    items = [{"exam": "jee", "id": f"jee-{s['prog']}", "prog": s["prog"], "quota": s["quota"], "gender": s["gender"], "path": s["path"]},
             {"exam": "comedk", "id": k["id"]}, {"exam": "bitsat", "id": "Pilani-cs"}]
    save("21_compare_branches", "POST", "/rank/compare", {"items": items})
    save("22_compare_colleges", "POST", "/rank/compare/colleges", {"items": [{"exam": "jee", "id": str(s["inst"])}, {"exam": "comedk", "id": k["code"]}, {"exam": "bitsat", "id": "Pilani"}],
                                                                  "category": "GEN", "female": False, "pwd": False, "state": "Bihar"})
    cutoff_examples(save, out, note)
    for name, path, body in (("jee_top50", "/rank/pdf/jee", {**form, "segment": "all"}), ("comedk_top50", "/rank/pdf/comedk", {"marks": 110, "branches": [], "area": "all"}),
                             ("bitsat_programs", "/rank/pdf/bitsat", {"score": 280, "campus": "all", "degree": "all"}),
                             ("target_jee_college", "/rank/pdf/target/jee", {"inst": s["inst"], "category": "GEN", "female": False, "pwd": False, "state": "Bihar"}),
                             ("target_comedk_college", "/rank/pdf/target/comedk", {"code": k["code"]}), ("target_bitsat", "/rank/pdf/target/bitsat", {"campus": "all"}),
                             ("saved_and_compare", "/rank/pdf/saved", {"items": items, "tags": ["borderline", "likely", None], "pick": [0, 1, 2]})):
        data, _ = call(path, body, raw=True)
        assert data[:5] == b"%PDF-", name
        pdfs.mkdir(parents=True, exist_ok=True)
        (pdfs / f"sample_{name}.pdf").write_bytes(data)
        dump(pdfs / f"sample_{name}.request.json", {"method": "POST", "url": f"/api{path}", "body": body})
    # Cut off PDF (new): the body is the one that drew the list on screen, with or without a score.
    me = {"level": "normal", "category": "GEN", "female": False, "pwd": False, "state": None}
    for name, body in (("cutoff_jee_college_eligible_200_marks", {"exam": "jee", "by": "college", "key": str(s["inst"]), "marks": 200, **me}),
                       ("cutoff_jee_branch_top_100", {"exam": "jee", "by": "branch", "key": "Computer Science", **me}),
                       ("cutoff_comedk_branch_eligible_rank_30000", {"exam": "comedk", "by": "branch", "key": "Computer Science", "rank": 30000}),
                       ("cutoff_bitsat_campus_five_years", {"exam": "bitsat", "by": "college", "key": "Pilani"})):
        data, _ = call("/rank/pdf/cutoff", body, raw=True)
        assert data[:5] == b"%PDF-", name
        (pdfs / f"sample_{name}.pdf").write_bytes(data)
        dump(pdfs / f"sample_{name}.request.json", {"method": "POST", "url": "/api/rank/pdf/cutoff", "body": body})
    return done


def cutoff_examples(save, out, note):
    """Cut off (new): the pickers, a college and a branch of every exam with and without a score, and what the server refuses."""
    opts = save("23_cutoff_options_pickers", "GET", "/rank/cutoff/options")
    key = lambda exam, title: next(c["key"] for c in opts[exam]["colleges"] if c["title"] == title)  # noqa: E731
    me = {"level": "normal", "category": "GEN", "female": False, "pwd": False, "state": None}
    trichy, dtu, first_comedk = key("jee", "NIT Trichy"), key("jee", "DTU Delhi"), opts["comedk"]["colleges"][0]["key"]
    cs = {"exam": "jee", "by": "branch", "key": "Computer Science"}
    save("24_cutoff_jee_college_every_branch_every_round", "POST", "/rank/cutoff", {"exam": "jee", "by": "college", "key": trichy, **me})
    save("25_cutoff_jee_college_eligible_at_200_marks", "POST", "/rank/cutoff", {"exam": "jee", "by": "college", "key": trichy, "marks": 200, **me})
    save("26_cutoff_jee_branch_top_100", "POST", "/rank/cutoff", {**cs, **me})
    save("27_cutoff_jee_branch_eligible_scorecard_rank_obc_ncl_home_state", "POST", "/rank/cutoff", {**cs, "rank": 7500, **me, "category": "OBC-NCL", "state": "Tamil Nadu"})
    save("28_cutoff_jee_jac_delhi_college_percentile", "POST", "/rank/cutoff", {"exam": "jee", "by": "college", "key": dtu, "percentile": 99.2, **me, "state": "Delhi"})
    save("29_cutoff_comedk_college_every_course", "POST", "/rank/cutoff", {"exam": "comedk", "by": "college", "key": first_comedk})
    save("30_cutoff_comedk_branch_eligible_rank_30000", "POST", "/rank/cutoff", {"exam": "comedk", "by": "branch", "key": "Computer Science", "rank": 30000})
    save("31_cutoff_bitsat_campus_five_years_no_rounds", "POST", "/rank/cutoff", {"exam": "bitsat", "by": "college", "key": "Pilani"})
    save("32_cutoff_bitsat_program_eligible_score_280", "POST", "/rank/cutoff", {"exam": "bitsat", "by": "branch", "key": "cs", "marks": 280})
    save("33_predict_scorecard_rank", "POST", "/rank/predict", {"rank": 7500, **me, "branches": [], "segment": "all", "page": 1})
    refused = []
    for body in ({"exam": "jee", "by": "college", "key": "9999"}, {"exam": "jee", "by": "branch", "key": "Nope"}, {"exam": "bitsat", "by": "college", "key": "Mumbai"},
                 {"exam": "bitsat", "by": "branch", "key": "nope"}, {"exam": "jee", "by": "college", "key": trichy, "marks": 350},
                 {"exam": "comedk", "by": "branch", "key": "Computer Science", "percentile": 90}, {"exam": "comedk", "by": "branch", "key": "Computer Science", "marks": 181},
                 {"exam": "comedk", "by": "branch", "key": "Computer Science", "rank": 250000}, {"exam": "bitsat", "by": "college", "key": "Pilani", "rank": 5},
                 {"exam": "neet", "by": "college", "key": "1"}):
        try:
            call("/rank/cutoff", body)
            raise RuntimeError(f"not refused: {body}")
        except urllib.error.HTTPError as e:
            refused.append({"request": {"method": "POST", "url": "/api/rank/cutoff", "body": body}, "status": e.code, "response": json.loads(e.read())})
    dump(out / "34_cutoff_what_the_server_refuses.json", {"note": note + " A sentence is ready to show; a list means a wrong field (validate in the form).", "answers": refused})


def live_has_cutoff():
    """True / False: whether the live app server already answers Cut off. None when the live server could not be asked."""
    try:
        call("/rank/cutoff/options", base=LIVE)
        return True
    except urllib.error.HTTPError:
        return False
    except OSError:
        return None


def mission_examples():
    """Mission answers with personal values masked, plus the real share-link redirect and the signed-out refusal."""
    out = PACK / "MISSION" / "api_examples"
    masked = "Shape of a real answer; the code and counts are masked (made up), never a real student's."
    dump(out / "01_website_mission_me.json", {"note": masked, "request": {"method": "GET", "url": "/api/mission/me (website, through the connector)",
         "headers": {"Cookie": "access_token=<the student's website session>"}},
         "response": {"status": 200, "headers": {"Cache-Control": "no-store"},
                      "body": {"code": "AB2CDEF", "helped": 12, "week": 3, "link": f"{LIVE}/j/AB2CDEF"}}})
    dump(out / "02_app_server_mission_me.json", {"note": masked, "request": {"method": "GET", "url": "/api/rf/mission/me (app server, called by the connector)",
         "headers": {"Authorization": "Bearer <15-minute pass from POST /api/rf/access>"}},
         "response": {"status": 200, "body": {"code": "AB2CDEF", "helped": 12, "week": 3}}})
    dump(out / "03_new_student_zero_state.json", {"note": masked + " A student who has never been helped yet.",
         "response": {"status": 200, "body": {"code": "QW7ERTY", "helped": 0, "week": 0, "link": f"{LIVE}/j/QW7ERTY"}}})
    dump(out / "04_access_pass.json", {"note": "Shape of the pass exchange; token and id masked.",
         "request": {"method": "POST", "url": "/api/rf/access", "body": {"access_cookie": "<value of the website's access_token cookie>"}},
         "response": {"status": 200, "body": {"token": "<43 random characters>", "user_id": "<the student's website id>", "expires_at": "2026-11-19T10:15:00+00:00"}},
         "errors": {"401": {"detail": "Your canonical session needs refreshing."}, "503": {"detail": "Could not verify your session. Please retry."}}})

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None

    opener = urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(LIVE + "/j/AAAAAAA", headers={"User-Agent": "Mozilla/5.0 (Linux; Android 14) Chrome/130 Mobile"})
    try:
        opener.open(req, timeout=30)
        raise RuntimeError("share link did not redirect")
    except urllib.error.HTTPError as e:
        head = {k: v for k, v in e.headers.items() if k.lower() in ("location", "cache-control", "referrer-policy", "set-cookie")}
        if "set-cookie" in {k.lower() for k in head}:
            head = {k: (re.sub(r"jlv=[^;]+", "jlv=<random visitor id>", v) if k.lower() == "set-cookie" else v) for k, v in head.items()}
        dump(out / "05_share_link_redirect.json", {"note": "Live answer for an unknown code (not counted). A real code answers the same way; the friend is counted once.",
             "request": {"method": "GET", "url": "/api/j/AAAAAAA", "headers": {"User-Agent": "<a real browser>"}},
             "response": {"status": e.code, "headers": head}})
    try:
        urllib.request.urlopen(LIVE + "/rf/mission/me", timeout=30)
    except urllib.error.HTTPError as e:
        dump(out / "06_signed_out_refused.json", {"note": "Live status without a pass. The app server's own sentence is worded for the app; the connector replaces it.",
             "request": {"method": "GET", "url": "/api/mission/me (website, no session)"},
             "response": {"app_server_status": e.code, "website_sees": {"status": 401, "body": {"detail": "Please sign in again."}}}})


# ------------------------------------------------------------------ checks
def checks():
    files = [f for f in PACK.rglob("*") if f.is_file()]
    bad_names = [str(f.relative_to(PACK)) for f in files if re.search(r"rapid|arena|duel|squad|cheer", f.name, re.I)]
    data_like = [str(f.relative_to(PACK)) for f in files if f.suffix in (".gz", ".csv") or "rank_data" in f.parts]
    imports, mentions = [], {}
    for f in files:
        if f.suffix not in TEXT:
            continue
        text = f.read_text(encoding="utf-8")
        if re.search(r"""from ["'][^"']*rapid""", text):
            imports.append(str(f.relative_to(PACK)))
        n = len(re.findall(r"rapid fire", text, re.I))
        if n:
            mentions[str(f.relative_to(PACK))] = n
    code_mentions = {k: v for k, v in mentions.items() if not k.endswith(".md") and Path(k).name not in COPY_OK}
    assert not bad_names, bad_names
    assert not data_like, data_like
    assert not imports, imports
    assert not code_mentions, code_mentions
    return {"rapid_fire_files": 0, "rapid_fire_imports": 0, "data_files": 0,
            "rapid_fire_words_only_in": mentions}


def manifest(summary):
    files = []
    for f in sorted(PACK.rglob("*")):
        if f.is_file() and f.name != "MANIFEST.json":
            files.append({"path": str(f.relative_to(PACK)), "bytes": f.stat().st_size, "sha256": hashlib.sha256(f.read_bytes()).hexdigest()})
    dump(PACK / "MANIFEST.json", {"built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "live_api": LIVE,
                                  "rule": "No Rank data is copied into this pack: the website reads it from the app server.",
                                  **summary, "files": files})
    return len(files)


def make_zip():
    if ZIP.exists():
        ZIP.unlink()
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in sorted(PACK.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(PACK.parent))
    return ZIP.stat().st_size


if __name__ == "__main__":
    fresh(PACK)
    copy_docs()
    copy_code()
    n_paths = openapi()
    done = api_examples()
    mission_examples()
    summary = {"checks": checks(), "openapi_paths": n_paths, "rank_api_examples": len(done) + 1,  # + the refusals file
               "new_in_this_pack": ["Cut off tool (docs/11)", "Meri details (docs/12)", "scorecard rank in every JEE form",
                                    "Cut off: last-year arrow, Compare, PDF + WhatsApp (docs/11 section 13)",
                                    "All India series on the app + who builds what (docs/13)", "CEO dashboard hand-off (docs/14)"],
               "cut_off_on_live": live_has_cutoff()}
    n = manifest(summary)
    size = make_zip()
    print(json.dumps(summary, indent=1))
    print("files:", n, "zip bytes:", size)
