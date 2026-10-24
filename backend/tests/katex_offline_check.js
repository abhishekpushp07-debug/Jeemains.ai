// Offline maths: run the real tex()/html() from AiSolution.tsx with bundled KaTeX over /tmp/ai_items.json
// Checks: no http(s) URLs in the HTML, katex spans present, no throws, count katex-error spans.
const fs = require("fs");
const ts = require("/app/frontend/node_modules/typescript");
(async () => {
  const katex = (await import("/app/frontend/node_modules/katex/dist/katex.mjs")).default;
  const cssSrc = fs.readFileSync("/app/frontend/src/katexCss.ts", "utf8");
  const KATEX_CSS = JSON.parse(cssSrc.slice(cssSrc.indexOf('"'), cssSrc.lastIndexOf('"') + 1));
  const src = fs.readFileSync("/app/frontend/src/components/AiSolution.tsx", "utf8");
  const a = src.indexOf("const esc"), b = src.indexOf("function Native");
  const body = src.slice(a, b).replace("export function plainMath", "function plainMath") + "\nmodule.exports={html,tex,plainMath};";
  const js = ts.transpileModule(body, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 } }).outputText;
  const colors = new Proxy({}, { get: () => "#123456" });
  const m = { exports: {} };
  new Function("module", "exports", "katex", "KATEX_CSS", "colors", js)(m, m.exports, katex, KATEX_CSS, colors);
  const { html, tex } = m.exports;
  const items = JSON.parse(fs.readFileSync("/tmp/ai_items.json", "utf8"));
  let ok = 0, throws = 0, withKatex = 0, withUrl = 0, katexErr = 0, rawDollar = 0, totalSpans = 0;
  const errs = [], urls = new Set();
  const cssUrls = KATEX_CSS.match(/https?:\/\/[^\s"')]+/g) || [];
  const cssNonData = (KATEX_CSS.match(/url\((?!data:)[^)]*\)/g) || []);
  for (const it of items) {
    if (it.state !== "ready" || !it.solution) continue;
    let h;
    try { h = html(it.solution, "label"); ok++; } catch (e) { throws++; errs.push(it.question_id + " " + e.message); continue; }
    const body = h.replace(KATEX_CSS, "");
    const u = body.match(/https?:\/\/[^\s"'<>)]+/g) || [];
    // KaTeX MathML namespace is not a network fetch; ignore it
    const real = u.filter((x) => !x.startsWith("http://www.w3.org/"));
    if (real.length) { withUrl++; real.forEach((x) => urls.add(x)); }
    const spans = (body.match(/class="katex"/g) || []).length;
    totalSpans += spans;
    if (spans) withKatex++;
    const ke = (body.match(/katex-error/g) || []).length;
    if (ke) { katexErr += ke; const mm = body.match(/<span class="katex-error"[^>]*>([^<]*)/); errs.push("katex-error in " + it.question_id + ": " + (mm ? mm[1].slice(0, 120) : "")); }
    const textOnly = body.replace(/<span class="katex[\s\S]*?<\/span>/g, "");
    if (/\$[^$<]{1,40}\$/.test(body.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").replace(/annotation[\s\S]*?annotation/g, ""))) rawDollar++;
  }
  const sample = tex("Value $2\\!- 3\\!- 1\\!- 6$ and $$\\frac{a}{b}$$ and \\(x^2\\) and \\[\\sqrt{2}\\] and $\\badcmd{x}$");
  console.log(JSON.stringify({ items: items.length, rendered_ok: ok, throws, withKatex, withUrl, urls: [...urls].slice(0, 10), katexErrSpans: katexErr, rawDollarLeftovers: rawDollar, totalSpans, cssHttpUrls: cssUrls.length, cssNonDataUrls: cssNonData.slice(0, 5), cssLen: KATEX_CSS.length, fontFaces: (KATEX_CSS.match(/@font-face/g) || []).length, woff2: (KATEX_CSS.match(/font\/woff2/g) || []).length }, null, 1));
  console.log("sample contains katex:", sample.includes('class="katex"'), "display:", sample.includes("katex-display"), "error span:", sample.includes("katex-error"), "len", sample.length);
  errs.slice(0, 10).forEach((e) => console.log("ERR", e));
  const strict = (() => { try { katex.renderToString("2\\!- 3\\!- 1\\!- 6", { throwOnError: true }); return "strict OK"; } catch (e) { return "strict throws: " + e.message.slice(0, 100); } })();
  console.log(strict);
})().catch((e) => { console.error("FATAL", e); process.exit(1); });
