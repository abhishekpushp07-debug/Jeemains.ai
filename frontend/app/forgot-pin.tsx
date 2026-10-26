import React, { useState } from "react";
import { StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import * as Linking from "expo-linking";
import { useAuth } from "@/src/auth";
import { websiteLoginUrl } from "@/src/api/client";
import { AuthShell } from "@/src/components/auth/AuthShell";
import { Button, Card, ErrorBox, Header, Icon, Notice, T } from "@/src/components/ui";
import { colors, space } from "@/src/theme";

export default function ForgotPin() {
  const { user } = useAuth();
  const router = useRouter();
  const [error, setError] = useState("");
  const back = () => router.canGoBack() ? router.back() : router.replace("/entry");
  return <AuthShell testID="forgot-pin-screen">
    <Header testID="forgot-pin-header" backTestID="forgot-pin-back" title="Forgot PIN?" eyebrow="Account access" onBack={back} />
    <View style={styles.hero}><Icon name="shield-key-outline" size={38} color={colors.brandText} /><T testID="forgot-pin-title" size={26} w="heavy">Keep your account intact.</T>
      <T testID="forgot-pin-description" size={14} color={colors.muted}>Your tests and results stay with your existing account. Don’t create another account to recover them.</T></View>
    <Card testID="forgot-pin-existing-session" style={styles.card}>
      <T testID="forgot-pin-existing-title" size={17} w="bold">Still signed in somewhere?</T>
      <T testID="forgot-pin-existing-instructions" size={14} color={colors.muted}>On that signed-in device, open Account / Profile → Change PIN. Confirm your registered mobile number, then choose a new 4-digit PIN.</T>
      {user ? <Button testID="forgot-pin-change-button" label="Change my PIN" icon="lock-reset" onPress={() => router.replace("/change-pin")} /> : null}
    </Card>
    <Notice testID="forgot-pin-reset-unavailable" tone="warning">JEELIVE does not currently offer a public PIN reset or OTP recovery. A mobile number alone cannot unlock an existing account.</Notice>
    <T testID="forgot-pin-help" size={14} color={colors.muted}>If you aren’t signed in on any device, contact your JEELIVE account administrator through your existing official contact. Do not share your PIN. The app cannot reset it for you.</T>
    <ErrorBox testID="forgot-pin-link-error" error={error} />
    <Button testID="forgot-pin-login-button" label={user ? "Back to account" : "Back to sign in"} onPress={() => router.dismissTo(user ? "/account" : "/entry")} />
    <Button testID="forgot-pin-website-button" kind="secondary" icon="open-in-new" label="Open JEELIVE website" onPress={() => { setError(""); Linking.openURL(websiteLoginUrl()).catch(() => setError("Couldn't open your browser. Please try again.")); }} />
  </AuthShell>;
}
const styles = StyleSheet.create({ hero: { gap: space.md }, card: { gap: space.md } });