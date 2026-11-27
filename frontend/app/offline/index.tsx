// The screen that opens without a line: what this phone keeps can be used here. Rapid Fire's Solo Sprint, and the
// results of the papers the student has finished (./results.tsx).
// Open to the account whose session was last confirmed on this phone, for 7 days (src/offline/door.tsx).
import React, { useEffect, useState } from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useAuth } from "@/src/auth";
import { uuid } from "@/src/api/client";
import { ARENA, HOME_ROUTE } from "@/src/arenaMode";
import { openBank, useBank } from "@/src/offline/bank";
import { Who, offlineIdentity } from "@/src/offline/identity";
import { useKeptRounds } from "@/src/offline/rounds";
import { OfflineShell } from "@/src/offline/Shell";
import { GoldTitle } from "@/src/rapid/arena";
import { ScopeSheet } from "@/src/rapid/ScopeSheet";
import { CARD_SECONDS, Pick, SHORT, cardCount, encodePicks, fitCount, getCardCount } from "@/src/rapid/scope";
import { Button, Card, Icon, Press, T } from "@/src/rapid/ui";
import { arena, rapidColors as colors, space } from "@/src/theme";

const NONE: Pick[] = [];

export default function OfflineHome() {
  return <OfflineShell testID="offline-home"><Home /></OfflineShell>;
}

function Home() {
  const router = useRouter(), { user, checkSession } = useAuth();
  const bank = useBank();
  const [who, setWho] = useState<Who | null | undefined>(undefined);
  const [sheet, setSheet] = useState(false), [checking, setChecking] = useState(false);
  const waiting = useKeptRounds(who?.uid);
  useEffect(() => {
    let alive = true;
    void openBank();
    (async () => { const mine = user ? { uid: user.id, name: user.name } : await offlineIdentity(); if (alive) setWho(mine); })();
    return () => { alive = false; };
  }, [user]);
  const leave = () => router.replace(user ? HOME_ROUTE : "/entry");
  const start = (picks: Pick[]) => {
    const n = fitCount(getCardCount(), cardCount(picks, bank.subjects));
    if (n) router.push({ pathname: "/offline/rapid", params: { picks: encodePicks(picks), n: String(n), r: uuid() } } as any);
  };
  const again = async () => { setChecking(true); try { await checkSession(); } finally { setChecking(false); } };

  return <>
    <View style={styles.top}>
      <Press testID="offline-back" onPress={leave} accessibilityLabel="Back" style={styles.close}><Icon name="arrow-left" size={22} color={colors.onSurface} /></Press>
      <View style={styles.flex}>
        <GoldTitle size={22} testID="offline-title">{ARENA ? "RAPID FIRE" : "BINA INTERNET"}</GoldTitle>
        <T testID="offline-sub" w="bold" size={12} color={arena.aqua}>{ARENA ? "Bina internet · Solo Sprint" : "Phone par rakha hua · Rapid Fire aur results"}</T>
      </View>
    </View>
    <ScrollView contentContainerStyle={styles.body} showsVerticalScrollIndicator={false}>
      {user ? <Card testID="offline-online" style={styles.card}>
        <T w="heavy" size={16}>Internet aa gaya</T>
        <T size={13} color={colors.muted}>Poora app khula hai: Rival, Friends, All India aur aapke saare tests.</T>
        <Button testID="offline-open-app" label="Poora app kholo" icon="arrow-right" onPress={() => router.replace(HOME_ROUTE)} />
      </Card> : null}
      {who === null ? <Card testID="offline-closed" style={styles.card}>
        <T w="heavy" size={16}>Pehle ek baar internet ke saath app kholo</T>
        <T size={13} color={colors.muted}>Bina internet khelne ke liye is phone par pichhle 7 din mein ek baar sign in hona zaroori hai.</T>
        <Button testID="offline-to-entry" kind="secondary" label="Sign in screen" onPress={() => router.replace("/entry")} />
      </Card> : who && !bank.ready ? <Card testID="offline-no-cards" style={styles.card}>
        <T w="heavy" size={16}>Cards abhi phone par nahi aaye</T>
        <T size={13} color={colors.muted}>Ek baar internet ke saath app kholo: cards apne aap phone par aa jayenge.</T>
      </Card> : who ? <Card testID="offline-rapid" style={styles.card}>
        <T testID="offline-cards-count" w="heavy" size={18}>{bank.cards.toLocaleString("en-IN")} cards phone par</T>
        <View style={styles.chips}>
          {bank.subjects.map((s) => <View key={s.name} style={styles.chip}><T w="bold" size={12} color={arena.text}>{`${SHORT[s.name] || s.name} · ${s.total.toLocaleString("en-IN")}`}</T></View>)}
        </View>
        <T size={13} color={colors.muted}>{`${CARD_SECONDS} second har card · 30, 50 ya 100 cards · seedha revision, bina animation.`}</T>
        <Button testID="offline-start" label="Chapters chuno aur khelo" icon="lightning-bolt" onPress={() => setSheet(true)} />
      </Card> : null}
      {/* Finished papers kept on this phone (src/offline/papers.ts). Papers are not part of the browser arena. */}
      {who && !ARENA ? <Card testID="offline-results" style={styles.card}>
        <T w="heavy" size={16}>Mere results</T>
        <T size={13} color={colors.muted}>Jo tests aap de chuke ho, unke score, answers aur solutions phone par rakhe hain.</T>
        <Button testID="offline-results-open" kind="secondary" icon="file-document-outline" label="Results dekho" onPress={() => router.push("/offline/results" as any)} />
      </Card> : null}
      {who && waiting ? <Card testID="offline-waiting" style={styles.card}>
        <T w="heavy" size={15}>{`${waiting} round phone par rakhe hain`}</T>
        <T size={13} color={colors.muted}>Internet aate hi apne aap bhej diye jayenge. Coins aur XP tab judenge.</T>
      </Card> : null}
      {user ? null : <Button testID="offline-retry" kind="secondary" icon="refresh" label="Internet dobara check karo" busy={checking} onPress={again} />}
      <T testID="offline-note" size={11} color={arena.faint} style={styles.center}>Rival, Friends, All India aur Cup ke liye internet chahiye: wahan saamne doosra student hota hai.</T>
    </ScrollView>
    <ScopeSheet visible={sheet} onClose={() => setSheet(false)} subjects={bank.subjects} value={NONE} onDone={start} action="START SOLO SPRINT" hint="Pick your subjects or chapters first" />
  </>;
}

const styles = StyleSheet.create({
  flex: { flex: 1 }, center: { textAlign: "center" },
  top: { flexDirection: "row", alignItems: "center", gap: space.md, paddingHorizontal: space.lg, minHeight: 56 },
  close: { width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center", backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.border },
  body: { padding: space.lg, gap: space.md },
  card: { gap: space.sm },
  chips: { flexDirection: "row", flexWrap: "wrap", gap: 6 },
  chip: { height: 30, paddingHorizontal: 10, borderRadius: 15, justifyContent: "center", backgroundColor: arena.panelHi, borderWidth: 1, borderColor: arena.rim },
});
