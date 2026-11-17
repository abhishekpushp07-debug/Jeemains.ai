// Small text-only building blocks of the dark Rank tab: section panel, switch, colour tag, toggle chip, star and a list picker.
import React from "react";
import { StyleSheet, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { Icon, Press, T } from "@/src/components/ui";
import { DSheet } from "@/src/components/design";
import { Glyph } from "@/src/components/Glyph";
import { rankColors as colors, radius, space } from "@/src/theme";

/** Section title in the Rank Card's voice: a blood-red hairline, then widely tracked silver caps. */
export function RuleTitle({ children }: { children: string }) {
  return <View style={styles.ruleTitle}>
    <View style={styles.rule} />
    <T w="bold" size={11} color={colors.custom_eyebrow} style={styles.caps} numberOfLines={1}>{children.toUpperCase()}</T>
  </View>;
}

/** A dark panel with a faint top-left sheen, like the back of the card. */
export function Strip({ title, right, children, testID }: { title?: string; right?: React.ReactNode; children: React.ReactNode; testID?: string }) {
  return <View testID={testID} style={styles.strip}>
    <LinearGradient colors={[colors.custom_rankPanelSheen, colors.custom_clear]} start={{ x: 0, y: 0 }} end={{ x: 0.7, y: 0.6 }} style={StyleSheet.absoluteFill} />
    {title ? <View style={styles.stripHead}>
      <View style={{ flexShrink: 1 }}><RuleTitle>{title}</RuleTitle></View>
      {right}
    </View> : null}
    {children}
  </View>;
}

/** Exam / mode switch: dark track, the chosen side raised with a sparkle-silver outline. */
export function Switch<K extends string>({ items, value, onChange, prefix }: {
  items: { key: K; label: string }[]; value: K; onChange: (k: K) => void; prefix: string;
}) {
  return <View accessibilityRole="tablist" style={styles.switch}>
    {items.map(it => {
      const on = it.key === value;
      return <Press key={it.key} testID={`${prefix}-${it.key}`} accessibilityRole="tab" accessibilityState={{ selected: on }} accessibilityLabel={it.label}
        onPress={() => onChange(it.key)} scaleTo={0.98} style={[styles.switchItem, on && styles.switchOn]}>
        <T w={on ? "bold" : "semibold"} size={13.5} color={on ? colors.onSurface : colors.muted} numberOfLines={1}>{it.label}</T>
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
  return <Press testID={testID} onPress={onPress} accessibilityLabel={label} accessibilityState={{ selected: !!on }} scaleTo={0.97}
    style={[styles.toggle, on ? { backgroundColor: soft ?? ink, borderColor: ink } : null]}>
    <T w="bold" size={13} color={on ? (soft ? ink : colors.onSurfaceInverse) : colors.custom_softText} numberOfLines={1}>{label}</T>
    {caret ? <Glyph name="chevron-down" size={14} color={on ? (soft ? ink : colors.onSurfaceInverse) : colors.custom_dim} /> : null}
  </Press>;
}

/** Shortlist star: outline when not saved, gold when saved. */
export function StarButton({ saved, onPress, testID }: { saved: boolean; onPress: () => void; testID?: string }) {
  return <Press testID={testID} onPress={onPress} accessibilityLabel={saved ? "Shortlist se hatao" : "Shortlist mein daalo"} accessibilityState={{ selected: saved }} scaleTo={0.9} style={styles.star}>
    <Icon name={saved ? "star" : "star-outline"} size={22} color={saved ? colors.custom_gold : colors.custom_dim} />
  </Press>;
}

/** The input after Show: one tappable line with Edit. */
export function Summary({ text, onEdit, testID }: { text: string; onEdit: () => void; testID: string }) {
  return <Press testID={testID} onPress={onEdit} accessibilityLabel={`${text}. Edit`} scaleTo={0.99} style={styles.summary}>
    <T w="semibold" size={14} numberOfLines={2} style={{ flex: 1 }}>{text}</T>
    <T w="bold" size={14} color={colors.brandText}>Edit</T>
  </Press>;
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

const styles = StyleSheet.create({
  strip: { borderRadius: 22, padding: space.lg, gap: space.md, overflow: "hidden", backgroundColor: colors.custom_card, borderWidth: 1, borderColor: colors.custom_cardLine },
  stripHead: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: space.sm, minHeight: 20 },
  ruleTitle: { flexDirection: "row", alignItems: "center", gap: space.sm },
  rule: { width: 18, height: 1.5, backgroundColor: colors.custom_rankBlood },
  caps: { letterSpacing: 3 },
  switch: { flexDirection: "row", padding: 4, gap: 4, borderRadius: radius.pill, backgroundColor: colors.custom_card, borderWidth: 1, borderColor: colors.custom_cardLine },
  switchItem: { flex: 1, minWidth: 0, minHeight: 44, borderRadius: radius.pill, alignItems: "center", justifyContent: "center", paddingHorizontal: 6, borderWidth: 1, borderColor: colors.custom_clear },
  switchOn: { backgroundColor: colors.custom_cardRaised, borderColor: colors.custom_rankSilverLine },
  tag: { borderRadius: radius.pill, borderWidth: 1, paddingHorizontal: 8, paddingVertical: 2, alignSelf: "flex-start" },
  toggle: { minHeight: 44, paddingHorizontal: 14, borderRadius: radius.pill, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_cardRaised, flexDirection: "row", alignItems: "center", gap: 4 },
  star: { width: 44, height: 44, alignItems: "center", justifyContent: "center" },
  summary: { minHeight: 52, borderRadius: 26, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card, paddingHorizontal: space.lg, paddingVertical: space.sm, flexDirection: "row", alignItems: "center", gap: space.md },
  row: { minHeight: 48, flexDirection: "row", alignItems: "center", borderBottomWidth: 1, borderBottomColor: colors.custom_barLine },
  done: { minHeight: 50, borderRadius: radius.pill, backgroundColor: colors.brandPrimary, alignItems: "center", justifyContent: "center", marginTop: space.sm },
});
