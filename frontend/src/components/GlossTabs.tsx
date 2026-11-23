// My Tests' tabs as glossy pills, with the Analysis screen's shine: a soft gloss sits on the upper half, a glass glint
// crosses on the diagonal and three colours of the tab's own family run round its edge. Every tab keeps its own colour:
// the open one wears it in full, with a soft glow, a thicker edge and its count on a white chip; the others rest in a softer wash.
import React from "react";
import { StyleSheet, View } from "react-native";
import { Press, T } from "@/src/components/ui";
import { Shine } from "@/src/analysis/Shine";
import { colors, radius } from "@/src/theme";

type Tones = readonly [string, string, ...string[]];
/** `on` / `rest` = the face when the tab is open / not open; `edge` = the colours that run round it; `glow` = the light under the open tab. */
export type TabLook = { on: Tones; rest: Tones; edge: Tones; glow: string };

export function GlossTabs<K extends string>({ items, value, onChange, prefix }: {
  items: { key: K; label: string; look: TabLook; sub?: string; subTestID?: string; labelTestID?: string }[];
  value: K; onChange: (key: K) => void; prefix: string;
}) {
  return <View accessibilityRole="tablist" style={styles.row}>
    {items.map((item, i) => {
      const on = item.key === value, look = item.look;
      return <Press key={item.key} testID={`${prefix}-${item.key}`} accessibilityRole="tab" accessibilityState={{ selected: on }} accessibilityLabel={item.label}
        onPress={() => onChange(item.key)} scaleTo={0.98} style={[styles.tab, on && styles.glow, on && { backgroundColor: look.on[1], shadowColor: look.glow }]}>
        {/* The glint and the colour change reach each tab a little after the one before it. */}
        <Shine radius={radius.pill} ring={on ? 3 : 2} tones={on ? look.on : look.rest} edge={look.edge} gloss={colors.custom_tabGloss} glint={colors.custom_tabGlint}
          band={26} part={34} delay={i * 220} face={on ? styles.faceOn : styles.face}>
          <T testID={item.labelTestID} w={on ? "heavy" : "semibold"} size={13} numberOfLines={1} color={on ? colors.custom_tabInk : colors.custom_tabInkSoft}>{item.label}</T>
          {item.sub !== undefined ? <View style={on ? styles.chip : null}>
            <T testID={item.subTestID} w="bold" size={10.5} color={on ? colors.custom_tabInk : colors.custom_tabInkSoft}>{item.sub}</T>
          </View> : null}
        </Shine>
      </Press>;
    })}
  </View>;
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", gap: 8 },
  tab: { flex: 1, minWidth: 0, borderRadius: radius.pill },
  // The soft light under the open tab; the solid colour behind the edge lets Android draw it too.
  glow: { shadowOpacity: 0.45, shadowRadius: 9, shadowOffset: { width: 0, height: 4 }, elevation: 6 },
  // The row is 52 high, as the old tab bar was: 48 for the face and 2 for the edge on each side, or 46 and 3 when open.
  face: { minHeight: 48, alignItems: "center", justifyContent: "center", gap: 1, paddingHorizontal: 5, paddingVertical: 3 },
  faceOn: { minHeight: 46, alignItems: "center", justifyContent: "center", gap: 1, paddingHorizontal: 4, paddingVertical: 2 },
  chip: { minWidth: 22, height: 16, paddingHorizontal: 6, borderRadius: 8, alignItems: "center", justifyContent: "center", backgroundColor: colors.custom_tabChip },
});
