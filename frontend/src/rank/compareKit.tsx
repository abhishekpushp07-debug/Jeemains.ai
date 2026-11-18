// Shared look of the College compare tables (branch vs branch, college vs college). Every column fits on the phone
// (no sideways scroll): a full-width label line, then one row of 2–3 equal cells, so each row grows to its tallest cell
// and the columns always stay level. `best` = the column to highlight (the easiest choice).
import React from "react";
import { StyleSheet, View } from "react-native";
import { T } from "@/src/components/ui";
import { rankColors as colors } from "@/src/theme";
import { SERIF } from "./tones";

export const Dash = () => <T size={12} color={colors.custom_dim}>—</T>;

export function TableRow({ id, label, count, tight, best, cell }: {
  id: string; label: string | null; count: number; tight: boolean; best: number; cell: (i: number) => React.ReactNode;
}) {
  return <View>
    {label ? <T w="bold" size={10.5} color={colors.custom_eyebrow} style={tableStyles.section}>{label.toUpperCase()}</T> : null}
    <View testID={id} style={tableStyles.tr}>
      {Array.from({ length: count }, (_, i) => <View key={i} style={[tableStyles.td, tight && tableStyles.tdTight, i > 0 && tableStyles.tdLine, i === best && tableStyles.best]}>
        {cell(i)}
      </View>)}
    </View>
  </View>;
}

export const tableStyles = StyleSheet.create({
  table: { borderRadius: 14, borderWidth: 1, borderColor: colors.custom_cardLine, overflow: "hidden" },
  section: { letterSpacing: 1, paddingHorizontal: 8, paddingTop: 7, paddingBottom: 5, backgroundColor: colors.custom_cardRaised,
    borderTopWidth: 1, borderTopColor: colors.custom_cardLine },
  tr: { flexDirection: "row" },
  td: { flex: 1, minWidth: 0, justifyContent: "center", paddingHorizontal: 8, paddingVertical: 7 },
  tdTight: { paddingHorizontal: 6 },
  tdLine: { borderLeftWidth: 1, borderLeftColor: colors.custom_cardLine },
  best: { backgroundColor: colors.custom_rankBloodSoft },
  cellLine: { flexDirection: "row", flexWrap: "wrap", alignItems: "baseline", columnGap: 6 },
  serif: { fontFamily: SERIF, fontSize: 18, lineHeight: 23 },
  check: { width: 24, height: 24, borderRadius: 7, borderWidth: 1.5, borderColor: colors.custom_cardLineStrong, alignItems: "center", justifyContent: "center" },
});
