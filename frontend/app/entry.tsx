import React, { useState } from "react";
import { ScrollView, TextInput, View } from "react-native";
import { useRouter } from "expo-router";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import { KeyboardAwareScrollView } from "react-native-keyboard-controller";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Animated, { FadeInDown } from "react-native-reanimated";
import { useAuth } from "@/src/auth";
import { Button, Icon, Notice, T, ErrorBox } from "@/src/components/ui";
import { colors, fonts, radius, space } from "@/src/theme";

export default function Entry() {
  const insets = useSafeAreaInsets();
  const { signIn } = useAuth();
  const router = useRouter();
  const [phone, setPhone] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const digits = phone.replace(/[^0-9+]/g, "");

  async function go() {
    setBusy(true);
    setError("");
    try {
      await signIn(digits);
      router.replace("/(tabs)");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <View style={{ flex: 1, backgroundColor: colors.surface }}>
      <KeyboardAwareScrollView bottomOffset={24} keyboardShouldPersistTaps="handled" contentContainerStyle={{ paddingTop: insets.top + space.xl, paddingBottom: insets.bottom + space.xl, paddingHorizontal: space.xl, gap: space.lg }}>
        <Animated.View entering={FadeInDown.duration(400)} style={{ alignItems: "center", gap: space.md }}>
          <Image source={require("../assets/images/jeelive-logo.webp")} style={{ width: 240, height: 90 }} contentFit="contain" accessibilityLabel="JEELIVE.AI logo" />
          <T w="heavy" size={26} style={{ textAlign: "center" }}>Practice with purpose.</T>
          <T size={15} color={colors.muted} style={{ textAlign: "center" }}>JEE Main · BITSAT · COMEDK — mocks, chapter tests, clear solutions and 20-second Rapid Fire recall.</T>
        </Animated.View>

        <Animated.View entering={FadeInDown.delay(120).duration(400)}>
          <LinearGradient colors={[colors.custom_series, colors.custom_seriesBright]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={{ borderRadius: radius.lg, padding: space.lg, gap: space.sm }}>
            <View style={{ flexDirection: "row", gap: space.sm, alignItems: "center" }}>
              <Icon name="flask-outline" size={18} color={colors.onBrandSecondary} />
              <T w="bold" size={12} color={colors.onBrandSecondary} style={{ letterSpacing: 1 }}>PRIVATE PILOT</T>
            </View>
            <T size={13} color={colors.custom_whiteA70}>This version is for approved pilot participants only. Please don’t use real private student records.</T>
          </LinearGradient>
        </Animated.View>

        <Animated.View entering={FadeInDown.delay(200).duration(400)} style={{ gap: space.sm }}>
          <T w="bold" size={14}>Phone number</T>
          <View style={{ flexDirection: "row", alignItems: "center", backgroundColor: colors.surfaceSecondary, borderRadius: radius.md, borderWidth: 1.5, borderColor: colors.borderStrong, paddingHorizontal: space.md, minHeight: 56 }}>
            <Icon name="phone-outline" size={20} color={colors.muted} />
            <TextInput
              testID="entry-phone-input"
              value={phone}
              onChangeText={setPhone}
              placeholder="e.g. 98765 43210"
              placeholderTextColor={colors.muted}
              keyboardType="phone-pad"
              maxLength={20}
              returnKeyType="go"
              onSubmitEditing={() => digits.length >= 10 && go()}
              style={{ flex: 1, fontFamily: fonts.semibold, fontSize: 17, color: colors.onSurface, paddingHorizontal: space.sm, paddingVertical: space.md }}
              accessibilityLabel="Phone number"
            />
          </View>
          <Notice tone="warning" icon="shield-alert-outline" testID="entry-unverified-notice">
            <T size={13} w="medium" color={colors.warning}>No OTP — this number is not verified. Anyone who enters the same number can open its practice profile. Your saved work returns when you re-enter it.</T>
          </Notice>
          <ErrorBox error={error} testID="entry-error" />
          <Button testID="entry-continue-button" label="Continue" icon="arrow-right" onPress={go} busy={busy} disabled={digits.length < 10} />
          <T size={12} color={colors.muted} style={{ textAlign: "center" }}>Public test lists are visible to everyone. Your attempts, results and Rapid Fire history stay with this profile.</T>
        </Animated.View>
      </KeyboardAwareScrollView>
    </View>
  );
}
// ScrollView import kept for type parity on web
void ScrollView;
