import React from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { Icon, IconName, Press, T } from "@/src/components/ui";
import { ToneTag } from "@/src/analysis/parts";
import { TONE, Tone } from "@/src/analysis/format";
import { colors, radius, space } from "@/src/theme";
import type { MisfireItem } from "./api";

// A paper without chapter names calls every question "Previous-year paper": that is not a chapter worth showing.
const GENERIC = /^(previous-year paper|uncategorised)$/i;
export const chapterName = (c?: string | null) => { const v = (c || "").trim(); return v && !GENERIC.test(v) ? v : ""; };
export const marks = (v?: number | null) => (v == null ? "" : String(Math.round(v * 100) / 100));
export const OUTCOME: Record<string, [string, Tone, IconName]> = { incorrect: ["Galat", "bad", "close"], skipped: ["Chhoda tha", "warn", "minus"] };
export const slugOf = (v: string) => (v || "all").toLowerCase().replace(/[^a-z0-9]+/g, "-");

/** Pills in one sideways row; the chosen one turns black like every other selector in the app. */
export function PillRow({ items, value, onChange, prefix, edge = space.lg }: {
  items: { key: string; label: string; count?: number }[]; value: string; onChange: (key: string) => void; prefix: string; edge?: number;
}) {
  return <ScrollView horizontal showsHorizontalScrollIndicator={false} accessibilityRole="tablist" style={{ flexGrow: 0, marginHorizontal: -edge }} contentContainerStyle={{ gap: 8, paddingHorizontal: edge }}>
    {items.map(it => {
      const on = it.key === value;
      return <Press key={it.key || "all"} testID={`${prefix}-${slugOf(it.key)}`} accessibilityRole="tab" accessibilityState={{ selected: on }} accessibilityLabel={it.label + (it.count != null ? `, ${it.count}` : "")}
        onPress={() => onChange(it.key)} scaleTo={0.97} style={[styles.pill, on && styles.pillOn]}>
        <T w={on ? "heavy" : "bold"} size={13} color={on ? colors.onSurfaceInverse : colors.custom_softText} numberOfLines={1}>{it.label}</T>
        {it.count != null ? <T testID={`${prefix}-${slugOf(it.key)}-count`} w="bold" size={11} color={on ? colors.custom_qFreshLine : colors.custom_eyebrow}>{it.count}</T> : null}
      </Press>;
    })}
  </ScrollView>;
}

/** One wrong or skipped question in a list. Opens it to be solved again. */
export function QuestionRow({ item, onPress, testID }: { item: MisfireItem; onPress: () => void; testID: string }) {
  const [label, tone, icon] = OUTCOME[item.outcome] || OUTCOME.incorrect;
  const chapter = chapterName(item.chapter);
  const facts = [chapter, item.lost ? `${marks(item.lost)} marks gaye` : "", item.tries ? `${item.tries} baar try kiya` : ""].filter(Boolean).join(" · ");
  return <Press testID={testID} onPress={onPress} scaleTo={0.99} accessibilityLabel={`Q${item.number}, ${item.subject}, ${label}. Dobara solve karo`} style={[styles.row, { borderLeftColor: TONE[tone].fill }]}>
    <T w="heavy" size={14} style={styles.no}>Q{item.number}</T>
    <View style={{ flex: 1, minWidth: 0, gap: 4 }}>
      <View style={styles.tags}>
        <T size={12.5} w="bold" numberOfLines={1} style={{ flexShrink: 1 }}>{item.subject}</T>
        <ToneTag label={label} tone={tone} icon={icon} />
        {item.status === "fixed" ? <ToneTag label="Samajh gaya" tone="good" icon="check" /> : null}
      </View>
      {facts ? <T size={11.5} color={colors.muted} numberOfLines={1}>{facts}</T> : null}
    </View>
    <Icon name="chevron-right" size={18} color={colors.custom_dim} />
  </Press>;
}

const styles = StyleSheet.create({
  pill: { minHeight: 44, paddingHorizontal: 14, borderRadius: radius.pill, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_card, flexDirection: "row", alignItems: "center", gap: 6 },
  pillOn: { backgroundColor: colors.onSurface, borderColor: colors.onSurface },
  row: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 58, paddingVertical: 8, paddingHorizontal: space.md, borderRadius: 14, borderWidth: 1, borderLeftWidth: 4, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_card },
  no: { minWidth: 38 },
  tags: { flexDirection: "row", alignItems: "center", flexWrap: "wrap", gap: 6 },
});
