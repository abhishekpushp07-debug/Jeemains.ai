import React, { useEffect, useState } from "react";
import { StyleSheet, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import Animated, { FadeInDown, useReducedMotion } from "react-native-reanimated";
import { useAuth } from "@/src/auth";
import { cleanPhone, pinFormError, useAuthSubmit, validPhone, validPin } from "@/src/authPin";
import { Button, ErrorBox, Notice, Press, T } from "@/src/components/ui";
import { BrandMark } from "@/src/components/BrandMark";
import { PhoneField, PinField } from "@/src/components/auth/Fields";
import { AuthShell } from "@/src/components/auth/AuthShell";
import { colors, radius, space } from "@/src/theme";

export default function Entry() {
  const { signIn, signUp, user, ready, sessionError, checkSession, expired, signOutWarning } = useAuth();
  const router = useRouter();
  const params = useLocalSearchParams<{ mode?: string }>();
  const reduced = useReducedMotion();
  const [mode, setMode] = useState<"login" | "signup">(params.mode === "signup" ? "signup" : "login");
  const [phone, setPhone] = useState("");
  const [pin, setPin] = useState("");
  const [confirm, setConfirm] = useState("");
  const submit = useAuthSubmit();
  const signup = mode === "signup";
  useEffect(() => { if (ready && user) router.replace("/(tabs)"); }, [ready, user, router]);
  function switchMode(next: typeof mode) { setMode(next); setPin(""); setConfirm(""); submit.setError(""); }
  const go = () => submit.run(() => pinFormError(phone, pin, signup ? confirm : undefined), async () => {
    if (signup) await signUp(cleanPhone(phone), pin, confirm);
    else await signIn(cleanPhone(phone), pin);
    setPin(""); setConfirm("");
    if (router.canDismiss()) router.dismissAll();
    router.replace("/(tabs)");
  });
  const invalid = !validPhone(phone) || !validPin(pin) || (signup && !validPin(confirm));
  return <AuthShell testID="entry-screen">
    <Animated.View entering={reduced ? undefined : FadeInDown.duration(300)} style={styles.intro}>
      <BrandMark testID="entry-brand" />
      <T testID="entry-eyebrow" size={11} w="bold" color={colors.brandText} style={styles.eyebrow}>YOUR PRACTICE. ONE ACCOUNT.</T>
      <T testID="entry-title" size={30} w="heavy">{signup ? "Start your next chapter." : "Welcome back."}</T>
      <T testID="entry-description" size={14} color={colors.muted}>{signup ? "Create a PIN for your JEELIVE account." : "Sign in with the same mobile number and PIN you use on jeelive.ai."}</T>
    </Animated.View>
    {expired ? <Notice testID="entry-session-expired" tone="warning">Your session ended. Sign in again. Saved results and account-scoped drafts are preserved.</Notice> : null}
    {signOutWarning ? <Notice testID="entry-signout-warning" tone="warning">{signOutWarning}</Notice> : null}
    {sessionError ? <ErrorBox testID="entry-session-error" error={sessionError} retry={checkSession} /> : null}
    <View style={styles.tabs}>
      {(["login", "signup"] as const).map(tab => <Press testID={`entry-tab-${tab}`} key={tab} accessibilityRole="tab" accessibilityState={{ selected: mode === tab }} disabled={submit.busy} onPress={() => switchMode(tab)} style={[styles.tab, mode === tab && styles.selected]}>
        <T testID={`entry-tab-${tab}-label`} size={14} w="bold" color={mode === tab ? colors.onBrandPrimary : colors.muted}>{tab === "login" ? "Sign in" : "Create account"}</T>
      </Press>)}
    </View>
    <View style={styles.form}>
      <PhoneField value={phone} onChange={setPhone} disabled={submit.busy} />
      <PinField testID="entry-pin-input" value={pin} onChange={setPin} disabled={submit.busy} onSubmit={go} />
      {signup ? <PinField testID="entry-confirm-pin-input" label="Confirm PIN" value={confirm} onChange={setConfirm} disabled={submit.busy} onSubmit={go} /> : <Press testID="entry-forgot-pin" onPress={() => { setPin(""); router.push("/forgot-pin"); }} disabled={submit.busy} style={styles.forgot}>
        <T testID="entry-forgot-pin-label" size={13} w="bold" color={colors.brandText}>Forgot PIN?</T>
      </Press>}
      <ErrorBox error={submit.error} testID="entry-error" />
      {submit.retrySeconds > 0 ? <T testID="entry-rate-limit" size={13} color={colors.warning}>Please wait {submit.retrySeconds}s before trying again.</T> : null}
      <Button testID="entry-continue-button" label={signup ? "Create account" : "Sign in"} icon="arrow-right" onPress={go} busy={submit.busy || !ready} disabled={invalid || submit.retrySeconds > 0} />
    </View>
    <View style={styles.footer}>
      <T testID="entry-sync-note" size={12} w="medium" color={colors.muted} style={styles.center}>{signup ? "Already have an account? Sign in instead—your history stays with your existing account." : "Your tests, progress and original solutions stay in sync with the website."}</T>
      <T testID="entry-pin-notice" size={11} color={colors.muted} style={styles.center}>Your PIN protects sign-in. No OTP is sent; phone ownership is not verified.</T>
    </View>
  </AuthShell>;
}
const styles = StyleSheet.create({
  intro: { gap: space.sm }, eyebrow: { letterSpacing: 1.5, marginTop: space.sm },
  tabs: { flexDirection: "row", padding: 4, borderRadius: radius.md, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surfaceSecondary },
  tab: { flex: 1, minHeight: 44, alignItems: "center", justifyContent: "center", borderRadius: 8 }, selected: { backgroundColor: colors.brandPrimary },
  form: { gap: space.md }, forgot: { alignSelf: "flex-end", minHeight: 44, justifyContent: "center", paddingHorizontal: space.sm, marginTop: -space.sm },
  footer: { gap: space.md, paddingBottom: space.sm }, center: { textAlign: "center" },
});