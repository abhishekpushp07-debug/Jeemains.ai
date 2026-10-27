const assert = require("assert");
const fs = require("fs");
const path = require("path");
const ts = require("/app/frontend/node_modules/typescript");

const wait = (ms = 0) => new Promise((r) => setTimeout(r, ms));

function loadTsModule(filePath, stubs = {}) {
  const source = fs.readFileSync(filePath, "utf8");
  const transpiled = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2020,
      esModuleInterop: true,
      jsx: ts.JsxEmit.ReactJSX,
    },
    fileName: filePath,
  }).outputText;

  const mod = { exports: {} };
  const localRequire = (id) => {
    if (Object.prototype.hasOwnProperty.call(stubs, id)) return stubs[id];
    if (id.startsWith("@/")) throw new Error(`Missing stub for alias import: ${id}`);
    return require(id);
  };
  const fn = new Function("require", "module", "exports", "__filename", "__dirname", transpiled);
  fn(localRequire, mod, mod.exports, filePath, path.dirname(filePath));
  return mod.exports;
}

const tests = [];
const test = (name, fn) => tests.push({ name, fn });

const queueModule = loadTsModule("/app/frontend/src/assets/PrivateAssetQueue.ts");
const { PrivateAssetQueue } = queueModule;

test("PrivateAssetQueue default concurrency is 6 with one reserved visible slot", async () => {
  const started = [];
  const inflight = new Map();
  const q = new PrivateAssetQueue(async (p) => {
    started.push(p);
    let resolve;
    const promise = new Promise((r) => (resolve = r));
    inflight.set(p, { resolve });
    return promise;
  });

  q.get("/bg-1", 10).catch(() => {});
  q.get("/bg-2", 10).catch(() => {});
  q.get("/bg-3", 10).catch(() => {});
  q.get("/bg-4", 10).catch(() => {});
  q.get("/bg-5", 10).catch(() => {});
  q.get("/bg-6", 10).catch(() => {});
  await wait(20);

  assert.strictEqual(started.filter((x) => x.startsWith("/bg")).length, 5, "one slot should stay reserved for visible priority");

  const focus = q.get("/focus", 100);
  await wait(20);
  assert.ok(started.includes("/focus"), "visible request should start immediately in reserved slot");

  for (const [k, d] of inflight.entries()) d.resolve({ uri: `blob://${k}`, bytes: 1 });
  await focus;
});

test("Queue deduplicates repeated request for same path", async () => {
  let calls = 0;
  const q = new PrivateAssetQueue(async () => {
    calls += 1;
    await wait(10);
    return { uri: "blob://same", bytes: 8 };
  });
  const all = await Promise.all(Array.from({ length: 8 }, () => q.get("/same", 100)));
  assert.strictEqual(calls, 1);
  assert.ok(all.every((x) => x === "blob://same"));
});

test("Queue keeps scheduling all paths; RAM limit evicts instead of admission stop", async () => {
  let calls = 0;
  const q = new PrivateAssetQueue(async (p) => {
    calls += 1;
    await wait(1);
    return { uri: `blob://${p}`, bytes: 6 };
  }, 6, 24);

  const paths = Array.from({ length: 30 }, (_, i) => `/p/${i}`);
  q.preload(paths);
  await wait(500);

  assert.strictEqual(calls, 30, "all requested paths should be attempted even under tight RAM");
});

test("openPyq sends start_key and never includes PIN", async () => {
  const calls = { post: [], warm: [], invalidate: [], remove: [] };
  const kv = new Map();
  let uidCounter = 0;

  const pyq = loadTsModule("/app/frontend/src/api/pyq.ts", {
    "./client": {
      api: async (pathArg) => (pathArg.startsWith("/my/sets/") ? { attempt: null } : {}),
      post: async (pathArg, body) => {
        calls.post.push({ path: pathArg, body });
        return { id: "attempt-new", status: "active" };
      },
      uuid: () => `uuid-${++uidCounter}`,
    },
    "./paperOpening": { warmAttempt: (id, data) => calls.warm.push({ id, data }) },
    "@/src/useCached": { invalidate: (key) => calls.invalidate.push(key) },
    "./readiness": { checkReadiness: async () => {} },
    "@/src/utils/storage": {
      storage: {
        getItem: async (k, fallback) => (kv.has(k) ? kv.get(k) : fallback),
        setItem: async (k, v) => { kv.set(k, v); return true; },
        removeItem: async (k) => { calls.remove.push(k); kv.delete(k); return true; },
      },
    },
  });

  const paper = {
    id: "jee-main-pyq-2026-01-21-s1", year: 2026, exam_date: "2026-01-21", shift: 1,
    count: 75, minutes: 180, maximum: 300, attempt: null, latest_result_id: null, attempt_count: 0,
  };
  const out = await pyq.openPyq("user-1", paper, 0);
  assert.strictEqual(out.id, "attempt-new");
  assert.strictEqual(calls.post.length, 1);
  assert.strictEqual(calls.post[0].body.start_key, "uuid-1");
  assert.ok(!Object.prototype.hasOwnProperty.call(calls.post[0].body, "pin"));
  assert.strictEqual(calls.warm.length, 1);
});

test("warmAttempt/loadAttempt share one staged metadata fetch", async () => {
  let fetchCount = 0;
  const paperOpening = loadTsModule("/app/frontend/src/api/paperOpening.ts", {
    "./client": {
      api: async () => {
        fetchCount += 1;
        await wait(5);
        return { id: "a1", questions: [], server_now: 1 };
      },
      apiRaw: async () => ({ status: 202, data: { status: "grading" }, retryAfterMs: 1000 }),
      getAssetAccount: () => "uid-1",
      getAssetEpoch: () => 1,
      onAssetScopeReset: () => () => {},
      privateAssets: { selectGroup: () => {}, preload: () => {} },
      registerAssetManifest: () => {},
    },
  });

  const [a, b] = await Promise.all([paperOpening.warmAttempt("a1"), paperOpening.loadAttempt("a1")]);
  assert.strictEqual(fetchCount, 1);
  assert.strictEqual(a.id, "a1");
  assert.strictEqual(b.id, "a1");
});

test("warmResult only preloads released 200 results", async () => {
  const calls = { prepare: 0 };
  const responses = [
    { status: 202, data: { status: "grading" }, retryAfterMs: 1000 },
    { status: 200, data: { id: "a1", questions: [], summary: { score: 1 }, status: "embargoed" }, retryAfterMs: 0 },
    { status: 200, data: { id: "a1", questions: [], summary: { score: 1 }, status: "completed" }, retryAfterMs: 0 },
  ];

  const paperOpening = loadTsModule("/app/frontend/src/api/paperOpening.ts", {
    "./client": {
      api: async () => ({ id: "a1", questions: [], server_now: 1 }),
      apiRaw: async () => responses.shift(),
      getAssetAccount: () => "uid-1",
      getAssetEpoch: () => 1,
      onAssetScopeReset: () => () => {},
      privateAssets: { selectGroup: () => {}, preload: () => {} },
      registerAssetManifest: () => { calls.prepare += 1; },
    },
  });

  await paperOpening.warmResult("a1").catch(() => {});
  await paperOpening.warmResult("a1", "v2").catch(() => {});
  await paperOpening.warmResult("a1", "v3").catch(() => {});
  assert.strictEqual(calls.prepare, 1, "only released 200 should trigger solution preload");
});

test("UI source removed Ready sheet and image counters from attempt/result", () => {
  const attempt = fs.readFileSync("/app/frontend/app/attempt/[id].tsx", "utf8");
  const result = fs.readFileSync("/app/frontend/app/result/[id].tsx", "utf8");
  const pyq = fs.readFileSync("/app/frontend/app/pyq.tsx", "utf8");
  const all = `${attempt}\n${result}\n${pyq}`.toLowerCase();

  assert.ok(!all.includes("ready to start"));
  assert.ok(!all.includes("image counter"));
  assert.ok(!all.includes("images ready"));
  assert.ok(!all.includes("75/78"));
});

test("Android size config keeps release optimizations and optional ARM64 profile", () => {
  const appConfig = fs.readFileSync("/app/frontend/app.config.js", "utf8");
  const eas = JSON.parse(fs.readFileSync("/app/frontend/eas.json", "utf8"));

  assert.ok(appConfig.includes("enableMinifyInReleaseBuilds: true"));
  assert.ok(appConfig.includes("enableShrinkResourcesInReleaseBuilds: true"));
  assert.ok(appConfig.includes("enableBundleCompression: true"));
  assert.ok(appConfig.includes("useLegacyPackaging: arm64"));

  assert.strictEqual(eas.build.release.android.buildType, "app-bundle");
  assert.strictEqual(eas.build["apk-arm64"].android.buildType, "apk");
});

test("loadOriginalImage requires active grant before any disk lookup", async () => {
  let diskReads = 0;
  const mod = loadTsModule("/app/frontend/src/assets/imageDownload.ts", {
    "react-native": { Platform: { OS: "web" } },
    "./PrivateAssetQueue": {},
    "./assetGrants": { imageGrant: () => undefined },
    "./deviceCache/cache": {
      readSavedImage: async () => { diskReads += 1; return null; },
      saveImage: async () => {},
    },
  });

  const transport = async () => ({ status: 200, headers: new Headers({ "content-type": "image/png" }), bytes: new Uint8Array([1, 2, 3]) });
  const ctl = new AbortController();
  await assert.rejects(() => mod.loadOriginalImage("/attempts/a/questions/q/asset/question/0", ctl.signal, transport), (e) => e?.name === "AbortError");
  assert.strictEqual(diskReads, 0, "disk lookup must not run before grant check");
});

test("loadOriginalImage uses validator request then reuses cached bytes on 304", async () => {
  const grant = { contentKey: "k1", validated: false };
  const saved = { bytes: new Uint8Array([10, 11, 12]), mime: "image/png", etag: '"etag-1"', modified: "" };
  const calls = [];

  const mod = loadTsModule("/app/frontend/src/assets/imageDownload.ts", {
    "react-native": { Platform: { OS: "web" } },
    "./PrivateAssetQueue": {},
    "./assetGrants": { imageGrant: () => grant },
    "./deviceCache/cache": {
      readSavedImage: async () => saved,
      saveImage: async () => {},
    },
  });

  const transport = async (_path, _signal, extra) => {
    calls.push(extra || {});
    return { status: 304, headers: new Headers({ etag: '"etag-1"', "content-range": "bytes 0-0/3" }), bytes: new Uint8Array() };
  };

  const out = await mod.loadOriginalImage("/attempts/a/questions/q/asset/question/0", new AbortController().signal, transport);
  assert.ok(typeof out.uri === "string");
  assert.strictEqual(calls.length, 1);
  assert.strictEqual(calls[0].Range, "bytes=0-0");
  assert.strictEqual(calls[0]["If-None-Match"], '"etag-1"');
  assert.strictEqual(grant.validated, true);
});

test("loadOriginalImage falls back to full fetch when validator missing, and persists", async () => {
  const grant = { contentKey: "k2", validated: false };
  let persisted = 0;
  const headers = new Headers({ "content-type": "image/png", etag: '"new"', "last-modified": "Mon, 26 Jan 2026 00:00:00 GMT" });

  const mod = loadTsModule("/app/frontend/src/assets/imageDownload.ts", {
    "react-native": { Platform: { OS: "web" } },
    "./PrivateAssetQueue": {},
    "./assetGrants": { imageGrant: () => grant },
    "./deviceCache/cache": {
      readSavedImage: async () => ({ bytes: new Uint8Array([1]), mime: "image/png", etag: "", modified: "" }),
      saveImage: async () => { persisted += 1; },
    },
  });

  let fullFetches = 0;
  const transport = async (_path, _signal, extra) => {
    if (!extra) fullFetches += 1;
    return { status: 200, headers, bytes: new Uint8Array([9, 9, 9]) };
  };

  await mod.loadOriginalImage("/attempts/a/questions/q/asset/question/1", new AbortController().signal, transport);
  assert.strictEqual(fullFetches, 1);
  assert.strictEqual(persisted, 1);
});

test("registerImageGrants revokes stale path grants when attempt/version scope changes", () => {
  const grants = loadTsModule("/app/frontend/src/assets/assetGrants.ts");
  const invalidated = [];

  grants.registerImageGrants("attemptA", [{ id: "q1", asset_count: 1, solution_asset_count: 1 }], false, "original", (p) => invalidated.push(p), true);
  assert.ok(grants.imageGrant("/attempts/attemptA/questions/q1/asset/question/0"));

  grants.registerImageGrants("attemptA", [{ id: "q1", asset_count: 0, solution_asset_count: 0 }], false, "original", (p) => invalidated.push(p), false);
  assert.ok(!grants.imageGrant("/attempts/attemptA/questions/q1/asset/question/0"));
  assert.ok(invalidated.length >= 1);
});

async function run() {
  let passed = 0;
  for (const t of tests) {
    try {
      await t.fn();
      passed += 1;
      console.log(`PASS: ${t.name}`);
    } catch (e) {
      console.error(`FAIL: ${t.name}`);
      console.error(e && e.stack ? e.stack : e);
      process.exitCode = 1;
      break;
    }
  }
  if (!process.exitCode) {
    console.log(`\nAll iteration40 isolated frontend tests passed (${passed}/${tests.length}).`);
    console.log("Note: timings/concurrency are isolated simulations, not live network latency proof.");
  }
}

run();
