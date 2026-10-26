import React, { useState } from "react";
import { ScrollView, View } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { Button, Card, Header, Icon, Notice, Sheet, T } from "@/src/components/ui";
import { colors, space } from "@/src/theme";

export default function Account() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user, signOut, pendingDraftCount, expired } = useAuth();
  const [sheet, setSheet] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);

  async function begin() {
    const n = await pendingDraftCount();
    if (n) setSheet(n);
    else finish("keep");
  }
  async function finish(mode: "keep" | "discard") {
    setBusy(true);
    await signOut(mode);
    setBusy(false);
    if (router.canDismiss()) router.dismissAll();
    router.replace("/entry");
  }

  return (
    <View style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
      <Header testID="account-header" backTestID="account-back-button" title="Account" eyebrow="JEELIVE profile" onBack={() => router.canGoBack() ? router.back() : router.replace("/(tabs)")} />
      <ScrollView contentContainerStyle={{ padding: space.lg, paddingBottom: insets.bottom + space.xl, gap: space.lg }}>
        <Card testID="account-profile" style={{ flexDirection: "row", gap: space.md, alignItems: "center" }}>
          <Icon name="account-circle" size={44} color={colors.brandText} />
          <View style={{ flex: 1 }}>
            <T testID="account-name" w="heavy" size={17}>{user?.name || "Practice profile"}</T>
            <T testID="account-phone-summary" size={13} color={colors.muted}>{user?.phone ? "Number ending " + user.phone.slice(-4) : "Signed-in JEELIVE profile"}</T>
          </View>
        </Card>
        <Notice testID="account-pin-notice">Sign in with your mobile number and 4-digit PIN. A PIN does not verify phone ownership; no OTP is sent.</Notice>
        {user?.role === "student" ? <Button testID="account-change-pin-button" label="Change PIN" icon="lock-reset" onPress={() => router.push("/change-pin")} /> : null}
        <Button testID="account-pin-help-button" label="PIN & account access help" kind="secondary" icon="help-circle-outline" onPress={() => router.push("/forgot-pin")} />
        {expired ? (
          <Button testID="account-reenter-button" label="Sign in again" icon="login" onPress={() => finish("keep")} />
        ) : null}
        <Button testID="account-signout-button" kind="secondary" label="Sign out" icon="logout" busy={busy} onPress={begin} />
        <T testID="account-signout-note" size={12} color={colors.muted}>Signing out clears this device’s session and cached question images. Saved answers and results stay with your existing JEELIVE account.</T>
      </ScrollView>
      <Sheet visible={sheet !== null} onClose={() => setSheet(null)} testID="signout-drafts-sheet">
        <T w="heavy" size={19}>Unsynced work on this phone</T>
        <T size={13} color={colors.muted}>{sheet} attempt{sheet === 1 ? "" : "s"} still have answers waiting for server acknowledgement. They are not submitted or scored.</T>
        <Button testID="signout-keep-drafts" label="Keep drafts & sign out" onPress={() => finish("keep")} />
        <Button testID="signout-discard-drafts" kind="danger" label="Discard drafts & sign out" onPress={() => finish("discard")} />
        <Button testID="signout-stay" kind="secondary" label="Stay signed in" onPress={() => setSheet(null)} />
      </Sheet>
    </View>
  );
}
