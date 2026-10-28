const assert = require("assert");
const fs = require("fs");
const path = require("path");
const ts = require("/app/frontend/node_modules/typescript");

const wait = (ms = 0) => new Promise((r) => setTimeout(r, ms));

function transpileTs(source, filePath, stubs = {}) {
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

function loadTsModule(filePath, stubs = {}) {
  const source = fs.readFileSync(filePath, "utf8");
  return transpileTs(source, filePath, stubs);
}

function withFastTimeouts(run, capMs = 25) {
  const realSetTimeout = global.setTimeout;
  global.setTimeout = (fn, ms, ...args) => realSetTimeout(fn, Math.min(Number(ms) || 0, capMs), ...args);
  return Promise.resolve()
    .then(run)
    .finally(() => {
      global.setTimeout = realSetTimeout;
    });
}

function mkStorage() {
  const db = new Map();
  return {
    getItem: async (k, d) => (db.has(k) ? db.get(k) : d),
    setItem: async (k, v) => db.set(k, v),
    removeItem: async (k) => db.delete(k),
  };
}

function mkClientModule() {
  const requestDeadlineModule = loadTsModule("/app/frontend/src/api/requestDeadline.ts");
  const fetchCalls = [];
  const storage = mkStorage();
  class QueueStub {
    constructor() {}
    pause() {}
    resume() {}
    clear() {}
    preload() {}
    invalidate() {}
    subscribePath() { return () => {}; }
    value() { return undefined; }
    get() { return Promise.reject(Object.assign(new Error("not used"), { name: "AbortError" })); }
  }
  const stubs = {
    "react-native": { Platform: { OS: "web" } },
    "expo-crypto": { randomUUID: () => "uuid-test" },
    "expo-constants": { expoConfig: { extra: { backendUrl: "https://preview.test", jeeliveApi: "https://jeelive.ai/api" } } },
    "@/src/utils/storage": { storage },
    "@/src/assets/PrivateAssetQueue": { PrivateAssetQueue: QueueStub },
    "expo-image": { Image: { clearMemoryCache: async () => {} } },
    "@/src/assets/assetGrants": {
      clearImageGrants: () => {},
      imageGrant: () => true,
      registerImageGrants: () => {},
    },
    "@/src/assets/deviceCache/cache": { configureImageDisk: () => {}, purgeImageDisk: () => {} },
    "@/src/assets/imageDownload": { loadOriginalImage: async () => ({ status: 200, headers: new Map(), bytes: new Uint8Array() }) },
    "@/src/resourceCache": { resources: { clear: () => {}, invalidate: () => {} } },
    "./requestDeadline": requestDeadlineModule,
  };

  const realFetch = global.fetch;
  const setFetch = (impl) => {
    global.fetch = async (url, options = {}) => {
      fetchCalls.push({ url, options });
      return impl(url, options);
    };
  };
  const resetFetch = () => {
    global.fetch = realFetch;
    fetchCalls.length = 0;
  };

  const mod = loadTsModule("/app/frontend/src/api/client.ts", stubs);
  return { mod, setFetch, resetFetch, fetchCalls, requestDeadlineModule };
}

function response({ status = 200, body = {}, headers = {} } = {}) {
  const map = new Map(Object.entries(headers));
  return {
    status,
    ok: status >= 200 && status < 300,
    headers: { get: (k) => map.get(k) ?? map.get(k.toLowerCase()) ?? null },
    json: async () => body,
  };
}

const tests = [];
const test = (name, fn) => tests.push({ name, fn });

test("requestDeadline enforces full run deadline and clears timer", async () => {
  const requestDeadline = loadTsModule("/app/frontend/src/api/requestDeadline.ts");
  let clearCount = 0;
  const realClear = global.clearTimeout;
  global.clearTimeout = (...args) => {
    clearCount += 1;
    return realClear(...args);
  };
  try {
    await withFastTimeouts(async () => {
      await assert.rejects(
        () => requestDeadline.requestDeadline(() => new Promise(() => {}), 32000),
        (e) => e && e.name === "RequestDeadlineError"
      );
    });
    assert.ok(clearCount >= 1, `clearTimeout should be called, got ${clearCount}`);
  } finally {
    global.clearTimeout = realClear;
  }
});

test("requestDeadline keeps AbortError distinct for caller abort before/during body", async () => {
  const requestDeadline = loadTsModule("/app/frontend/src/api/requestDeadline.ts");
  const pre = new AbortController();
  pre.abort();
  await assert.rejects(
    () => requestDeadline.requestDeadline(async () => ({ ok: true }), 1000, pre.signal),
    (e) => e?.name === "AbortError"
  );

  const mid = new AbortController();
  const run = requestDeadline.requestDeadline(async () => {
    await wait(5);
    return new Promise(() => {});
  }, 32000, mid.signal);
  setTimeout(() => mid.abort(), 10);
  await assert.rejects(() => run, (e) => e?.name === "AbortError");
});

test("apiRaw deadline includes hanging json body and maps deadline to ApiError 503", async () => {
  const { mod, setFetch, resetFetch } = mkClientModule();
  try {
    setFetch(async () => ({
      status: 200,
      ok: true,
      headers: { get: () => null },
      json: async () => new Promise(() => {}),
    }));
    await withFastTimeouts(async () => {
      await assert.rejects(
        () => mod.apiRaw("/my/tests?tab=completed&page=1"),
        (e) => e && e.status === 503 && /taking longer than usual/i.test(String(e.message))
      );
    });
  } finally {
    resetFetch();
  }
});

test("apiRaw never refreshes credential POST; session gets one canonical refresh chance", async () => {
  const { mod, setFetch, resetFetch, fetchCalls } = mkClientModule();
  try {
    setFetch(async (url) => {
      if (String(url).includes("/auth/refresh")) return response({ status: 200, body: { ok: true } });
      return response({ status: 401, body: { detail: "unauthorized" } });
    });

    await assert.rejects(() => mod.apiRaw("/auth/phone", { method: "POST", body: { phone: "x", pin: "0000" } }), (e) => e?.status === 401);
    assert.strictEqual(fetchCalls.filter((x) => String(x.url).includes("/auth/refresh")).length, 0, "credential POST must not trigger refresh");

    fetchCalls.length = 0;
    await assert.rejects(() => mod.apiRaw("/auth/session"), (e) => e?.status === 401);
    assert.strictEqual(fetchCalls.filter((x) => String(x.url).includes("/auth/refresh")).length, 1, "supplied GET/session contract allows rotation and one refresh, never a loop");
  } finally {
    resetFetch();
  }
});

test("apiRaw preserves caller abort signal behaviour", async () => {
  const { mod, setFetch, resetFetch } = mkClientModule();
  try {
    setFetch(async () => ({
      status: 200,
      ok: true,
      headers: { get: () => null },
      json: async () => new Promise(() => {}),
    }));
    const ctl = new AbortController();
    const run = mod.apiRaw("/my/tests?tab=completed&page=1", { signal: ctl.signal });
    setTimeout(() => ctl.abort(), 10);
    await assert.rejects(() => run, (e) => e?.name === "AbortError");
  } finally {
    resetFetch();
  }
});

test("priorityOperations blocks post-barrier high-priority read from crossing barrier", async () => {
  const { priorityOperations } = loadTsModule("/app/frontend/src/assets/deviceCache/priorityOperations.ts");
  const run = priorityOperations();
  const order = [];

  const w1 = run(async () => { order.push("write-1"); await wait(4); }, 0, false);
  const barrier = run(async () => { order.push("barrier-open"); await wait(4); }, 0, true);
  const readAfterBarrier = run(async () => { order.push("read-after"); await wait(1); }, 100, false);
  const w2 = run(async () => { order.push("write-2"); await wait(1); }, 0, false);

  await Promise.all([w1, barrier, readAfterBarrier, w2]);
  const idxRead = order.indexOf("read-after");
  const idxBarrier = order.indexOf("barrier-open");
  assert.ok(idxBarrier >= 0 && idxRead >= 0, `missing events: ${order.join(" -> ")}`);
  assert.ok(idxBarrier < idxRead, `post-barrier read crossed barrier: ${order.join(" -> ")}`);
});

test("imageBase64 roundtrip verifies all bytes with sha + boundary sizes + abort", async () => {
  const crypto = require("crypto");
  const { imageBase64 } = loadTsModule("/app/frontend/src/assets/base64.ts");
  const sizes = [48 * 1024, 48 * 1024 + 1, 1024 * 1024, 1024 * 1024 + 17];

  for (const n of sizes) {
    const src = crypto.randomBytes(n);
    const ctl = new AbortController();
    const b64 = await imageBase64(new Uint8Array(src), ctl.signal);
    const back = Buffer.from(b64, "base64");
    assert.deepStrictEqual(back, src, `all-bytes mismatch for size=${n}`);
    const srcSha = crypto.createHash("sha256").update(src).digest("hex");
    const backSha = crypto.createHash("sha256").update(back).digest("hex");
    assert.strictEqual(backSha, srcSha, `sha mismatch for size=${n}`);
  }

  const ctl = new AbortController();
  const huge = new Uint8Array(1024 * 1024);
  const p = imageBase64(huge, ctl.signal);
  setTimeout(() => ctl.abort(), 0);
  await assert.rejects(() => p, (e) => e?.name === "AbortError");
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
    console.log(`\nAll iteration49 isolated tests passed (${passed}/${tests.length}).`);
  }
}

module.exports = { loadTsModule, mkClientModule, response, wait, withFastTimeouts, mkStorage };
if (require.main === module) run();
