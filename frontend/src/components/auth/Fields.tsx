import React, { useEffect, useState } from "react";
import { AppState, StyleSheet, TextInput, View } from "react-native";
import { colors, fonts, radius, space } from "@/src/theme";
import { Icon, Press, T } from "../ui";

export function PhoneField({ value, onChange, disabled, testID = "entry-phone-input", label = "Mobile number" }: {
  value: string; onChange: (value: string) => void; disabled?: boolean; testID?: string; label?: string;
}) {
  return <View style={styles.group}>
    <T testID={`${testID}-label`} size={13} w="bold">{label}</T>
    <View style={styles.field}>
      <Icon name="phone-outline" size={20} color={colors.muted} />
      <TextInput testID={testID} accessibilityLabel={label} value={value} onChangeText={onChange} editable={!disabled}
        placeholder="Mobile number" placeholderTextColor={colors.muted} keyboardType="phone-pad" autoComplete="tel"
        maxLength={32} autoCorrect={false} style={styles.input} />
    </View>
  </View>;
}

export function PinField({ value, onChange, label = "4-digit PIN", testID, disabled, onSubmit }: {
  value: string; onChange: (value: string) => void; label?: string; testID: string; disabled?: boolean; onSubmit?: () => void;
}) {
  const [visible, setVisible] = useState(false);
  useEffect(() => { const listener = AppState.addEventListener("change", state => { if (state !== "active") setVisible(false); }); return () => listener.remove(); }, []);
  return <View style={styles.group}>
    <T testID={`${testID}-label`} size={13} w="bold">{label}</T>
    <View style={styles.field}>
      <Icon name="lock-outline" size={20} color={colors.muted} />
      <TextInput testID={testID} accessibilityLabel={label} value={value} onChangeText={text => onChange(text.replace(/[^0-9]/g, "").slice(0, 4))}
        editable={!disabled} placeholder="4 digits" placeholderTextColor={colors.muted} keyboardType="number-pad" maxLength={4}
        secureTextEntry={!visible} autoComplete="off" textContentType="none" autoCorrect={false} autoCapitalize="none"
        onBlur={() => setVisible(false)} returnKeyType="done" onSubmitEditing={onSubmit} style={[styles.input, styles.pin]} />
      <Press testID={`${testID}-visibility`} accessibilityLabel={`${visible ? "Hide" : "Show"} ${label}`} disabled={disabled}
        accessibilityState={{ checked: visible }} onPress={() => setVisible(v => !v)} style={styles.eye}>
        <Icon name={visible ? "eye-off-outline" : "eye-outline"} size={20} color={colors.muted} />
      </Press>
    </View>
  </View>;
}

const styles = StyleSheet.create({
  group: { gap: space.sm },
  field: { flexDirection: "row", alignItems: "center", minHeight: 56, borderRadius: radius.md, borderWidth: 1, borderColor: colors.borderStrong, backgroundColor: colors.surfaceSecondary, paddingLeft: space.md, paddingRight: 4 },
  input: { flex: 1, minWidth: 0, fontFamily: fonts.medium, fontSize: 16, color: colors.onSurface, paddingHorizontal: space.sm, paddingVertical: space.md },
  pin: { letterSpacing: 3 },
  eye: { width: 48, height: 48, alignItems: "center", justifyContent: "center" },
});