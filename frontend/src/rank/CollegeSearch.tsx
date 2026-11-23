// Search-and-pick sheet for a college (Target marks, College compare): a filter box over a short list, no extra package.
// `header` sits above the box (e.g. an exam switch); `picked` rows show "Juda" and tapping them again takes them off.
import React, { useMemo, useState } from "react";
import { StyleSheet, TextInput, View } from "react-native";
import { Press, T } from "@/src/components/ui";
import { DSheet } from "@/src/components/design";
import { Glyph } from "@/src/components/Glyph";
import { rankColors as colors, fonts, noOutline, radius, space } from "@/src/theme";

export type Option = { key: string; title: string; sub: string; find?: string };

export function CollegeSearch({ visible, title, options, onPick, onClose, testID, header, picked, hint = "College ka naam ya shehar likho", none = "Koi college nahi mila. Naam thoda chhota likh kar dekho." }: {
  visible: boolean; title: string; options: Option[]; onPick: (key: string) => void; onClose: () => void; testID: string;
  header?: React.ReactNode; picked?: Set<string>; hint?: string; none?: string;
}) {
  const [q, setQ] = useState("");
  const shown = useMemo(() => {
    const words = q.toLowerCase().split(/\s+/).filter(Boolean);
    return options.filter(o => words.every(w => `${o.title} ${o.sub} ${o.find ?? ""}`.toLowerCase().includes(w))).slice(0, 60);
  }, [q, options]);
  return <DSheet visible={visible} onClose={onClose} title={title} testID={testID}>
    {header}
    <TextInput testID={`${testID}-search`} value={q} onChangeText={setQ} placeholder={hint} placeholderTextColor={colors.custom_dim}
      style={styles.input} keyboardAppearance="dark" selectionColor={colors.custom_rankBloodInk} autoCorrect={false} returnKeyType="search" accessibilityLabel={hint} />
    <View>
      {shown.map(o => {
        const on = !!picked?.has(o.key);
        return <Press key={o.key} testID={`${testID}-${o.key}`} onPress={() => { onPick(o.key); onClose(); }} scaleTo={0.99} style={styles.row}
          accessibilityLabel={`${o.title}, ${o.sub}${on ? ", juda hua" : ""}`} accessibilityState={picked ? { selected: on } : undefined}>
          <View style={{ flex: 1, gap: 2 }}>
            <T w="bold" size={14.5} numberOfLines={2}>{o.title}</T>
            <T size={12} color={colors.muted} numberOfLines={1}>{o.sub}</T>
          </View>
          {on ? <View testID={`${testID}-${o.key}-on`} style={styles.on}>
            <Glyph name="check" size={13} color={colors.custom_fOn} stroke={2.4} />
            <T w="bold" size={11.5} color={colors.custom_fOn}>Juda</T>
          </View> : null}
        </Press>;
      })}
      {shown.length === 0 ? <T size={13} color={colors.muted} style={{ paddingVertical: space.md }}>{none}</T> : null}
    </View>
  </DSheet>;
}

const styles = StyleSheet.create({
  input: { height: 48, borderRadius: 14, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_cardRaised, paddingHorizontal: space.md, fontFamily: fonts.semibold, fontSize: 15, color: colors.onSurface, ...noOutline },
  row: { minHeight: 56, flexDirection: "row", alignItems: "center", gap: space.sm, paddingVertical: space.sm, borderBottomWidth: 1, borderBottomColor: colors.custom_barLine },
  on: { flexDirection: "row", alignItems: "center", gap: 3, paddingHorizontal: 9, paddingVertical: 4, borderRadius: radius.pill, backgroundColor: colors.custom_fSky },
});
