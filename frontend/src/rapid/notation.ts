/**
 * Rapid Fire notation engine.
 *
 * Card text is typed on one line: x^2, v_max, e^{iπ}, ∫₀^(π/2), (∂G/∂T)_P, log_a x. This file turns those typed marks
 * into real superscripts and subscripts without changing the maths. Pure functions (no React), so the phone, the
 * browser arena and the whole-bank test (tests/notation_bank_tests.cjs) all read a card the same way.
 */
export type Script = { kind: "sup" | "sub"; body: Piece[] };
/** A raised and a lowered index on the same base (∫₀^π, I_rms², CO₃²⁻): drawn one above the other, as in a textbook. */
export type Stack = { kind: "both"; sup: Piece[]; sub: Piece[] };
/** A base character with the indices that belong to it: a line may never break between them. */
export type Keep = { kind: "keep"; body: Piece[] };
export type Piece = string | Script | Stack | Keep;

const pairs = (plain: string, glyphs: string) => Array.from(plain).map((c, i) => [c, Array.from(glyphs)[i]] as const);
// Glyphs every phone font has. A short index made only of these stays ordinary text (no typesetter needed).
const SUP = Object.fromEntries(pairs("0123456789+−=()nix", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱˣ"));
const SUB = Object.fromEntries(pairs("0123456789+−=()aehijklmnoprstuvx", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓ"));
// Raised and lowered glyphs already typed in the bank. In a typeset line they are drawn like every other index.
const UP = Object.fromEntries(pairs("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱˣᵃᵇᶜᵈᵉᵍᵏᵐᵒᵖʳˢᵗᵘᵛʸᶻᵀ", "0123456789+−=()nixabcdegkmoprstuvyzT"));
const DOWN = Object.fromEntries(pairs("₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓᵦᵧ", "0123456789+−=()aehijklmnoprstuvxβγ"));
const GLYPH_RUNS = new RegExp(`([${Object.keys(UP).join("")}]+|[${Object.keys(DOWN).join("")}]+)`);

// Limits typed half in glyphs: ∫₋(π/2)^(π/2) and ∫₋π/2^(π/2) mean "from −π/2".
const tidy = (s: string) => s
  .replace(/([₋₊])\(([^()\s]{1,8})\)(?=\^)/g, (_, sign: string, v: string) => `_{${sign === "₋" ? "−" : "+"}${v}}`)
  .replace(/₋(π\/2)(?=\^)/g, "_{−$1}");
// Inside an index a hyphen is always a minus sign.
const minus = (body: Piece[]): Piece[] => body.map(p => (typeof p === "string" ? p.replace(/[-–]/g, "−") : p));
const first = (rest: string, patterns: RegExp[]) => { for (const p of patterns) { const m = p.exec(rest); if (m) return m[0]; } return ""; };

function close(s: string, from: number, open: string, shut: string) {
  for (let depth = 0, j = from; j < s.length; j++) {
    if (s[j] === open) depth++;
    else if (s[j] === shut && --depth === 0) return j;
  }
  return -1;
}

/** What a ^ or _ at `j - 1` raises or lowers: a {group}, a (group), or the bare token that follows. Null = not an index. */
function argument(s: string, j: number, kind: Script["kind"]): { body: Piece[]; end: number } | null {
  const open = s[j];
  if (open === "{" || open === "(") {
    const e = close(s, j, open, open === "{" ? "}" : ")");
    const inner = e < 0 ? "" : s.slice(j + 1, e);
    return inner.trim() ? { body: minus(parse(inner)), end: e + 1 } : null;
  }
  const rest = s.slice(j, j + 40), before = s[j - 2] ?? "";
  let token: string;
  if (kind === "sup") {
    token = first(rest, [
      /^[−–-]?∫[^∫=]{0,12}?d[a-z](?![a-z])/,               // e^∫P dx
      /^[−–-]?t\/(?:RC|τ)(?![A-Za-z])/,                     // e^−t/RC
      /^[−–+-]?\d+\/\d+(?![\dA-Za-z])/,                     // (Ksp/4)^1/3
      /^[−–+-]?\d*Δ[A-Za-z]+[ᵍɡ]?(?:_[a-z](?![A-Za-z]))?/,  // (RT)^Δn, (RT)^2Δn, (RT)^Δn_g
      /^[−–+-]?\d+/,                                        // (RT)^1, (mol/L)^−1
      /^\[[^[\]\s]{1,8}\]/, /^\|[^|\s]{1,8}\|/,             // (−1)^[x], e^|x|
      /^n[+−-](?![A-Za-z0-9(])/,                            // M^n+
      /^[a-z]{4,}/,                                         // [reactant]^stoich
      ...(before === ")" ? [/^[A-Za-z]\([a-z]\)/] : []),    // f(x)^g(x)
      /^[−–-]?[A-Za-zΑ-Ωα-ω∞½⅓⅔¼¾]/,                        // x^n, PV^γ, ∫₀^∞
    ]);
    if (token) token += /^[⁰¹²³⁴-⁹ⁿ₀-₉ᵢ]*/.exec(s.slice(j + token.length))![0]; // x^x², Mᵢ^xᵢ
  } else {
    token = first(rest, [
      ...(before === "d" ? [/^(?:x²[−-]y²|z²)/] : []),              // d_x²−y², d_z² orbitals
      ...(before === ")" ? [/^[A-Z],[A-Z](?![A-Za-z_])/] : []),     // (∂G/∂ξ)_T,P
      ...(before === "k" ? [/^B(?=T)/] : []),                       // ½k_BT
      /^\d+[a-z]*/,                                                 // x_1, KE_2m
      // v_max, T_H, P_Cu, w_H₂O. Stops where the next quantity starts: nC_vΔT, Δn_gRT.
      /^(?:[A-Z]+[a-z]*|[a-z]+)(?:[₀-₉]+[A-Z]*)*/,
      /^[Α-Ωα-ω]/,                                                  // λ_α
    ]);
  }
  return token ? { body: minus(parse(token)), end: j + token.length } : null;
}

/** Typed text -> ordinary text and indices. A ^ or _ that is not an index (a blank ___, a lone ^) stays as typed. */
export function parse(source: string): Piece[] {
  const text = tidy(source), out: Piece[] = [];
  let buf = "", i = 0;
  while (i < text.length) {
    const c = text[i];
    if ((c === "^" || c === "_") && i > 0 && !/[\s_^]/.test(text[i - 1])) {
      const kind = c === "^" ? "sup" : "sub";
      const got = argument(text, i + 1, kind);
      if (got) {
        const last = out[out.length - 1];
        if (!buf && kind === "sub" && typeof last === "object" && last.kind === "sub") last.body.push(" ", ...got.body); // F_net_external
        else {
          if (buf) { out.push(buf); buf = ""; }
          out.push({ kind, body: got.body });
        }
        i = got.end;
        continue;
      }
    }
    buf += c;
    i++;
  }
  if (buf) out.push(buf);
  return out;
}

/** One ordinary string when every index is short and has safe glyphs (x², vₘ, aₙ₊₁); null when the line needs typesetting. */
export function flat(pieces: Piece[]): string | null {
  let out = "";
  for (const p of pieces) {
    if (typeof p === "string") { out += p; continue; }
    if ((p.kind !== "sup" && p.kind !== "sub") || p.body.length !== 1 || typeof p.body[0] !== "string") return null;
    const map = p.kind === "sup" ? SUP : SUB, chars = Array.from(p.body[0]);
    if (!chars.every(c => map[c]) || chars.filter(c => /[a-z]/.test(c)).length > 2) return null;
    out += chars.map(c => map[c]).join("");
  }
  return out;
}

/**
 * For a typeset line: glyph indices already in the text (x², Kₐ, ∫₀) become real indices too, so the whole line matches;
 * a raised index next to a lowered one on the same base is stacked; and each base is tied to its indices.
 */
export function rich(pieces: Piece[]): Piece[] {
  const out: Piece[] = [];
  const add = (p: Script) => {
    const last = out[out.length - 1];
    if (typeof last === "object" && (last.kind === "sup" || last.kind === "sub") && last.kind !== p.kind) out[out.length - 1] = { kind: "both", sup: (p.kind === "sup" ? p : last).body, sub: (p.kind === "sub" ? p : last).body };
    else out.push(p);
  };
  for (const p of pieces) {
    if (typeof p === "string") {
      p.split(GLYPH_RUNS).forEach((part, k) => {
        if (!part) return;
        if (k % 2 === 0) { out.push(part); return; }
        const up = UP[Array.from(part)[0]] != null;
        add({ kind: up ? "sup" : "sub", body: [Array.from(part).map(g => (up ? UP : DOWN)[g]).join("")] });
      });
    } else if (p.kind === "sup" || p.kind === "sub") add({ kind: p.kind, body: rich(p.body) });
    else out.push(p);
  }
  const tied: Piece[] = [];
  for (const p of out) {
    const last = tied[tied.length - 1];
    const base = typeof p !== "string" && typeof last === "string" ? /\S[\u0300-\u036F\u20D0-\u20FF]*$/.exec(last) : null;
    if (typeof p !== "string" && typeof last === "object" && last.kind === "keep") last.body.push(p);
    else if (base && typeof last === "string") tied.splice(tied.length - 1, 1, ...(base.index ? [last.slice(0, base.index)] : []), { kind: "keep", body: [base[0], p] });
    else tied.push(p);
  }
  return tied;
}

/** Typeset line as HTML for the phone's offline typesetter. `text` escapes (and may typeset) the ordinary runs. */
export const html = (pieces: Piece[], text: (s: string) => string): string => pieces.map(p => (
  typeof p === "string" ? text(p)
    : p.kind === "keep" ? `<span class="keep">${html(p.body, text)}</span>`
      : p.kind === "both" ? `<span class="both"><sup>${html(p.sup, text)}</sup><sub>${html(p.sub, text)}</sub></span>`
        : `<${p.kind}>${html(p.body, text)}</${p.kind}>`)).join("");
