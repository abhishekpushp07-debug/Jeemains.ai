// A row of equal tabs; the chosen one is clean blood red with white words, the others white with a hairline.
// My Tests' exam filters and the Misfire Mock's choices use it.
import React from "react";
import { StyleSheet, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { Press, T } from "@/src/components/ui";
import { colors, radius } from "@/src/theme";

export type RedTab<K extends string> = { key: K; label: string; disabled?: boolean; testID?: string };

export function RedTabs<K extends string>({ items, value, onChange, prefix, size = 12.5 }: {
  items: RedTab<K>[]; value: K; onChange: (key: K) => void; prefix: string; size?: number;
}) {
  return <View accessibilityRole="tablist" style={styles.row}>
    {items.map((it) => {
      const on = it.key === value;
      return <Press key={it.key || "all"} testID={it.testID || `${prefix}-${it.key || "all"}`} disabled={it.disabled} onPress={() => onChange(it.key)} scaleTo={0.97}
        accessibilityRole="tab" accessibilityState={{ selected: on, disabled: !!it.disabled }} accessibilityLabel={it.label}
        style={[styles.tab, on ? styles.on : styles.off, it.disabled && styles.disabled]}>
        {on ? <LinearGradient pointerEvents="none" colors={[colors.custom_chipBlood, colors.custom_chipBloodDeep]} start={{ x: 0, y: 0 }} end={{ x: 0, y: 1 }} style={StyleSheet.absoluteFill} /> : null}
        <T w={on ? "heavy" : "bold"} size={size} numberOfLines={1} color={on ? colors.custom_chipBloodInk : colors.custom_softText}>{it.label}</T>
      </Press>;
    })}
  </View>;
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", gap: 6 },
  tab: { flex: 1, minWidth: 0, minHeight: 44, borderRadius: radius.pill, alignItems: "center", justifyContent: "center", paddingHorizontal: 4, overflow: "hidden" },
  on: { borderWidth: 0 },
  off: { borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card },
  disabled: { opacity: 0.35 },
});
