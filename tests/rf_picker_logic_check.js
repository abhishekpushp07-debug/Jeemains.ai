// Rapid Fire's chapter picker, the part with no screen (frontend/src/rapid/scope.ts), against the real chapter bank.
// Run: node /app/tests/rf_picker_logic_check.js   (the app's server must be up; exit code 1 when a check fails)
// Nothing is written anywhere: it reads the public catalog and asks backend/scope.py for the name of each list.
const ts = require("/app/frontend/node_modules/typescript");
const fs = require("fs");
const { execFileSync } = require("child_process");
const src = fs.readFileSync("/app/frontend/src/rapid/scope.ts", "utf8");
const js = ts.transpileModule(src, { compilerOptions: { module: "commonjs", target: "es2019", esModuleInterop: true } }).outputText;
const stand = { react: { useSyncExternalStore: () => undefined }, "@react-native-async-storage/async-storage": { __esModule: true, default: { getItem: async () => null, setItem: async () => undefined } } };
const m = { exports: {} };
new Function("module", "exports", "require", js)(m, m.exports, (name) => stand[name] || require(name));
const S = m.exports;

let bad = 0;
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
function check(name, ok, detail = "") { if (!ok) bad++; console.log((ok ? "PASS " : "FAIL ") + name + (detail !== "" ? " | " + detail : "")); }
const oldEncode = (picks) => JSON.stringify(S.normalise(picks)); // the route param exactly as it was before 27 Nov 2026
const whole = (name) => ({ subject: name, chapter: null });

(async () => {
  const cat = await (await fetch("http://localhost:8001/api/rf/catalog?exam=JEE")).json();
  const subjects = cat.subjects, by = Object.fromEntries(subjects.map((s) => [s.name, s]));
  const names = (s) => by[s].chapters.filter((c) => c.count > 0).map((c) => c.name);
  const P = by.Physics, C = by.Chemistry, M = by.Mathematics, E = by.English, pcm = [P, C, M];
  const total = subjects.reduce((n, s) => n + names(s.name).length, 0);
  console.log(`bank: ${subjects.map((s) => `${S.SHORT[s.name]} ${names(s.name).length}`).join(", ")} = ${total} chapters`);
  check("the ceiling of one list is above every chapter of the bank", S.MAX_PICKS >= total, `${S.MAX_PICKS} >= ${total}`);

  // --- nothing ticked, one chapter, several chapters ---
  let d = [];
  check("nothing ticked: nothing to play, no cards", same(S.picksToPlay(d, subjects), []) && S.cardCount(d, subjects) === 0);
  d = S.tickChapter(d, P, names("Physics")[0]);
  check("one tick is one chapter", same(d, [{ subject: "Physics", chapter: names("Physics")[0] }]) && S.scopeLabel(d) === names("Physics")[0]);
  d = S.tickChapter(d, P, names("Physics")[0]);
  check("the same tap again unticks it", same(d, []));
  for (const c of names("Physics").slice(0, 7)) d = S.tickChapter(d, P, c);
  check("seven chapters can be ticked (5 was the most before)", d.length === 7 && S.tickedOf(d, P).length === 7 && !S.allTicked(d, P), S.scopeLabel(d));
  check("…and are named by their number", S.scopeLabel(d) === "7 chapters · Physics");

  // --- Select all, and unticking after it ---
  let all = S.tickAll([], pcm, true);
  check("Select all on the PCM tab is PCM Mixed, three whole subjects", S.isPCM(all) && S.scopeLabel(all) === "PCM Mixed" && same(S.picksToPlay(all, subjects), all));
  check("…sent exactly as before", S.encodePicks(all) === oldEncode(S.PCM) && S.encodePicks(all) === '[{"subject":"Physics","chapter":null},{"subject":"Chemistry","chapter":null},{"subject":"Mathematics","chapter":null}]');
  check("…every chapter of the three subjects shows ticked", pcm.every((s) => S.allTicked(all, s) && S.tickedOf(all, s).length === names(s.name).length));
  const gone = names("Physics")[3];
  let less = S.tickChapter(all, P, gone);
  check("one chapter can be unticked after Select all", !S.tickedOf(less, P).includes(gone) && S.tickedOf(less, P).length === names("Physics").length - 1 && S.allTicked(less, C) && S.allTicked(less, M) && !S.allTicked(less, P));
  const play = S.picksToPlay(less, subjects);
  const pcmChapters = pcm.reduce((n, s) => n + names(s.name).length, 0);
  check("…the round is then on every ticked chapter, one by one", play.length === pcmChapters - 1 && play.every((p) => p.chapter) && !play.some((p) => p.subject === "Physics" && p.chapter === gone), `${play.length} chapters`);
  check("…with the same number of cards as the ticks show", S.cardCount(play, subjects) === S.cardCount(less, subjects));
  check("…named by its number", S.scopeLabel(play) === `${pcmChapters - 1} chapters · PCM`, S.scopeLabel(play));
  check("ticking that chapter again gives PCM Mixed back", same(S.tickChapter(less, P, gone), all));
  let chem = [];
  for (const c of names("Chemistry")) chem = S.tickChapter(chem, C, c);
  check("every chapter of a subject ticked one by one is the whole subject", same(chem, [whole("Chemistry")]) && S.scopeLabel(chem) === "Mixed Chemistry");
  const loose = [whole("Physics"), ...names("Chemistry").map((c) => ({ subject: "Chemistry", chapter: c }))];
  check("…also when the list arrives that way from an older screen", same(S.picksToPlay(loose, subjects), [whole("Physics"), whole("Chemistry")]));

  // --- Clear, and tabs that do not touch each other ---
  let mixed = S.tickChapter(S.tickChapter(all, E, names("English")[0]), E, names("English")[1]);
  check("ticks in English stay when PCM is cleared", same(S.tickAll(mixed, pcm, false), [0, 1].map((k) => ({ subject: "English", chapter: names("English")[k] })).sort((a, b) => a.chapter.localeCompare(b.chapter))));
  check("Clear on one subject leaves the others", same(S.tickAll(all, [C], false), [whole("Physics"), whole("Mathematics")]));
  check("Select all on one subject keeps the single chapters of another", same(S.tickAll([{ subject: "Physics", chapter: gone }], [C], true), [{ subject: "Physics", chapter: gone }, whole("Chemistry")]));
  const sent = S.picksToPlay(S.tickAll([{ subject: "Physics", chapter: gone }], [C], true), subjects);
  check("…and that round is on 1 + every chapter of Chemistry, an even share each", sent.length === 1 + names("Chemistry").length && sent.every((p) => p.chapter));
  const twin = names("Physics").find((c) => names("Chemistry").includes(c));
  if (twin) check(`a chapter with the same name in two subjects ("${twin}") is ticked in one only`, S.tickedOf(S.tickChapter([], P, twin), C).length === 0);

  // --- the route param ---
  const lists = { "PCM Mixed": all, "one chapter": [{ subject: "Physics", chapter: gone }], "five picks": [whole("Mathematics"), ...names("Chemistry").slice(0, 4).map((c) => ({ subject: "Chemistry", chapter: c }))],
    "six chapters": names("Physics").slice(0, 6).map((c) => ({ subject: "Physics", chapter: c })), "PCM but one chapter": play,
    "every chapter but one of each subject": subjects.flatMap((s) => names(s.name).slice(1).map((c) => ({ subject: s.name, chapter: c }))),
    "every chapter of the bank, one by one": subjects.flatMap((s) => names(s.name).map((c) => ({ subject: s.name, chapter: c }))) };
  let longest = 0;
  for (const [name, picks] of Object.entries(lists)) {
    const enc = S.encodePicks(picks), url = encodeURIComponent(enc).length, back = S.decodePicks(enc);
    longest = Math.max(longest, url);
    check(`route param, ${name}: comes back the same`, same(back, S.normalise(picks)), `${picks.length} picks, ${url} bytes in an address (${encodeURIComponent(oldEncode(picks)).length} in the old form)`);
    if (picks.length <= S.CLASSIC_PICKS) check(`route param, ${name}: byte for byte as before`, enc === oldEncode(picks));
    check(`route param, ${name}: the old form is still read`, same(S.decodePicks(oldEncode(picks)), S.normalise(picks)));
  }
  check("the longest list fits an address with room to spare", longest < 4000, `${longest} bytes; servers take 8000`);
  check("a list above the ceiling, junk and an unknown subject are refused", S.decodePicks(JSON.stringify(Array.from({ length: S.MAX_PICKS + 1 }, (_, k) => ({ subject: "Physics", chapter: "x" + k })))) === null
    && S.decodePicks("{") === null && S.decodePicks("7") === null && S.decodePicks('{"Biology":0}') === null && S.decodePicks('[{"subject":"Biology"}]') === null && S.decodePicks("") === null);

  // --- the app's name of a list is the server's name of it ---
  const all5 = [...Object.values(lists), [whole("Physics")], [whole("English"), whole("Logical Reasoning")], [whole("Physics"), ...names("Chemistry").slice(0, 6).map((c) => ({ subject: "Chemistry", chapter: c }))],
    names("English").slice(0, 6).map((c) => ({ subject: "English", chapter: c })), [...names("Physics").slice(0, 3), ...[]].map((c) => ({ subject: "Physics", chapter: c })).concat(names("Mathematics").slice(0, 4).map((c) => ({ subject: "Mathematics", chapter: c })))];
  const py = "import json,sys; sys.path.insert(0,'/app/backend'); from scope import normalise,label_of; print(json.dumps([label_of(normalise(p)) for p in json.load(sys.stdin)]))";
  const server = JSON.parse(execFileSync("python3", ["-c", py], { input: JSON.stringify(all5), encoding: "utf8" }));
  all5.forEach((picks, k) => check(`same name in the app and on the server: ${server[k]}`, S.scopeLabel(S.normalise(picks)) === server[k], S.scopeLabel(S.normalise(picks)) === server[k] ? "" : `app says ${S.scopeLabel(S.normalise(picks))}`));

  console.log(bad ? `${bad} FAILED` : "all passed");
  process.exit(bad ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
