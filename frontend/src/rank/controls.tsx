// Small text-only building blocks of the dark Rank tab: section panel, switch, colour tag, toggle chip, remove button and a list picker.
import React, { useEffect, useState } from "react";
import { StyleSheet, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import Animated, { cancelAnimation, Easing, useAnimatedStyle, useReducedMotion, useSharedValue, withDelay, withRepeat, withSequence, withTiming } from "react-native-reanimated";
import { Press, T } from "@/src/components/ui";
import { DSheet } from "@/src/components/design";
import { Glyph } from "@/src/components/Glyph";
import { rankColors as colors, radius, space } from "@/src/theme";
import { InForm, useAccent, useFormAccent } from "./accent";

/** Section title in the Rank Card's voice: a blood-red hairline, then widely tracked silver caps. */
export function RuleTitle({ children }: { children: string }) {
  return <View style={styles.ruleTitle}>
    <View style={styles.rule} />
    <T w="bold" size={11} color={colors.custom_eyebrow} style={styles.caps} numberOfLines={1}>{children.toUpperCase()}</T>
  </View>;
}

/** A dark panel with a faint top-left sheen, like the back of the card. With `form` it is the open tool's form: framed in the
 *  tool's bright colour, a solid header band in that colour (tool icon, tool name, `title`) and chosen chips in it too. */
export function Strip({ title, right, children, testID, form }: { title?: string; right?: React.ReactNode; children: React.ReactNode; testID?: string; form?: boolean }) {
  const tool = useAccent();
  const a = form ? tool : null;
  return <View testID={testID} style={[styles.strip, a && { ...formGlow, borderColor: a.line, shadowColor: a.text }]}>
    <LinearGradient colors={[a ? a.soft : colors.custom_rankPanelSheen, colors.custom_clear]} start={{ x: 0, y: 0 }} end={{ x: 0.7, y: 0.6 }} style={StyleSheet.absoluteFill} />
    {a ? <View testID={testID ? `${testID}-head` : undefined} style={[styles.formHead, { backgroundColor: a.ink }]}>
      <View style={[styles.formIcon, { backgroundColor: a.on }]}><Glyph name={a.icon} size={16} color={a.ink} stroke={1.6} /></View>
      <View style={{ flex: 1, minWidth: 0 }}>
        <T w="bold" size={10} color={a.on} style={styles.formName} numberOfLines={1}>{a.name.toUpperCase()}</T>
        {title ? <T w="heavy" size={15.5} color={a.on} numberOfLines={1}>{title}</T> : null}
      </View>
      {right}
    </View> : title ? <View style={styles.stripHead}>
      <View style={{ flexShrink: 1 }}><RuleTitle>{title}</RuleTitle></View>
      {right}
    </View> : null}
    <InForm.Provider value={!!a}>{children}</InForm.Provider>
  </View>;
}

/** Exam / mode switch: dark track, the chosen side raised with a sparkle-silver outline (the tool's colour inside a tool). */
export function Switch<K extends string>({ items, value, onChange, prefix }: {
  items: { key: K; label: string }[]; value: K; onChange: (k: K) => void; prefix: string;
}) {
  const a = useAccent();
  return <View accessibilityRole="tablist" style={styles.switch}>
    {items.map(it => {
      const on = it.key === value;
      return <Press key={it.key} testID={`${prefix}-${it.key}`} accessibilityRole="tab" accessibilityState={{ selected: on }} accessibilityLabel={it.label}
        onPress={() => onChange(it.key)} scaleTo={0.98} style={[styles.switchItem, on && styles.switchOn, on && a && { borderColor: a.line, backgroundColor: a.soft }]}>
        <T w={on ? "bold" : "semibold"} size={13.5} color={on ? (a ? a.text : colors.onSurface) : colors.muted} numberOfLines={1}>{it.label}</T>
      </Press>;
    })}
  </View>;
}

export function Tag({ label, ink, soft, testID }: { label: string; ink: string; soft: string; testID?: string }) {
  return <View testID={testID} style={[styles.tag, { backgroundColor: soft, borderColor: ink }]}>
    <T w="bold" size={10.5} color={ink} style={{ letterSpacing: 0.6 }} numberOfLines={1}>{label}</T>
  </View>;
}

export function Toggle({ label, on, onPress, ink = colors.onSurface, soft, testID, caret }: {
  label: string; on?: boolean; onPress: () => void; ink?: string; soft?: string; testID?: string; caret?: boolean;
}) {
  // Plain chips (no colour of their own) take the tool's colour inside its form.
  const form = useFormAccent();
  const a = !soft && ink === colors.onSurface ? form : null;
  const onInk = a ? a.on : soft ? ink : colors.onSurfaceInverse;
  return <Press testID={testID} onPress={onPress} accessibilityLabel={label} accessibilityState={{ selected: !!on }} scaleTo={0.97}
    style={[styles.toggle, on ? { backgroundColor: a ? a.ink : soft ?? ink, borderColor: a ? a.ink : ink } : null]}>
    <T w="bold" size={13} color={on ? onInk : colors.custom_softText} numberOfLines={1}>{label}</T>
    {caret ? <Glyph name="chevron-down" size={14} color={on ? onInk : colors.custom_dim} /> : null}
  </Press>;
}

/** A 44×44 "×" that takes a row off a list. */
export function RemoveButton({ onPress, testID, label }: { onPress: () => void; testID?: string; label: string }) {
  return <Press testID={testID} onPress={onPress} accessibilityLabel={label} scaleTo={0.9} style={styles.remove}>
    <Glyph name="close" size={18} color={colors.custom_dim} />
  </Press>;
}

/** The input after Show: the score line and a bright filled "Edit" button in the tool's colour, so trying another number is obvious.
 *  The whole row reopens the form. College predictor's bar is shining purple (a light sweep passes over it) with a blood red Edit. */
export function Summary({ text, onEdit, testID }: { text: string; onEdit: () => void; testID: string }) {
  const a = useAccent();
  const bg = a?.ink ?? colors.brandPrimary, fg = a?.on ?? colors.onBrandPrimary, tint = a?.text ?? colors.brandText;
  const bar = a?.bar;
  const edit = <View testID={`${testID}-edit`} style={[styles.editBtn, { ...editGlow, backgroundColor: bg, shadowColor: bg }]}>
    <Glyph name="pencil" size={15} color={fg} />
    <T w="heavy" size={14} color={fg}>Edit</T>
  </View>;
  if (bar) return <View style={[styles.barGlow, { shadowColor: bar.glow, backgroundColor: bar.to }]}>
    <Press testID={testID} onPress={onEdit} accessibilityRole="button" accessibilityLabel={`${text}. Edit karke doosra number dekho`} scaleTo={0.99} style={styles.bar}>
      <LinearGradient colors={[bar.from, bar.to]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
      <Shine />
      <View style={[styles.summaryIcon, { backgroundColor: bar.chip, borderColor: bar.hint }]}><Glyph name={a.icon} size={15} color={bar.hint} stroke={1.6} /></View>
      <View style={{ flex: 1, minWidth: 0, gap: 2 }}>
        <T w="bold" size={14} color={colors.onBrandPrimary} numberOfLines={2}>{text.replace(/-/g, "\u2011")}</T>
        <T testID={`${testID}-hint`} w="semibold" size={11.5} color={bar.hint} numberOfLines={2}>Doosra number dekhna hai?</T>
      </View>
      {edit}
    </Press>
  </View>;
  return <Press testID={testID} onPress={onEdit} accessibilityRole="button" accessibilityLabel={`${text}. Edit karke doosra number dekho`} scaleTo={0.99}
    style={[styles.summary, a && { borderColor: a.line, backgroundColor: colors.custom_card }]}>
    {a ? <View style={[styles.summaryIcon, { backgroundColor: a.soft, borderColor: a.line }]}><Glyph name={a.icon} size={15} color={a.text} stroke={1.6} /></View> : null}
    <View style={{ flex: 1, minWidth: 0, gap: 2 }}>
      <T w="semibold" size={14} numberOfLines={2}>{text.replace(/-/g, "\u2011")}</T>
      <T testID={`${testID}-hint`} w="semibold" size={11.5} color={tint} numberOfLines={2}>Doosra number dekhna hai?</T>
    </View>
    {edit}
  </Press>;
}

/** A soft band of light that sweeps across its parent every few seconds (still under Reduce Motion). */
export function Shine() {
  const reduced = useStill();
  const [w, setW] = useState(0);
  const x = useSharedValue(-1);
  useEffect(() => {
    if (reduced || !w) return;
    x.value = withRepeat(withSequence(withTiming(-1, { duration: 0 }), withDelay(1600, withTiming(1, { duration: 1200, easing: Easing.inOut(Easing.quad) }))), -1);
    return () => cancelAnimation(x);
  }, [reduced, w, x]);
  const sweep = useAnimatedStyle(() => ({ transform: [{ translateX: x.value * w }, { skewX: "-20deg" }] }));
  return <View pointerEvents="none" style={StyleSheet.absoluteFill} onLayout={e => setW(e.nativeEvent.layout.width)}>
    {w && !reduced ? <Animated.View style={[styles.shine, sweep]}>
      <LinearGradient colors={[colors.custom_clear, colors.custom_fShine, colors.custom_clear]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={StyleSheet.absoluteFill} />
    </Animated.View> : null}
  </View>;
}

/** Bottom sheet list for home state (one) or branches (many). */
export function Picker({ visible, title, options, value, multi, allLabel, onChange, onClose, testID }: {
  visible: boolean; title: string; options: string[]; value: string[]; multi?: boolean; allLabel: string;
  onChange: (v: string[]) => void; onClose: () => void; testID: string;
}) {
  const pick = (o: string | null) => {
    if (o === null) { onChange([]); if (!multi) onClose(); return; }
    if (!multi) { onChange([o]); onClose(); return; }
    onChange(value.includes(o) ? value.filter(v => v !== o) : [...value, o]);
  };
  return <DSheet visible={visible} onClose={onClose} title={title} testID={testID}>
    {[null, ...options].map(o => {
      const on = o === null ? value.length === 0 : value.includes(o);
      return <Press key={o ?? "all"} testID={`${testID}-${(o ?? "all").replace(/[^a-z0-9]+/gi, "-").toLowerCase()}`} onPress={() => pick(o)}
        accessibilityState={{ selected: on }} accessibilityLabel={o ?? allLabel} scaleTo={0.99} style={styles.row}>
        <T w={on ? "bold" : "medium"} size={15} color={on ? colors.onSurface : colors.custom_softText} style={{ flex: 1 }}>{o ?? allLabel}</T>
        {on ? <Glyph name="check" size={18} color={colors.custom_rankBloodInk} stroke={2} /> : null}
      </Press>;
    })}
    {multi ? <Press testID={`${testID}-done`} onPress={onClose} style={styles.done} accessibilityLabel="Done">
      <T w="bold" size={15} color={colors.onBrandPrimary}>Done</T>
    </Press> : null}
  </DSheet>;
}

// Glows kept as plain objects and spread into one inline style with their colour (web draws the blur, Android gets elevation).
const formGlow = { borderWidth: 1.5, shadowOpacity: 0.45, shadowRadius: 18, shadowOffset: { width: 0, height: 0 }, elevation: 8 };
const editGlow = { shadowOpacity: 0.55, shadowRadius: 10, shadowOffset: { width: 0, height: 2 }, elevation: 5 };

const styles = StyleSheet.create({
  strip: { borderRadius: 22, padding: space.lg, gap: space.md, overflow: "hidden", backgroundColor: colors.custom_card, borderWidth: 1, borderColor: colors.custom_cardLine },
  formHead: { flexDirection: "row", alignItems: "center", gap: 10, marginTop: -space.lg, marginHorizontal: -space.lg, paddingHorizontal: space.lg, paddingVertical: 10 },
  formIcon: { width: 32, height: 32, borderRadius: 16, alignItems: "center", justifyContent: "center" },
  formName: { letterSpacing: 1.6, opacity: 0.72 },
  summaryIcon: { width: 30, height: 30, borderRadius: 15, borderWidth: 1, alignItems: "center", justifyContent: "center" },
  editBtn: { flexDirection: "row", alignItems: "center", gap: 6, minHeight: 44, paddingHorizontal: 16, borderRadius: radius.pill },
  barGlow: { borderRadius: 18, shadowOpacity: 0.75, shadowRadius: 20, shadowOffset: { width: 0, height: 4 }, elevation: 10 },
  bar: { flexDirection: "row", alignItems: "center", gap: space.md, minHeight: 64, paddingVertical: space.md, paddingHorizontal: space.lg, borderRadius: 18, overflow: "hidden" },
  shine: { position: "absolute", top: -10, bottom: -10, left: 0, width: 90 },
  stripHead: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: space.sm, minHeight: 20 },
  ruleTitle: { flexDirection: "row", alignItems: "center", gap: space.sm },
  rule: { width: 18, height: 1.5, backgroundColor: colors.custom_rankBlood },
  caps: { letterSpacing: 3 },
  switch: { flexDirection: "row", padding: 4, gap: 4, borderRadius: radius.pill, backgroundColor: colors.custom_card, borderWidth: 1, borderColor: colors.custom_cardLine },
  switchItem: { flex: 1, minWidth: 0, minHeight: 44, borderRadius: radius.pill, alignItems: "center", justifyContent: "center", paddingHorizontal: 6, borderWidth: 1, borderColor: colors.custom_clear },
  switchOn: { backgroundColor: colors.custom_cardRaised, borderColor: colors.custom_rankSilverLine },
  tag: { borderRadius: radius.pill, borderWidth: 1, paddingHorizontal: 8, paddingVertical: 2, alignSelf: "flex-start" },
  toggle: { minHeight: 44, paddingHorizontal: 14, borderRadius: radius.pill, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_cardRaised, flexDirection: "row", alignItems: "center", gap: 4 },
  remove: { width: 44, height: 44, alignItems: "center", justifyContent: "center" },
  summary: { minHeight: 52, borderRadius: 26, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card, paddingHorizontal: space.lg, paddingVertical: space.sm, flexDirection: "row", alignItems: "center", gap: space.md },
  row: { minHeight: 48, flexDirection: "row", alignItems: "center", borderBottomWidth: 1, borderBottomColor: colors.custom_barLine },
  done: { minHeight: 50, borderRadius: radius.pill, backgroundColor: colors.brandPrimary, alignItems: "center", justifyContent: "center", marginTop: space.sm },
});
