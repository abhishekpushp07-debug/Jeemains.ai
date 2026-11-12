import React, { useState } from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { Icon, Notice, T } from "@/src/components/ui";
import { DCard, DSheet, GroupList, ListRow, Pill, ScreenHeader } from "@/src/components/design";
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
      <ScreenHeader testID="account-header" backTestID="account-back-button" title="Account" eyebrow="JEECIRCLE profile" onBack={() => router.canGoBack() ? router.back() : router.replace("/(tabs)")} />
      <ScrollView contentContainerStyle={{ padding: space.lg, paddingTop: space.xs, paddingBottom: insets.bottom + space.xxl, gap: space.xl }}>
        <DCard testID="account-profile" style={styles.profile}>
          <View style={styles.avatar}><Icon name="account" size={30} color={colors.onSurface} /></View>
          <View style={{ flex: 1, gap: 2 }}>
            <T testID="account-name" w="heavy" size={18}>{user?.name || "Practice profile"}</T>
            <T testID="account-phone-summary" size={13} color={colors.muted}>{user?.phone ? "Number ending " + user.phone.slice(-4) : "Signed-in JEECIRCLE profile"}</T>
          </View>
        </DCard>
        <Notice testID="account-pin-notice">Sign in with your mobile number and 4-digit PIN. A PIN does not verify phone ownership; no OTP is sent.</Notice>
        {expired ? <Pill testID="account-reenter-button" size="lg" label="Sign in again" icon="login" onPress={() => finish("keep")} /> : null}
        <GroupList title="Security" testID="account-group-security">
          {user?.role === "student" ? <ListRow testID="account-change-pin-button" icon="lock-reset" label="Change PIN" sub="Set a new 4-digit PIN" onPress={() => router.push("/change-pin")} /> : null}
          <ListRow testID="account-pin-help-button" icon="help-circle-outline" label="PIN & account access help" onPress={() => router.push("/forgot-pin")} />
        </GroupList>
        <GroupList title="Privacy" testID="account-group-privacy">
          <ListRow testID="account-privacy" icon="shield-check-outline" label="Privacy policy & support" onPress={() => router.push("/privacy")} />
          <ListRow testID="account-loading-performance" icon="speedometer" label="Loading performance" sub="Check how fast papers and images load" onPress={() => router.push("/performance")} />
        </GroupList>
        <GroupList title="Account" testID="account-group-account">
          <ListRow testID="account-deletion" icon="account-remove-outline" label="Delete account" sub="How account deletion works" onPress={() => router.push("/delete-account")} />
          <ListRow testID="account-signout-button" icon="logout" label="Sign out" danger busy={busy} onPress={begin} />
        </GroupList>
        <T testID="account-signout-note" size={12} color={colors.custom_eyebrow}>Signing out clears this device’s session and cached question images. Saved answers and results stay with your existing JEECIRCLE account.</T>
      </ScrollView>
      <DSheet visible={sheet !== null} onClose={() => setSheet(null)} testID="signout-drafts-sheet" title="Unsynced work on this phone">
        <T size={13} color={colors.muted}>{sheet} attempt{sheet === 1 ? "" : "s"} still have answers waiting for server acknowledgement. They are not submitted or scored.</T>
        <Pill testID="signout-stay" label="Stay signed in" onPress={() => setSheet(null)} />
        <Pill testID="signout-keep-drafts" kind="outline" label="Keep drafts & sign out" onPress={() => finish("keep")} />
        <Pill testID="signout-discard-drafts" kind="danger" label="Discard drafts & sign out" onPress={() => finish("discard")} />
      </DSheet>
    </View>
  );
}

const styles = StyleSheet.create({
  profile: { flexDirection: "row", gap: space.md, alignItems: "center", padding: 20 },
  avatar: { width: 56, height: 56, borderRadius: 28, backgroundColor: colors.brandTertiary, borderWidth: 1, borderColor: colors.brandLine, alignItems: "center", justifyContent: "center" },
});
