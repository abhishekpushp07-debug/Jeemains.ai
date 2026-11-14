import React, { useState } from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import { rf } from "@/src/api/client";
import { useAuth } from "@/src/auth";
import { T } from "@/src/components/ui";
import { useGameProfile } from "@/src/components/game";
import { playSfx } from "@/src/sfx";
import { arena, gemColors } from "@/src/theme";
import { GoldTitle, Panel, RaisedButton } from "@/src/rapid/arena";
import { CheerSquad } from "@/src/rapid/CheerSquad";
import { Pop } from "@/src/rapid/juice";
import { GemStrip, InnerScreen } from "@/src/rapid/parts";
import { PriceButton, canAfford, costText, haveText } from "@/src/rapid/StoreParts";
import { SquadItem, useInbox, useSquads } from "@/src/rapid/social";
import { squadFrames } from "@/src/rapid/squadArt";
import { ErrorBox, Sheet, withRapid } from "@/src/rapid/ui";

const TINT: Record<number, string> = { 1: arena.goldSoft, 2: `${gemColors.gold}33`, 3: `${gemColors.blue}33`, 4: `${gemColors.kohinoor}26` };

/** One squad: a peek at two of its dancers, what it brings, and Preview / Use / Buy. */
function SquadCard({ s, on, diamonds, busy, onPreview, onUse, onBuy }: { s: SquadItem; on: boolean; diamonds: Record<string, number>; busy: boolean; onPreview: () => void; onUse: () => void; onBuy: () => void }) {
  const status = on ? "Dancing for you ✓" : s.unlocked ? (s.bought ? "Bought with diamonds" : `Opened by ${s.wins} cup win${s.wins === 1 ? "" : "s"}`)
    : `Win ${s.need} more cup${s.need === 1 ? "" : "s"} to open${s.gems ? ", or buy it now" : ""}`;
  return <Pop delay={s.level * 60}>
    <Panel gold={on} testID={`squad-${s.id}`} style={styles.card}>
      <LinearGradient pointerEvents="none" colors={[TINT[s.level] || arena.goldSoft, arena.clear]} style={StyleSheet.absoluteFill} />
      <View style={styles.row}>
        <View style={styles.peek}>
          <Image source={squadFrames(s.level, "a")[0]} style={[styles.peekBack, !s.unlocked && styles.locked]} contentFit="contain" />
          <Image source={squadFrames(s.level, "c")[0]} style={[styles.peekFront, !s.unlocked && styles.locked]} contentFit="contain" />
        </View>
        <View style={styles.flex}>
          <T w="heavy" size={11} color={arena.aqua} style={styles.spaced}>LEVEL {s.level}</T>
          <GoldTitle size={20} testID={`squad-${s.id}-title`}>{s.title}</GoldTitle>
          <T w="bold" size={12} color={arena.text}>{s.body}</T>
          <T testID={`squad-${s.id}-status`} w="heavy" size={12} color={on ? arena.online : s.unlocked ? arena.gold : arena.muted}>{status}</T>
        </View>
      </View>
      <View style={styles.row}>
        <RaisedButton testID={`squad-${s.id}-preview`} tone="wine" glyph="play" label="Preview" onPress={onPreview} style={styles.flex} />
        <View style={styles.flex}>
          {on ? <View testID={`squad-${s.id}-on`} style={styles.on}><T w="heavy" size={13} color={arena.badgeInk}>IN USE ✓</T></View>
            : s.unlocked ? <RaisedButton testID={`squad-${s.id}-use`} label="USE" busy={busy} onPress={onUse} />
            : s.gems ? <PriceButton testID={`squad-${s.id}-buy`} it={{ id: s.id, price: 0, gems: s.gems }} wallet={{ diamonds }} busy={busy} onPress={onBuy} /> : null}
        </View>
      </View>
    </Panel>
  </Pop>;
}

/** Cheer Squads: every level opens with more Knockout Cup wins, or buy one early with diamonds. Pick the one that dances in your Trophy Cabinet. */
function Squads() {
  const uid = useAuth().user?.id || "";
  const q = useSquads(uid), d = q.data, me = useInbox()?.me;
  const reloadProfile = useGameProfile(uid).reload; // the diamonds at the top of the arena follow a purchase
  const [busy, setBusy] = useState(""), [error, setError] = useState(""), [preview, setPreview] = useState<SquadItem | null>(null), [buying, setBuying] = useState<SquadItem | null>(null);
  const act = async (s: SquadItem, path: "buy" | "equip") => {
    setBusy(s.id); setError("");
    try { await rf(`/squads/${path}`, uid, { method: "POST", body: { id: s.id } }); q.reload(); return true; }
    catch (e: any) { setError(e.message); return false; }
    finally { setBusy(""); }
  };
  const price = buying?.gems ? { id: buying.id, price: 0, gems: buying.gems } : null, wallet = { diamonds: d?.diamonds };
  // Bought: the new squad dances straight away.
  const buy = async () => { if (buying && await act(buying, "buy")) { playSfx("coin"); reloadProfile(); setPreview(buying); setBuying(null); } };
  return <InnerScreen testID="squads-screen" title="Cheer Squads" sub="More cup wins, a more glamorous squad">
    {!d ? (q.error ? <ErrorBox testID="squads-error" error={q.error} retry={q.reload} /> : <ActivityIndicator testID="squads-loading" color={arena.aqua} size="large" />) : <>
      <Panel gold testID="squads-wallet" style={styles.wallet}>
        <T w="heavy" size={12} color={arena.gold} style={[styles.spaced, styles.center]}>YOU HAVE WON {d.cups_won} CUP{d.cups_won === 1 ? "" : "S"}</T>
        <GemStrip diamonds={d.diamonds} size={30} />
        <T w="bold" size={11} color={arena.muted} style={styles.center}>Cup champions and runners-up win diamonds. Cup Night pays the most.</T>
      </Panel>
      <ErrorBox testID="squads-action-error" error={buying ? "" : error} />
      {d.items.map((s) => <SquadCard key={s.id} s={s} on={d.equipped === s.id} diamonds={d.diamonds} busy={busy === s.id}
        onPreview={() => setPreview(s)} onUse={() => act(s, "equip")} onBuy={() => { setError(""); setBuying(s); }} />)}
    </>}
    {preview ? <CheerSquad visible name={me?.name || "Champion"} avatar={me?.avatar} frame={me?.frame} crown={me?.crown?.won ? me.crown : { won: Math.max(1, d?.cups_won || 0), real: 0 }}
      level={preview.level} title={preview.title} onClose={() => setPreview(null)} /> : null}
    <Sheet visible={!!buying} onClose={() => !busy && setBuying(null)} testID="squad-buy-sheet">
      <T w="heavy" size={11} color={arena.aqua} style={styles.spaced}>LEVEL {buying?.level} · UNLOCK EARLY</T>
      <GoldTitle size={24} testID="squad-buy-title">{buying?.title}</GoldTitle>
      <T testID="squad-buy-why" w="bold" size={13} color={arena.text}>Skip the {buying?.need} cup win{buying?.need === 1 ? "" : "s"} still needed. They dance for every crown you win from today.</T>
      <T testID="squad-buy-cost" w="heavy" size={14} color={arena.gold}>{costText(price)} · You have {haveText(price, wallet)}</T>
      <T size={12} color={arena.muted}>Uses diamonds won in Knockout Cups and Phoenix streaks. No real money is charged. Cup wins still open every squad for free.</T>
      <ErrorBox testID="squad-buy-error" error={error} />
      <RaisedButton testID="squad-buy-confirm" glyph="diamond-stone" label="UNLOCK WITH DIAMONDS" sub={costText(price)} height={58} busy={!!busy} disabled={!price || !canAfford(price, wallet)} onPress={buy} />
      <RaisedButton testID="squad-buy-cancel" tone="wine" label="Not now" disabled={!!busy} onPress={() => setBuying(null)} />
    </Sheet>
  </InnerScreen>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, center: { textAlign: "center" }, spaced: { letterSpacing: 1.5 },
  row: { flexDirection: "row", alignItems: "center", gap: 10 },
  wallet: { padding: 12, gap: 8 },
  card: { padding: 12, gap: 10, overflow: "hidden" },
  peek: { width: 96, height: 112 },
  peekBack: { position: "absolute", left: 0, top: 0, width: 70, height: 104 },
  peekFront: { position: "absolute", right: 0, bottom: 0, width: 72, height: 96 },
  locked: { opacity: 0.45 },
  on: { height: 52, borderRadius: 18, alignItems: "center", justifyContent: "center", backgroundColor: arena.gold, borderWidth: 1.5, borderColor: arena.goldDeep },
});

export default withRapid(Squads);
