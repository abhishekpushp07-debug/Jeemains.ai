// Cut questions (website "pieces"): scale rules, picture paths and image grants. Run: node tests/pieces_isolated_tests.cjs
const assert = require("assert");
const fs = require("fs");
const ts = require("/app/frontend/node_modules/typescript");

function load(file, stubs = {}) {
  const js = ts.transpileModule(fs.readFileSync(file, "utf8"), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020, esModuleInterop: true }, fileName: file }).outputText;
  const mod = { exports: {} };
  new Function("require", "module", "exports", js)(id => { if (id in stubs) return stubs[id]; throw new Error("Missing stub: " + id); }, mod, mod.exports);
  return mod.exports;
}
const SRC = "/app/frontend/src/assets";
const pieces = load(`${SRC}/pieces.ts`);
const grants = load(`${SRC}/assetGrants.ts`, { "./pieces": pieces });
const paper = load(`${SRC}/paperAssets.ts`, {
  react: { useCallback: f => f, useLayoutEffect: () => {}, useMemo: f => f() }, "expo-router": { useFocusEffect: () => {} },
  "@/src/api/client": { privateAssets: {}, registerAssetManifest: () => {} }, "./pieces": pieces,
});

const near = (a, b, label) => assert.ok(Math.abs(a - b) < 0.002, `${label}: ${a} vs ${b}`);
const STEM = { part: "q", w: 539.5, h: 90.5 };
const short = [STEM, { part: "A", w: 23, h: 19.5 }, { part: "B", w: 23, h: 19 }, { part: "C", w: 22.5, h: 19.5 }, { part: "D", w: 22, h: 19 }];
const long = [STEM, { part: "A", w: 300, h: 23 }, { part: "B", w: 315, h: 39 }, { part: "C", w: 315, h: 39 }, { part: "D", w: 315, h: 23 }];
const cutQ = { id: "q1", number: 1, subject: "Maths", asset_count: 1, solution_asset_count: 1, pieces: short };
const wholeQ = { id: "q2", number: 2, subject: "Maths", asset_count: 2, solution_asset_count: 1 };
const paper0 = p => p.questions.flatMap(q => paper.questionPaths("a1", q));

const tests = {
  "piecesOf: only a non-empty list counts"() {
    assert.strictEqual(pieces.piecesOf(null), null);
    assert.strictEqual(pieces.piecesOf({}), null);
    assert.strictEqual(pieces.piecesOf({ pieces: [] }), null);
    assert.strictEqual(pieces.piecesOf(cutQ), short);
  },
  "owner's rule: a PYQ paper keeps its original look; mocks, chapter tests and the All India series keep their pieces"() {
    const paper = extra => ({ ...extra, questions: [{ ...cutQ }, { ...wholeQ }] });
    for (const pyq of [paper({ test_kind: "pyq", set_id: "jee-main-pyq-2026-04-08-s2" }), paper({ set_id: "jee-main-pyq-2025-01-22-s2" }), paper({ test_kind: "pyq" })]) {
      assert.strictEqual(pieces.isPyq(pyq), true);
      assert.strictEqual(pieces.originalLook(pyq), pyq);
      assert.strictEqual(pieces.piecesOf(pyq.questions[0]), null, "pieces dropped");
      // ... so the paper asks for its whole pictures, exactly as before the cut look existed.
      assert.deepStrictEqual(paper0(pyq), ["/attempts/a1/questions/q1/asset/question/0", "/attempts/a1/questions/q2/asset/question/0", "/attempts/a1/questions/q2/asset/question/1"]);
    }
    for (const other of [paper({ test_kind: "chapter", set_id: "f6ad0ca5-b3c8-59dc-a814-e358c197dd7a" }), paper({ test_kind: "mock", set_id: "bitsat-mock-01" }), paper({ test_kind: "series", mode: "series_live", series_id: "s1" }), paper({})]) {
      assert.strictEqual(pieces.isPyq(other), false);
      assert.strictEqual(pieces.piecesOf(pieces.originalLook(other).questions[0]), short, "pieces kept");
    }
    for (const empty of [null, undefined, {}, { test_kind: "pyq" }, { test_kind: "pyq", questions: [null] }]) assert.strictEqual(pieces.originalLook(empty), empty);
  },
  "phone (328 column): the question fits the paper, short options come at the printed size"() {
    const s = pieces.pieceLayout(short, null, 328);
    near(s.stem, (328 - 30) / 539.5, "stem");
    near(s.option, 1, "option");
  },
  "phone: long options take the whole card width (letter above the paper) and shrink together until the widest fits"() {
    const s = pieces.pieceLayout(long, null, 328);
    assert.strictEqual(s.stack, true);
    near(s.option, (328 - 50) / 315, "option");
    assert.ok(s.option > s.stem, "options stay larger than the shrunk question");
    assert.strictEqual(pieces.pieceLayout(short, null, 328).stack, false, "short options stay beside their letter");
    // An option that fits at its printed size beside the letter is never stacked.
    assert.strictEqual(pieces.pieceLayout([STEM, { part: "A", w: 198, h: 20 }], null, 328).stack, false);
    assert.strictEqual(pieces.pieceLayout([STEM, { part: "A", w: 199, h: 20 }], null, 328).stack, true);
  },
  "tablet (728 column): question and options share one scale, never past 1.5x"() {
    const s = pieces.pieceLayout(long, null, 728);
    near(s.stem, (728 - 30) / 539.5, "stem");
    near(s.option, s.stem, "option");
    assert.strictEqual(s.stack, false);
    near(pieces.pieceLayout(short, null, 2000).stem, 1.5, "cap");
  },
  "zoom: question and options grow alike; what no longer fits scrolls sideways in its paper"() {
    const z = pieces.PIECE_ZOOM[2];
    near(pieces.pieceLayout(short, null, 328, z).stem, z * (328 - 30) / 539.5, "stem");
    near(pieces.pieceLayout(short, null, 328, z).option, z, "short option");
    near(pieces.pieceLayout(long, null, 328, z).option, z * (328 - 50) / 315, "long option");
  },
  "without zoom nothing leaves its paper at any width"() {
    for (const width of [288, 320, 328, 358, 380, 568, 728]) for (const set of [short, long]) {
      const s = pieces.pieceLayout(set, null, width), widest = Math.max(...set.filter(p => p.part !== "q").map(p => p.w));
      assert.ok(widest * s.option <= width - (s.stack ? 50 : 130) + 0.001, `option width ${width}`);
      assert.ok(539.5 * s.stem <= width - 30 + 0.001, `stem width ${width}`);
    }
  },
  "a typed option does not shrink the pictures of the others"() {
    near(pieces.pieceLayout(long, { B: "x", C: "y", D: "z" }, 328).option, (328 - 50) / 300, "option");
    near(pieces.pieceLayout([STEM], null, 328).option, 1, "no option pictures");
  },
  "paths: a cut question is drawn from its pieces, any other from its whole picture"() {
    assert.deepStrictEqual(paper.questionPaths("a1", cutQ), [0, 1, 2, 3, 4].map(i => `/attempts/a1/questions/q1/asset/piece/${i}`));
    assert.deepStrictEqual(paper.questionPaths("a1", wholeQ), [0, 1].map(i => `/attempts/a1/questions/q2/asset/question/${i}`));
    assert.deepStrictEqual(paper.imagePaths("a1", cutQ, "piece", "v2")[0], "/attempts/a1/questions/q1/asset/piece/0?score_version=v2");
    assert.deepStrictEqual(paper.imagePaths("a1", wholeQ, "piece"), []);
    const all = paper.prioritizedPaths("a1", [wholeQ, cutQ], "q1", true);
    assert.strictEqual(all[0], "/attempts/a1/questions/q1/asset/piece/0");
    assert.ok(all.includes("/attempts/a1/questions/q1/asset/solution/0") && !all.includes("/attempts/a1/questions/q1/asset/question/0"));
  },
  "warm sizes: every piece of the neighbouring questions at its drawn size"() {
    const rows = [{ ...cutQ, id: "q0" }, cutQ, { ...cutQ, id: "q3", pieces: long }, wholeQ];
    const sizes = paper.pieceWarmSizes("a1", rows, "q1", 328, 1);
    assert.strictEqual(Object.keys(sizes).length, 10);
    near(sizes["/attempts/a1/questions/q3/asset/piece/0"].width, 298, "stem width");
    near(sizes["/attempts/a1/questions/q3/asset/piece/2"].width, 278, "option width");
    near(sizes["/attempts/a1/questions/q0/asset/piece/1"].height, 19.5, "option height");
    assert.deepStrictEqual(paper.pieceWarmSizes("a1", [], undefined, 328), {});
  },
  "grants: pieces replace the whole picture; other questions keep their old cache keys"() {
    const dropped = [];
    grants.clearImageGrants();
    grants.registerImageGrants("a1", [cutQ, wholeQ], true, "original", p => dropped.push(p));
    for (let i = 0; i < 5; i++) assert.ok(grants.imageGrant(`/attempts/a1/questions/q1/asset/piece/${i}`), `piece ${i}`);
    assert.strictEqual(grants.imageGrant("/attempts/a1/questions/q1/asset/piece/5"), undefined);
    assert.strictEqual(grants.imageGrant("/attempts/a1/questions/q1/asset/question/0"), undefined);
    assert.ok(grants.imageGrant("/attempts/a1/questions/q1/asset/solution/0"));
    assert.strictEqual(grants.imageGrant("/attempts/a1/questions/q2/asset/question/1").contentKey, JSON.stringify(["q2", "question", 1, "original", 2, null]));
    assert.strictEqual(grants.imageGrant("/attempts/a1/questions/q1/asset/piece/1").contentKey, JSON.stringify(["q1", "piece", 1, "original", 5, null, "A", 23, 19.5]));
    // A paper that stops sending pieces goes back to its whole picture and forgets the piece grants.
    grants.registerImageGrants("a1", [{ ...cutQ, pieces: null }, wholeQ], false, "original", p => dropped.push(p));
    assert.strictEqual(grants.imageGrant("/attempts/a1/questions/q1/asset/piece/0"), undefined);
    assert.ok(grants.imageGrant("/attempts/a1/questions/q1/asset/question/0"));
    assert.ok(dropped.includes("/attempts/a1/questions/q1/asset/piece/0"));
  },
  async "text size: kept on the phone, clamped to the three steps; a pick made before the saved size arrives wins"() {
    const saved = {}, calls = [];
    const store = (was, wait = 0) => load(`${SRC}/pieceZoom.ts`, {
      react: { useSyncExternalStore: (subscribe, read) => { subscribe(() => calls.push(read())); return read(); } },
      "@/src/utils/storage": { storage: { getItem: async (k, fallback) => { await new Promise(r => setTimeout(r, wait)); return was ?? fallback; }, setItem: async (k, v) => { saved[k] = v; return true; } } },
      "./pieces": pieces,
    });
    const first = store(null);
    assert.strictEqual(first.usePieceZoom(), 0);
    first.setPieceZoom(1); first.setPieceZoom(9); first.setPieceZoom(-4);
    assert.deepStrictEqual(calls, [1, 2, 0]);
    assert.strictEqual(saved["piece.zoom.v1"], 0);
    const second = store(2);
    await new Promise(r => setTimeout(r, 5));
    assert.strictEqual(second.usePieceZoom(), 2, "the saved size comes back");
    const third = store(2, 20);
    third.setPieceZoom(1);
    await new Promise(r => setTimeout(r, 40));
    assert.strictEqual(third.usePieceZoom(), 1, "a late read does not undo the student's pick");
  },
  async "paper pack: a cut paper asks for look=cut and keeps every piece under its own path"() {
    const rows = ["q1", "q2", "q3"].map(id => ({ ...cutQ, id })); // 15 pieces: parts of 12 + 3
    const all = rows.flatMap(q => paper.questionPaths("a1", q));
    const run = await pack(rows, { links: null, items: all.map((path, i) => ({ question_id: path.split("/")[4], kind: "piece", index: Number(path.split("/").pop()), size: 3 + (i % 4) })) });
    assert.deepStrictEqual(run.asked, ["/attempts/a1/assets/links?look=cut", "/attempts/a1/assets/pack?offset=0&limit=12&look=cut", "/attempts/a1/assets/pack?offset=12&limit=12&look=cut"]);
    assert.deepStrictEqual(run.kept.map(k => k.path).sort(), [...all].sort());
    assert.ok(run.kept.every(k => k.bytes === 3 + (all.indexOf(k.path) % 4)), "every piece keeps its own bytes");
    assert.deepStrictEqual(run.preloaded, [[]]);
  },
  async "paper pack: a paper without pieces (every PYQ paper) is asked for exactly as before, one part after the other"() {
    const rows = Array.from({ length: 30 }, (_, i) => ({ id: `w${i}`, asset_count: 1 }));
    const run = await pack(rows, { links: ["/cdn/0", "/cdn/1", "/cdn/2"], items: rows.map(q => ({ question_id: q.id, index: 0, size: 5 })) });
    assert.deepStrictEqual(run.asked, ["/attempts/a1/assets/links", "cdn:https://jeelive.ai/cdn/0", "cdn:https://jeelive.ai/cdn/1", "cdn:https://jeelive.ai/cdn/2"]);
    assert.strictEqual(run.kept.length, 30);
    assert.ok(run.kept.every(k => /^\/attempts\/a1\/questions\/w\d+\/asset\/question\/0$/.test(k.path)));
    assert.strictEqual(run.busiest, 1);
  },
  async "paper pack: a cut paper loads two parts at a time"() {
    const rows = Array.from({ length: 8 }, (_, i) => ({ ...cutQ, id: `c${i}` })); // 40 pieces: 4 parts
    const all = rows.flatMap(q => paper.questionPaths("a1", q));
    const run = await pack(rows, { links: ["/cdn/0", "/cdn/1", "/cdn/2", "/cdn/3"], items: all.map(path => ({ question_id: path.split("/")[4], kind: "piece", index: Number(path.split("/").pop()), size: 4 })) });
    assert.strictEqual(run.asked[0], "/attempts/a1/assets/links?look=cut");
    assert.strictEqual(run.kept.length, 40);
    assert.strictEqual(run.busiest, 2);
  },
  async "paper pack: a part that fails leaves the rest to the normal image queue"() {
    const rows = ["q1", "q2", "q3"].map(id => ({ ...cutQ, id }));
    const all = rows.flatMap(q => paper.questionPaths("a1", q));
    const run = await pack(rows, { links: null, failFrom: 12, items: all.map(path => ({ question_id: path.split("/")[4], kind: "piece", index: Number(path.split("/").pop()), size: 4 })) });
    assert.strictEqual(run.kept.length, 12);
    assert.deepStrictEqual(run.preloaded, [all.slice(12)]);
  },
};

// Runs usePaperPack once against a fake website: `items` is the whole paper in order, 12 pictures to a part.
async function pack(rows, { links, items, failFrom = Infinity }) {
  const asked = [], kept = [], preloaded = [];
  let open = 0, busiest = 0;
  const part = offset => {
    const slice = items.slice(offset, offset + 12), header = Buffer.from(JSON.stringify({ total: items.length, items: slice }));
    const length = Buffer.alloc(4); length.writeUInt32BE(header.length);
    return new Uint8Array(Buffer.concat([length, header, ...slice.map(item => Buffer.alloc(item.size, 7))]));
  };
  const slow = async value => { busiest = Math.max(busiest, ++open); await new Promise(r => setTimeout(r, 5)); open--; return value; };
  grants.clearImageGrants();
  grants.registerImageGrants("a1", rows, false, "original", () => {});
  const effects = [];
  const realFetch = global.fetch;
  global.fetch = async url => { asked.push("cdn:" + url); const k = Number(String(url).split("/").pop()); return slow({ ok: true, arrayBuffer: async () => part(k * 12).buffer }); };
  const mod = load(`${SRC}/paperPack.ts`, {
    react: { useEffect: f => effects.push(f), useMemo: f => f(), useState: v => [v, () => {}] },
    "@/src/api/client": {
      api: async path => { asked.push(path); if (!links) throw new Error("no links"); return { total: items.length, limit: 12, parts: links }; },
      apiBytes: async path => { asked.push(path); const offset = Number(/offset=(\d+)/.exec(path)[1]); if (offset >= failFrom) throw new Error("part failed"); return slow(part(offset)); },
      privateAssets: { status: path => (kept.some(k => k.path === path) ? "ready" : "idle"), adopt: (path, value) => { kept.push({ path, bytes: value.bytes }); return true; }, preload: paths => preloaded.push(paths) },
      websiteHomeUrl: () => "https://jeelive.ai/",
    },
    "./assetGrants": grants, "./imageDownload": { originalImageValue: async image => ({ uri: "x", bytes: image.bytes.length }) },
    "./deviceCache/cache": { saveImage: async () => {} }, "./paperAssets": paper, "./pieces": pieces,
  });
  mod.usePaperPack("a1", rows, true);
  const stop = effects[0]();
  await new Promise(r => setTimeout(r, 120));
  stop(); global.fetch = realFetch;
  return { asked, kept, preloaded, busiest };
}

(async () => {
  let failed = 0;
  for (const [name, run] of Object.entries(tests)) {
    try { await run(); console.log("PASS", name); } catch (e) { failed++; console.log("FAIL", name, "\n  ", e.message); }
  }
  console.log(failed ? `${failed} FAILED` : `ALL ${Object.keys(tests).length} PASSED`);
  process.exit(failed ? 1 : 0);
})();
