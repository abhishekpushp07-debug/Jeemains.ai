// My Tests' tabs as glossy pills, with the Analysis screen's shine: five colours run round each edge, a soft gloss sits
// on the upper half and a glass glint crosses on the diagonal. A tab rests in its own colour and is blood red when open.
import React from "react";
import { StyleSheet, View } from "react-native";
import { Press, T } from "@/src/components/ui";
import { Shine } from "@/src/analysis/Shine";
import { colors, radius } from "@/src/theme";

export type TabTones = readonly [string, string];
const BLOOD: TabTones = [colors.custom_tabBlood, colors.custom_tabBloodDeep];

export function GlossTabs<K extends string>({ items, value, onChange, prefix }: {
  items: { key: K; label: string; tones: TabTones; sub?: string; subTestID?: string; labelTestID?: string }[];
  value: K; onChange: (key: K) => void; prefix: string;
}) {
  return <View accessibilityRole="tablist" style={styles.row}>
    {items.map((item, i) => {
      const on = item.key === value;
      return <Press key={item.key} testID={`${prefix}-${item.key}`} accessibilityRole="tab" accessibilityState={{ selected: on }} accessibilityLabel={item.label}
        onPress={() => onChange(item.key)} scaleTo={0.98} style={styles.tab}>
        {/* The glint and the colour change reach each tab a little after the one before it. */}
        <Shine radius={radius.pill} ring={2} tones={on ? BLOOD : item.tones} gloss={on ? colors.custom_tabBloodGloss : colors.custom_tabGloss}
          glint={on ? colors.custom_tabBloodGlint : colors.custom_tabGlint} band={26} part={34} delay={i * 220} face={styles.face}>
          <T testID={item.labelTestID} w={on ? "heavy" : "bold"} size={13} numberOfLines={1} color={on ? colors.custom_tabOnBlood : colors.custom_tabInk}>{item.label}</T>
          {item.sub !== undefined ? <T testID={item.subTestID} w="bold" size={10.5} color={on ? colors.custom_tabOnBloodSoft : colors.custom_tabInkSoft}>{item.sub}</T> : null}
        </Shine>
      </Press>;
    })}
  </View>;
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", gap: 8 },
  tab: { flex: 1, minWidth: 0, borderRadius: radius.pill },
  // 48 for the face and 2 for the edge on each side: the row is 52 high, as the old tab bar was.
  face: { minHeight: 48, alignItems: "center", justifyContent: "center", paddingHorizontal: 6, paddingVertical: 3 },
});
