import React, { useState } from "react";
import { StyleSheet, View } from "react-native";
import { rf } from "@/src/api/client";
import { Icon, T } from "@/src/components/ui";
import { GameProfile } from "@/src/components/game";
import { playSfx } from "@/src/sfx";
import { arena } from "@/src/theme";
import { Alive, GameIcon, Gem, GemColor } from "./Art";
import { Panel } from "./arena";
import { Jelly } from "./juice";
import { Bar } from "./parts";
import { ErrorBox } from "./ui";

type Rush = NonNullable<GameProfile["rush"]>;

function Chest({ s }: { s: Rush["steps"][number] }) {
  const ready = s.done && !s.claimed;
  return <>
    {ready ? <Alive kind="hop" once><GameIcon name="chest" size={40} /></Alive> : <GameIcon name="chest" size={40} style={s.done ? undefined : styles.locked} />}
    <T w="heavy" size={10.5} color={s.done ? arena.text : arena.muted} numberOfLines={1}>{s.chest}</T>
    <View style={styles.line}>
      <GameIcon name="coin" size={14} /><T w="heavy" size={10.5} color={arena.gold}>{s.coins}</T>
      {s.bonus === "freeze" ? <Icon name="snowflake" size={13} color={arena.aqua} /> : s.bonus ? <Gem color={s.bonus as GemColor} size={14} /> : null}
    </View>
    {s.claimed ? <T w="heavy" size={10} color={arena.gold}>Opened ✓</T>
      : ready ? <View style={styles.open}><T w="heavy" size={10} color={arena.badgeInk}>OPEN</T></View>
      : <View style={styles.line}><Gem color="red" size={12} dim /><T w="bold" size={10} color={arena.muted}>{s.at}</T></View>}
  </>;
}

/** Diamond Rush: every diamond won today moves the track, and each milestone opens a chest. Starts again at midnight (IST). */
export function RushTrack({ uid, rush, onClaimed }: { uid: string; rush?: Rush; onClaimed: () => void }) {
  const [busy, setBusy] = useState(0), [error, setError] = useState("");
  if (!rush?.steps.length) return null;
  const goal = rush.steps[rush.steps.length - 1].at;
  const claim = async (at: number) => {
    setBusy(at); setError("");
    try { await rf("/rush/claim", uid, { method: "POST", body: { at } }); playSfx("coin"); onClaimed(); }
    catch (e: any) { setError(e.message); }
    finally { setBusy(0); }
  };
  return <Panel gold testID="rf-rush" style={styles.box}>
    <View style={styles.head}>
      <Gem color="red" size={36} />
      <View style={styles.flex}>
        <T w="heavy" size={16} color={arena.gold}>Diamond Rush</T>
        <T testID="rf-rush-points" w="bold" size={11} color={arena.aqua}>{rush.points} diamond{rush.points === 1 ? "" : "s"} won today · resets at midnight</T>
      </View>
    </View>
    <Bar value={rush.points / goal} color={arena.gold} />
    <View style={styles.steps}>
      {rush.steps.map((s) => (s.done && !s.claimed
        ? <Jelly key={s.at} testID={`rf-rush-claim-${s.at}`} accessibilityLabel={`Open the ${s.chest} chest`} disabled={!!busy} onPress={() => claim(s.at)} style={[styles.step, styles.ready]}><Chest s={s} /></Jelly>
        : <View key={s.at} testID={`rf-rush-step-${s.at}`} style={styles.step}><Chest s={s} /></View>))}
    </View>
    <ErrorBox testID="rf-rush-error" error={error} />
  </Panel>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, box: { padding: 14, gap: 10 }, head: { flexDirection: "row", alignItems: "center", gap: 10 },
  steps: { flexDirection: "row", gap: 6 },
  step: { flex: 1, minWidth: 0, minHeight: 104, alignItems: "center", justifyContent: "center", gap: 2, paddingVertical: 6, borderRadius: 14, backgroundColor: arena.panelEdge, borderWidth: 1.5, borderColor: arena.rim },
  ready: { borderColor: arena.gold, backgroundColor: arena.panelHi }, locked: { opacity: 0.4 },
  line: { flexDirection: "row", alignItems: "center", gap: 2 },
  open: { paddingHorizontal: 8, height: 18, borderRadius: 9, justifyContent: "center", backgroundColor: arena.badge },
});
