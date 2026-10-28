const fs = require("fs");
const path = require("path");
const vm = require("vm");
const assert = require("assert");
const Module = require("module");
const FRONTEND_NODE_MODULES = "/app/frontend/node_modules";
const ts = require(path.join(FRONTEND_NODE_MODULES, "typescript"));
const React = require(path.join(FRONTEND_NODE_MODULES, "react"));
const processColorWeb = require(path.join(
  FRONTEND_NODE_MODULES,
  "react-native-web/dist/cjs/exports/processColor",
));

const ROOT = "/app";
const FRONTEND = path.join(ROOT, "frontend");
const EXTRACTOR_PATH = path.join(
  FRONTEND,
  "node_modules/react-native-svg/lib/commonjs/lib/extract/extractGradient.js",
);
const GRADIENT_STOP_TS = path.join(FRONTEND, "src/gradientStop.ts");
const WEBSITE_GRADIENT_TSX = path.join(FRONTEND, "src/components/WebsiteGradient.tsx");
const TOKENS_JSON = path.join(FRONTEND, "assets/website-2026-10-26/design-tokens.json");

function alphaByte(packed) {
  return (packed >>> 24) & 0xff;
}

function rgbHexFromPacked(packed) {
  return `#${(packed & 0x00ffffff).toString(16).padStart(6, "0")}`;
}

function approxEqual(a, b, epsilon = 1e-9) {
  return Math.abs(a - b) <= epsilon;
}

function loadTsModuleWithProcessColor(tsPath, processColorImpl, stubs = {}) {
  const source = fs.readFileSync(tsPath, "utf8");
  const transpiled = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2020,
      jsx: ts.JsxEmit.ReactJSX,
      esModuleInterop: true,
    },
    fileName: tsPath,
  }).outputText;

  const moduleObj = { exports: {} };
  const localRequire = (specifier) => {
    if (Object.prototype.hasOwnProperty.call(stubs, specifier)) return stubs[specifier];
    if (specifier === "react-native") {
      return { processColor: processColorImpl };
    }
    if (specifier.startsWith("@/")) {
      const resolved = path.join(FRONTEND, specifier.slice(2));
      if (fs.existsSync(resolved) || fs.existsSync(`${resolved}.ts`) || fs.existsSync(`${resolved}.tsx`)) {
        return require(resolved);
      }
    }
    if (specifier.startsWith("./") || specifier.startsWith("../")) {
      const resolved = path.resolve(path.dirname(tsPath), specifier);
      if (resolved.endsWith(".json") || fs.existsSync(`${resolved}.json`)) {
        return require(resolved.endsWith(".json") ? resolved : `${resolved}.json`);
      }
    }
    return require(specifier);
  };

  vm.runInNewContext(transpiled, {
    module: moduleObj,
    exports: moduleObj.exports,
    require: localRequire,
    __dirname: path.dirname(tsPath),
    __filename: tsPath,
    console,
  });

  return moduleObj.exports;
}

function loadNativeSvgExtractorWithProcessColor(processColorImpl) {
  const origLoad = Module._load;
  try {
    Module._load = function patched(request, parent, isMain) {
      if (request === "react-native") {
        return { processColor: processColorImpl };
      }
      return origLoad(request, parent, isMain);
    };
    delete require.cache[EXTRACTOR_PATH];
    const mod = require(EXTRACTOR_PATH);
    return typeof mod === "function" ? mod : mod.default;
  } finally {
    Module._load = origLoad;
  }
}

function gradientFromStops(extractGradient, stops) {
  const children = stops.map((stop) => React.createElement("stop", stop));
  const out = extractGradient({ id: "g", children }, {});
  return out?.gradient ?? [];
}

function parseAlphaExpectationsFromTokens() {
  const tokens = JSON.parse(fs.readFileSync(TOKENS_JSON, "utf8"));
  const allIndia = tokens.viewports["390"].home_cards["all-india"];
  const values = {
    bannerLayers: allIndia.default.backgroundImage,
    shine: allIndia.before.backgroundImage,
    cta: allIndia[".flagship-primary"].backgroundImage,
    ribbon: allIndia[".series-100ai-badge"].backgroundImage,
  };
  return values;
}

function testGradientStopConversion() {
  const { gradientStop } = loadTsModuleWithProcessColor(
    GRADIENT_STOP_TS,
    (color) => processColorWeb(color),
  );

  const alphas = [0, 0.04, 0.1, 0.13, 0.15, 0.2, 0.25, 1];
  for (const a of alphas) {
    const color = `rgba(255,255,255,${a})`;
    const packed = processColorWeb(color);
    const out = gradientStop(color);
    assert.strictEqual(out.stopColor, "#ffffff", `stopColor mismatch for alpha ${a}`);
    const expected = alphaByte(packed) / 255;
    assert(
      approxEqual(out.stopOpacity, expected),
      `stopOpacity mismatch for alpha ${a}: got ${out.stopOpacity}, want ${expected}`,
    );
  }

  const named = gradientStop("transparent");
  assert.strictEqual(named.stopColor, "#000000");
  assert.strictEqual(named.stopOpacity, 0);

  const hexWithAlpha = gradientStop("#ff000080");
  assert.strictEqual(hexWithAlpha.stopColor, "#ff0000");
  assert(approxEqual(hexWithAlpha.stopOpacity, 128 / 255));

  const cssRgbaHexTransparent = gradientStop("#80ff0000");
  assert.strictEqual(cssRgbaHexTransparent.stopColor, "#80ff00");
  assert.strictEqual(cssRgbaHexTransparent.stopOpacity, 0);

  const invalid = gradientStop("not-a-color");
  assert.strictEqual(invalid.stopColor, "not-a-color");
  assert.strictEqual(invalid.stopOpacity, 1);

  const unsignedPacked = 0x33ff0000; // alpha 51 -> 0.2 red
  const signedPacked = -1342177280; // 0xb0000000 alpha 176 -> ~0.6902
  const { gradientStop: gsUnsigned } = loadTsModuleWithProcessColor(
    GRADIENT_STOP_TS,
    () => unsignedPacked,
  );
  const { gradientStop: gsSigned } = loadTsModuleWithProcessColor(
    GRADIENT_STOP_TS,
    () => signedPacked,
  );
  assert.strictEqual(gsUnsigned("any").stopColor, "#ff0000");
  assert(approxEqual(gsUnsigned("any").stopOpacity, 51 / 255));
  assert.strictEqual(gsSigned("any").stopColor, "#000000");
  assert(approxEqual(gsSigned("any").stopOpacity, 176 / 255));
}

function testActualNativeSvgExtractorBeforeAfter() {
  const extractGradient = loadNativeSvgExtractorWithProcessColor((c) => processColorWeb(c));

  const before = gradientFromStops(extractGradient, [
    { offset: "0%", stopColor: "rgba(0,0,0,0)" },
    { offset: "50%", stopColor: "rgba(255,255,255,0.2)" },
    { offset: "100%", stopColor: "rgba(255,255,255,0.1)" },
  ]);

  assert.strictEqual(alphaByte(before[1]), 255, "Before pipeline alpha should be forced to 255");
  assert.strictEqual(alphaByte(before[3]), 255, "Before pipeline alpha should be forced to 255");
  assert.strictEqual(alphaByte(before[5]), 255, "Before pipeline alpha should be forced to 255");

  const after = gradientFromStops(extractGradient, [
    { offset: "0%", stopColor: "#000000", stopOpacity: 0 },
    { offset: "50%", stopColor: "#ffffff", stopOpacity: 0.2 },
    { offset: "100%", stopColor: "#ffffff", stopOpacity: 0.1 },
  ]);

  assert.strictEqual(alphaByte(after[1]), 0, "transparent alpha must be 0 on native");
  assert.strictEqual(alphaByte(after[3]), 51, "0.2 alpha must map to byte 51");
  assert.strictEqual(alphaByte(after[5]), 26, "0.1 alpha must map to byte 26 (quantized)");
  assert.strictEqual(rgbHexFromPacked(after[3]), "#ffffff");
  assert.strictEqual(rgbHexFromPacked(after[1]), "#000000");
}

function testTokenPipelinesAndAlphaSet() {
  const extractGradient = loadNativeSvgExtractorWithProcessColor((c) => processColorWeb(c));
  const { gradientStop } = loadTsModuleWithProcessColor(
    GRADIENT_STOP_TS,
    (c) => processColorWeb(c),
  );

  const vals = parseAlphaExpectationsFromTokens();
  const alphaTargets = new Set([0, 10, 26, 33, 38, 51, 64, 255]);
  // 0,.04,.1,.13,.15,.2,.25,1 -> quantized bytes [0,10,26,33,38,51,64,255]

  const all = [vals.bannerLayers, vals.shine, vals.cta, vals.ribbon].join("\n");
  const rgbaMatches = all.match(/rgba?\([^\)]+\)/g) || [];
  const alphaBytesFound = new Set();
  for (const c of rgbaMatches) {
    const p = processColorWeb(c);
    alphaBytesFound.add(alphaByte(p));
  }
  for (const x of alphaTargets) {
    assert(alphaBytesFound.has(x), `Expected alpha byte ${x} from exported all-india layers`);
  }

  // CTA check: before native extractor is wrong without explicit stopOpacity.
  const ctaBefore = gradientFromStops(extractGradient, [
    { offset: "0%", stopColor: "rgba(255, 255, 255, 0.1)" },
    { offset: "55%", stopColor: "rgba(0, 0, 0, 0)" },
  ]);
  assert.strictEqual(alphaByte(ctaBefore[1]), 255);
  assert.strictEqual(alphaByte(ctaBefore[3]), 255);

  // After gradientStop split.
  const ctaAfterStops = [
    { offset: "0%", color: "rgba(255, 255, 255, 0.1)" },
    { offset: "55%", color: "rgba(0, 0, 0, 0)" },
  ].map((s) => ({ offset: s.offset, ...gradientStop(s.color) }));
  const ctaAfter = gradientFromStops(extractGradient, ctaAfterStops);
  assert.strictEqual(alphaByte(ctaAfter[1]), 26, "CTA 0.1 should be alpha byte 26");
  assert.strictEqual(alphaByte(ctaAfter[3]), 0, "CTA transparent black should be alpha byte 0");
}

function testWebsiteGradientForwardingStatic() {
  const src = fs.readFileSync(WEBSITE_GRADIENT_TSX, "utf8");
  assert(src.includes("useMemo(() => parseGradientLayers(value).reverse().map"), "useMemo+reverse pipeline missing");
  assert(src.includes("...gradientStop(stop.color)"), "gradientStop split not forwarded");
  assert(src.includes("stopColor={stop.stopColor}"), "Stop stopColor prop missing");
  assert(src.includes("stopOpacity={stop.stopOpacity}"), "Stop stopOpacity prop missing");
  assert(src.includes("[value]"), "useMemo dependency on value missing");
  assert(src.includes("Math.max(layout.width, 1)"), "layout width floor missing");
  assert(src.includes("Math.max(layout.height, 1)"), "layout height floor missing");
}

function testActualComponentToNativeExtractor() {
  const renderToStaticMarkup = require(path.join(FRONTEND_NODE_MODULES, "react-dom/server")).renderToStaticMarkup;
  const design = loadTsModuleWithProcessColor(path.join(FRONTEND, "src/websiteDesign.ts"), processColorWeb);
  const conversion = loadTsModuleWithProcessColor(GRADIENT_STOP_TS, processColorWeb);
  const extractGradient = loadNativeSvgExtractorWithProcessColor(processColorWeb);
  let emitted = [], geometry = [];
  const svg = {
    __esModule: true, default: "svg", Defs: "defs", Rect: "rect",
    LinearGradient: (props) => { geometry.push(props); return React.createElement("linearGradient", props); },
    Stop: (props) => { emitted.push(props); return React.createElement("stop", props); },
  };
  const { WebsiteGradient } = loadTsModuleWithProcessColor(WEBSITE_GRADIENT_TSX, processColorWeb, {
    react: React,
    "react/jsx-runtime": require(path.join(FRONTEND_NODE_MODULES, "react/jsx-runtime")),
    "react-native": { StyleSheet: { absoluteFill: {} }, View: ({ children }) => React.createElement("div", {}, children) },
    "react-native-svg": svg,
    "@/src/websiteDesign": design,
    "@/src/gradientStop": conversion,
  });
  for (const [name, value] of Object.entries(parseAlphaExpectationsFromTokens())) {
    emitted = []; geometry = [];
    renderToStaticMarkup(React.createElement(WebsiteGradient, { value }));
    const layers = design.parseGradientLayers(value).reverse();
    assert.strictEqual(geometry.length, layers.length, `${name}: layer count`);
    assert.strictEqual(emitted.length, layers.reduce((sum, layer) => sum + layer.stops.length, 0));
    let start = 0;
    layers.forEach((layer, layerIndex) => {
      const expectedLine = design.cssGradientLine(layer.angle, 1, 1);
      for (const key of ["x1", "y1", "x2", "y2"]) assert.strictEqual(geometry[layerIndex][key], expectedLine[key]);
      const props = emitted.slice(start, start + layer.stops.length);
      const actual = gradientFromStops(extractGradient, props);
      layer.stops.forEach((stop, i) => {
        assert.strictEqual(props[i].offset, stop.offset, `${name}: original offset`);
        assert.strictEqual(actual[i * 2], stop.offset, `${name}: native offset`);
        assert.strictEqual(actual[i * 2 + 1] >>> 0, processColorWeb(stop.color) >>> 0, `${name}: original ARGB preserved`);
      });
      start += layer.stops.length;
    });
  }
}

function run() {
  const tests = [
    ["gradientStop conversion set", testGradientStopConversion],
    ["native svg extractor before/after behavior", testActualNativeSvgExtractorBeforeAfter],
    ["token pipeline + alpha quantization coverage", testTokenPipelinesAndAlphaSet],
    ["WebsiteGradient forwarding/static invariants", testWebsiteGradientForwardingStatic],
    ["actual component → original layers → native packed gradients", testActualComponentToNativeExtractor],
  ];

  let passed = 0;
  for (const [name, fn] of tests) {
    try {
      fn();
      passed += 1;
      console.log(`PASS: ${name}`);
    } catch (err) {
      console.error(`FAIL: ${name}`);
      console.error(err && err.stack ? err.stack : err);
      process.exitCode = 1;
      break;
    }
  }
  if (!process.exitCode) {
    console.log(`All iteration52 gradient regression tests passed (${passed}/${tests.length}).`);
  }
}

run();
