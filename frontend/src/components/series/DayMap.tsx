import React, { useState } from "react";
import { StyleSheet, View } from "react-native";
import { Press, T } from "@/src/components/ui";
import { DCard, PastelSurface } from "@/src/components/design";
import { colors, pastel, SeriesTone, space } from "@/src/theme";
import { istDate } from "@/src/navigation";
import { DayInfo } from "@/src/series";

const ROWS = 7, GAP = 6;
const LEGEND: SeriesTone[] = ["done", "today", "upcoming", "missed"];

/** GitHub-style 62-day grid; tap a day to see it in the day strip. */
export function DayMap({ days, selected, onSelect }: { days: DayInfo[]; selected: number; onSelect: (day: number) => void }) {
  const [w, setW] = useState(0);
  const cols = Math.ceil(days.length / ROWS) || 9;
  const size = w ? Math.min(34, Math.floor((w - GAP * (cols - 1)) / cols)) : 0;
  const todayDay = days.find(d => d.isToday)?.day ?? (days[0] && days[0].tone === "upcoming" ? 0 : 99);
  const columns = Array.from({ length: cols }, (_, c) => days.slice(c * ROWS, c * ROWS + ROWS));
  return <DCard testID="series-calendar" style={{ gap: space.lg }}>
    <View onLayout={e => setW(e.nativeEvent.layout.width)} style={{ flexDirection: "row", gap: GAP, justifyContent: "center" }}>
      {size ? columns.map((col, c) => <View key={c} style={{ gap: GAP }}>
        {col.map(d => {
          const faded = d.tone === "upcoming" && d.day > todayDay + 1;
          const on = d.day === selected;
          return <Press key={d.day} testID={"series-map-day-" + d.day} haptic={false} onPress={() => onSelect(d.day)} accessibilityLabel={`Day ${d.day}, ${istDate(d.date)}, ${d.label}`} accessibilityState={{ selected: on }}
            style={{ opacity: faded ? 0.35 : 1 }}>
            <PastelSurface tone={d.tone} style={[styles.cell, { width: size, height: size, borderRadius: Math.round(size / 4) }, (d.isToday || on) && styles.cellOn]}>
              {d.isToday || on ? <T w="heavy" size={Math.max(9, Math.round(size / 3))} color={colors.custom_pastelInk}>{d.day}</T> : null}
            </PastelSurface>
          </Press>;
        })}
      </View>) : null}
    </View>
    <View style={styles.legend}>
      {LEGEND.map(t => <View key={t} style={styles.legendItem}>
        <PastelSurface tone={t} style={styles.swatch} />
        <T size={11} color={colors.muted}>{pastel[t].label}</T>
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
