import React, { memo, useMemo } from "react";
import { Platform, StyleSheet, Text, View } from "react-native";
import { tex } from "@/src/components/AiSolution";
import { MathText } from "@/src/components/MathText";
import { OfflineMath } from "@/src/components/OfflineMath";
import { fonts, rapidColors as colors } from "@/src/theme";
import { flat, html, parse, rich, type Piece } from "./notation";
import { T } from "./ui";

type Weight = NonNullable<React.ComponentProps<typeof T>["w"]>;
type Props = { text: string; size?: number; testID: string; color?: string; w?: Weight };
// Card text keeps its real scientific notation. Typed indices (x^2, v_max, e^{iπ}, ∫₀^(π/2)) are read by ./notation:
// short ones become ordinary text (x², vₘ); the rest are typeset as real superscripts and subscripts, in the page
// itself on web and by the bundled offline typesetter on phones. Explicit TeX ($…$) goes to the app's KaTeX as before.
export const RapidText = memo(function RapidText({ text, size = 16, testID, color = colors.custom_onReading, w = "semibold" }: Props) {
  const explicit = /\$[^$]+\$|\\\(|\\\[/.test(text);
  const line = useMemo(() => {
    if (explicit) return null;
    const pieces = parse(text), plain = flat(pieces);
    if (Platform.OS === "web") return { plain, pieces: plain == null ? rich(pieces) : null, body: "" };
    if (plain != null && !MARKED.test(plain)) return { plain, pieces: null, body: "" };
    return { plain: null, pieces: null, body: html(plain != null ? [plain] : rich(pieces), s => tex(accents(s))) };
  }, [text, explicit]);
  if (!line) return <View style={styles.math}><MathText text={text} size={size} testID={testID} color={color} backgroundColor={colors.custom_reading} /></View>;
  if (line.plain != null) return <T testID={testID} size={size} w={w} color={color} style={styles.text}>{line.plain}</T>;
  if (line.pieces) return <T testID={testID} size={size} w={w} color={color} style={[styles.text, { lineHeight: Math.round(size * 1.5) }]}>{draw(line.pieces, size, { color, fontFamily: fonts[w] })}</T>;
  // Only a line with an accent (a⃗, x̄) needs the maths fonts; plain indices use the light page.
  const katex = line.body.includes('class="katex');
  return <View style={styles.math}><OfflineMath key={katex ? "katex" : "light"} katex={katex} body={line.body} testID={testID} backgroundColor={colors.custom_reading} css={sheet(size, color, w)} /></View>;
});
// Web: an index is nested text moved off the baseline, so the line keeps its height. Two indices on one base sit in a
// small column; text inside it starts a new block on web, so it is given the line's colour and face again.
function draw(pieces: Piece[], size: number, face: { color: string; fontFamily: string }): React.ReactNode[] {
  const small = Math.max(9, size * 0.72);
  return pieces.map((p, k) => {
    if (typeof p === "string") return p;
    if (p.kind === "keep") return <Text key={k} style={styles.keep}>{draw(p.body, size, face)}</Text>;
    if (p.kind === "both") return <View key={k} style={styles.both}>
      {[p.sup, p.sub].map((body, row) => <Text key={row} style={[face, { fontSize: small, lineHeight: Math.round(small * 1.05) }]}>{draw(body, small, face)}</Text>)}
    </View>;
    return <Text key={k} style={[styles.index, { fontSize: small, top: p.kind === "sup" ? -size * 0.4 : size * 0.2 }]}>{draw(p.body, small, face)}</Text>;
  });
}
const WEIGHT: Partial<Record<Weight, number>> = { regular: 400, medium: 500, semibold: 600, bold: 700, heavy: 800 };
const sheet = (size: number, color: string, w: Weight) => `body{margin:0;background:transparent;color:${color};font:${WEIGHT[w] ?? 400} ${size}px -apple-system,Roboto,sans-serif;line-height:1.55;overflow-wrap:anywhere}#content{white-space:pre-wrap}sup,sub{font-size:.72em;line-height:0;position:relative;vertical-align:baseline}sup{top:-.45em}sub{top:.22em}.keep{white-space:nowrap}.both{display:inline-flex;flex-direction:column;vertical-align:middle;line-height:1}.both>sup,.both>sub{position:static;line-height:1.05}.katex-display{overflow-x:auto;overflow-y:hidden}.katex{font-size:1.05em}`;
// Letters with a combining mark (a⃗, b̂, x̄, A̅): many phone fonts have no glyph for the mark, so on native the
// offline typesetter draws them (\vec, \hat, \bar, \overline). Browsers fall back to a system font by themselves.
const ACCENT: Record<string, string> = { "\u20D7": "vec", "\u0304": "bar", "\u0305": "overline", "\u0302": "hat", "\u0303": "tilde", "\u0307": "dot", "\u0308": "ddot" };
const GREEK: Record<string, string> = { α: "alpha", β: "beta", γ: "gamma", δ: "delta", ε: "epsilon", ζ: "zeta", η: "eta", θ: "theta", κ: "kappa", λ: "lambda", μ: "mu", ν: "nu", ξ: "xi", π: "pi", ρ: "rho", σ: "sigma", τ: "tau", φ: "phi", χ: "chi", ψ: "psi", ω: "omega" };
function accents(text: string) {
  return text.replace(/([A-Za-z0-9α-ω])([\u0302-\u0308\u20D7]+)/g, (whole, base: string, marks: string) => {
    let out = GREEK[base] ? `\\${GREEK[base]}` : base;
    for (const m of Array.from(marks)) {
      if (!ACCENT[m]) return whole;
      out = `\\${ACCENT[m]}{${out}}`;
    }
    return `$${out}$`;
  });
}
const MARKED = /[A-Za-z0-9α-ω][\u0302-\u0308\u20D7]/;
const styles = StyleSheet.create({ math: { width: "100%" }, text: { flexShrink: 1 }, index: { position: "relative" }, both: { flexDirection: "column", verticalAlign: "middle" } as object, keep: { whiteSpace: "nowrap" } as object });
