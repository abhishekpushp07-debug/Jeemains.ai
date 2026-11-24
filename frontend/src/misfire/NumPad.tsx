// The number answer of a Misfire question, typed on the app's own keys: nothing slides over the question, and it is the
// same on every phone.
import React from "react";
import { StyleSheet, View } from "react-native";
import { Icon, Press, T } from "@/src/components/ui";
import { colors, space } from "@/src/theme";

const ROWS = [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"], ["−", "0", "."]];

export function NumPad({ value, onChange, decimal, disabled }: { value: string; onChange: (next: string) => void; decimal?: boolean; disabled?: boolean }) {
  const press = (k: string) => {
    if (k === "−") return onChange(value.startsWith("-") ? value.slice(1) : "-" + value);
    if (k === "." && (value.includes(".") || !decimal)) return;
    if (value.replace(/[-.]/g, "").length >= 20) return;
    onChange(value + k);
  };
  return <View testID="misfire-numpad" style={{ gap: space.sm }}>
    <View style={[styles.field, !!value && styles.fieldOn]}>
      <T testID="misfire-answer-value" w="heavy" size={24} color={value ? colors.onSurface : colors.custom_dim} numberOfLines={1} style={{ flex: 1 }}>{value || "Apna jawab likho"}</T>
      <Press testID="misfire-key-back" disabled={disabled || !value} onPress={() => onChange(value.slice(0, -1))} accessibilityLabel="Ek ank mitao" style={styles.back}>
        <Icon name="backspace-outline" size={22} color={colors.custom_softText} />
      </Press>
    </View>
    {ROWS.map(row => <View key={row[0]} style={styles.keys}>
      {row.map(k => (k === "." && !decimal ? <View key={k} style={styles.gap} />
        : <Press key={k} testID={`misfire-key-${k === "−" ? "minus" : k === "." ? "dot" : k}`} disabled={disabled} onPress={() => press(k)} scaleTo={0.95}
          accessibilityLabel={k === "−" ? "Minus" : k === "." ? "Dashamlav" : k} style={styles.key}>
          <T w="heavy" size={20}>{k}</T>
        </Press>))}
    </View>)}
  </View>;
}

const styles = StyleSheet.create({
  field: { minHeight: 60, flexDirection: "row", alignItems: "center", gap: space.sm, paddingLeft: space.lg, paddingRight: 6, borderRadius: 16, borderWidth: 1.5, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card },
  fieldOn: { borderColor: colors.onSurface },
  back: { width: 48, height: 48, borderRadius: 24, alignItems: "center", justifyContent: "center" },
  keys: { flexDirection: "row", gap: space.sm },
  key: { flex: 1, height: 52, borderRadius: 14, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_cardRaised, alignItems: "center", justifyContent: "center" },
  gap: { flex: 1 },
});
