import React, { useState } from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { nameOf, useAuth } from "@/src/auth";
import { Notice, T } from "@/src/components/ui";
import { Glyph } from "@/src/components/Glyph";
import { DCard, DSheet, GroupList, ListRow, Pill, ScreenHeader } from "@/src/components/design";
import { colors, space } from "@/src/theme";
import { ARENA, HOME_ROUTE } from "@/src/arenaMode";
import { NameSheet } from "@/src/components/series/NameSheet";
import { useChosenName } from "@/src/profileName";
import { useBank } from "@/src/offline/bank";
import { useKeptResults } from "@/src/offline/papers";

export default function Account() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user, signOut, pendingDraftCount, expired } = useAuth();
  const [sheet, setSheet] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  // The name the student wrote for themselves ("" = none yet): the one every leaderboard and Rapid Fire show.
  const chosen = useChosenName(user?.id);
  const [naming, setNaming] = useState(false);
  const [kept, setKept] = useState<string>();
  const mine = kept ?? chosen;
  const bank = useBank(); // Rapid Fire's cards kept on this phone (src/offline/bank.ts)
  const keptRows = useKeptResults(); // finished papers kept on this phone (src/offline/papers.ts)

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
      <ScreenHeader testID="account-header" backTestID="account-back-button" title="Account" eyebrow="JEELIVE profile" onBack={() => router.canGoBack() ? router.back() : router.replace(HOME_ROUTE)} />
      <ScrollView contentContainerStyle={{ padding: space.lg, paddingTop: space.xs, paddingBottom: insets.bottom + space.xxl, gap: space.xl }}>
        <DCard testID="account-profile" style={styles.profile}>
          <View style={styles.avatar}><Glyph name="account-outline" size={28} color={colors.onSurface} stroke={1.4} /></View>
          <View style={{ flex: 1, gap: 2 }}>
            <T testID="account-name" w="heavy" size={18}>{mine || (user ? nameOf(user) : "Practice profile")}</T>
            <T testID="account-phone-summary" size={13} color={colors.muted}>{user?.phone ? "Number ending " + user.phone.slice(-4) : "Signed-in JEELIVE profile"}</T>
          </View>
        </DCard>
        {user && !expired ? <GroupList title="Profile" testID="account-group-profile">
          <ListRow testID="account-name-button" icon="account-edit-outline" label={mine ? "Change your name" : "Add your name"}
            sub={mine ? "Shown on leaderboards and in Rapid Fire" : "Leaderboards and Rapid Fire show “Learner” until you add one"} onPress={() => setNaming(true)} />
        </GroupList> : null}
        <Notice testID="account-pin-notice">Sign in with your mobile number and 4-digit PIN. A PIN does not verify phone ownership; no OTP is sent.</Notice>
        {expired ? <Pill testID="account-reenter-button" size="lg" label="Sign in again" icon="login" onPress={() => finish("keep")} /> : null}
        <GroupList title="Security" testID="account-group-security">
          {user?.role === "student" ? <ListRow testID="account-change-pin-button" icon="lock-reset" label="Change PIN" sub="Set a new 4-digit PIN" onPress={() => router.push("/change-pin")} /> : null}
          <ListRow testID="account-pin-help-button" icon="help-circle-outline" label="PIN & account access help" onPress={() => router.push("/forgot-pin")} />
        </GroupList>
        {user && !expired ? <GroupList title="Bina internet" testID="account-group-offline">
          <ListRow testID="account-offline-rapid" icon="lightning-bolt-outline" label="Rapid Fire bina internet"
            sub={bank.ready ? `${bank.cards.toLocaleString("en-IN")} cards phone par${bank.busy ? " · aur aa rahe hain" : " · ready"}` : bank.busy ? "Cards phone par aa rahe hain…" : "Cards abhi phone par nahi aaye"}
            onPress={() => router.push("/offline" as any)} />
          {/* Papers and their results are not part of the browser arena. */}
          {ARENA ? null : <ListRow testID="account-offline-results" icon="file-document-outline" label="Results bina internet"
            sub={!keptRows.length ? "Aapke diye hue tests ke results apne aap phone par aate hain"
              : `${keptRows.length} results phone par · ${keptRows.every((r) => r.kept >= r.pictures) ? "solutions ke saath" : `${keptRows.filter((r) => r.kept < r.pictures).length} ki pictures abhi baaki`}`}
            onPress={() => router.push("/offline/results" as any)} />}
        </GroupList> : null}
        <GroupList title="Privacy" testID="account-group-privacy">
          <ListRow testID="account-privacy" icon="shield-check-outline" label="Privacy policy & support" onPress={() => router.push("/privacy")} />
          {/* Papers and their images are not part of the browser arena. */}
          {ARENA ? null : <ListRow testID="account-loading-performance" icon="speedometer" label="Loading performance" sub="Check how fast papers and images load" onPress={() => router.push("/performance")} />}
        </GroupList>
        <GroupList title="Account" testID="account-group-account">
          <ListRow testID="account-deletion" icon="account-remove-outline" label="Delete account" sub="Erase your account and game data" onPress={() => router.push("/delete-account")} />
          <ListRow testID="account-signout-button" icon="logout" label="Sign out" danger busy={busy} onPress={begin} />
        </GroupList>
        <T testID="account-signout-note" size={12} color={colors.custom_eyebrow}>Signing out clears this device’s session and cached question images. Saved answers and results stay with your existing JEELIVE account.</T>
      </ScrollView>
      <DSheet visible={sheet !== null} onClose={() => setSheet(null)} testID="signout-drafts-sheet" title="Unsynced work on this phone">
        <T size={13} color={colors.muted}>{sheet} attempt{sheet === 1 ? "" : "s"} still have answers waiting for server acknowledgement. They are not submitted or scored.</T>
        <Pill testID="signout-stay" label="Stay signed in" onPress={() => setSheet(null)} />
        <Pill testID="signout-keep-drafts" kind="outline" label="Keep drafts & sign out" onPress={() => finish("keep")} />
        <Pill testID="signout-discard-drafts" kind="danger" label="Discard drafts & sign out" onPress={() => finish("discard")} />
      </DSheet>
      <NameSheet visible={naming} current={mine ?? ""} onClose={() => setNaming(false)} onSaved={(name) => { setNaming(false); setKept(name); }} />
    </View>
  );
}

const styles = StyleSheet.create({
  profile: { flexDirection: "row", gap: space.md, alignItems: "center", padding: 20 },
  avatar: { width: 56, height: 56, borderRadius: 28, backgroundColor: colors.custom_cardRaised, borderWidth: 1, borderColor: colors.custom_cardLine, alignItems: "center", justifyContent: "center" },
});
