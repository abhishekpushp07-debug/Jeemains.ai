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
    router.replace("/entry");
  }

  return (
    <View style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
      <Header title="Account" eyebrow="Pilot profile" onBack={() => router.back()} />
      <ScrollView contentContainerStyle={{ padding: space.lg, paddingBottom: insets.bottom + space.xl, gap: space.lg }}>
        <Card testID="account-profile" style={{ flexDirection: "row", gap: space.md, alignItems: "center" }}>
          <Icon name="account-circle" size={44} color={colors.brandText} />
          <View style={{ flex: 1 }}>
            <T w="heavy" size={17}>{user?.name || "Practice profile"}</T>
            <T size={13} color={colors.muted}>{user?.phone ? "Number ending " + user.phone.slice(-4) : "Not signed in"}</T>
          </View>
        </Card>
        <Notice tone="warning" testID="account-unverified-notice">Unverified phone access (no OTP). Private pilot only — not a secure identity. Don’t store real private student data.</Notice>
        {expired ? (
          <Button testID="account-reenter-button" label="Re-enter number to resume" icon="login" onPress={() => finish("keep")} />
        ) : null}
        <Button testID="account-signout-button" kind="secondary" label="Sign out / switch number" icon="logout" busy={busy} onPress={begin} />
        <T size={11} color={colors.muted}>Signing out clears this phone’s session and cached question images. Server-acknowledged answers stay with the profile. Account deletion and verified identity arrive in a later approved phase.</T>
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
