const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");
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

const tests = [];
const test = (name, fn) => tests.push({ name, fn });

test("Listener fanout drops with path-scoped subscription vs 63241ad baseline", async () => {
  const currentSource = fs.readFileSync("/app/frontend/src/assets/PrivateAssetQueue.ts", "utf8");
  const oldSource = execSync("git -C /app show 63241ad:frontend/src/assets/PrivateAssetQueue.ts", { encoding: "utf8" });

  const { PrivateAssetQueue: CurrentQueue } = transpileTs(currentSource, "/app/frontend/src/assets/PrivateAssetQueue.ts");
  const { PrivateAssetQueue: OldQueue } = transpileTs(oldSource, "/tmp/PrivateAssetQueue.old.ts");

  const mkQueue = (Q) => new Q(async (p) => {
    await wait(1);
    return { uri: `blob://${p}`, bytes: 1 };
  }, 6, 1024 * 1024);

  const paths = Array.from({ length: 75 }, (_, i) => `/attempts/A/questions/Q${i}/asset/question/0`);

  const oldQ = mkQueue(OldQueue);
  let oldFanout = 0;
  const unsubOld = oldQ.subscribe(() => { oldFanout += 1; });
  oldQ.preload(paths);
  await wait(350);
  unsubOld();

  const currentQ = mkQueue(CurrentQueue);
  let pathFanout = 0;
  const unsubPath = currentQ.subscribePath(paths[0], () => { pathFanout += 1; });
  currentQ.preload(paths);
  await wait(350);
  unsubPath();

  assert.ok(oldFanout > pathFanout, `expected old fanout (${oldFanout}) > path fanout (${pathFanout})`);
  console.log(`FANOUT_COUNTS old_global=${oldFanout} current_path=${pathFanout} synthetic_completions=75`);
});

test("priorityOperations lets read overtake queued writes but not barrier", async () => {
  const { priorityOperations } = loadTsModule("/app/frontend/src/assets/deviceCache/priorityOperations.ts");
  const run = priorityOperations();
  const order = [];

  const p1 = run(async () => { order.push("write-1"); await wait(5); }, 0, false);
  const p2 = run(async () => { order.push("write-2"); await wait(5); }, 0, false);
  const p3 = run(async () => { order.push("read"); await wait(1); }, 100, false);
  const p4 = run(async () => { order.push("barrier-open"); await wait(5); }, 0, true);

  await Promise.all([p1, p2, p3, p4]);
  const readIndex = order.indexOf("read");
  const write2Index = order.indexOf("write-2");
  const barrierIndex = order.indexOf("barrier-open");
  assert.ok(readIndex >= 0 && barrierIndex >= 0 && write2Index >= 0);
  assert.ok(readIndex < write2Index, `read should overtake queued write before barrier; got ${order.join(" -> ")}`);
  assert.ok(readIndex < barrierIndex, `read should execute before barrier; got ${order.join(" -> ")}`);
});

test("imageBase64 exact roundtrip on boundary sizes and aborts", async () => {
  const { imageBase64 } = loadTsModule("/app/frontend/src/assets/base64.ts");
  const sizes = [0, 1, 2, 3, 48 * 1024, 48 * 1024 + 1, 1024 * 1024];

  for (const n of sizes) {
    const src = new Uint8Array(n);
    for (let i = 0; i < src.length; i++) src[i] = (i * 131 + 17) & 255;
    const ctl = new AbortController();
    const b64 = await imageBase64(src, ctl.signal);
    const back = new Uint8Array(Buffer.from(b64, "base64"));
    assert.strictEqual(back.length, src.length, `size mismatch for ${n}`);
    for (let i = 0; i < src.length; i += Math.max(1, Math.floor(src.length / 17) || 1)) assert.strictEqual(back[i], src[i], `byte mismatch at ${i} size ${n}`);
  }

  const ctl = new AbortController();
  const large = new Uint8Array(1024 * 1024);
  const encode = imageBase64(large, ctl.signal);
  setTimeout(() => ctl.abort(), 0);
  await assert.rejects(() => encode, (e) => e?.name === "AbortError");
});

test("imageDimensions parses PNG/JPEG/WebP/GIF headers and ignores corrupt values", () => {
  const { imageDimensions } = loadTsModule("/app/frontend/src/assets/imageDimensions.ts");

  const png = new Uint8Array(24);
  png.set([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a], 0);
  png[16] = 0x00; png[17] = 0x00; png[18] = 0x01; png[19] = 0x90; // 400
  png[20] = 0x00; png[21] = 0x00; png[22] = 0x00; png[23] = 0x64; // 100
  assert.deepStrictEqual(imageDimensions(png), { width: 400, height: 100 });

  const gif = new Uint8Array(10);
  gif.set([71, 73, 70, 56, 57, 97], 0);
  gif[6] = 0x20; gif[7] = 0x03; // 800
  gif[8] = 0x58; gif[9] = 0x02; // 600
  assert.deepStrictEqual(imageDimensions(gif), { width: 800, height: 600 });

  const webp = new Uint8Array(30);
  webp.set([0x52, 0x49, 0x46, 0x46], 0); // RIFF
  webp.set([0x57, 0x45, 0x42, 0x50], 8); // WEBP
  webp.set([0x56, 0x50, 0x38, 0x58], 12); // VP8X
  webp[24] = 99; webp[25] = 0; webp[26] = 0; // width-1 = 99 => 100
  webp[27] = 49; webp[28] = 0; webp[29] = 0; // height-1 = 49 => 50
  assert.deepStrictEqual(imageDimensions(webp), { width: 100, height: 50 });

  const jpeg = new Uint8Array([0xff, 0xd8, 0xff, 0xc0, 0x00, 0x11, 0x08, 0x01, 0x2c, 0x02, 0x58, 0x03, 0x01, 0x11, 0x00, 0xff, 0xd9]);
  assert.deepStrictEqual(imageDimensions(jpeg), { width: 600, height: 300 });

  const bad = new Uint8Array([0, 1, 2, 3, 4]);
  assert.deepStrictEqual(imageDimensions(bad), {});
});

test("OfflineMath shell uses stable in-RAM updates and blocks external navigation", () => {
  const offline = fs.readFileSync("/app/frontend/src/components/OfflineMath.tsx", "utf8");
  const mathText = fs.readFileSync("/app/frontend/src/components/MathText.tsx", "utf8");
  const rapid = fs.readFileSync("/app/frontend/app/rapid/session.tsx", "utf8");

  assert.ok(offline.includes("source={SOURCE}"), "WebView should keep a stable SOURCE shell");
  assert.ok(offline.includes("originWhitelist={[\"about:blank\"]}"), "WebView origin whitelist should stay local");
  assert.ok(offline.includes("request.url === \"about:blank\" || request.url.startsWith(\"data:text/html\")"), "WebView must block external navigations");
  assert.ok(offline.includes("window.updateMath"), "Math payload should update in RAM via updateMath");
  assert.ok(offline.includes("revision"), "Math updates should be revision-gated");

  assert.ok(mathText.includes("Platform.OS === \"web\""), "Web should avoid native WebView typesetting path");
  assert.ok(mathText.includes("plainMath(text)"), "Web/plain fallback should use plainMath");

  assert.ok(rapid.includes("setInterval(() =>"), "Rapid session timer should still tick");
  assert.ok(rapid.includes("Math.ceil(previous / 1000) === Math.ceil(Math.max(0, l) / 1000)"), "Rapid timer UI should update once per second");
  assert.ok(rapid.includes("const LIMIT = 20000"), "Rapid timer limit must remain 20 seconds");
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
    console.log(`\nAll iteration48 isolated tests passed (${passed}/${tests.length}).`);
  }
}

run();
