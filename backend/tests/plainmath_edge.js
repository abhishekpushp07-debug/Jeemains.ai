// plainMath edge cases: unclosed \sqrt[ / \xrightarrow[ must not hang; fraction followed by letter gets '·'
const fs = require("fs");
const ts = require("/app/frontend/node_modules/typescript");
const src = fs.readFileSync("/app/frontend/src/components/AiSolution.tsx", "utf8");
const a = src.indexOf("const SYM"), b = src.indexOf("function html");
const js = ts.transpileModule(src.slice(a, b).replace("export function plainMath", "function plainMath") + "\nmodule.exports={plainMath};", { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2019 } }).outputText;
const m = { exports: {} }; new Function("module", "exports", js)(m, m.exports);
const { plainMath } = m.exports;
const cases = ["\\sqrt[", "\\sqrt[3", "\\sqrt[3{x}", "x=\\sqrt[", "\\xrightarrow[", "\\xrightarrow[abc", "A \\xrightarrow[ B", "K_i=\\frac{1}{2}m_1u_1^2", "\\frac{1}{2} mv^2", "\\frac{a}{b}(x+1)", "\\frac{1}{2}", "\\frac{1}{2}=0.5", "\\sqrt[3]{x+1}", "\\xrightarrow[Sn/HCl]{}", "\\frac{1}{2}\\sqrt{x}", "\\frac{1}{2}\\pi r"];
for (const c of cases) {
  const t0 = Date.now();
  const o = plainMath(c);
  console.log(JSON.stringify(c), "=>", JSON.stringify(o), (Date.now() - t0) + "ms");
}
