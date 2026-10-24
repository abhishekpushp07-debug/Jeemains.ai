import React, { useMemo, useState } from "react";
import { Platform, View } from "react-native";
import { WebView } from "react-native-webview";
import katex from "katex";
import { KATEX_CSS } from "@/src/katexCss";
import { Icon, T } from "@/src/components/ui";
import { colors, radius, space } from "@/src/theme";

export type AiItem = { question_id: string; state: string; label?: string; model?: string; flag?: string | null; solution?: any };

const esc = (s: any) => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

// Web preview fallback: readable plain-text maths (native uses real KaTeX typesetting).
const SYM: Record<string, string> = { times: "×", cdot: "·", div: "÷", pm: "±", mp: "∓", le: "≤", leq: "≤", ge: "≥", geq: "≥", ne: "≠", neq: "≠", approx: "≈", sim: "~", simeq: "≃", equiv: "≡", propto: "∝", infty: "∞",
  to: "→", rightarrow: "→", longrightarrow: "→", Rightarrow: "⇒", Longrightarrow: "⇒", implies: "⇒", iff: "⇔", leftarrow: "←", leftrightarrow: "↔", rightleftharpoons: "⇌", uparrow: "↑", downarrow: "↓",
  alpha: "α", beta: "β", gamma: "γ", Gamma: "Γ", delta: "δ", Delta: "Δ", theta: "θ", Theta: "Θ", lambda: "λ", Lambda: "Λ", mu: "μ", pi: "π", Pi: "Π", rho: "ρ", sigma: "σ", Sigma: "Σ", omega: "ω", Omega: "Ω",
  phi: "φ", varphi: "φ", Phi: "Φ", epsilon: "ε", varepsilon: "ε", eta: "η", tau: "τ", nu: "ν", chi: "χ", psi: "ψ", Psi: "Ψ", kappa: "κ", zeta: "ζ", xi: "ξ", iota: "ι", ell: "ℓ", hbar: "ħ",
  circ: "°", degree: "°", sum: "Σ", prod: "Π", int: "∫", oint: "∮", partial: "∂", nabla: "∇", ldots: "…", cdots: "⋯", dots: "…", quad: " ", qquad: "  ", in: "∈", notin: "∉", ni: "∋",
  angle: "∠", parallel: "∥", perp: "⊥", therefore: "∴", because: "∵", mid: "|", cap: "∩", cup: "∪", subset: "⊂", subseteq: "⊆", supset: "⊃", supseteq: "⊇", emptyset: "∅", varnothing: "∅",
  neg: "¬", lnot: "¬", land: "∧", wedge: "∧", lor: "∨", vee: "∨", forall: "∀", exists: "∃", prime: "′", star: "*", ast: "*", gg: "≫", ll: "≪", lt: "<", gt: ">", vert: "|", lvert: "|", rvert: "|",
  langle: "⟨", rangle: "⟩", lfloor: "⌊", rfloor: "⌋", lceil: "⌈", rceil: "⌉", triangle: "△", square: "□", checkmark: "✓", log: "log", ln: "ln", sin: "sin", cos: "cos", tan: "tan", cot: "cot", sec: "sec",
  csc: "cosec", lim: "lim", max: "max", min: "min", exp: "exp", det: "det" };
const KEEP = new Set(["text", "textrm", "textbf", "textit", "mathrm", "mathbf", "mathit", "mathcal", "mathbb", "boxed", "operatorname", "overline", "underline", "underbrace", "overbrace", "hat", "bar", "tilde", "dot", "ddot", "widehat", "mbox", "ce", "pu", "bm", "boldsymbol"]);
const SKIP = new Set(["left", "right", "displaystyle", "textstyle", "big", "Big", "bigg", "Bigg", "bigl", "bigr", "Bigl", "Bigr", "limits", "nolimits", "middle"]);
const SUP: Record<string, string> = { "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹", "+": "⁺", "-": "⁻", "n": "ⁿ", "o": "°", "∘": "°", "°": "°", "′": "′", "*": "*" };
const SUB: Record<string, string> = { "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄", "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉", "+": "₊", "-": "₋" };

function arg(s: string, i: number): [string, number] {
  while (s[i] === " ") i++;
  if (s[i] === "{") {
    let d = 0, j = i;
    for (; j < s.length; j++) { if (s[j] === "{" && s[j - 1] !== "\\") d++; else if (s[j] === "}" && s[j - 1] !== "\\" && --d === 0) break; }
    return [s.slice(i + 1, j), j + 1];
  }
  if (s[i] === "\\") { const m = /^\\([A-Za-z]+|.)/.exec(s.slice(i)); if (m) return [m[0], i + m[0].length]; }
  return [s[i] ?? "", i + 1];
}
const wrap = (x: string) => (/^[\w.′°²³⁻⁺√πα-ω]+$/.test(x) ? x : `(${x})`);
const script = (x: string, map: Record<string, string>, mark: string) => ([...x].every((c) => map[c]) ? [...x].map((c) => map[c]).join("") : `${mark}${wrap(x)}`);

function conv(s: string): string {
  let out = "", i = 0;
  while (i < s.length) {
    const c = s[i];
    if (c === "\\") {
      const m = /^\\([A-Za-z]+|.)/.exec(s.slice(i));
      if (!m) { i++; continue; }
      const name = m[1];
      i += m[0].length;
      if (name === "frac" || name === "dfrac" || name === "tfrac" || name === "cfrac") {
        const [a, j] = arg(s, i); const [b, k] = arg(s, j); i = k;
        out += `${wrap(conv(a))}/${wrap(conv(b))}`;
        if (/[A-Za-z0-9(√]/.test(s[i] === " " ? s[i + 1] || "" : s[i] || "")) out += "·";
      } else if (name === "sqrt") {
        let n = "";
        if (s[i] === "[") { const e = s.indexOf("]", i); if (e < 0) { i++; } else { n = s.slice(i + 1, e); i = e + 1; } }
        const [a, j] = arg(s, i); i = j;
        out += `${n ? script(n, SUP, "^") : ""}√${wrap(conv(a))}`;
      } else if (name === "binom" || name === "dbinom") {
        const [a, j] = arg(s, i); const [b, k] = arg(s, j); i = k;
        out += `C(${conv(a)},${conv(b)})`;
      } else if (name === "xrightarrow" || name === "xleftarrow") {
        if (s[i] === "[") { const e = s.indexOf("]", i); i = e < 0 ? i + 1 : e + 1; }
        const [a, j] = arg(s, i); i = j;
        out += ` →${a ? "[" + conv(a) + "]" : ""} `;
      } else if (name === "begin" || name === "end") {
        i = arg(s, i)[1];
      } else if (KEEP.has(name)) {
        const [a, j] = arg(s, i); i = j;
        out += name === "vec" ? conv(a) + "⃗" : conv(a);
      } else if (name === "vec") {
        const [a, j] = arg(s, i); i = j; out += conv(a) + "⃗";
      } else if (SKIP.has(name)) {
        // sizing only
      } else if (SYM[name] != null) {
        out += SYM[name];
        if (/^[a-z]{2,}$/.test(SYM[name]) && /[A-Za-z0-9(]/.test(s[i] || "")) out += " ";
      } else if (name.length === 1) {
        out += name === "," || name === ";" || name === " " || name === "!" ? (name === "!" ? "" : " ") : name === "\\" ? "\n" : name;
      } else out += name;
    } else if (c === "^" || c === "_") {
      const [a, j] = arg(s, i + 1); i = j;
      out += script(conv(a), c === "^" ? SUP : SUB, c === "^" ? "^" : "_");
    } else if (c === "{" || c === "}" || c === "$") {
      i++;
    } else if (c === "&") {
      out += " "; i++;
    } else { out += c; i++; }
  }
  return out;
}
export function plainMath(s: string) {
  return conv(String(s ?? "").replace(/\u0000/g, "")).replace(/[ \t]{2,}/g, " ").trim();
}

// Typeset maths in JS with the bundled KaTeX (no network); text around it is HTML-escaped.
const MATH = /\$\$([\s\S]+?)\$\$|\\\[([\s\S]+?)\\\]|\$([^$]+?)\$|\\\(([\s\S]+?)\\\)/g;
function tex(src: any) {
  const s = String(src ?? "").replace(/\u0000/g, ""); // upstream text sometimes carries NUL bytes
  let out = "", last = 0;
  for (const m of s.matchAll(MATH)) {
    out += esc(s.slice(last, m.index));
    const display = m[1] != null || m[2] != null;
    const body = m[1] ?? m[2] ?? m[3] ?? m[4] ?? "";
    try { out += katex.renderToString(body, { displayMode: display, throwOnError: false, output: "html", strict: "ignore", trust: false }); }
    catch { out += esc(m[0]); }
    last = (m.index ?? 0) + m[0].length;
  }
  return out + esc(s.slice(last));
}

function html(sol: any, label: string) {
  const sec = (title: string, body: string, tone = "") => body ? `<section class="${tone}"><h4>${title}</h4>${body}</section>` : "";
  const list = (xs: any[]) => (xs?.length ? `<ul>${xs.map((x) => `<li>${tex(x)}</li>`).join("")}</ul>` : "");
  const steps = (sol.steps || []).map((s: any, i: number) => `<div class="step"><div class="n">${i + 1}</div><div><b>${tex(String(s.title || "").replace(/^\d+\.\s*/, ""))}</b><p>${tex(s.explanation)}</p></div></div>`).join("");
  return `<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<style>${KATEX_CSS}</style>
<style>
body{margin:0;font-family:-apple-system,Roboto,sans-serif;font-size:15px;line-height:1.55;color:${colors.custom_onReading};background:transparent}
h4{margin:0 0 6px;font-size:11px;letter-spacing:1px;text-transform:uppercase;color:${colors.muted}}
section{margin:0 0 14px;padding:12px;border-radius:12px;background:${colors.surface};border:1px solid ${colors.border}}
section.good{background:${colors.custom_successSoft};border-color:${colors.success}55}
section.warn{background:${colors.custom_warningSoft};border-color:${colors.custom_amber}55}
section.info{background:${colors.custom_infoSoft};border-color:${colors.brandPrimary}44}
p{margin:4px 0 0}ul{margin:0;padding-left:18px}li{margin:3px 0}
.step{display:flex;gap:10px;margin:10px 0}.step .n{flex:0 0 24px;height:24px;border-radius:12px;background:${colors.brandPrimary};color:#fff;font-weight:800;font-size:12px;display:flex;align-items:center;justify-content:center;margin-top:2px}
.final{font-size:17px;font-weight:800;color:${colors.success}}
.katex-display{overflow-x:auto;overflow-y:hidden;padding:2px 0}.katex{font-size:1.05em}
</style></head><body><div id="c">
${sec("Concept", `<p>${tex(sol.concept)}</p>`, "info")}
${sec("Given", list(sol.given))}
${sec("Step-by-step", steps)}
${sec("Final answer", `<div class="final">Option ${esc(sol.final_answer)} ${sol.key_agrees ? "✓ matches the official key" : ""}</div>`, "good")}
${sec("Shortcut", sol.shortcut ? `<p>${tex(sol.shortcut)}</p>` : "", "info")}
${sec("Common mistakes", list(sol.common_mistakes), "warn")}
${sec("Time tip", sol.time_tip ? `<p>${tex(sol.time_tip)}</p>` : "")}
${sec("Examiner insight", sol.insight ? `<p>${tex(sol.insight)}</p>` : "")}
<p style="font-size:11px;color:${colors.muted}">${esc(label)}</p></div>
<script>
function size(){window.ReactNativeWebView&&window.ReactNativeWebView.postMessage(String(document.getElementById('c').scrollHeight+8))}
window.addEventListener('load',size);setTimeout(size,200);setTimeout(size,1000);
if(document.fonts&&document.fonts.ready)document.fonts.ready.then(size);
</script></body></html>`;
}

function Native({ sol, label, number }: { sol: any; label: string; number: number }) {
  const [h, setH] = useState(600);
  const src = useMemo(() => ({ html: html(sol, label) }), [sol, label]);
  return (
    <WebView testID={`ai-solution-web-${number}`} originWhitelist={["*"]} source={src} scrollEnabled={false} style={{ height: h, backgroundColor: "transparent" }}
      onMessage={(e) => { const n = Number(e.nativeEvent.data); if (n > 50) setH(n); }} setSupportMultipleWindows={false} javaScriptEnabled />
  );
}

function Box({ title, tone, children }: { title: string; tone?: string; children: React.ReactNode }) {
  return (
    <View style={{ padding: space.md, borderRadius: radius.md, gap: 4, backgroundColor: tone || colors.surface, borderWidth: 1, borderColor: colors.border }}>
      <T w="bold" size={11} color={colors.muted} style={{ letterSpacing: 1 }}>{title.toUpperCase()}</T>
      {children}
    </View>
  );
}

function Fallback({ sol, label }: { sol: any; label: string }) {
  const P = ({ s }: { s: any }) => <T size={14} color={colors.custom_onReading}>{plainMath(s)}</T>;
  return (
    <View style={{ gap: space.sm }}>
      {sol.concept ? <Box title="Concept" tone={colors.custom_infoSoft}><P s={sol.concept} /></Box> : null}
      {sol.given?.length ? <Box title="Given">{sol.given.map((g: string, i: number) => <P key={i} s={"• " + g} />)}</Box> : null}
      <Box title="Step-by-step">
        {(sol.steps || []).map((s: any, i: number) => (
          <View key={i} style={{ flexDirection: "row", gap: space.sm, marginTop: 6 }}>
            <View style={{ width: 24, height: 24, borderRadius: 12, backgroundColor: colors.brandPrimary, alignItems: "center", justifyContent: "center" }}><T w="heavy" size={12} color={colors.onBrandPrimary}>{i + 1}</T></View>
            <View style={{ flex: 1, gap: 2 }}><T w="bold" size={14}>{String(s.title || "").replace(/^\d+\.\s*/, "")}</T><P s={s.explanation} /></View>
          </View>
        ))}
      </Box>
      <Box title="Final answer" tone={colors.custom_successSoft}><T w="heavy" size={17} color={colors.success}>Option {sol.final_answer}{sol.key_agrees ? "  ✓ matches the official key" : ""}</T></Box>
      {sol.shortcut ? <Box title="Shortcut" tone={colors.custom_infoSoft}><P s={sol.shortcut} /></Box> : null}
      {sol.common_mistakes?.length ? <Box title="Common mistakes" tone={colors.custom_warningSoft}>{sol.common_mistakes.map((g: string, i: number) => <P key={i} s={"• " + g} />)}</Box> : null}
      {sol.time_tip ? <Box title="Time tip"><P s={sol.time_tip} /></Box> : null}
      {sol.insight ? <Box title="Examiner insight"><P s={sol.insight} /></Box> : null}
      <T size={11} color={colors.muted}>{label}</T>
    </View>
  );
}

// AI step-by-step solution from the JEELIVE backend (GET /attempts/{id}/ai-solutions).
export function AiSolution({ item, number, disclosure }: { item?: AiItem; number: number; disclosure?: string }) {
  if (!item) return null;
  const head = (
    <View style={{ flexDirection: "row", alignItems: "center", gap: space.sm, flexWrap: "wrap" }}>
      <Icon name="robot-happy-outline" size={18} color={colors.brandPrimary} />
      <T w="heavy" size={15} style={{ flex: 1 }}>AI step-by-step solution</T>
      {item.solution?.difficulty ? <View style={{ paddingHorizontal: 8, paddingVertical: 2, borderRadius: radius.pill, backgroundColor: colors.custom_infoSoft }}><T w="bold" size={11} color={colors.brandPrimary}>{item.solution.difficulty}</T></View> : null}
    </View>
  );
  if (item.state !== "ready" || !item.solution) {
    return (
      <View testID={`ai-solution-pending-${number}`} style={{ gap: space.sm, padding: space.md, borderRadius: radius.md, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border }}>
        {head}
        <T size={13} color={colors.muted}>{item.flag ? "The AI solution for this question was held back after a quality check." : "The AI solution for this question is being prepared. Check back soon."}</T>
      </View>
    );
  }
  const label = disclosure || `${item.label || "AI generated"} by ${item.model || "AI"}. AI can make mistakes; the supplied key and your score never change.`;
  return (
    <View testID={`ai-solution-${number}`} style={{ gap: space.sm }}>
      {head}
      {item.solution.key_agrees === false ? <T size={12} w="bold" color={colors.error}>AI’s answer differs from the official key — trust the official key.</T> : null}
      {Platform.OS === "web" ? <Fallback sol={item.solution} label={label} /> : <Native sol={item.solution} label={label} number={number} />}
    </View>
  );
}
