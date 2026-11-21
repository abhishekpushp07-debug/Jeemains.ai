import React, { useState } from "react";
import { View } from "react-native";
import { useRouter } from "expo-router";
import { useAuth } from "@/src/auth";
import { cleanPhone, pinFormError, useAuthSubmit, validPhone, validPin } from "@/src/authPin";
import { DeletionReceipt, requestAccountDeletion } from "@/src/api/client";
import { PhoneField, PinField, WordField } from "@/src/components/auth/Fields";
import { ErrorBox, Notice, T, buzz } from "@/src/components/ui";
import { DSheet, Pill } from "@/src/components/design";
import { space, useTheme } from "@/src/theme";
import content from "@/src/legal/content.json";
import { LegalLayout, legalStyles } from "@/src/legal/LegalLayout";
import { DeletionDone, DeletionSteps } from "@/src/legal/DeletionParts";

const confirmed = (word: string) => word.trim().toUpperCase() === "DELETE";

export default function DeleteAccount() {
  const router = useRouter();
  const { colors } = useTheme();
  const { user, signOut } = useAuth();
  const [phone, setPhone] = useState("");
  const [pin, setPin] = useState("");
  const [word, setWord] = useState("");
  const [asking, setAsking] = useState(false);
  const [receipt, setReceipt] = useState<DeletionReceipt | null>(null);
  const submit = useAuthSubmit();
  const ready = validPhone(phone) && validPin(pin) && confirmed(word) && submit.retrySeconds === 0;

  const ask = () => { if (ready && !submit.busy) setAsking(true); };
  const go = () => submit.run(() => pinFormError(phone, pin) || (confirmed(word) ? "" : "Type DELETE to confirm."), async () => {
    try {
      const done = await requestAccountDeletion(cleanPhone(phone), pin, user?.id);
      setPin(""); setWord(""); setPhone("");
      // The server already ended this device's session: clear the phone's copy (drafts, images, grants) too.
      if (user) await signOut("discard", true);
      buzz("success");
      setReceipt(done);
    } finally { setAsking(false); }
  });
  const finish = () => { if (router.canDismiss()) router.dismissAll(); router.replace("/entry"); };

  return <LegalLayout page="delete-account" title={content.deletion.title}>
    {receipt ? <DeletionDone receipt={receipt} onDone={finish} /> : <>
      <View style={{ gap: space.sm }}>
        <T testID="delete-account-status" accessibilityRole="header" w="heavy" size={22}>{content.deletion.status}</T>
        <T testID="delete-account-explanation" size={15} color={colors.muted} style={legalStyles.body}>{content.deletion.explanation}</T>
      </View>
      <DeletionSteps />
      <T testID="delete-account-retained" size={12.5} color={colors.muted} style={legalStyles.body}>{content.deletion.retained}</T>
      <View testID="delete-account-form" style={{ gap: space.lg }}>
        {user ? <Notice testID="delete-account-signed-in" icon="account-outline">{`Signed in${user.phone ? " · number ending " + user.phone.slice(-4) : ""}. Enter this account's number to delete it.`}</Notice> : null}
        <PhoneField testID="delete-account-phone-input" label="Registered mobile number" value={phone} onChange={setPhone} disabled={submit.busy} />
        <PinField testID="delete-account-pin-input" label="4-digit PIN" value={pin} onChange={setPin} disabled={submit.busy} />
        <WordField testID="delete-account-confirm-input" label="Type DELETE to confirm" placeholder="DELETE" value={word} onChange={setWord} disabled={submit.busy} onSubmit={ask} />
        <ErrorBox testID="delete-account-error" error={submit.error} />
        {submit.retrySeconds > 0 ? <T testID="delete-account-rate-limit" size={13} color={colors.warning}>Please wait {submit.retrySeconds}s before trying again.</T> : null}
        <Pill testID="delete-account-submit" size="lg" kind="danger" icon="account-remove-outline" label="Delete my account" busy={submit.busy} disabled={!ready} onPress={ask} />
        <T testID="delete-account-web-note" size={12.5} color={colors.muted} style={legalStyles.body}>{content.deletion.web}</T>
      </View>
    </>}
    <DSheet visible={asking} onClose={() => { if (!submit.busy) setAsking(false); }} testID="delete-account-sheet" title="Delete account for good?">
      <T size={14.5} color={colors.muted} style={legalStyles.body}>Your Rapid Fire progress, coins and friends are erased now and cannot come back. Your website account and results are deleted within 30 days. You will be signed out.</T>
      <Pill testID="delete-account-sheet-confirm" size="lg" kind="danger" icon="delete-outline" label="Yes, delete my account" busy={submit.busy} onPress={go} />
      <Pill testID="delete-account-sheet-keep" kind="outline" label="Keep my account" disabled={submit.busy} onPress={() => setAsking(false)} />
    </DSheet>
  </LegalLayout>;
}
