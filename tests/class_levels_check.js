// Class 11 / Class 12: the app's own lookup (frontend/src/classLevel.ts) against the server's (backend/class_levels.py),
// on the real chapters: Rapid Fire's bank (read from the app's server) and the website's chapter-wise lists as they were
// on 27 Nov 2026 (tests/data/website_chapters_27nov2026.json).
// Run: node /app/tests/class_levels_check.js   (the app's server must be up; exit code 1 when a check fails)
// Nothing is written anywhere.
const ts = require("/app/frontend/node_modules/typescript");
const fs = require("fs");
const { execFileSync } = require("child_process");
const src = fs.readFileSync("/app/frontend/src/classLevel.ts", "utf8");
const js = ts.transpileModule(src, { compilerOptions: { module: "commonjs", target: "es2019", esModuleInterop: true } }).outputText;
const book = JSON.parse(fs.readFileSync("/app/frontend/src/classLevels.json", "utf8"));
let switches = null, heard = null, asked = [];
const stand = {
  react: { useSyncExternalStore: (_sub, get) => get() },
  "@/src/api/client": { BACKEND: "http://server", appSwitches: () => switches, onAppSwitches: (listener) => { heard = listener; return () => {}; } },
  "./classLevels.json": book,
};
const load = (fetcher) => { // a fresh copy of the module, as at an app launch
  global.fetch = fetcher;
  const m = { exports: {} };
  new Function("module", "exports", "require", js)(m, m.exports, (name) => stand[name] || require(name));
  return m.exports;
};
const pause = () => new Promise((r) => setTimeout(r, 20));

let bad = 0;
function check(name, ok, detail = "") { if (!ok) bad++; console.log((ok ? "PASS " : "FAIL ") + name + (detail !== "" ? " | " + detail : "")); }

(async () => {
  const cat = await (await fetch("http://localhost:8001/api/rf/catalog?exam=JEE")).json();
  const website = JSON.parse(fs.readFileSync("/app/tests/data/website_chapters_27nov2026.json", "utf8"));
  const rows = [];
  for (const s of cat.subjects) for (const c of s.chapters) rows.push(["jee-main", s.name, c.name]);
  for (const [exam, subjects] of Object.entries(website)) for (const [subject, list] of Object.entries(subjects)) for (const r of list) rows.push([exam, subject, r.title]);
  for (const odd of ["  7.  Gravitation ", "3D Geometry", "12) p-Block", "d & f Block", "Résumé & Co", "", "24 Miscellaneous (beyond the current syllabus)"]) rows.push(["jee-main", "Physics", odd], ["jee-main", "Chemistry", odd], ["jee-main", "Mathematics", odd]);

  // 1. no switches answer yet: the list that came with the app is used, and nothing is asked for
  asked = []; switches = null;
  let S = load((url) => { asked.push(url); return Promise.reject(new Error("no network in this check")); });
  check("the list that comes with the app is used without asking anybody", asked.length === 0 && S.useClassBook() === book.version);
  const py = JSON.parse(execFileSync("python3", ["-c", `
import json, sys
sys.path.insert(0, "/app/backend")
import class_levels
rows = json.load(sys.stdin)
print(json.dumps([[class_levels.key(t), class_levels.level_of(e, s, t)] for e, s, t in rows]))`], { input: JSON.stringify(rows) }).toString());
  const differ = rows.filter(([e, s, t], i) => S.classKey(t) !== py[i][0] || S.classOf(e, s, t) !== py[i][1]);
  check(`the app and the server agree on all ${rows.length} names`, differ.length === 0, differ.slice(0, 3).map((r) => r.join(" / ")).join("; "));
  const of = (subject, level) => cat.subjects.find((s) => s.name === subject).chapters.filter((c) => S.classOf("jee-main", subject, c.name) === level).length;
  check("Rapid Fire: every Physics, Chemistry and Maths chapter has a class", ["Physics", "Chemistry", "Mathematics"].every((s) => of(s, null) === 0 && of(s, 11) > 0 && of(s, 12) > 0),
    ["Physics", "Chemistry", "Mathematics"].map((s) => `${s} ${of(s, 11)} + ${of(s, 12)}`).join(", "));
  check("English and Reasoning are not split into classes", !S.hasClasses("jee-main", "English") && !S.hasClasses("jee-main", "Logical Reasoning") && S.hasClasses("jee-main", "Physics"));
  check("another exam is left alone until the list names it", !S.hasClasses("bitsat", "Mathematics") && S.classOf("bitsat", "Mathematics", "Limits") === null);

  // 2. the server says the same number: still nothing is asked for
  switches = { pictures: 5, matched: false, classes: book.version }; heard();
  await pause();
  check("the server's list has the same number: nothing is fetched", asked.length === 0);

  // 3. the server says a newer number: the list is fetched once and used
  const newer = { version: book.version + 1, exams: { "jee-main": { ...book.exams["jee-main"], Physics: { ...book.exams["jee-main"].Physics, kinematics: 12 } }, bitsat: { Mathematics: { limits: 11 } } } };
  asked = []; switches = null;
  S = load((url) => { asked.push(url); return Promise.resolve({ ok: true, json: async () => newer }); });
  switches = { classes: newer.version }; heard(); heard();
  await pause();
  check("a newer list is fetched once, by its number", asked.length === 1 && asked[0] === `http://server/api/app/classes?v=${newer.version}`, asked.join(" "));
  check("…and used from then on", S.useClassBook() === newer.version && S.classOf("jee-main", "Physics", "02 Kinematics") === 12 && S.classOf("bitsat", "Mathematics", "12 Limits") === 11 && S.hasClasses("bitsat", "Mathematics"));

  // 4. a list that is not newer, or not a list, is not used; a failed fetch is tried again with the next answer
  for (const [name, answer] of [["an older list", { version: book.version, exams: {} }], ["a broken answer", { version: "2" }], ["no answer", null]]) {
    asked = []; switches = null;
    S = load((url) => { asked.push(url); return Promise.resolve({ ok: true, json: async () => answer }); });
    switches = { classes: book.version + 1 }; heard();
    await pause();
    check(`${name} is not used`, S.useClassBook() === book.version && S.classOf("jee-main", "Physics", "Kinematics") === 11);
  }
  asked = []; switches = null;
  S = load((url) => { asked.push(url); return Promise.resolve({ ok: false, status: 503 }); });
  switches = { classes: book.version + 1 }; heard();
  await pause(); heard(); await pause();
  check("a fetch that failed is tried again with the next switches answer", asked.length === 2 && S.useClassBook() === book.version);

  console.log(bad ? `${bad} FAILED` : "all passed");
  process.exit(bad ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
