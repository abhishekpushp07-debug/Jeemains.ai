import React, { useCallback, useRef, useState } from "react";
import { StyleSheet, TextInput, View } from "react-native";
import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import Animated, { FadeInDown, useReducedMotion } from "react-native-reanimated";
import { useAuth } from "@/src/auth";
import { cleanPhone, pinFormError, useAuthSubmit, validPhone, validPin, waitText } from "@/src/authPin";
import { Button, ErrorBox, Icon, Notice, Press, T } from "@/src/components/ui";
import { BrandMark } from "@/src/components/BrandMark";
import { PhoneField, PinField } from "@/src/components/auth/Fields";
import { AuthShell } from "@/src/components/auth/AuthShell";
import { colors, radius, space } from "@/src/theme";
import { ARENA, HOME_ROUTE } from "@/src/arenaMode";
import { isRoomPath } from "@/src/rapid/social";
import { isMatchedPath } from "@/src/matched/api";
import { useMatchedOn } from "@/src/matched/gate";
import { MatchedBanner } from "@/src/matched/MatchedCard";

export default function Entry() {
  const { signIn, signUp, user, ready, sessionError, checkSession, expired, signOutWarning, lastPhone, forgetPhone } = useAuth();
  const router = useRouter();
  const params = useLocalSearchParams<{ mode?: string; next?: string }>();
  // Opened from a match link: back to that Match Room after sign-in. Opened from Matched's "Attempt all matched": back
  // to that shift. Otherwise home.
  const room = isRoomPath(params.next), toMatched = !ARENA && isMatchedPath(params.next);
  const target = (room || toMatched ? params.next : HOME_ROUTE) as typeof HOME_ROUTE;
  const reduced = useReducedMotion();
  const [mode, setMode] = useState<"login" | "signup">(params.mode === "signup" ? "signup" : "login");
  const [typed, setTyped] = useState<string | null>(null); // null: the number kept from the last sign-in is shown
  const phone = typed ?? lastPhone;
  const remembered = !!lastPhone && typed === null;
  const [pin, setPin] = useState("");
  const [confirm, setConfirm] = useState("");
  const submit = useAuthSubmit();
  const matched = useMatchedOn();
  const entryFocused = useRef(false);
  const pinRef = useRef<React.ComponentRef<typeof TextInput>>(null);
  const signup = mode === "signup";
  useFocusEffect(useCallback(() => { entryFocused.current = true; return () => { entryFocused.current = false; }; }, []));
  useFocusEffect(useCallback(() => { if (ready && user) router.replace(target); }, [ready, user, router, target]));
  // Session ended with the number kept: the PIN box is ready to type in straight away (also on coming back from Forgot PIN).
  useFocusEffect(useCallback(() => { if (expired && remembered && !signup) pinRef.current?.focus(); }, [expired, remembered, signup]));
  function switchMode(next: typeof mode) { setMode(next); setPin(""); setConfirm(""); submit.setError(""); }
  function changeNumber() { setTyped(""); setPin(""); submit.setError(""); forgetPhone(); }
  const go = () => {
    if (!ready) return; // Keyboard submit must also respect session bootstrap.
    return submit.run(() => pinFormError(phone, pin, signup ? confirm : undefined), async () => {
      if (signup) await signUp(cleanPhone(phone), pin, confirm);
      else await signIn(cleanPhone(phone), pin);
      setPin(""); setConfirm("");
      if (!entryFocused.current) return; // A late login must not hijack policy reading.
      if (router.canDismiss()) router.dismissAll();
      router.replace(target);
    });
  };
  const invalid = !validPhone(phone) || !validPin(pin) || (signup && !validPin(confirm));
  return <AuthShell testID="entry-screen">
    <Animated.View entering={reduced ? undefined : FadeInDown.duration(300)} style={styles.intro}>
      <BrandMark testID="entry-brand" />
      <T testID="entry-eyebrow" size={11} w="bold" color={colors.brandText} style={styles.eyebrow}>{ARENA ? "RAPID FIRE · ONE ACCOUNT" : "YOUR PRACTICE. ONE ACCOUNT."}</T>
      <T testID="entry-title" size={30} w="heavy">{signup ? "Start your next chapter." : "Welcome back."}</T>
      <T testID="entry-description" size={14} color={colors.muted}>{signup ? "Create a PIN for your JEELIVE.AI account. It works on the website and the app too." : "Sign in with the same mobile number and PIN you use on our website."}</T>
    </Animated.View>
    {matched ? <MatchedBanner /> : null}
    {room ? <Notice testID="entry-match-note" tone="info">Sign in or create an account to take your seat in the Rapid Fire match.</Notice> : null}
    {toMatched ? <Notice testID="entry-matched-note" tone="info">Account banao ya sign in karo. Uske baad Matched paper attempt kar sakte ho.</Notice> : null}
    {expired ? <Notice testID="entry-session-expired" tone="info">{remembered
      ? "Aapka session khatam ho gaya. Number pehle se bhara hai — bas PIN daal kar wapas aao. Aapke results aur saved kaam safe hain."
      : "Aapka session khatam ho gaya. Number aur PIN daal kar wapas aao. Aapke results aur saved kaam safe hain."}</Notice> : null}
    {signOutWarning ? <Notice testID="entry-signout-warning" tone="warning">{signOutWarning}</Notice> : null}
    {sessionError ? <ErrorBox testID="entry-session-error" error={sessionError} retry={checkSession} /> : null}
    <View style={styles.tabs}>
      {(["login", "signup"] as const).map(tab => <Press testID={`entry-tab-${tab}`} key={tab} accessibilityRole="tab" accessibilityState={{ selected: mode === tab }} disabled={submit.busy} onPress={() => switchMode(tab)} style={[styles.tab, mode === tab && styles.selected]}>
        <T testID={`entry-tab-${tab}-label`} size={14} w="bold" color={mode === tab ? colors.onSurfaceInverse : colors.muted}>{tab === "login" ? "Sign in" : "Create account"}</T>
      </Press>)}
    </View>
    <View style={styles.form}>
      <PhoneField value={phone} onChange={setTyped} disabled={submit.busy} />
      {remembered ? <View testID="entry-remembered-phone" style={styles.remembered}>
        <Icon name="check-circle-outline" size={16} color={colors.success} />
        <T testID="entry-remembered-label" size={12.5} w="medium" color={colors.muted} style={styles.grow}>Pichhli baar wala number</T>
        <Press testID="entry-change-number" accessibilityLabel="Doosra number daalo" onPress={changeNumber} disabled={submit.busy} style={styles.change}>
          <T testID="entry-change-number-label" size={13} w="bold" color={colors.brandText}>Doosra number?</T>
        </Press>
      </View> : null}
      <PinField testID="entry-pin-input" inputRef={pinRef} value={pin} onChange={setPin} disabled={submit.busy} onSubmit={go} />
      {signup ? <PinField testID="entry-confirm-pin-input" label="Confirm PIN" value={confirm} onChange={setConfirm} disabled={submit.busy} onSubmit={go} /> : <Press testID="entry-forgot-pin" onPress={() => { setPin(""); router.push("/forgot-pin"); }} disabled={submit.busy} style={styles.forgot}>
        <T testID="entry-forgot-pin-label" size={13} w="bold" color={colors.brandText}>Forgot PIN?</T>
      </Press>}
      <ErrorBox error={submit.error} testID="entry-error" />
      {submit.retrySeconds > 0 ? <T testID="entry-rate-limit" size={13} color={colors.warning}>Please wait {waitText(submit.retrySeconds)} before trying again{signup ? "." : " — or use Forgot PIN."}</T> : null}
      <Button testID="entry-continue-button" label={signup ? "Create account" : "Sign in"} icon="arrow-right" onPress={go} busy={submit.busy || !ready} disabled={invalid || submit.retrySeconds > 0} />
      <Press testID="entry-privacy-link" onPress={() => { setPin(""); setConfirm(""); router.push("/privacy"); }} style={{ minHeight: 44, alignItems: "center", justifyContent: "center" }}><T testID="entry-privacy-label" size={13} color={colors.muted}>Privacy policy & account deletion</T></Press>
    </View>
    <View style={styles.footer}>
      <T testID="entry-sync-note" size={12} w="medium" color={colors.muted} style={styles.center}>{signup ? "Already have an account? Sign in instead—your history stays with your existing account." : ARENA ? "Your coins, diamonds, friends and gangs are the same as in the app." : "Your tests, progress and original solutions stay in sync with the website."}</T>
      <T testID="entry-pin-notice" size={11} color={colors.muted} style={styles.center}>Your PIN protects sign-in. No OTP is sent; phone ownership is not verified.</T>
    </View>
  </AuthShell>;
}
const styles = StyleSheet.create({
  intro: { gap: space.sm }, eyebrow: { letterSpacing: 1.5, marginTop: space.sm },
  tabs: { flexDirection: "row", padding: 4, borderRadius: radius.pill, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_cardRaised },
  tab: { flex: 1, minHeight: 44, alignItems: "center", justifyContent: "center", borderRadius: radius.pill }, selected: { backgroundColor: colors.onSurface },
  form: { gap: space.md }, forgot: { alignSelf: "flex-end", minHeight: 44, justifyContent: "center", paddingHorizontal: space.sm, marginTop: -space.sm },
  footer: { gap: space.md, paddingBottom: space.sm }, center: { textAlign: "center" },
  remembered: { flexDirection: "row", alignItems: "center", gap: space.sm, marginTop: -space.sm, paddingLeft: space.xs },
  grow: { flex: 1 }, change: { minHeight: 44, justifyContent: "center", paddingHorizontal: space.sm },
});