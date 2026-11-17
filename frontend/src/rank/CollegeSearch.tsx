// Search-and-pick sheet for a college (Target marks): a filter box over a short list, no extra package.
import React, { useMemo, useState } from "react";
import { StyleSheet, TextInput, View } from "react-native";
import { Press, T } from "@/src/components/ui";
import { DSheet } from "@/src/components/design";
import { rankColors as colors, fonts, noOutline, space } from "@/src/theme";

export type Option = { key: string; title: string; sub: string; find?: string };

export function CollegeSearch({ visible, title, options, onPick, onClose, testID }: {
  visible: boolean; title: string; options: Option[]; onPick: (key: string) => void; onClose: () => void; testID: string;
}) {
  const [q, setQ] = useState("");
  const shown = useMemo(() => {
    const words = q.toLowerCase().split(/\s+/).filter(Boolean);
    return options.filter(o => words.every(w => `${o.title} ${o.sub} ${o.find ?? ""}`.toLowerCase().includes(w))).slice(0, 60);
  }, [q, options]);
  return <DSheet visible={visible} onClose={onClose} title={title} testID={testID}>
    <TextInput testID={`${testID}-search`} value={q} onChangeText={setQ} placeholder="College ka naam ya shehar likho" placeholderTextColor={colors.custom_dim}
      style={styles.input} keyboardAppearance="dark" selectionColor={colors.custom_rankBloodInk} autoCorrect={false} returnKeyType="search" accessibilityLabel="College search" />
    <View>
      {shown.map(o => <Press key={o.key} testID={`${testID}-${o.key}`} onPress={() => { onPick(o.key); onClose(); }} scaleTo={0.99} style={styles.row} accessibilityLabel={`${o.title}, ${o.sub}`}>
        <T w="bold" size={14.5} numberOfLines={2}>{o.title}</T>
        <T size={12} color={colors.muted} numberOfLines={1}>{o.sub}</T>
      </Press>)}
      {shown.length === 0 ? <T size={13} color={colors.muted} style={{ paddingVertical: space.md }}>Koi college nahi mila. Naam thoda chhota likh kar dekho.</T> : null}
    </View>
  </DSheet>;
}

const styles = StyleSheet.create({
  input: { height: 48, borderRadius: 14, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_cardRaised, paddingHorizontal: space.md, fontFamily: fonts.semibold, fontSize: 15, color: colors.onSurface, ...noOutline },
  row: { minHeight: 56, justifyContent: "center", gap: 2, paddingVertical: space.sm, borderBottomWidth: 1, borderBottomColor: colors.custom_barLine },
});
