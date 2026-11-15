import React, { useState } from "react";
import { StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useAuth } from "@/src/auth";
import { resetForgottenPin } from "@/src/api/client";
import { cleanPhone, pinFormError, useAuthSubmit, validPhone, validPin } from "@/src/authPin";
import { AuthShell } from "@/src/components/auth/AuthShell";
import { PhoneField, PinField } from "@/src/components/auth/Fields";
import { Button, ErrorBox, Header, Icon, T } from "@/src/components/ui";
import { colors, space } from "@/src/theme";
import { HOME_ROUTE } from "@/src/arenaMode";

/** Forgot PIN: mobile number, new PIN, confirm PIN, done. The student is signed in straight away. */
export default function ForgotPin() {
  const { signIn } = useAuth();
  const router = useRouter();
  const [phone, setPhone] = useState("");
  const [pin, setPin] = useState("");
  const [confirm, setConfirm] = useState("");
  const [saved, setSaved] = useState(false); // new PIN saved, but signing in needs another try
  const submit = useAuthSubmit();
  const back = () => router.canGoBack() ? router.back() : router.replace("/entry");
  const home = () => { if (router.canDismiss()) router.dismissAll(); router.replace(HOME_ROUTE); };
  const go = () => submit.run(() => pinFormError(phone, pin, confirm), async () => {
    const number = cleanPhone(phone);
    await resetForgottenPin(number, pin, confirm);
    try { await signIn(number, pin); }
    catch { setSaved(true); setPin(""); setConfirm(""); return; }
    setPin(""); setConfirm(""); home();
  });
  if (saved) return <AuthShell testID="forgot-pin-screen">
    <View testID="forgot-pin-success" style={styles.section}>
      <Icon name="shield-check-outline" size={44} color={colors.success} />
      <T testID="forgot-pin-success-title" size={26} w="heavy">Your new PIN is set.</T>
      <T testID="forgot-pin-success-description" size={15} color={colors.muted}>Sign in with your mobile number and the new PIN. Your tests and results are unchanged.</T>
      <Button testID="forgot-pin-signin-button" label="Go to sign in" icon="arrow-right" onPress={() => router.dismissTo("/entry")} />
    </View>
  </AuthShell>;
  return <AuthShell testID="forgot-pin-screen">
    <Header testID="forgot-pin-header" backTestID="forgot-pin-back" title="Forgot PIN?" eyebrow="Account access" onBack={submit.busy ? undefined : back} />
    <View style={styles.hero}>
      <Icon name="lock-reset" size={38} color={colors.brandText} />
      <T testID="forgot-pin-title" size={26} w="heavy">Set a new PIN.</T>
      <T testID="forgot-pin-description" size={14} color={colors.muted}>Enter your mobile number and choose a new 4-digit PIN. Your tests and results stay with your account.</T>
    </View>
    <View style={styles.section}>
      <PhoneField testID="forgot-pin-phone-input" value={phone} onChange={setPhone} disabled={submit.busy} />
      <PinField testID="forgot-pin-new-input" label="New 4-digit PIN" value={pin} onChange={setPin} disabled={submit.busy} />
      <PinField testID="forgot-pin-confirm-input" label="Confirm new PIN" value={confirm} onChange={setConfirm} disabled={submit.busy} onSubmit={go} />
      <ErrorBox testID="forgot-pin-error" error={submit.error} />
      {submit.retrySeconds > 0 ? <T testID="forgot-pin-rate-limit" size={13} color={colors.warning}>Please wait {submit.retrySeconds > 90 ? `${Math.ceil(submit.retrySeconds / 60)} min` : `${submit.retrySeconds}s`} before trying again.</T> : null}
      <Button testID="forgot-pin-submit" label="Set new PIN" icon="check" onPress={go} busy={submit.busy}
        disabled={!validPhone(phone) || !validPin(pin) || !validPin(confirm) || submit.retrySeconds > 0} />
    </View>
  </AuthShell>;
}
const styles = StyleSheet.create({ hero: { gap: space.md }, section: { gap: space.lg } });
