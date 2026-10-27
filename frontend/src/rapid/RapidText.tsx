import React, { memo } from "react";
import { StyleSheet, View } from "react-native";
import { MathText } from "@/src/components/MathText";
import { rapidColors as colors } from "@/src/theme";
import { T } from "./ui";

// Preserve the actual scientific notation; use the app's offline KaTeX for TeX.
// Existing Unicode fractions, Greek letters and superscripts remain exact.
export const RapidText = memo(function RapidText({ text, size = 16, testID }: { text: string; size?: number; testID: string }) {
  const explicitMath = /\$[^$]+\$|\\\(|\\\[/.test(text);
  const readable = explicitMath ? text : notation(text);
  // Non-Unicode indices such as v_b and fractional powers use the already
  // bundled offline typesetter on native, rather than showing code notation.
  const marked = explicitMath ? text : readable.replace(/([A-Za-zα-ωΑ-Ω]+(?:[_^](?:\{[^{}\s]+\}|\([^()\s]+\)|[A-Za-z0-9+-]+))+)/g,
    token => `$${token.replace(/\^\(([^)]+)\)/g, "^{$1}")}$`);
  return /\$[^$]+\$|\\\(|\\\[/.test(marked)
    ? <View style={styles.math}><MathText text={marked} size={size} testID={testID} color={colors.custom_onReading} backgroundColor={colors.custom_reading} /></View>
    : <T testID={testID} size={size} w="semibold" color={colors.custom_onReading} style={styles.text}>{readable}</T>;
});
const sup: Record<string, string> = Object.fromEntries(Array.from("0123456789+-=()nix").map((c, i) => [c, Array.from("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱˣ")[i]]));
const sub: Record<string, string> = Object.fromEntries(Array.from("0123456789+-=()aehijklmnoprstuvx").map((c, i) => [c, Array.from("₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓ")[i]]));
function notation(text: string) {
  // Only losslessly convert representable short indices; never simplify equations.
  return text.replace(/([\^_])(\([^\s()]{1,12}\)|\{[^\s{}]{1,12}\}|[a-z0-9+-])/gi, (whole, mode: string, index: string) => {
    const map = mode === "^" ? sup : sub;
    const letters = Array.from(index.replace(/[{}]/g, ""));
    return letters.every(c => map[c]) ? letters.map(c => map[c]).join("") : whole;
  });
}
const styles = StyleSheet.create({ math: { width: "100%" }, text: { flexShrink: 1 } });