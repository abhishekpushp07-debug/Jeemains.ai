// Smooth Mode (src/analysis/smooth.ts): when the Shine calms itself, what is kept on the phone, when it is tried again.
// Run: node tests/smooth_mode_tests.cjs
const assert = require("assert");
const fs = require("fs");
const ts = require("/app/frontend/node_modules/typescript");

const FILE = "/app/frontend/src/analysis/smooth.ts";
const DAY = 86400 * 1000, FAST = 1000 / 60, SLOW = 1000 / 40, CRAWL = 1000 / 24;

/** A fresh copy of the module with its own phone storage; `kept` = what an earlier run left there. */
async function fresh(kept) {
  const store = new Map(kept === undefined ? [] : [["shine.level.v1", kept]]);
  const stubs = {
    react: { useEffect: () => {}, useSyncExternalStore: (_s, get) => get() },
    "react-native-reanimated": { runOnJS: f => f, useFrameCallback: () => ({ setActive() {} }), useSharedValue: v => ({ value: v }) },
    "@/src/utils/storage": { storage: { getItem: async (k, fallback) => (store.has(k) ? store.get(k) : fallback), setItem: async (k, v) => { store.set(k, v); return true; } } },
  };
  const js = ts.transpileModule(fs.readFileSync(FILE, "utf8"), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020, esModuleInterop: true }, fileName: FILE }).outputText;
  const mod = { exports: {} };
  new Function("require", "module", "exports", js)(id => { if (id in stubs) return stubs[id]; throw new Error("Missing stub: " + id); }, mod, mod.exports);
  await new Promise(r => setTimeout(r, 0)); // the kept level is read as the module loads
  return { ...mod.exports, store, level: () => mod.exports.useShineLevel() };
}
// A look that ends well after the screen has settled.
const later = () => Date.now() + 60000;

const tests = {
  async "a phone that keeps up stays at FULL and nothing is kept"() {
    const m = await fresh();
    m.shineMoves();
    for (let i = 0; i < 20; i++) m.looked(FAST, later());
    assert.strictEqual(m.level(), m.FULL);
    assert.strictEqual(m.store.size, 0);
  },
  async "two slow looks in a row calm the Shine; one alone does not"() {
    const m = await fresh();
    m.shineMoves();
    m.looked(SLOW, later());
    assert.strictEqual(m.level(), m.FULL, "one slow look is not enough");
    m.looked(FAST, later());
    m.looked(SLOW, later());
    assert.strictEqual(m.level(), m.FULL, "a good look in between starts the count again");
    m.looked(SLOW, later());
    assert.strictEqual(m.level(), m.CALM);
    assert.match(m.store.get("shine.level.v1"), /^1:\d+$/);
  },
  async "a phone that crawls (under 30 frames a second) goes straight to STILL"() {
    const m = await fresh();
    m.shineMoves();
    m.looked(CRAWL, later()); m.looked(CRAWL, later());
    assert.strictEqual(m.level(), m.STILL);
    assert.match(m.store.get("shine.level.v1"), /^2:\d+$/);
  },
  async "exactly 48 frames a second is not slow; exactly 30 is calm, not still"() {
    const m = await fresh();
    m.shineMoves();
    for (let i = 0; i < 4; i++) m.looked(1000 / 48, later());
    assert.strictEqual(m.level(), m.FULL);
    m.looked(1000 / 30, later()); m.looked(1000 / 30, later());
    assert.strictEqual(m.level(), m.CALM);
  },
  async "a screen that has just opened is not looked at"() {
    const m = await fresh();
    m.shineMoves();
    for (let i = 0; i < 5; i++) m.looked(CRAWL, Date.now() + 3000); // the look began before the screen had settled
    assert.strictEqual(m.level(), m.FULL);
    m.looked(CRAWL, Date.now() + 3600); m.looked(CRAWL, Date.now() + 5600);
    assert.strictEqual(m.level(), m.STILL);
  },
  async "no look counts while no Shine is moving"() {
    const m = await fresh();
    for (let i = 0; i < 5; i++) m.looked(CRAWL, later());
    assert.strictEqual(m.level(), m.FULL);
    const stop = m.shineMoves(); stop();
    for (let i = 0; i < 5; i++) m.looked(CRAWL, later());
    assert.strictEqual(m.level(), m.FULL);
  },
  async "once calmed, later looks change nothing (never from CALM to STILL, never back up in the same run)"() {
    const m = await fresh();
    m.shineMoves();
    m.looked(SLOW, later()); m.looked(SLOW, later());
    for (let i = 0; i < 10; i++) m.looked(CRAWL, later());
    for (let i = 0; i < 10; i++) m.looked(FAST, later());
    assert.strictEqual(m.level(), m.CALM);
  },
  async "a slow phone starts calm the next time"() {
    assert.strictEqual((await fresh(`1:${Date.now() - DAY}`)).level(), 1);
    assert.strictEqual((await fresh(`2:${Date.now() - 6 * DAY}`)).level(), 2);
  },
  async "after a week the phone gets one more look at FULL, and is calmed again if it is still slow"() {
    const m = await fresh(`2:${Date.now() - 8 * DAY}`);
    assert.strictEqual(m.level(), m.FULL);
    m.shineMoves();
    m.looked(SLOW, later()); m.looked(SLOW, later());
    assert.strictEqual(m.level(), m.CALM);
    assert.ok(Number(m.store.get("shine.level.v1").split(":")[1]) > Date.now(), "kept with the new time");
  },
  async "anything unreadable on the phone means FULL"() {
    const m = await fresh();
    const now = Date.now();
    for (const kept of ["", "x", "1", "1:", "3:" + now, "0:" + now, "-1:" + now, "1:abc", `1:${now + DAY}`, null, undefined, 1, true, {}])
      assert.strictEqual(m.startLevel(kept, now), m.FULL, JSON.stringify(kept));
    assert.strictEqual(m.startLevel(`1:${now}`, now), m.CALM);
    assert.strictEqual(m.startLevel(`2:${now - 7 * DAY + 1000}`, now), m.STILL);
    assert.strictEqual(m.startLevel(`2:${now - 7 * DAY}`, now), m.FULL);
  },
  async "screens hear about a change once, and the frame counter only runs at FULL while a Shine moves"() {
    const store = new Map();
    let heard = 0, watching = null;
    const stubs = {
      react: { useEffect: () => {}, useSyncExternalStore: (subscribe, get) => { subscribe(() => { heard++; }); return get(); } },
      "react-native-reanimated": { runOnJS: f => f, useFrameCallback: () => ({ setActive() {} }), useSharedValue: v => ({ value: v }) },
      "@/src/utils/storage": { storage: { getItem: async (_k, fallback) => fallback, setItem: async (k, v) => { store.set(k, v); return true; } } },
    };
    const js = ts.transpileModule(fs.readFileSync(FILE, "utf8"), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020, esModuleInterop: true }, fileName: FILE }).outputText;
    const mod = { exports: {} };
    new Function("require", "module", "exports", js)(id => stubs[id], mod, mod.exports);
    const m = mod.exports;
    m.useShineLevel(); // one listener
    // The counter's own "watching" value, read the way the component reads it.
    stubs.react.useSyncExternalStore = (_s, get) => { watching = get(); return watching; };
    m.SmoothMode(); assert.strictEqual(watching, false, "nothing moves yet");
    const a = m.shineMoves(), b = m.shineMoves();
    m.SmoothMode(); assert.strictEqual(watching, true);
    assert.strictEqual(heard, 1, "told once when the first Shine starts moving");
    a(); m.SmoothMode(); assert.strictEqual(watching, true, "one is still moving");
    m.looked(SLOW, later()); m.looked(SLOW, later());
    assert.strictEqual(heard, 2, "told once when the level changes");
    m.SmoothMode(); assert.strictEqual(watching, false, "calmed: no more counting");
    b(); assert.strictEqual(heard, 3);
  },
};

(async () => {
  let failed = 0;
  for (const [name, run] of Object.entries(tests)) {
    try { await run(); console.log("PASS", name); } catch (e) { failed++; console.log("FAIL", name, "\n   ", e.message); }
  }
  console.log(`\n${Object.keys(tests).length - failed}/${Object.keys(tests).length} passed`);
  process.exit(failed ? 1 : 0);
})();
