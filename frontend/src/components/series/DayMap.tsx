import React, { useState } from "react";
import { StyleSheet, View } from "react-native";
import { Press, T } from "@/src/components/ui";
import { LinearGradient } from "expo-linear-gradient";
import { DCard } from "@/src/components/design";
import { colors, space } from "@/src/theme";
import { istDate } from "@/src/navigation";
import { DayInfo } from "@/src/series";
import { DAY_LOOK_ORDER, DAY_LOOKS, dayLook } from "./dayLook";

const ROWS = 7, GAP = 6;
const SLOPE = { start: { x: 0, y: 0 }, end: { x: 1, y: 1 } };

/** GitHub-style grid of every series day, in the day strip's colours; tap a day to see it in the day strip. */
export function DayMap({ days, selected, onSelect }: { days: DayInfo[]; selected: number; onSelect: (day: number) => void }) {
  const [w, setW] = useState(0);
  const cols = Math.ceil(days.length / ROWS) || 9;
  const size = w ? Math.min(34, Math.floor((w - GAP * (cols - 1)) / cols)) : 0;
  const columns = Array.from({ length: cols }, (_, c) => days.slice(c * ROWS, c * ROWS + ROWS));
  return <DCard testID="series-calendar" style={{ gap: space.lg }}>
    <View onLayout={e => setW(e.nativeEvent.layout.width)} style={{ flexDirection: "row", gap: GAP, justifyContent: "center" }}>
      {size ? columns.map((col, c) => <View key={c} style={{ gap: GAP }}>
        {col.map(d => {
          const on = d.day === selected, look = DAY_LOOKS[dayLook(d.tone)];
          return <Press key={d.day} testID={"series-map-day-" + d.day} haptic={false} hitSlop={GAP / 2} onPress={() => onSelect(d.day)} accessibilityLabel={`Day ${d.day}, ${istDate(d.date)}, ${d.label}`} accessibilityState={{ selected: on }}>
            <LinearGradient colors={[look.from, look.to]} {...SLOPE} style={[styles.cell, { width: size, height: size, borderRadius: Math.round(size / 4) }, (d.isToday || on) && styles.cellOn]}>
              {d.isToday || on ? <T w="heavy" size={Math.max(9, Math.round(size / 3))} color={look.ink}>{d.day}</T> : null}
            </LinearGradient>
          </Press>;
        })}
      </View>) : null}
    </View>
    <View style={styles.legend}>
      {DAY_LOOK_ORDER.map(k => <View key={k} testID={"series-map-legend-" + k} style={styles.legendItem}>
        <LinearGradient colors={[DAY_LOOKS[k].from, DAY_LOOKS[k].to]} {...SLOPE} style={styles.swatch} />
        <T size={11} color={colors.muted}>{DAY_LOOKS[k].label}</T>
      </View>)}
    </View>
  </DCard>;
}

const styles = StyleSheet.create({
  cell: { alignItems: "center", justifyContent: "center", borderWidth: 2, borderColor: "transparent" },
  cellOn: { borderColor: colors.onSurface },
  legend: { flexDirection: "row", flexWrap: "wrap", justifyContent: "center", gap: space.lg },
  legendItem: { flexDirection: "row", alignItems: "center", gap: 6 },
  swatch: { width: 12, height: 12, borderRadius: 3 },
});
