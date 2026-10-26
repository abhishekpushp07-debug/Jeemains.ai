const assert = require("assert");
const fs = require("fs");
const path = require("path");
const ts = require("/app/frontend/node_modules/typescript");

const wait = (ms = 0) => new Promise((r) => setTimeout(r, ms));
const deferred = () => {
  let resolve;
  let reject;
  const promise = new Promise((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
};

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
    if (id.startsWith("@/")) {
      throw new Error(`Missing stub for alias import: ${id}`);
    }
    return require(id);
  };
  const fn = new Function("require", "module", "exports", "__filename", "__dirname", transpiled);
  fn(localRequire, mod, mod.exports, filePath, path.dirname(filePath));
  return mod.exports;
}

const tests = [];
const test = (name, fn) => tests.push({ name, fn });

const queueModule = loadTsModule("/app/frontend/src/assets/PrivateAssetQueue.ts");
const paperAssets = loadTsModule("/app/frontend/src/assets/paperAssets.ts", {
  react: {
    useCallback: (f) => f,
    useEffect: () => {},
    useMemo: (f) => f(),
    useSyncExternalStore: () => 0,
  },
  "expo-router": { useFocusEffect: () => {} },
  "@/src/api/client": {
    privateAssets: {
      subscribe: () => () => {},
      snapshot: () => 0,
      selectGroup: () => {},
      isGroup: () => true,
      preload: () => {},
      pin: () => {},
      get: async () => "uri",
      retry: () => {},
      progress: () => ({ total: 0, ready: 0, failed: 0, queued: 0, limited: false }),
    },
  },
});

const { PrivateAssetQueue } = queueModule;

test("PrivateAssetQueue deduplicates simultaneous same-path requests", async () => {
  let calls = 0;
  const gate = deferred();
  const q = new PrivateAssetQueue(async () => {
    calls += 1;
    return gate.promise;
  }, 4, 1024 * 1024);

  const all = Array.from({ length: 12 }, () => q.get("/same", 100));
  await wait(5);
  assert.strictEqual(calls, 1, "loader should run once for same path");
  gate.resolve({ uri: "blob://same", bytes: 10 });
  const out = await Promise.all(all);
  assert.ok(out.every((x) => x === "blob://same"));
});

test("Queue reserves one slot for visible question priority", async () => {
  const started = [];
  const inflight = new Map();
  let active = 0;
  let maxActive = 0;

  const q = new PrivateAssetQueue(async (p) => {
    started.push(p);
    active += 1;
    maxActive = Math.max(maxActive, active);
    const d = deferred();
    inflight.set(p, d);
    return d.promise.finally(() => {
      active -= 1;
    });
  }, 4, 1024 * 1024);

  q.get("/bg-1", 10).catch(() => {});
  q.get("/bg-2", 10).catch(() => {});
  q.get("/bg-3", 10).catch(() => {});
  q.get("/bg-4", 10).catch(() => {});
  await wait(10);
  assert.strictEqual(started.filter((x) => x.startsWith("/bg")).length, 3, "only 3 background jobs should start");

  const focus = q.get("/focus", 100);
  await wait(10);
  assert.ok(started.includes("/focus"), "visible/focus job should use reserved slot");
  assert.ok(maxActive <= 4, "max parallel must remain bounded to 4");

  for (const [k, d] of inflight.entries()) d.resolve({ uri: `blob://${k}`, bytes: 1 });
  await focus;
});

test("Queue bounded concurrency and preload completes normal 75/150 jobs", async () => {
  let active = 0;
  let maxActive = 0;
  let calls = 0;
  const q = new PrivateAssetQueue(async (p) => {
    calls += 1;
    active += 1;
    maxActive = Math.max(maxActive, active);
    await wait(1);
    active -= 1;
    return { uri: `blob://${p}`, bytes: 1024 };
  }, 4, 128 * 1024 * 1024);

  const paths150 = Array.from({ length: 150 }, (_, i) => `/p/${i}`);
  q.preload(paths150);

  const start = Date.now();
  while (Date.now() - start < 3000) {
    const prog = q.progress(paths150);
    if (prog.ready === 150) break;
    await wait(20);
  }
  const prog = q.progress(paths150);
  assert.strictEqual(prog.ready, 150, "all 150 normal-size preload jobs should complete in simulation");
  assert.ok(maxActive <= 4, "parallelism must stay <=4");
  assert.strictEqual(calls, 150, "each path should load exactly once");
});

test("Cache hit avoids refetch on back navigation", async () => {
  let calls = 0;
  const q = new PrivateAssetQueue(async () => {
    calls += 1;
    return { uri: "blob://once", bytes: 10 };
  }, 4, 1024 * 1024);

  await q.get("/cached", 100);
  await q.get("/cached", 100);
  assert.strictEqual(calls, 1, "second read should hit cache without loader");
});

test("Two-crop image order and selected-question prioritization stay stable", async () => {
  const rows = [
    { id: "q1", number: 1, subject: "Physics", asset_count: 2, solution_asset_count: 2 },
    { id: "q2", number: 2, subject: "Physics", asset_count: 1, solution_asset_count: 1 },
    { id: "q3", number: 3, subject: "Chemistry", asset_count: 1, solution_asset_count: 0 },
  ];
  const paths = paperAssets.prioritizedPaths("A1", rows, "q1", true, "original");
  assert.strictEqual(paths[0], "/attempts/A1/questions/q1/asset/question/0");
  assert.strictEqual(paths[1], "/attempts/A1/questions/q1/asset/question/1");
  assert.strictEqual(paths[2], "/attempts/A1/questions/q1/asset/solution/0");
  assert.ok(paths.indexOf("/attempts/A1/questions/q2/asset/question/0") < paths.indexOf("/attempts/A1/questions/q3/asset/question/0"));
});

test("Failure + manual retry recovers for non-cooldown failures", async () => {
  let calls = 0;
  const q = new PrivateAssetQueue(async () => {
    calls += 1;
    if (calls === 1) throw new Error("boom");
    return { uri: "blob://ok", bytes: 10 };
  }, 4, 1024 * 1024);

  await assert.rejects(() => q.get("/retry-me", 100));
  q.retry(["/retry-me"]);
  const uri = await q.get("/retry-me", 100);
  assert.strictEqual(uri, "blob://ok");
});

test("Retry cooldown is respected; 429 has anti-hammer floor and manual retry cannot bypass", async () => {
  let calls429 = 0;
  const q429 = new PrivateAssetQueue(async () => {
    calls429 += 1;
    const e = new Error("rate");
    e.status = 429;
    e.retryAfterMs = 120;
    throw e;
  }, 4, 1024 * 1024);

  await assert.rejects(() => q429.get("/rate", 100));
  await assert.rejects(() => q429.get("/rate", 100));
  q429.retry(["/rate"]);
  await assert.rejects(() => q429.get("/rate", 100));
  await wait(150);
  await assert.rejects(() => q429.get("/rate", 100));
  assert.strictEqual(calls429, 1, "429 should stay in cooldown (anti-hammer floor) for this short window");

  let calls503 = 0;
  const q503 = new PrivateAssetQueue(async () => {
    calls503 += 1;
    const e = new Error("busy");
    e.status = 503;
    e.retryAfterMs = 120;
    throw e;
  }, 4, 1024 * 1024);

  await assert.rejects(() => q503.get("/busy", 100));
  await assert.rejects(() => q503.get("/busy", 100));
  assert.strictEqual(calls503, 1, "cooldown should block immediate re-hit");
  await wait(150);
  await assert.rejects(() => q503.get("/busy", 100));
  assert.strictEqual(calls503, 2, "after retryAfter window loader should run again");
});

test("clear() aborts running work and late completion does not cache stale account", async () => {
  const d = deferred();
  const q = new PrivateAssetQueue(async () => d.promise, 4, 1024 * 1024);
  const p = q.get("/late", 100);
  await wait(5);
  q.clear();
  d.resolve({ uri: "blob://late", bytes: 10 });
  await assert.rejects(() => p, (e) => e && e.name === "AbortError");
  assert.strictEqual(q.peek("/late"), undefined);
});

test("pause() blocks new loads", async () => {
  let calls = 0;
  const q = new PrivateAssetQueue(async () => {
    calls += 1;
    return { uri: "blob://x", bytes: 10 };
  }, 4, 1024 * 1024);

  q.pause();
  await assert.rejects(() => q.get("/blocked", 100), (e) => e && e.name === "AbortError");
  assert.strictEqual(calls, 0);
});

test("selectGroup cancels obsolete background jobs", async () => {
  const q = new PrivateAssetQueue((p, signal) => new Promise((resolve, reject) => {
    const t = setTimeout(() => resolve({ uri: `blob://${p}`, bytes: 1 }), 100);
    signal.addEventListener("abort", () => {
      clearTimeout(t);
      reject(Object.assign(new Error("aborted"), { name: "AbortError" }));
    }, { once: true });
  }), 4, 1024 * 1024);

  q.selectGroup("g1");
  const old = q.get("/g1-bg", 10);
  await wait(10);
  q.selectGroup("g2");
  await assert.rejects(() => old, (e) => e && e.name === "AbortError");
});

test("Pinned items are not evicted; maxBytes budget is strict", async () => {
  const disposed = [];
  const q = new PrivateAssetQueue(async (p) => ({ uri: `blob://${p}`, bytes: 6, dispose: () => disposed.push(p) }), 4, 12);

  await q.get("/a", 100);
  await q.get("/b", 100);
  q.pin(["/a"]);
  await q.get("/c", 100);

  assert.ok(q.peek("/a"), "pinned /a must stay");
  assert.strictEqual(q.peek("/b"), undefined, "unpinned /b should evict first");
  assert.ok(disposed.includes("/b"));

  const q2 = new PrivateAssetQueue(async () => ({ uri: "blob://huge", bytes: 1000 }), 4, 12);
  await assert.rejects(() => q2.get("/huge", 100), /exceeds safe image memory/i);
});

test("Repeated preload failures do not spin an infinite refill loop", async () => {
  let calls = 0;
  const q = new PrivateAssetQueue(async () => {
    calls += 1;
    throw new Error("fail");
  }, 4, 1024 * 1024);

  const paths = ["/f1", "/f2", "/f3", "/f4", "/f5"];
  q.preload(paths);
  await wait(80);
  const first = calls;
  await wait(120);
  assert.strictEqual(calls, first, "failed preload should not refill indefinitely without explicit retry");
});

test("Readiness check does storage write/read/delete and canonical preflight only", async () => {
  const calls = [];
  const kv = new Map();
  let uid = 0;
  const readiness = loadTsModule("/app/frontend/src/api/readiness.ts", {
    "./client": {
      api: async (pathArg, opts) => {
        calls.push({ path: pathArg, opts });
        return { ok: true };
      },
      uuid: () => `u-${++uid}`,
    },
    "@/src/utils/storage": {
      storage: {
        setItem: async (k, v) => {
          kv.set(k, v);
          return true;
        },
        getItem: async (k, fallback) => (kv.has(k) ? kv.get(k) : fallback),
        removeItem: async (k) => {
          kv.delete(k);
          return true;
        },
      },
    },
  });

  const t = await readiness.checkReadiness("set-1");
  assert.ok(Number.isFinite(t));
  assert.strictEqual(calls.length, 1);
  assert.strictEqual(calls[0].path, "/sets/set-1/preflight");
  assert.deepStrictEqual(calls[0].opts.body, { preview: false, test_response: "25" });
});

test("openPyq uses UUID start_key and never uses PIN", async () => {
  const calls = { api: [], post: [], invalidate: [] };
  const kv = new Map();
  let uidCounter = 0;
  const pyq = loadTsModule("/app/frontend/src/api/pyq.ts", {
    "./client": {
      api: async (pathArg) => {
        calls.api.push(pathArg);
        if (pathArg.startsWith("/my/sets/")) return { attempt: null };
        if (pathArg.startsWith("/attempts/")) return { id: "attempt-existing", status: "active" };
        return {};
      },
      post: async (pathArg, body) => {
        calls.post.push({ path: pathArg, body });
        return { id: "attempt-new", status: "active" };
      },
      uuid: () => `uuid-${++uidCounter}`,
    },
    "@/src/utils/storage": {
      storage: {
        getItem: async (k, fallback) => (kv.has(k) ? kv.get(k) : fallback),
        setItem: async (k, v) => {
          kv.set(k, v);
          return true;
        },
        removeItem: async (k) => {
          kv.delete(k);
          return true;
        },
      },
    },
    "@/src/useCached": { invalidate: (k) => calls.invalidate.push(k) },
    "./readiness": { checkReadiness: async () => {} },
  });

  const paper = {
    id: "jee-main-pyq-2026-01-21-s1",
    year: 2026,
    exam_date: "2026-01-21",
    shift: 1,
    count: 75,
    minutes: 180,
    maximum: 300,
    attempt: null,
    latest_result_id: null,
    attempt_count: 0,
  };

  const out = await pyq.openPyq("user-1", paper, 0);
  assert.strictEqual(out.id, "attempt-new");
  assert.strictEqual(calls.post.length, 1);
  assert.strictEqual(calls.post[0].path, `/sets/${paper.id}/start`);
  assert.strictEqual(calls.post[0].body.start_key, "uuid-1");
  assert.ok(!Object.prototype.hasOwnProperty.call(calls.post[0].body, "pin"), "start payload must not include PIN");
});

test("subjectOf handles missing metadata as Uncategorised", async () => {
  assert.strictEqual(paperAssets.subjectOf(undefined), "Uncategorised");
  assert.strictEqual(paperAssets.subjectOf({ subject: "  " }), "Uncategorised");
  assert.strictEqual(paperAssets.subjectOf({ subject: "Physics" }), "Physics");
});

test("Locked bonus and sealed grading payloads cannot enter preload rows", () => {
  const source = [{ id: 'main', subject: 'Physics', asset_count: 2 }, { id: 'bonus', subject: 'Physics', asset_count: 1, bonus: true }];
  assert.deepStrictEqual(paperAssets.availableQuestions(source, false).map(q => q.id), ['main']);
  assert.deepStrictEqual(paperAssets.availableQuestions(source, true).map(q => q.id), ['main', 'bonus']);
  assert.strictEqual(source.length, 2);
  assert.strictEqual(paperAssets.resultIsReleased(202, { summary: {} }), false);
  assert.strictEqual(paperAssets.resultIsReleased(200, { summary: {}, status: 'embargoed' }), false);
  assert.strictEqual(paperAssets.resultIsReleased(200, { status: 'completed' }), false);
  assert.strictEqual(paperAssets.resultIsReleased(200, { summary: {}, status: 'completed' }), true);
  const q = { id: 'q1', asset_count: 1, solution_asset_count: 1 };
  assert.notStrictEqual(paperAssets.imagePaths('a1', q, 'solution', 'original')[0], paperAssets.imagePaths('a1', q, 'solution', 'revised')[0]);
});

test("Actual navigation hook remembers questions per real subject, with uneven five-subject paper", () => {
  const state = []; let cursor = 0;
  const navigation = loadTsModule('/app/frontend/src/components/player/SubjectNavigation.tsx', {
    react: { useMemo: f => f(), useState: initial => { const index = cursor++; if (!(index in state)) state[index] = typeof initial === 'function' ? initial() : initial; return [state[index], next => { state[index] = typeof next === 'function' ? next(state[index]) : next; }]; } },
    'react-native': { StyleSheet: { create: x => x } },
    '@/src/assets/paperAssets': paperAssets,
    '@/src/theme': { colors: {}, space: {}, radius: {}, foregroundOn: x => x, subjectColor: x => x },
    '../ui': {},
  });
  const source = [
    { id: 'p1', number: 1, subject: 'Physics' }, { id: 'p2', number: 2, subject: 'Physics' },
    { id: 'c1', number: 3, subject: 'Chemistry' }, { id: 'm1', number: 4, subject: 'Mathematics' },
    { id: 'e1', number: 5, subject: 'English' }, { id: 'r1', number: 6, subject: 'Reasoning' }, { id: 'r2', number: 7, subject: 'Reasoning' },
  ];
  const before = JSON.stringify(source);
  const render = () => { cursor = 0; return navigation.useSubjectNavigation(source); };
  let nav = render();
  assert.deepStrictEqual(nav.subjects, ['Physics', 'Chemistry', 'Mathematics', 'English', 'Reasoning']);
  assert.strictEqual(nav.question.id, 'p1');
  nav.select('p2'); nav = render(); assert.strictEqual(nav.index, 1);
  assert.strictEqual(nav.rows[nav.index + 1], undefined, 'Next cannot silently jump across subject');
  nav.selectSubject('Reasoning'); nav = render(); assert.strictEqual(nav.question.id, 'r1');
  nav.select('r2'); nav = render();
  nav.selectSubject('Physics'); nav = render(); assert.strictEqual(nav.question.id, 'p2');
  nav.selectSubject('Reasoning'); nav = render(); assert.strictEqual(nav.question.id, 'r2');
  nav.selectSubject('Nonexistent'); nav = render(); assert.strictEqual(nav.question.id, 'r2');
  assert.strictEqual(JSON.stringify(source), before, 'Canonical question order/metadata cannot mutate');
  for (const viewport of [320, 375, 390, 768]) {
    const width = viewport - 48, columns = navigation.gridColumns(width);
    assert.ok(columns * 44 + (columns - 1) * 8 <= width, '44px grid must fit available phone width');
    assert.ok(columns >= 1 && columns <= 6);
  }
});

async function run() {
  const unhandled = [];
  process.on("unhandledRejection", (e) => unhandled.push(e));

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
  await wait(20);
  if (!process.exitCode) {
    assert.strictEqual(unhandled.length, 0, `Unhandled rejections detected: ${unhandled.length}`);
    console.log(`\nAll isolated frontend tests passed (${passed}/${tests.length}).`);
    console.log("Performance note: all timings/concurrency checks are SIMULATED, not real network latency.");
  }
}

run();
