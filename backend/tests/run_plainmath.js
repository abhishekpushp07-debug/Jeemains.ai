// AI solutions web fallback: run the real plainMath from AiSolution.tsx over /tmp/ai_items.json and report LaTeX leftovers
const fs = require("fs");
const ts = require("/app/frontend/node_modules/typescript");
const src = fs.readFileSync("/app/frontend/src/components/AiSolution.tsx", "utf8");
const a = src.indexOf("const SYM"), b = src.indexOf("function html");
const js = ts.transpileModule(src.slice(a, b).replace("export function plainMath", "function plainMath") + "\nmodule.exports={plainMath};", { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2019 } }).outputText;
const m = { exports: {} }; new Function("module", "exports", js)(m, m.exports);
const { plainMath } = m.exports;
const items = JSON.parse(fs.readFileSync("/tmp/ai_items.json", "utf8"));
const texts = (s) => [s.concept, s.shortcut, s.time_tip, s.insight, ...(s.given || []), ...(s.common_mistakes || []), ...(s.steps || []).flatMap((x) => [x.title, x.explanation])].filter(Boolean);
const words = /\b(frac|dfrac|tfrac|binom|mid|longrightarrow|xrightarrow|rightarrow|begin|end|sqrt|mathrm|text|left|right|underbrace|subseteq|varnothing|neg|kappa|rightleftharpoons|cdot|times|quad|boxed|operatorname|mathbf)\b/;
let total = 0, bad = [], backslash = 0, wordHits = 0, crashes = 0, unbalanced = 0, caret = 0;
const cmdCount = {};
for (const it of items) for (const t of texts(it.solution || {})) {
  total++;
  let o;
  try { o = plainMath(t); } catch (e) { crashes++; bad.push({ t, o: "CRASH " + e.message }); continue; }
  const hasBs = o.includes("\\");
  // only count word hits that were LaTeX commands in source (avoid prose like "end of", "left side")
  const srcCmds = new Set([...t.matchAll(/\\([A-Za-z]+)/g)].map((x) => x[1]));
  const wm = [...o.matchAll(new RegExp(words.source, "g"))].map((x) => x[1]).filter((w) => srcCmds.has(w));
  if (hasBs) backslash++;
  if (wm.length) { wordHits++; wm.forEach((w) => (cmdCount[w] = (cmdCount[w] || 0) + 1)); }
  if (/[\^_]/.test(o)) caret++;
  if (hasBs || wm.length) bad.push({ t, o, wm });
}
console.log(JSON.stringify({ total, leftovers: bad.length, pct: ((100 * bad.length) / total).toFixed(2), backslash, wordHits, crashes, caretOrUnderscoreRemaining: caret, cmdCount }, null, 1));
for (const x of bad.slice(0, 25)) console.log("---\nIN :", x.t.slice(0, 300), "\nOUT:", String(x.o).slice(0, 300), x.wm || "");
if (process.argv[2] === "samples") {
  const pick = /frac|binom|circ|sqrt|xrightarrow|begin|mid|%/;
  let n = 0;
  for (const it of items) for (const t of texts(it.solution || {})) if (pick.test(t) && n++ < 40) console.log("===\nIN :", t.slice(0, 220), "\nOUT:", plainMath(t).slice(0, 220));
}
