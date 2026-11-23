// The website's new picture answers (memory/PICTURES_APP.md, memory/WEBSITE_PICTURES_REPLY_2.md) against a pretend
// website that answers exactly as its note says: the owner's switch, asset_revision, format=webp, parts for a finished
// attempt, kind=solution, and every trap of the note's section 5. Run: node tests/pictures_new_answers_tests.cjs
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

const PNG = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]), WEBP = Buffer.from("RIFF\0\0\0\0WEBPVP8L", "latin1");
const picture = (webp, size, fill = 7) => { const b = Buffer.alloc(size, fill); (webp ? WEBP : PNG).copy(b); return new Uint8Array(b); };
const refused = status => Object.assign(new Error("refused " + status), { status });
const paperRows = (n, extra = {}) => Array.from({ length: n }, (_, i) => ({ id: `q${i}`, asset_count: 1, solution_asset_count: 1, asset_revision: `r${i}`.padEnd(16, "0"), ...extra }));
const CUT = [{ part: "q", w: 500, h: 90 }, { part: "A", w: 23, h: 19 }, { part: "B", w: 23, h: 19 }, { part: "C", w: 23, h: 19 }, { part: "D", w: 23, h: 19 }];
const pathsOf = (rows, solution, version = "original") => rows.flatMap(q => solution ? paper.imagePaths("a1", q, "solution", version) : paper.questionPaths("a1", q, version));
const keyOf = path => grants.imageGrant(path).contentKey;

// ---- The pretend website -------------------------------------------------------------------------------------------
// `old`: it still gives its old answers (ignores kind=solution and format=webp, no etag, flags 0 to 3).
function website(rows, { old = false, refuses = 0, sealed = false, noLinks = false, brokenLinks = false, failPackFrom = Infinity } = {}) {
  const list = solution => rows.flatMap(q => solution
    ? Array.from({ length: q.solution_asset_count || 0 }, (_, i) => ({ question_id: q.id, kind: "solution", index: i }))
    : q.pieces ? q.pieces.map((_, i) => ({ question_id: q.id, kind: "piece", index: i })) : Array.from({ length: q.asset_count || 0 }, (_, i) => ({ question_id: q.id, index: i })));
  const read = path => {
    const u = new URL(path, "https://x");
    return { solution: !old && u.searchParams.get("kind") === "solution", webp: !old && u.searchParams.get("format") === "webp", cut: u.searchParams.get("look") === "cut", offset: Number(u.searchParams.get("offset")) || 0 };
  };
  const etag = (item, webp) => `${webp ? "aa" : "bb"}${Buffer.from(`${item.question_id}${item.kind || ""}${item.index}`).toString("hex")}`.padEnd(32, "0").slice(0, 32);
  const part = (offset, solution, webp) => {
    const slice = list(solution).slice(offset, offset + 12).map((item, i) => ({ ...item, size: 16 + ((offset + i) % 5), ...(old ? {} : { etag: etag(item, webp) }) }));
    const header = Buffer.from(JSON.stringify({ total: list(solution).length, items: slice })), length = Buffer.alloc(4);
    length.writeUInt32BE(header.length);
    return new Uint8Array(Buffer.concat([length, header, ...slice.map(item => picture(webp, item.size))]));
  };
  return {
    etag,
    links(path) {
      const w = read(path);
      if (refuses) throw refused(refuses);
      if (w.solution && sealed) throw refused(403);
      if (noLinks) throw refused(404);
      const flags = old ? (w.cut ? 3 : 1) : 1 + (w.cut ? 2 : 0) + 4 + (w.solution ? 8 : 0) + (w.webp ? 16 : 0), total = list(w.solution).length;
      return { total, limit: 12, cdn: false, expires_at: "2026-11-25T00:00:00Z", parts: Array.from({ length: Math.ceil(total / 12) }, (_, k) => `/api/media/pack/pk1/${k * 12}-12-${flags}-1764028800-sig${k}.bin`) };
    },
    link(url) {
      const [, offset, flags] = /\/(\d+)-12-(\d+)-/.exec(url);
      return brokenLinks ? null : part(Number(offset), !!(flags & 8), !!(flags & 16));
    },
    pack(path) {
      const w = read(path);
      if (refuses) throw refused(refuses);
      if (w.solution && sealed) throw refused(403);
      if (w.offset >= failPackFrom) throw refused(503);
      return part(w.offset, w.solution, w.webp);
    },
  };
}

// Opens a released result once. `onPhone`: the paths already kept on this phone; `waiting`: paths a screen is waiting for.
async function result(rows, site, { step = 5, version = "original", onPhone = [], waiting = [], noDisk = false, leaveAfter = Infinity, getReady = false } = {}) {
  const asked = [], saved = [], adopted = [], preloaded = [], effects = [];
  let open = 0, busiest = 0, fetched = 0;
  const slow = async value => { busiest = Math.max(busiest, ++open); await new Promise(r => setTimeout(r, 4)); open--; return value; };
  grants.clearImageGrants();
  grants.registerImageGrants("a1", rows, !getReady, version, () => {}, false, step);
  const have = new Set(onPhone.map(keyOf));
  const realFetch = global.fetch;
  global.fetch = async url => {
    const name = String(url).split("/").pop().split("-");
    asked.push(`link ${name[0]} flags ${name[2]}`); fetched++;
    assert.ok(String(url).startsWith("https://jeelive.ai/api/media/pack/"), "a link without a host is joined to the website");
    const bytes = site.link(String(url));
    return slow(bytes ? { ok: true, arrayBuffer: async () => bytes.buffer } : { ok: false, status: 502 });
  };
  const mod = load(`${SRC}/paperPack.ts`, {
    react: { useEffect: f => effects.push(f), useMemo: f => f(), useState: v => [v, () => {}] },
    "@/src/api/client": {
      api: async path => { asked.push(path); return site.links(path); },
      apiBytes: async path => { asked.push(path); fetched++; return slow(site.pack(path)); },
      onAssetScopeReset: () => () => {},
      privateAssets: {
        status: path => (adopted.some(a => a.path === path) ? "ready" : waiting.includes(path) ? "loading" : "idle"),
        adopt: (path, value) => { adopted.push({ path, bytes: value.bytes }); return true; },
        preload: paths => preloaded.push(paths),
        isGroup: () => fetched < leaveAfter,
      },
      websiteHomeUrl: () => "https://jeelive.ai/",
    },
    "./assetGrants": grants, "./imageDownload": { originalImageValue: async image => ({ uri: "x", bytes: image.bytes.length }) },
    "./deviceCache/cache": {
      saveImage: async (key, image) => { saved.push({ key, mime: image.mime, etag: image.etag, size: image.bytes.length }); },
      savedImages: async keys => (noDisk ? null : keys.map(k => have.has(k))),
    },
    "./paperAssets": paper, "./pieces": pieces,
  });
  let took, stop;
  if (getReady) { mod.usePaperPack("a1", rows, true); stop = effects[0](); await new Promise(r => setTimeout(r, 120)); stop(); }
  else {
    took = mod.loadResultPictures("a1", rows, version);
    for (let i = 0; i < 200 && paper.partLoads.size; i++) await new Promise(r => setTimeout(r, 5));
    assert.strictEqual(paper.partLoads.size, 0, "the queue gets its background loading back");
  }
  global.fetch = realFetch;
  return { took, asked, saved, adopted, preloaded, busiest };
}

function download(grant, saved, answer) {
  const calls = [], kept = [];
  const mod = load(`${SRC}/imageDownload.ts`, {
    "react-native": { Platform: { OS: "web" } }, "./PrivateAssetQueue": {}, "./assetGrants": { imageGrant: () => grant },
    "./imageDimensions": { imageDimensions: () => ({ width: 1, height: 1 }) }, "./base64": { imageBase64: async () => "AQID" },
    "./loadingMetrics": { loadingMetrics: { count: () => {} }, timed: async (_name, fn) => fn() },
    "./deviceCache/cache": { readSavedImage: async () => saved, saveImage: async (key, image) => { kept.push(image); } },
  });
  const transport = async (path, _signal, extra) => { calls.push({ path, extra }); return answer(path, extra); };
  return { calls, kept, run: path => mod.loadOriginalImage(path, new AbortController().signal, transport) };
}
const answer200 = (bytes, type, etag) => () => ({ status: 200, headers: new Headers({ "content-type": type, etag }), bytes });
const ONE = "/attempts/a1/questions/q0/asset/question/0";
const DAY = 86400 * 1000;

const tests = {
  // ---- The owner's switch and asset_revision ----
  "switch off: a row that carries asset_revision is still loaded exactly as before"() {
    grants.clearImageGrants();
    grants.registerImageGrants("a1", paperRows(2), true, "original", () => {});
    assert.strictEqual(grants.imageGrant(ONE).step, 0);
    assert.strictEqual(keyOf(ONE), JSON.stringify(["q0", "question", 0, "original", 1, "r000000000000000"]), "the key already carries the revision, as in every build so far");
  },
  "switch on, website still gives its old answers (no asset_revision): exactly as before"() {
    grants.clearImageGrants();
    grants.registerImageGrants("a1", paperRows(2, { asset_revision: undefined }), true, "original", () => {}, false, 5);
    assert.strictEqual(grants.imageGrant(ONE).step, 0);
    grants.registerImageGrants("a1", paperRows(2, { asset_revision: null }), true, "original", () => {}, false, 5);
    assert.strictEqual(grants.imageGrant(ONE).step, 0, "null is not a revision");
  },
  "switch on + asset_revision: the new way; the switch's answer arriving in the middle of a paper reloads nothing"() {
    const dropped = [];
    grants.clearImageGrants();
    grants.registerImageGrants("a1", paperRows(2), true, "original", p => dropped.push(p));
    const before = grants.imageGrant(ONE);
    before.validated = true;
    dropped.length = 0;
    grants.registerImageGrants("a1", paperRows(2), true, "original", p => dropped.push(p), false, 5);
    assert.strictEqual(grants.imageGrant(ONE), before, "the same grant");
    assert.strictEqual(before.step, 5);
    assert.strictEqual(before.validated, true);
    assert.deepStrictEqual(dropped, [], "no picture on screen is dropped");
    // A picture the website replaces gets a new revision: a new key, and the old copy is dropped.
    grants.registerImageGrants("a1", paperRows(2).map((q, i) => (i ? q : { ...q, asset_revision: "ffffffffffffffff" })), true, "original", p => dropped.push(p), false, 5);
    assert.deepStrictEqual(dropped.sort(), [ONE, "/attempts/a1/questions/q0/asset/solution/0"].sort());
    assert.notStrictEqual(grants.imageGrant(ONE), before);
  },

  // ---- One picture ----
  async "one picture, new way: asked for with format=webp (after score_version too); the WebP is kept with its own ETag"() {
    const d = download({ contentKey: "k", validated: false, step: 5 }, null, answer200(picture(true, 40), "image/webp", '"aa11"'));
    await d.run(ONE);
    await d.run(`${ONE}?score_version=v2`);
    assert.deepStrictEqual(d.calls.map(c => c.path), [`${ONE}?format=webp`, `${ONE}?score_version=v2&format=webp`]);
    assert.ok(d.calls.every(c => !c.extra), "a plain call: no Range, no If-None-Match");
    assert.deepStrictEqual(d.kept.map(k => [k.mime, k.etag]), [["image/webp", '"aa11"'], ["image/webp", '"aa11"']]);
  },
  async "one picture, old way: no format word ever leaves the phone"() {
    const d = download({ contentKey: "k", validated: false, step: 0 }, null, answer200(picture(false, 40), "image/png", ""));
    await d.run(ONE);
    await d.run(`${ONE}?score_version=v2`);
    assert.deepStrictEqual(d.calls.map(c => c.path), [ONE, `${ONE}?score_version=v2`]);
  },
  async "one picture: a format=webp call answered with the PNG is kept as a PNG (type from the first bytes)"() {
    const png = download({ contentKey: "k", validated: false, step: 5 }, null, answer200(picture(false, 40), "image/png", '"bb22"'));
    await png.run(ONE);
    assert.deepStrictEqual([png.kept[0].mime, png.kept[0].etag], ["image/png", '"bb22"']);
    const mislabelled = download({ contentKey: "k", validated: false, step: 5 }, null, answer200(picture(false, 40), "image/webp", '"bb22"'));
    await mislabelled.run(ONE);
    assert.strictEqual(mislabelled.kept[0].mime, "image/png", "the bytes win over the header");
    const page = download({ contentKey: "k", validated: false, step: 5 }, null, answer200(new Uint8Array(Buffer.from("<html>busy</html>")), "text/html", ""));
    await assert.rejects(() => page.run(ONE), /could not be read/);
    assert.strictEqual(page.kept.length, 0, "an error page is never kept as a picture");
  },
  async "one picture, new way: a copy kept under the revision is shown without asking, however old"() {
    const old = { bytes: picture(true, 40), mime: "image/webp", etag: '"aa11"', modified: "", at: Date.now() - 40 * DAY };
    const grant = { contentKey: "k", validated: false, step: 5 };
    const d = download(grant, old, () => { throw new Error("no call expected"); });
    assert.ok((await d.run(ONE)).uri);
    assert.strictEqual(d.calls.length, 0);
    assert.strictEqual(grant.validated, true);
  },
  async "one picture, old way: an old copy with an ETag is re-checked in one small call (304 or 206 keeps it, 200 replaces it)"() {
    const old = () => ({ bytes: picture(false, 40), mime: "image/png", etag: '"bb22"', modified: "", at: Date.now() - 4 * DAY });
    const same = download({ contentKey: "k", validated: false, step: 0 }, old(), () => ({ status: 304, headers: new Headers({ etag: '"bb22"' }), bytes: new Uint8Array() }));
    await same.run(ONE);
    assert.deepStrictEqual(same.calls, [{ path: ONE, extra: { Range: "bytes=0-0", "If-None-Match": '"bb22"', "If-Range": '"bb22"' } }]);
    assert.strictEqual(same.kept.length, 0);
    const oneByte = download({ contentKey: "k", validated: false, step: 0 }, old(), () => ({ status: 206, headers: new Headers({ etag: '"bb22"', "content-range": "bytes 0-0/40" }), bytes: new Uint8Array([0x89]) }));
    await oneByte.run(ONE);
    assert.strictEqual(oneByte.calls.length, 1);
    assert.strictEqual(oneByte.kept.length, 0);
    const changed = download({ contentKey: "k", validated: false, step: 0 }, old(), answer200(picture(false, 50), "image/png", '"cc33"'));
    await changed.run(ONE);
    assert.strictEqual(changed.calls.length, 1, "If-Range with an old ETag answers the whole new picture: no second call");
    assert.deepStrictEqual([changed.kept[0].etag, changed.kept[0].bytes.length], ['"cc33"', 50]);
  },
  async "a picture the phone could not draw is fetched afresh as the plain PNG, and replaces the kept copy"() {
    grants.clearImageGrants();
    grants.registerImageGrants("a1", paperRows(1), true, "original", () => {}, false, 5);
    grants.drawAsPlain(ONE);
    const grant = grants.imageGrant(ONE);
    assert.strictEqual(grant.plain, true);
    const kept = { bytes: picture(true, 40), mime: "image/webp", etag: '"aa11"', modified: "", at: Date.now() };
    const d = download(grant, kept, answer200(picture(false, 60), "image/png", '"bb22"'));
    await d.run(ONE);
    assert.deepStrictEqual(d.calls, [{ path: ONE, extra: undefined }], "one plain call: no format word, no re-check of the copy it could not draw");
    assert.deepStrictEqual([d.kept[0].mime, d.kept[0].etag, d.kept[0].bytes.length], ["image/png", '"bb22"', 60]);
    assert.strictEqual(grant.plain, false, "the kept copy is the plain picture now: it is used again from here on");
    // The other pictures of the paper are not touched, and a later open of the paper starts normally again.
    assert.strictEqual(grants.imageGrant("/attempts/a1/questions/q0/asset/solution/0").plain, undefined);
    grants.registerImageGrants("a1", paperRows(1), true, "original", () => {}, true, 5);
    assert.strictEqual(grants.imageGrant(ONE).plain, undefined);
  },
  "one picture: the only extra word the app lets through is format=webp"() {
    const source = fs.readFileSync("/app/frontend/src/api/client.ts", "utf8");
    const rule = eval(/if \(!(\/\^.*\$\/)\.test\(path\)\) throw new ApiError\("Unsupported private image path\."\)/.exec(source)[1]);
    for (const ok of [ONE, `${ONE}?format=webp`, `${ONE}?score_version=v2`, `${ONE}?score_version=v2&format=webp`, "/attempts/a/questions/q/asset/solution/3?format=webp", "/attempts/a/questions/q/asset/piece/4"])
      assert.ok(rule.test(ok), ok);
    for (const bad of [`${ONE}?format=jpeg`, `${ONE}?format=webp&x=1`, `${ONE}?format=webp&score_version=v2`, `${ONE}?kind=solution`, "/attempts/a/assets/pack?format=webp", `${ONE}/../x`])
      assert.ok(!rule.test(bad), bad);
  },

  // ---- A released result in parts ----
  async "result, switch off: nothing new is asked, the caller loads one by one as before"() {
    const rows = paperRows(30), run = await result(rows, website(rows), { step: 0 });
    assert.strictEqual(run.took, false);
    assert.deepStrictEqual([run.asked, run.saved, run.preloaded], [[], [], []]);
  },
  async "result, switch on but old website answers: nothing new is asked"() {
    const rows = paperRows(30, { asset_revision: undefined }), run = await result(rows, website(rows, { old: true, refuses: 409 }));
    assert.strictEqual(run.took, false);
    assert.deepStrictEqual(run.asked, []);
  },
  async "result just after the paper: only the solutions come, in parts, as WebP, each kept with its ETag"() {
    const rows = paperRows(30), site = website(rows), questions = pathsOf(rows, false), solutions = pathsOf(rows, true);
    const run = await result(rows, site, { onPhone: questions });
    assert.strictEqual(run.took, true);
    assert.deepStrictEqual(run.asked.slice(0, 1), ["/attempts/a1/assets/links?kind=solution&format=webp"]);
    assert.deepStrictEqual(run.asked.slice(1).sort(), ["link 0 flags 29", "link 12 flags 29", "link 24 flags 29"]);
    assert.deepStrictEqual(run.saved.map(s => s.key).sort(), solutions.map(keyOf).sort(), "every solution, and only solutions");
    assert.ok(run.saved.every(s => s.mime === "image/webp"));
    assert.strictEqual(run.saved.find(s => s.key === keyOf(solutions[0])).etag, `"${site.etag({ question_id: "q0", kind: "solution", index: 0 }, true)}"`, "the one-picture route's ETag, quoted");
    assert.deepStrictEqual(run.adopted, [], "nothing is turned into a screen picture before a screen asks");
    assert.deepStrictEqual(run.preloaded, [[]], "nothing left for the queue");
    assert.strictEqual(run.busiest, 2, "two parts at a time");
  },
  async "result on a new phone: questions and solutions both come in parts"() {
    const rows = paperRows(30), run = await result(rows, website(rows));
    assert.deepStrictEqual(run.asked.filter(a => a.startsWith("/")).sort(), ["/attempts/a1/assets/links?format=webp", "/attempts/a1/assets/links?kind=solution&format=webp"]);
    assert.strictEqual(run.asked.filter(a => /flags 21$/.test(a)).length, 3, "question parts: finished + new fields + WebP");
    assert.strictEqual(run.asked.filter(a => /flags 29$/.test(a)).length, 3);
    assert.deepStrictEqual(run.saved.map(s => s.key).sort(), [...pathsOf(rows, false), ...pathsOf(rows, true)].map(keyOf).sort());
    assert.deepStrictEqual(run.preloaded, [[]]);
    assert.ok(run.busiest <= 2);
  },
  async "result of another score version: the same score_version word goes on links, pack and every picture path"() {
    const rows = paperRows(30), site = website(rows, { brokenLinks: true });
    const run = await result(rows, site, { version: "v2", onPhone: pathsOf(rows, false, "v2") });
    assert.strictEqual(run.asked[0], "/attempts/a1/assets/links?kind=solution&format=webp&score_version=v2");
    assert.ok(run.asked.includes("/attempts/a1/assets/pack?offset=12&limit=12&kind=solution&format=webp&score_version=v2"), "a link that fails comes through the app's server");
    assert.deepStrictEqual(run.saved.map(s => s.key).sort(), pathsOf(rows, true, "v2").map(keyOf).sort());
    assert.ok(keyOf(pathsOf(rows, true, "v2")[0]).includes('"v2"'));
  },
  async "result of a cut paper: look=cut for the question pieces only"() {
    const rows = paperRows(6, { pieces: CUT }), run = await result(rows, website(rows));
    assert.deepStrictEqual(run.asked.filter(a => a.startsWith("/")).sort(), ["/attempts/a1/assets/links?kind=solution&format=webp", "/attempts/a1/assets/links?look=cut&format=webp"]);
    assert.strictEqual(run.saved.length, 30 + 6);
    assert.ok(pathsOf(rows, false).every(p => p.includes("/asset/piece/") && run.saved.some(s => s.key === keyOf(p))));
  },
  async "trap 1: a website that ignores kind=solution sends question pictures; none is ever kept as a solution"() {
    const rows = paperRows(30), questions = pathsOf(rows, false), solutions = pathsOf(rows, true);
    // Its links answer: the part names carry flags below 8, so no part is even fetched.
    const named = await result(rows, website(rows, { old: true }), { onPhone: questions });
    assert.deepStrictEqual(named.asked, ["/attempts/a1/assets/links?kind=solution&format=webp"]);
    assert.deepStrictEqual(named.saved, []);
    assert.deepStrictEqual(named.preloaded, [solutions], "the solutions load one by one, through the solution route");
    // No links answer (404): the parts come through /assets/pack, and every item is read: none says "solution".
    const packed = await result(rows, website(rows, { old: true, noLinks: true }), { onPhone: questions });
    assert.deepStrictEqual(packed.asked, ["/attempts/a1/assets/links?kind=solution&format=webp", "/attempts/a1/assets/pack?offset=0&limit=12&kind=solution&format=webp"], "the first part shows it: no further part is fetched");
    assert.deepStrictEqual(packed.saved, [], "a question picture is never filed under a solution");
    assert.deepStrictEqual(packed.preloaded, [solutions]);
  },
  async "trap 3: a finished attempt answered 409 falls back to one by one after a single call for each kind"() {
    const rows = paperRows(30), run = await result(rows, website(rows, { refuses: 409 }));
    assert.deepStrictEqual(run.asked.sort(), ["/attempts/a1/assets/links?format=webp", "/attempts/a1/assets/links?kind=solution&format=webp"]);
    assert.deepStrictEqual(run.saved, []);
    assert.deepStrictEqual(run.preloaded, [[...pathsOf(rows, false), ...pathsOf(rows, true)]]);
  },
  async "solutions refused (403): the question parts still come; the solutions go to the queue"() {
    const rows = paperRows(30), run = await result(rows, website(rows, { sealed: true }));
    assert.deepStrictEqual(run.saved.map(s => s.key).sort(), pathsOf(rows, false).map(keyOf).sort());
    assert.ok(!run.asked.some(a => a.includes("/assets/pack")), "no second try for the solutions");
    assert.deepStrictEqual(run.preloaded, [pathsOf(rows, true)]);
  },
  async "a part whose pictures are already on the phone is not fetched again"() {
    const rows = paperRows(30), solutions = pathsOf(rows, true);
    const run = await result(rows, website(rows), { onPhone: [...pathsOf(rows, false), ...solutions.slice(0, 24)] });
    assert.deepStrictEqual(run.asked, ["/attempts/a1/assets/links?kind=solution&format=webp", "link 24 flags 29"]);
    assert.deepStrictEqual(run.saved.map(s => s.key).sort(), solutions.slice(24).map(keyOf).sort());
  },
  async "a short last part (2 pictures) is still fetched as a part when both are missing"() {
    const rows = paperRows(26), run = await result(rows, website(rows), { onPhone: pathsOf(rows, false) });
    assert.deepStrictEqual(run.asked.slice(1).sort(), ["link 0 flags 29", "link 12 flags 29", "link 24 flags 29"]);
    assert.strictEqual(run.saved.length, 26);
    assert.deepStrictEqual(run.preloaded, [[]]);
  },
  async "a few pictures missing: no part is fetched for them, the queue brings them"() {
    const rows = paperRows(30), solutions = pathsOf(rows, true);
    const run = await result(rows, website(rows), { onPhone: [...pathsOf(rows, false), ...solutions.slice(3)] });
    assert.deepStrictEqual(run.asked, []);
    assert.deepStrictEqual(run.preloaded, [solutions.slice(0, 3)]);
  },
  async "a phone that keeps no copies: everything one by one, as before"() {
    const rows = paperRows(30), run = await result(rows, website(rows), { noDisk: true });
    assert.deepStrictEqual(run.asked, []);
    assert.deepStrictEqual(run.preloaded, [[...pathsOf(rows, false), ...pathsOf(rows, true)]]);
  },
  async "a picture a screen is waiting for is shown the moment its part arrives"() {
    const rows = paperRows(30), solutions = pathsOf(rows, true);
    const run = await result(rows, website(rows), { onPhone: pathsOf(rows, false), waiting: [solutions[5]] });
    assert.deepStrictEqual(run.adopted.map(a => a.path), [solutions[5]]);
    assert.strictEqual(run.saved.length, 30, "and it is kept on the phone like the others");
  },
  async "leaving the result stops the parts; nothing more is fetched or queued for it"() {
    const rows = paperRows(60), run = await result(rows, website(rows), { onPhone: pathsOf(rows, false), leaveAfter: 2 });
    assert.ok(run.asked.filter(a => a.startsWith("link")).length <= 3, run.asked.join(" | "));
    assert.deepStrictEqual(run.preloaded, []);
  },
  async "a part that cannot be loaded leaves its pictures, and the ones after it, to the queue"() {
    const rows = paperRows(30), solutions = pathsOf(rows, true);
    const run = await result(rows, website(rows, { noLinks: true, failPackFrom: 12 }), { onPhone: pathsOf(rows, false) });
    assert.strictEqual(run.saved.length, 12);
    assert.deepStrictEqual(run.preloaded, [solutions.slice(12)]);
  },

  // ---- One step at a time, in the website note's order ----
  async "step 2 (asset_revision): a kept copy is not asked about again; no new word leaves the phone; a result loads one by one"() {
    const grant = { contentKey: "k", validated: false, step: 2 };
    const kept = download(grant, { bytes: picture(false, 40), mime: "image/png", etag: '"bb22"', modified: "", at: Date.now() - 40 * DAY }, () => { throw new Error("no call expected"); });
    await kept.run(ONE);
    assert.strictEqual(kept.calls.length, 0);
    const fresh = download({ contentKey: "k", validated: false, step: 2 }, null, answer200(picture(false, 40), "image/png", '"bb22"'));
    await fresh.run(ONE);
    assert.deepStrictEqual(fresh.calls.map(c => c.path), [ONE], "no format word");
    const rows = paperRows(30), run = await result(rows, website(rows), { step: 2 });
    assert.strictEqual(run.took, false);
    assert.deepStrictEqual(run.asked, []);
  },
  async "step 3 (finished attempt in parts): the question pictures come in parts as PNG; solutions stay one by one"() {
    const rows = paperRows(30), run = await result(rows, website(rows), { step: 3 });
    assert.strictEqual(run.took, true);
    assert.deepStrictEqual(run.asked.filter(a => a.startsWith("/")), ["/attempts/a1/assets/links"], "no kind word, no format word");
    assert.strictEqual(run.asked.filter(a => /flags 5$/.test(a)).length, 3, "finished + new fields");
    assert.deepStrictEqual(run.saved.map(s => s.key).sort(), pathsOf(rows, false).map(keyOf).sort());
    assert.ok(run.saved.every(s => s.mime === "image/png" && /^"bb/.test(s.etag)), "the PNG's ETag");
    assert.deepStrictEqual(run.preloaded, [pathsOf(rows, true)], "every solution goes to the queue");
    const wire = download({ contentKey: "k", validated: false, step: 3 }, null, answer200(picture(false, 40), "image/png", ""));
    await wire.run(ONE);
    assert.deepStrictEqual(wire.calls.map(c => c.path), [ONE]);
  },
  async "step 4 (kind=solution): the solutions come in parts too, still as PNG"() {
    const rows = paperRows(30), run = await result(rows, website(rows), { step: 4 });
    assert.deepStrictEqual(run.asked.filter(a => a.startsWith("/")).sort(), ["/attempts/a1/assets/links", "/attempts/a1/assets/links?kind=solution"]);
    assert.strictEqual(run.asked.filter(a => /flags 13$/.test(a)).length, 3, "finished + new fields + solutions");
    assert.strictEqual(run.saved.length, 60);
    assert.ok(run.saved.every(s => s.mime === "image/png"));
    assert.deepStrictEqual(run.preloaded, [[]]);
  },
  async "step 5 (format=webp): the same calls with the format word; get-ready below step 5 keeps asking for PNG"() {
    const rows = paperRows(30), run = await result(rows, website(rows), { step: 5 });
    assert.deepStrictEqual(run.asked.filter(a => a.startsWith("/")).sort(), ["/attempts/a1/assets/links?format=webp", "/attempts/a1/assets/links?kind=solution&format=webp"]);
    assert.ok(run.saved.every(s => s.mime === "image/webp"));
    const ready = await result(rows, website(rows), { getReady: true, step: 4 });
    assert.strictEqual(ready.asked[0], "/attempts/a1/assets/links");
    assert.ok(ready.saved.every(s => s.mime === "image/png" && /^"bb/.test(s.etag)), "PNG, and the new website's etag is kept already");
  },

  // ---- The get-ready minute ----
  async "get-ready, new way: the paper's parts are asked for as WebP and every picture keeps its ETag"() {
    const rows = paperRows(30), site = website(rows), run = await result(rows, site, { getReady: true });
    assert.strictEqual(run.asked[0], "/attempts/a1/assets/links?format=webp");
    assert.deepStrictEqual(run.adopted.map(a => a.path).sort(), pathsOf(rows, false).sort(), "shown from memory when the paper begins, as before");
    assert.ok(run.saved.every(s => s.mime === "image/webp" && /^"aa[0-9a-f]{30}"$/.test(s.etag)));
    assert.strictEqual(run.busiest, 1, "one part after the other, as before");
  },
  async "get-ready, switch off: asked for exactly as before"() {
    const rows = paperRows(30), run = await result(rows, website(rows, { old: true }), { getReady: true, step: 0 });
    assert.strictEqual(run.asked[0], "/attempts/a1/assets/links");
    assert.ok(run.asked.slice(1).every(a => /^link \d+ flags 1$/.test(a)));
    assert.ok(run.saved.every(s => s.mime === "image/png" && s.etag === ""));
    assert.strictEqual(run.adopted.length, 30);
  },
};

(async () => {
  let failed = 0;
  for (const [name, run] of Object.entries(tests)) {
    try { await run(); console.log("PASS", name); } catch (e) { failed++; console.log("FAIL", name, "\n  ", e.message); }
  }
  console.log(failed ? `${failed} FAILED` : `ALL ${Object.keys(tests).length} PASSED`);
  process.exit(failed ? 1 : 0);
})();
