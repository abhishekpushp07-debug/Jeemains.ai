import React, { useState } from "react";
import { StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useAuth } from "@/src/auth";
import { cleanPhone, pinFormError, useAuthSubmit, validPhone, validPin } from "@/src/authPin";
import { AuthShell } from "@/src/components/auth/AuthShell";
import { PhoneField, PinField } from "@/src/components/auth/Fields";
import { Button, ErrorBox, Header, Icon, Notice, T } from "@/src/components/ui";
import { colors, space } from "@/src/theme";

export default function ChangePin() {
  const { user, changePin } = useAuth();
  const router = useRouter();
  const [phone, setPhone] = useState("");
  const [pin, setPin] = useState("");
  const [confirm, setConfirm] = useState("");
  const [done, setDone] = useState(false);
  const submit = useAuthSubmit();
  const back = () => router.canGoBack() ? router.back() : router.replace("/account");
  const go = () => submit.run(() => pinFormError(phone, pin, confirm), async () => {
    await changePin(cleanPhone(phone), pin, confirm);
    setPin(""); setConfirm(""); setPhone(""); setDone(true);
  });
  return <AuthShell testID="change-pin-screen">
    <Header testID="change-pin-header" backTestID="change-pin-back" title="Change PIN" eyebrow="Your account" onBack={submit.busy ? undefined : back} />
    {done ? <View testID="change-pin-success" style={styles.section}>
      <Icon name="shield-check-outline" size={44} color={colors.success} />
      <T testID="change-pin-success-title" size={26} w="heavy">Your PIN is updated.</T>
      <T testID="change-pin-success-description" size={15} color={colors.muted}>Your account, attempts and results are unchanged. Use your new PIN when signing in on other devices.</T>
      <Button testID="change-pin-done-button" label="Back to account" onPress={() => router.dismissTo("/account")} />
    </View> : <View style={styles.section}>
      <T testID="change-pin-description" size={15} color={colors.muted}>Confirm your registered mobile number and choose a new PIN. This changes only the account you’re signed into.</T>
      <PhoneField testID="change-pin-phone-input" label="Confirm registered mobile number" value={phone} onChange={setPhone} disabled={submit.busy} />
      <PinField testID="change-pin-new-input" label="New 4-digit PIN" value={pin} onChange={setPin} disabled={submit.busy} />
      <PinField testID="change-pin-confirm-input" label="Confirm new PIN" value={confirm} onChange={setConfirm} disabled={submit.busy} onSubmit={go} />
      <Notice testID="change-pin-session-warning" tone="warning">Changing your PIN signs out your other sessions. This device stays signed in; saved work is preserved.</Notice>
      <ErrorBox testID="change-pin-error" error={submit.error} />
      {submit.retrySeconds > 0 ? <T testID="change-pin-rate-limit" size={13} color={colors.warning}>Please wait {submit.retrySeconds}s before trying again.</T> : null}
      <Button testID="change-pin-submit" label="Update PIN" icon="lock-reset" busy={submit.busy} disabled={!user || !validPhone(phone) || !validPin(pin) || !validPin(confirm) || submit.retrySeconds > 0} onPress={go} />
      <Button testID="change-pin-cancel" label="Cancel" kind="secondary" disabled={submit.busy} onPress={back} />
    </View>}
  </AuthShell>;
}
const styles = StyleSheet.create({ section: { gap: space.lg } });