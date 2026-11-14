import React, { useCallback, useEffect, useRef, useState } from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import { rf } from "@/src/api/client";
import { useAuth } from "@/src/auth";
import { T } from "@/src/components/ui";
import { Avatar } from "@/src/components/Entry";
import { arena } from "@/src/theme";
import { Alive, GameIcon, GameIconName } from "@/src/rapid/Art";
import { GoldTitle, Panel, RaisedButton, SectionTitle } from "@/src/rapid/arena";
import { STANDS, nightState, useServerNow } from "@/src/rapid/CupNight";
import { LiveDot, Pop } from "@/src/rapid/juice";
import { Face, InnerScreen, Note } from "@/src/rapid/parts";
import { ErrorBox, withRapid } from "@/src/rapid/ui";
import { NightCup, countdown, dismissNotice, go, refreshInbox, useCupNight, useInbox } from "@/src/rapid/social";

const STEPS: [GameIconName, string, string][] = [
  ["chest", "Doors open", "Take your seat any time in the hour before the start."],
  ["swords", "The draw", "On the dot, everybody is drawn into cups of up to 16. Practice rivals fill empty seats."],
  ["trophy", "Lift the crown", "Win every round, 15 cards each, and the crown sits next to your name."],
];

/** One of tonight's cups: who is in, the round being played, or its champion. Watch it live, or open yours. */
function CupRow({ c, busy, onOpen }: { c: NightCup; busy: boolean; onOpen: () => void }) {
  return <View testID={`night-cup-${c.no}`} style={[styles.cup, c.mine && styles.cupMine]}>
    <View style={styles.cupNo}><T w="heavy" size={15} color={arena.badgeInk}>#{c.no}</T></View>
    <View style={styles.flex}>
      <T w="heavy" size={14} color={arena.text} numberOfLines={1}>{c.mine ? "Your cup" : `Cup ${c.no}`} · {c.size} players</T>
      {c.champion ? <View style={styles.inline}><Avatar icon={c.champion.avatar} frame={c.champion.frame} size={22} /><T w="bold" size={12} color={arena.gold} numberOfLines={1} style={styles.shrink}>{c.champion.you ? "You won it!" : `${c.champion.name} won it`}</T></View>
        : <View style={styles.inline}>{c.status === "live" ? <LiveDot size={7} /> : null}<T w="bold" size={12} color={c.status === "live" ? arena.danger : arena.muted} numberOfLines={1}>{c.status === "live" ? `${c.round || "Live"} now` : "Starting"} · {c.real_players} real</T></View>}
    </View>
    <RaisedButton testID={`night-cup-${c.no}-open`} tone={c.mine ? "teal" : "wine"} height={44} glyph={c.mine ? undefined : "eye"} label={c.mine ? "Open" : "Watch"} busy={busy} onPress={onOpen} style={styles.cupBtn} />
  </View>;
}

/**
 * Cup Night: a free Open Cup every day at 8 pm IST. Seats open an hour before; at 8 pm sharp everybody who joined is
 * drawn into cups of up to 16 and the first round starts for all of them together. After that, every cup can be watched.
 */
function Night() {
  const router = useRouter(), uid = useAuth().user?.id || "";
  const q = useCupNight(uid), n = q.data, reload = q.reload;
  const now = useServerNow(n);
  const [busy, setBusy] = useState(""), [error, setError] = useState("");
  const s = n ? nightState(n, now) : null, key = s?.key;
  useFocusEffect(useCallback(() => {
    reload();
    const iv = setInterval(reload, 5000);
    return () => clearInterval(iv);
  }, [reload]));
  useEffect(() => { if (key) reload(); }, [key]); // eslint-disable-line react-hooks/exhaustive-deps
  // 8 pm: your cup is drawn, so go straight to its bracket (and from there into your first match).
  const sent = useRef("");
  const mine = n?.cups.find((c) => c.mine);
  // On this screen the 7:55 pm reminder has done its job.
  const reminder = useInbox()?.notices.find((x) => x.kind === "cup_night")?.id;
  useEffect(() => { if (reminder && uid) dismissNotice(uid, reminder).then(() => refreshInbox(uid)).catch(() => {}); }, [reminder, uid]);
  useEffect(() => {
    if (key === "mine" && mine && sent.current !== mine.id) { sent.current = mine.id; router.push(go.cup(mine.id)); }
  }, [key, mine?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const act = async (what: "join" | "leave") => {
    setBusy(what); setError("");
    try { await rf(`/cups/night/${what}`, uid, { method: "POST", body: {} }); reload(); refreshInbox(uid); }
    catch (e: any) { setError(e.message); }
    finally { setBusy(""); }
  };
  const open = async (c: NightCup) => {
    if (c.mine) { router.push(go.cup(c.id)); return; }
    setBusy(c.id); setError("");
    try { const got = await rf<any>("/cups/watch", uid, { method: "POST", body: { code: c.code } }); router.push(go.cup(got.id)); }
    catch (e: any) { setError(e.message); }
    finally { setBusy(""); }
  };

  const headline: Record<string, string> = { soon: "DOORS OPEN IN", doors: "STARTS IN", in: "STARTS IN", drawing: "DRAWING THE CUPS", mine: "LIVE NOW", live: "LIVE NOW", over: "NEXT CUP NIGHT IN" };
  const footer = !n || !s ? null
    : s.key === "doors" ? <RaisedButton testID="night-join" icon="trophy" height={62} streak label="JOIN CUP NIGHT" sub={`${n.label} · ${n.cards} cards a match · free`} busy={busy === "join"} onPress={() => act("join")} />
    : s.key === "in" ? <RaisedButton testID="night-leave" tone="wine" label="Leave Cup Night" busy={busy === "leave"} onPress={() => act("leave")} />
    : s.key === "mine" && mine ? <RaisedButton testID="night-my-cup" icon="trophy" height={62} streak label="GO TO MY CUP" sub="Your match is waiting" onPress={() => router.push(go.cup(mine.id))} />
    : <RaisedButton testID="night-wait" tone="wine" height={56} disabled busy={s.key === "drawing"}
      label={s.key === "soon" ? `DOORS OPEN AT ${n.doors_label.toUpperCase()}` : s.key === "drawing" ? "DRAWING THE CUPS…" : `NEXT ONE AT ${n.time_label.toUpperCase()}`} />;

  return <InnerScreen testID="night-screen" title="Cup Night" sub={n ? `Every day · ${n.time_label} IST` : "Every day · 8 pm"} footer={footer}>
    {!n || !s ? (q.error ? <ErrorBox testID="night-error" error={q.error} retry={q.reload} /> : <ActivityIndicator testID="night-loading" color={arena.aqua} size="large" />) : <>
      <View testID="night-hero" style={styles.hero}>
        <Image source={STANDS} style={StyleSheet.absoluteFill} contentFit="cover" contentPosition="center" />
        <LinearGradient pointerEvents="none" colors={[arena.clear, arena.shade, arena.scrim]} locations={[0, 0.45, 1]} style={StyleSheet.absoluteFill} />
        <View style={styles.heroBody}>
          <Alive kind="breathe"><GameIcon name="trophy" size={70} /></Alive>
          <View style={styles.inline}>{s.key === "mine" || s.key === "live" || s.key === "drawing" ? <LiveDot /> : null}
            <T testID="night-headline" w="heavy" size={12} color={arena.aqua} style={styles.spaced}>{headline[s.key]}</T></View>
          {s.left > 0 ? <T testID="night-countdown" w="heavy" size={46} color={arena.gold} style={styles.count}>{countdown(s.left)}</T>
            : <GoldTitle size={30} center testID="night-countdown">{s.key === "drawing" ? "Get ready…" : "The Colosseum is roaring"}</GoldTitle>}
          <T w="bold" size={12} color={arena.text} style={styles.center}>{n.label} · up to {n.seats} per cup · starts {n.time_label} sharp</T>
        </View>
      </View>
      {s.key === "in" ? <Pop><Panel gold testID="night-joined" style={styles.joined}><GameIcon name="flame" size={36} /><View style={styles.flex}>
        <T w="heavy" size={15} color={arena.gold}>You’re in! Stay close.</T>
        <T w="bold" size={12} color={arena.text}>At {n.time_label} your cup is drawn and your first match starts by itself.</T>
      </View></Panel></Pop> : null}
      {n.missed && !mine ? <Panel testID="night-missed" style={styles.joined}><GameIcon name="swords" size={36} /><View style={styles.flex}>
        <T w="heavy" size={15} color={arena.gold}>You were still in another cup</T>
        <T w="bold" size={12} color={arena.text}>At {n.time_label} your other cup was still on, so tonight’s draw went ahead without you. Watch tonight’s cups below, and take a seat again tomorrow.</T>
      </View></Panel> : null}
      <ErrorBox testID="night-action-error" error={error} />

      <SectionTitle title={`Who’s in (${n.count})`} />
      <Panel flat testID="night-people" style={styles.people}>
        {n.friends.length ? <View style={styles.faces}>{n.friends.map((f) => <View key={f.pid} testID={`night-friend-${f.pid}`} style={styles.friend}>
          <Face p={f} size={44} onPress={() => router.push(go.player(f.pid))} /><T w="heavy" size={10.5} color={arena.text} numberOfLines={1}>{f.name}</T>
        </View>)}</View> : null}
        <T testID="night-count" w="bold" size={12} color={arena.muted} style={styles.center}>
          {n.count ? `${n.count} student${n.count === 1 ? "" : "s"} tonight${n.friends.length ? ` · ${n.friends.length} of your friends` : ""}` : s.key === "soon" || s.key === "doors" ? "Nobody yet. Take the first seat and bring your friends!" : "Nobody took a seat tonight."}
        </T>
      </Panel>

      {n.cups.length ? <>
        <SectionTitle title={`Tonight’s cups (${n.cups.length})`} />
        {n.cups.map((c) => <CupRow key={c.id} c={c} busy={busy === c.id} onOpen={() => open(c)} />)}
      </> : null}

      <SectionTitle title="How Cup Night works" />
      {STEPS.map(([icon, title, body], i) => <View key={title} testID={`night-step-${i + 1}`} style={styles.step}>
        <GameIcon name={icon} size={40} />
        <View style={styles.flex}>
          <T w="heavy" size={14} color={arena.gold}>{i === 0 ? `${title} · ${n.doors_label}` : i === 1 ? `${title} · ${n.time_label}` : title}</T>
          <T w="bold" size={12} color={arena.muted}>{body}</T>
        </View>
      </View>)}
      <Note>Free to play. Every match is {n.cards} Rapid Fire cards on {n.label}. Leaving a match counts as a loss.</Note>
    </>}
  </InnerScreen>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, center: { textAlign: "center" }, spaced: { letterSpacing: 2 }, shrink: { flexShrink: 1 },
  inline: { flexDirection: "row", alignItems: "center", gap: 6 },
  hero: { minHeight: 300, borderRadius: 24, overflow: "hidden", borderWidth: 2, borderColor: arena.gold, borderBottomWidth: 5, borderBottomColor: arena.goldDeep, justifyContent: "flex-end" },
  heroBody: { alignItems: "center", gap: 4, paddingHorizontal: 16, paddingBottom: 18, paddingTop: 80 },
  count: { letterSpacing: 1 },
  joined: { flexDirection: "row", alignItems: "center", gap: 12, padding: 14 },
  people: { padding: 12, gap: 10 }, faces: { flexDirection: "row", flexWrap: "wrap", gap: 10, justifyContent: "center" }, friend: { width: 64, alignItems: "center", gap: 3 },
  cup: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 64, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 18, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim },
  cupMine: { borderColor: arena.gold, backgroundColor: arena.panelHi },
  cupNo: { width: 40, height: 40, borderRadius: 20, alignItems: "center", justifyContent: "center", backgroundColor: arena.gold, borderWidth: 1.5, borderColor: arena.goldDeep },
  cupBtn: { width: 96 },
  step: { flexDirection: "row", alignItems: "center", gap: 12, padding: 12, borderRadius: 18, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim },
});

export default withRapid(Night);
