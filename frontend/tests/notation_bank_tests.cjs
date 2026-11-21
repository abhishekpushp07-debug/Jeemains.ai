// Rapid Fire notation engine: rules on known lines + every text of every live card. Run: node tests/notation_bank_tests.cjs
// `--dump` also prints every different index the engine found in the bank (for reading by eye).
const assert = require("assert");
const fs = require("fs");
const path = require("path");
const ts = require("/app/frontend/node_modules/typescript");

const file = "/app/frontend/src/rapid/notation.ts";
const js = ts.transpileModule(fs.readFileSync(file, "utf8"), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 }, fileName: file }).outputText;
const mod = { exports: {} };
new Function("require", "module", "exports", js)(require, mod, mod.exports);
const { parse, flat, rich, html } = mod.exports;

// ‹…› raised, «…» lowered, ⟦raised|lowered⟧ stacked on one base: one readable line per parse.
const show = pieces => pieces.map(p => (typeof p === "string" ? p : p.kind === "keep" ? show(p.body) : p.kind === "both" ? `⟦${show(p.sup)}|${show(p.sub)}⟧` : p.kind === "sup" ? `‹${show(p.body)}›` : `«${show(p.body)}»`)).join("");
const esc = s => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

const LINES = {
  // braces and brackets
  "∫₀^{2π} sin x dx": "∫₀‹2π› sin x dx",
  "∫_{f(a)}^{f(b)} f⁻¹(y)dy": "∫«f(a)»‹f(b)› f⁻¹(y)dy",
  "(∂G/∂ξ)_{T,P} = ΔG": "(∂G/∂ξ)«T,P» = ΔG",
  "−1 = e^{iπ}, so z = e^{i(π+2kπ)/4}": "−1 = e‹iπ›, so z = e‹i(π+2kπ)/4›",
  "(1/n)Σ (k/n)^{-1/2} → ∫₀^1 x^{-1/2}dx = 2.": "(1/n)Σ (k/n)‹−1/2› → ∫₀‹1› x‹−1/2›dx = 2.",
  "nₑ = nᵢ e^{(E_F − E_i)/kT}": "nₑ = nᵢ e‹(E«F» − E«i»)/kT›",
  "For rate = k[A]^(3/2), the order is:": "For rate = k[A]‹3/2›, the order is:",
  "(-1)^((n-1)/2)·ⁿC_((n-1)/2)": "(-1)‹(n−1)/2›·ⁿC«(n−1)/2»",
  "e^(e^(−x))": "e‹e‹−x››",
  "Leibniz rule: d/dx[∫_(u(x))^(v(x)) f(t)dt] = ?": "Leibniz rule: d/dx[∫«u(x)»‹v(x)› f(t)dt] = ?",
  "∫₋(π/2)^(π/2) cos x dx = ?": "∫«−π/2»‹π/2› cos x dx = ?",
  "∫₋π/2^(π/2) |sin x| dx = ?": "∫«−π/2»‹π/2› |sin x| dx = ?",
  "a^(log_a x) = ?": "a‹log«a» x› = ?",
  "T_{n/2 + 1}": "T«n/2 + 1»",
  // bare caret
  "Kp = Kc(RT)^Δn": "Kp = Kc(RT)‹Δn›",
  "(RT)^Δn becomes (RT)^2Δn = (RT)².": "(RT)‹Δn› becomes (RT)‹2Δn› = (RT)².",
  "Kp = Kc(RT)^Δn_g where Δn_g = moles": "Kp = Kc(RT)‹Δn«g»› where Δn«g» = moles",
  "Kc units = (mol/L)^Δn = (mol/L)^−1 = L/mol.": "Kc units = (mol/L)‹Δn› = (mol/L)‹−1› = L/mol.",
  "[CO₂]/([CO][O₂]^½)": "[CO₂]/([CO][O₂]‹½›)",
  "Kc = [products]^stoich / [reactants]^stoich": "Kc = [products]‹stoich› / [reactants]‹stoich›",
  "s = (Ksp/4)^1/3.": "s = (Ksp/4)‹1/3›.",
  "∫₀^∞ xe⁻ˣ dx = Γ(2)": "∫₀‹∞› xe⁻ˣ dx = Γ(2)",
  "∫₀^π x f(sin x)dx =": "∫₀‹π› x f(sin x)dx =",
  "∫₀^1(1-x)dx + ∫₁^2(x-1)dx": "∫₀‹1›(1-x)dx + ∫₁‹2›(x-1)dx",
  "e^θ(cosθ+i sinθ)": "e‹θ›(cosθ+i sinθ)",
  "If y = f(x)^g(x), ln y = ?": "If y = f(x)‹g(x)›, ln y = ?",
  "f′ = e^x(x−1)/x² < 0": "f′ = e‹x›(x−1)/x² < 0",
  "cos(π[x]) = (−1)^[x]": "cos(π[x]) = (−1)‹[x]›",
  "f(x) = e^|x| at x = 0 is:": "f(x) = e‹|x|› at x = 0 is:",
  "d/dx[x^x²] = ?": "d/dx[x‹x²›] = ?",
  "ΠMᵢ^xᵢ only for ideal gases": "ΠMᵢ‹xᵢ› only for ideal gases",
  "IF = e^∫P dx, so P = 3/x.": "IF = e‹∫P dx›, so P = 3/x.",
  "I.F. = e^∫(−1)dy = e^(−y).": "I.F. = e‹∫(−1)dy› = e‹−y›.",
  "e^−∫P dy": "e‹−∫P dy›",
  "V₀(1−e^−t/RC)": "V₀(1−e‹−t/RC›)",
  "E(M^n+/M) at 298 K": "E(M‹n+›/M) at 298 K",
  "sin^n(2π−x) = sin^n x": "sin‹n›(2π−x) = sin‹n› x",
  "T^γP^(1−γ) = constant": "T‹γ›P‹1−γ› = constant",
  "Z = A^½B^½": "Z = A‹½›B‹½›",
  "I^A and I^B alleles": "I‹A› and I‹B› alleles",
  "Product of active masses ^ coefficients": "Product of active masses ^ coefficients",
  // bare underscore
  "Cv = (∂U/∂T)_V; Cp = (∂H/∂T)_P": "Cv = (∂U/∂T)«V»; Cp = (∂H/∂T)«P»",
  "(∂G/∂ξ)_T,P = ΔG": "(∂G/∂ξ)«T,P» = ΔG",
  "At resonance X_L = X_C, φ = 0": "At resonance X«L» = X«C», φ = 0",
  "ΔH°_comb ≈ −890 kJ/mol": "ΔH°«comb» ≈ −890 kJ/mol",
  "T − mg = mv²_b/r": "T − mg = mv²«b»/r",
  "λ = h/√(2m_α(2e)V)": "λ = h/√(2m«α»(2e)V)",
  "w = ΔU = nC_vΔT": "w = ΔU = nC«v»ΔT",
  "ΔH − ΔU = Δn_gRT": "ΔH − ΔU = Δn«g»RT",
  "Δ_egH: S > Se": "Δ«eg»H: S > Se",
  "½k_BT²": "½k«B»T²",
  "μ_JT = 0": "μ«JT» = 0",
  "(0.0592/2) log(P_H₂/[H⁺]²)": "(0.0592/2) log(P«H₂»/[H⁺]²)",
  "(2/18) × (w_H₂O/W) × 100.": "(2/18) × (w«H₂O»/W) × 100.",
  "d_x²−y² lobes lie on the axes; d_z² has two": "d«x²−y²» lobes lie on the axes; d«z²» has two",
  "H = I_rms² R t.": "H = I«rms»² R t.",
  "KE_m : KE_2m = 2 : 1": "KE«m» : KE«2m» = 2 : 1",
  "M·a_cm = F_net_external only.": "M·a«cm» = F«net external» only.",
  "n = √(μ_rε_r)": "n = √(μ«r»ε«r»)",
  "∫_c^d g(y) dy": "∫«c»‹d› g(y) dy",
  "log_a|−x| = log_a|x|": "log«a»|−x| = log«a»|x|",
  "t₂g⁶ e_g⁰": "t₂g⁶ e«g»⁰",
  "p_A°x_A + p_B°x_B": "p«A»°x«A» + p«B»°x«B»",
  // not indices
  "She said the weather was ___.": "She said the weather was ___.",
  "\"___ you like some tea?\"": "\"___ you like some tea?\"",
  "OAA is a __-carbon compound": "OAA is a __-carbon compound",
  "approximately ___% of total": "approximately ___% of total",
  "A = {●,▲,■,◆}, B = {▲,◆,★,✚}": "A = {●,▲,■,◆}, B = {▲,◆,★,✚}",
  "[x] + {x} = x": "[x] + {x} = x",
};
const FLAT = { "x^2 + y^2": "x² + y²", "v_r = v_0 + at": "vᵣ = v₀ + at", "a_(n+1) = a_n + d": "aₙ₊₁ = aₙ + d", "x^(-1)": "x⁻¹", "10^-3 m": "10⁻³ m", "C_ij = (−1)^(i+j) M_ij": "Cᵢⱼ = (−1)ⁱ⁺ʲ Mᵢⱼ" };
const TYPESET = ["r_max", "K_b", "X_C", "e^{iπ}", "x^(1/3)", "PV^γ", "d_xy"];

const tests = {
  "known lines parse the way a teacher would write them"() {
    for (const [typed, want] of Object.entries(LINES)) assert.strictEqual(show(parse(typed)), want, typed);
  },
  "short indices with safe glyphs stay ordinary text"() {
    for (const [typed, want] of Object.entries(FLAT)) {
      if (typed.includes("i+j")) continue; // j has no raised glyph: that line is typeset
      assert.strictEqual(flat(parse(typed)), want, typed);
    }
    assert.strictEqual(flat(parse("C_ij = (−1)^(i+j) M_ij")), null);
  },
  "anything else is typeset"() {
    for (const typed of TYPESET) assert.strictEqual(flat(parse(typed)), null, typed);
  },
  "a typeset line draws typed glyph indices as real indices too, and stacks a raised and a lowered index on one base"() {
    assert.strictEqual(show(rich(parse("∫₀^{π/2} sinⁿx dx"))), "∫⟦π/2|0⟧ sin‹n›x dx");
    assert.strictEqual(show(rich(parse("∫_{f(a)}^{f(b)} f⁻¹(y)dy"))), "∫⟦f(b)|f(a)⟧ f‹−1›(y)dy");
    assert.strictEqual(show(rich(parse("Kₐ·K_b = Kw; [H⁺]²"))), "K«a»·K«b» = Kw; [H‹+›]‹2›");
    assert.strictEqual(show(rich(parse("d/dx[x^x²]"))), "d/dx[x‹x‹2››]");
    assert.strictEqual(show(rich(parse("P_avg = I_rms²R; T − mg = mv²_b/r"))), "P«avg» = I⟦2|rms⟧R; T − mg = mv⟦2|b⟧/r");
    assert.strictEqual(show(rich(parse("K_sp of CaCO₃: [Ca²⁺][CO₃²⁻]"))), "K«sp» of CaCO«3»: [Ca‹2+›][CO⟦2−|3⟧]");
    assert.strictEqual(show(rich(parse("lim(n→∞) (1/n)Σₖ₌₁ⁿ 2^{k/n} = ?"))), "lim(n→∞) (1/n)Σ⟦n|k=1⟧ 2‹k/n› = ?");
  },
  "HTML for the phone typesetter is escaped and balanced; a base is tied to its indices so a line never breaks between them"() {
    assert.strictEqual(html(rich(parse("a<b gives x^(a<b) & K_b")), esc), 'a&lt;b gives <span class="keep">x<sup>a&lt;b</sup></span> &amp; <span class="keep">K<sub>b</sub></span>');
    assert.strictEqual(html(rich(parse("∫_c^d g(y) dy")), esc), '<span class="keep">∫<span class="both"><sup>d</sup><sub>c</sub></span></span> g(y) dy');
    assert.strictEqual(html(rich(parse("x̄_w = Σwᵢxᵢ; ⁿC_r")), esc), '<span class="keep">x̄<sub>w</sub></span> = Σ<span class="keep">w<sub>i</sub></span><span class="keep">x<sub>i</sub></span>; <sup>n</sup><span class="keep">C<sub>r</sub></span>');
  },
  "whole bank: nothing code-like is left, nothing else is touched"() {
    const dir = "/app/backend/rapidfire/cards";
    const seen = { texts: 0, plain: 0, flat: 0, typeset: 0, cards: 0 }, indices = new Map(), bad = [];
    const walk = (pieces, note, inScript) => pieces.forEach(p => {
      if (typeof p !== "string") { note(p); walk(p.body, note, true); return; }
      // Left as typed on purpose: blanks (___) and a caret after a space ("each ^1"). Everything else must be gone.
      const rest = p.replace(/_{2,}/g, "").replace(/(^|[\s"'“‘(])_(?=[\s.,?!:;)%"'”’-]|$)/g, "$1").replace(/ \^/g, " ");
      if (/[\^]/.test(rest) || /\S_\S/.test(rest) || (inScript && /[{}]/.test(p))) bad.push(p);
    });
    for (const name of fs.readdirSync(dir).filter(f => f.endsWith(".json"))) {
      for (const card of JSON.parse(fs.readFileSync(path.join(dir, name), "utf8"))) {
        seen.cards++;
        for (const text of [card.prompt, card.formula, card.explain, ...card.options].filter(Boolean)) {
          seen.texts++;
          const pieces = parse(text);
          if (!/[\^_]/.test(text)) { assert.deepStrictEqual(pieces, [text], "untouched: " + text); seen.plain++; continue; }
          walk(pieces, s => { const k = (s.kind === "sup" ? "^ " : "_ ") + show(s.body); indices.set(k, (indices.get(k) || 0) + 1); }, false);
          const one = flat(pieces);
          if (one != null) seen.flat++;
          else {
            seen.typeset++;
            const out = html(rich(pieces), esc);
            assert.strictEqual((out.match(/<su[pb]>/g) || []).length, (out.match(/<\/su[pb]>/g) || []).length, text);
            assert.strictEqual((out.match(/<span /g) || []).length, (out.match(/<\/span>/g) || []).length, text);
            assert.strictEqual(out.replace(/<[^>]+>/g, "").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&").length > 0, true);
          }
        }
      }
    }
    console.log("   bank:", JSON.stringify(seen), "different indices:", indices.size);
    if (process.argv.includes("--dump")) for (const [k, n] of [...indices].sort((a, b) => b[1] - a[1])) console.log(String(n).padStart(5), k);
    assert.deepStrictEqual(bad.slice(0, 20), [], `${bad.length} runs still look like code`);
    assert.ok(seen.cards > 15000 && seen.typeset > 1000);
  },
};

let failed = 0;
for (const [name, run] of Object.entries(tests)) {
  try { run(); console.log("ok  ", name); } catch (e) { failed++; console.log("FAIL", name, "\n    ", e.message); }
}
console.log(failed ? `${failed} failed` : `all ${Object.keys(tests).length} passed`);
process.exit(failed ? 1 : 0);
