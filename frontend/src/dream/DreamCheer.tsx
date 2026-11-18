// "Dream Unlocked": the first time a mock crosses a dream college's target marks, the Kohinoor Legends (Rapid Fire's
// level 4 Cheer Squad) run a 30-second routine to their own cheer track: the banner drops into the holders' hands,
// the squad shouts on the beat, fireworks and stage lights, confetti cannons on the drop and the finale.
// Skip is always there while it plays; at the end, Continue or watch it again. Plays once per dream college.
import React, { useEffect, useRef, useState } from "react";
import { Modal, Platform, ScrollView, StyleSheet, View, useWindowDimensions } from "react-native";
import * as Haptics from "expo-haptics";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import { useIsFocused } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Animated, { Easing, Extrapolation, SharedValue, cancelAnimation, interpolate, useAnimatedStyle, useReducedMotion, useSharedValue, withDelay, withRepeat, withSpring, withTiming } from "react-native-reanimated";
import type { AudioPlayer } from "expo-audio";
import { RF_BASE } from "@/src/api/client";
import { useAuth } from "@/src/auth";
import { Press, T } from "@/src/components/ui";
import { Glyph } from "@/src/components/Glyph";
import { loadTrack, playSfx } from "@/src/sfx";
import { arena, cheer, fx, gemColors } from "@/src/theme";
import { GoldTitle, RaisedButton } from "@/src/rapid/arena";
import { CheerBanner, CheerLevel, Pole } from "@/src/rapid/CheerBanner";
import { Beam, Burst, Dancer } from "@/src/rapid/CheerSquad";
import { Confetti, Pop, rnd, Twinkles } from "@/src/rapid/juice";
import { SQUAD_GEO, prefetchSquad, squadFrames } from "@/src/rapid/squadArt";
import { Diamond } from "@/src/rank/Diamond";
import { CheerWin, claimCheer, DreamExam, EXAM_NAME, FULL, useDreams } from "./store";
import { BEAT, COUNTS, HOLD, HOLD_HOP, LEAD, LEAD_HOP, LEAD_SPIN, ROUTINE_MS, chantsFor } from "./routine";
import { useDreamShare } from "./DreamShare";

const ARENA = require("../../assets/arena/bg_colosseum.webp");
const TRACK = `${RF_BASE}/art/dream_cheer.m4a`;
const KOHINOOR = 4, LOAD_MS = 4000;
const K = cheer[4];
const SPARKLE = [gemColors.kohinoor, K.foil[1], arena.gold, fx.ice, K.glitter[1], gemColors.blue, fx.white] as const;
const BEAMS = [gemColors.kohinoor, K.foil[1], fx.ice, arena.gold];
// Without the track (still loading, blocked, or silent) a few effects mark the big moments instead.
const ACCENT: Record<number, string> = { 0: "levelup", 8: "go", 16: "correct", 24: "tick", 28: "tick", 32: "combo", 40: "correct", 48: "coin", 56: "tick", 60: "win" };

/** Opens the celebration when this screen (in focus) shows a mock that crossed a dream for the first time. */
export function DreamCheerHost({ exam, mockId }: { exam: DreamExam; mockId?: string }) {
  const s = useDreams();
  const focused = useIsFocused();
  const { user } = useAuth();
  const [win, setWin] = useState<CheerWin | null>(null);
  useEffect(() => {
    if (!focused || win) return;
    const got = claimCheer(exam, mockId);
    if (got) setWin(got);
  }, [s, focused, exam, mockId, win]);
  return win ? <DreamCheer win={win} exam={exam} name={user?.name || "Champion"} onClose={() => setWin(null)} /> : null;
}

/** One confetti piece shot from a cannon: flies up with air drag, then flutters down. */
function Shot({ i, x0, y0, dir, v, g, color }: { i: number; x0: number; y0: number; dir: number; v: number; g: number; color: string }) {
  const t = useSharedValue(0);
  const a = (0.05 + rnd(i, 1) * 0.3) * dir, sp = v * (0.72 + rnd(i, 2) * 0.4), vx = Math.sin(a) * sp, vy = -Math.cos(a) * sp;
  const spin = 360 + rnd(i, 3) * 900, size = 7 + rnd(i, 4) * 7, drag = 1.5, D = 2.8;
  useEffect(() => { t.value = withDelay(rnd(i, 5) * 140, withTiming(1, { duration: D * 1000, easing: Easing.linear })); }, [t, i]);
  const style = useAnimatedStyle(() => {
    const T = t.value * D, e = 1 - Math.exp(-drag * T);
    return { opacity: t.value === 0 ? 0 : t.value > 0.8 ? (1 - t.value) / 0.2 : 1,
      transform: [{ translateX: x0 + (vx * e) / drag }, { translateY: y0 + (vy * e) / drag + (g * T) / drag - (g * e) / (drag * drag) },
        { rotate: `${t.value * spin}deg` }, { scaleY: 0.35 + 0.65 * Math.abs(Math.cos(t.value * spin * 0.05)) }] };
  });
  return <Animated.View style={[styles.piece, { width: size, height: size * 0.55, borderRadius: i % 4 ? 2 : size, backgroundColor: color }, style]} />;
}

/** Two confetti cannons in the bottom corners firing up across the stage. */
function Cannons({ count = 34, power = 2.6 }: { count?: number; power?: number }) {
  const { width: W, height: H } = useWindowDimensions();
  if (useReducedMotion()) return null;
  return <View pointerEvents="none" testID="dream-cheer-cannons" style={[StyleSheet.absoluteFill, styles.top]}>
    {[1, -1].flatMap(dir => Array.from({ length: count }, (_, k) => {
      const i = k + (dir < 0 ? 500 : 0);
      return <Shot key={i} i={i} x0={dir > 0 ? W * 0.04 : W * 0.96} y0={H * 0.94} dir={dir} v={H * power} g={H * 1.4} color={SPARKLE[i % SPARKLE.length]} />;
    }))}
  </View>;
}

/** What the squad shouts, popping in on the beat. Calls `onBeat` once per count. */
function Chant({ start, lines, running, onBeat }: { start: number; lines: [number, string][]; running: boolean; onBeat: (count: number) => void }) {
  const [count, setCount] = useState(-1);
  const beat = useRef(onBeat);
  beat.current = onBeat;
  useEffect(() => {
    if (!running) return;
    let last = -1;
    setCount(-1);
    const iv = setInterval(() => {
      const n = Math.min(COUNTS - 1, Math.floor((Date.now() - start) / BEAT));
      if (n === last) return;
      for (let k = n - last > 2 ? n : last + 1; k <= n; k++) beat.current(k);
      last = n;
      setCount(n);
    }, 30);
    return () => clearInterval(iv);
  }, [start, running]);
  const at = running ? count : COUNTS - 1;
  const line = [...lines].reverse().find(([c]) => c <= at);
  return <View style={styles.chant} testID="dream-cheer-chant">
    {line ? <Pop key={`${start}-${line[0]}`}><GoldTitle size={line[1].length > 14 ? 24 : 34} center testID="dream-cheer-chant-text">{line[1]}</GoldTitle></Pop> : null}
  </View>;
}

function Stat({ label, value, hi, testID }: { label: string; value: string; hi?: boolean; testID?: string }) {
  return <View style={[styles.stat, hi && styles.statHi]}>
    <T w="bold" size={9.5} color={hi ? arena.badgeInk : arena.muted} style={styles.spaced} numberOfLines={1}>{label}</T>
    <T testID={testID} w="heavy" size={20} color={hi ? arena.badgeInk : arena.text}>{value}</T>
  </View>;
}

/** Thin bar under the stage: how far through the 30-second routine. */
function Progress({ clock }: { clock: SharedValue<number> }) {
  const fill = useAnimatedStyle(() => ({ width: `${Math.min(100, clock.value * 100)}%` }));
  return <View style={styles.track} testID="dream-cheer-progress">
    <Animated.View style={[styles.fill, fill]}><LinearGradient colors={[K.trim[0], K.foil[1], arena.gold]} start={{ x: 0, y: 0.5 }} end={{ x: 1, y: 0.5 }} style={StyleSheet.absoluteFill} /></Animated.View>
  </View>;
}

type Phase = "loading" | "dance" | "done";

function DreamCheer({ win, exam, name, onClose }: { win: CheerWin; exam: DreamExam; name: string; onClose: () => void }) {
  const { width: W, height: H } = useWindowDimensions();
  const insets = useSafeAreaInsets();
  const reduced = !!useReducedMotion();
  const [level, setLevel] = useState<CheerLevel>(KOHINOOR);
  const [phase, setPhase] = useState<Phase>("loading");
  const [round, setRound] = useState(0);
  const [start, setStart] = useState(0);
  const [fired, setFired] = useState<number[]>([]);
  const milestones = useRef(new Set<number>());
  const player = useRef<AudioPlayer | null>(null);
  const music = useRef(false);
  const clock = useSharedValue(0), drop = useSharedValue(0), glitter = useSharedValue(0), flutter = useSharedValue(0), sweep = useSharedValue(0), lights = useSharedValue(0);
  const d = win.dreams[0], more = win.dreams.slice(1), score = win.mock.score, over = Math.round(score - d.need);
  const lines = chantsFor(name, d.college, over);
  const sharer = useDreamShare(d, win.mock);

  // Load the Kohinoor art and the track (at most 4 s). Offline, the Rookie Squad that ships inside the app dances instead.
  useEffect(() => {
    let live = true;
    const p = loadTrack(TRACK);
    player.current = p;
    const began = Date.now();
    const art = Promise.race([prefetchSquad(KOHINOOR), new Promise<boolean>(res => setTimeout(() => res(false), LOAD_MS))]);
    const track = new Promise<void>(res => {
      const iv = setInterval(() => { if (!live || !p || p.isLoaded || Date.now() - began > LOAD_MS) { clearInterval(iv); res(); } }, 100);
    });
    Promise.all([art, track]).then(([ok]) => {
      if (!live) return;
      if (!ok) setLevel(1);
      if (reduced) { drop.value = 1; clock.value = (COUNTS - 0.001) / COUNTS; playSfx("win"); setPhase("done"); } else setPhase("dance");
    });
    if (!reduced) {
      const loop = (v: SharedValue<number>, ms: number) => { v.value = withRepeat(withTiming(1, { duration: ms, easing: Easing.linear }), -1, false); };
      loop(glitter, 1900); loop(flutter, 1600); loop(sweep, 2300); loop(lights, 6000);
    }
    return () => {
      live = false;
      [glitter, flutter, sweep, lights, clock, drop].forEach(v => cancelAnimation(v));
      try { p?.pause(); p?.remove(); } catch { /* already released */ }
      player.current = null;
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // The dance: the track, the clock of the routine and the shouts all start together.
  useEffect(() => {
    if (phase !== "dance") return;
    const p = player.current;
    music.current = false;
    try {
      if (p?.isLoaded) {
        p.seekTo(0).catch(() => {}); p.play(); music.current = true;
        // A browser can block sound that starts without a tap: then the effects mark the big moments instead.
        setTimeout(() => { try { music.current = !!p.playing; } catch { music.current = false; } }, 800);
      }
    } catch { /* the effects carry the beat */ }
    milestones.current = new Set();
    setFired([]);
    setStart(Date.now());
    clock.value = 0;
    clock.value = withTiming((COUNTS - 0.001) / COUNTS, { duration: ROUTINE_MS, easing: Easing.linear });
    drop.value = 0;
    drop.value = withDelay(BEAT * 1.5, withSpring(1, { damping: 9, stiffness: 90, mass: 0.9 }));
    const end = setTimeout(() => setPhase("done"), ROUTINE_MS + 300);
    return () => clearTimeout(end);
  }, [phase, round]); // eslint-disable-line react-hooks/exhaustive-deps

  const onBeat = (c: number) => {
    if (Platform.OS !== "web") {
      if (c === 60) Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
      else if (c % 8 === 0) Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});
    }
    if (!music.current && ACCENT[c]) playSfx(ACCENT[c]);
    // Confetti for the start, the drop and the finale, even when the timer skipped a few counts (app in the background).
    const due = [0, 32, 60].filter(m => c >= m && !milestones.current.has(m));
    if (due.length) { due.forEach(m => milestones.current.add(m)); setFired(f => [...f, ...due]); }
  };
  const close = () => { try { player.current?.pause(); } catch { /* released */ } onClose(); };
  const again = () => { setRound(n => n + 1); setPhase("dance"); };

  // The stage, laid out like the Trophy Cabinet's: the banner hangs between the holders' raised fists, the lead dances in front.
  const geo = SQUAD_GEO[level];
  const narrow = W < 360, short = H < 700;
  const SW = Math.min(W - 12, 620), bw = Math.min(SW * 0.56, 500), gl = (SW - bw) / 2, gr = gl + bw;
  const Hh = Math.max(118, Math.min(H * 0.3, 236, SW * 0.58, (H - 560) / 1.1)), Hl = Hh * 0.95;
  const bh = Math.max(86, Math.min(124, bw * 0.42)), medal = Math.min(56, bh * 0.6);
  const ga = geo.a.grip, gb = geo.b.grip, wa = Hh * geo.a.aspect, wb = Hh * geo.b.aspect;
  const top = bh + medal / 2 + Hh * 0.08 + 6 - Math.min(ga[0][1], gb[0][1]) * Hh;
  const SH = top + Hh * 1.1;
  const leftA = gl - ga[0][0] * wa, leftB = gr - (1 - gb[0][0]) * wb;
  // Plain numbers only inside the animation: on a phone it runs on the UI thread, which cannot call app functions.
  const hands = ga.map((g, p) => ((g[1] + gb[p][1]) / 2) * Hh), lift = top + bh;
  const carry = useAnimatedStyle(() => {
    const x = clock.value * COUNTS, n = Math.min(COUNTS - 1, Math.floor(x)), k = x - Math.floor(x), p = HOLD[n];
    const tilt = Math.atan2((gb[p][1] - ga[p][1]) * Hh, bw) * (180 / Math.PI);
    return { opacity: interpolate(drop.value, [0, 0.25], [0, 1], Extrapolation.CLAMP),
      transform: [{ translateY: hands[p] - hands[0] - Math.sin(k * Math.PI) * HOLD_HOP[n] * Hh - (1 - drop.value) * lift }, { rotate: `${tilt + Math.sin(flutter.value * Math.PI * 2) * 0.8}deg` }] };
  });
  const bursts = Array.from({ length: 7 }, (_, i) => ({ x: SW * (0.12 + ((i * 0.37) % 0.78)), y: 18 + ((i * 53) % Math.max(40, top - bh)), size: 70 + ((i * 29) % 50), color: SPARKLE[i % SPARKLE.length], delay: i * 330 }));
  const live = phase !== "loading";

  return <Modal visible transparent animationType="fade" onRequestClose={close} statusBarTranslucent>
    <View testID="dream-cheer" style={styles.flex}>
      <Image source={ARENA} style={StyleSheet.absoluteFill} contentFit="cover" />
      <LinearGradient pointerEvents="none" colors={[arena.scrim, arena.shade, arena.scrim]} locations={[0, 0.5, 1]} style={StyleSheet.absoluteFill} />
      <View pointerEvents="none" style={[StyleSheet.absoluteFill, styles.tint]} />
      {live ? BEAMS.map((c, i) => <Beam key={i} x={W * ((i + 0.5) / BEAMS.length)} color={c} clock={lights} height={H * 0.95} phase={i / BEAMS.length} />) : null}
      <ScrollView style={styles.flex} contentContainerStyle={[styles.root, { paddingTop: insets.top + 8, paddingBottom: insets.bottom + 20 }]} showsVerticalScrollIndicator={false} bounces={false}>
        <View style={styles.topBar}>
          <View testID="dream-cheer-pill" style={styles.pill}>
            <Glyph name="bullseye-arrow" size={14} color={arena.badgeInk} />
            <T w="heavy" size={narrow ? 10 : 11} color={arena.badgeInk} style={narrow ? styles.spacedTight : styles.spaced} numberOfLines={1}>{narrow ? "" : "DREAM UNLOCKED · "}{EXAM_NAME[exam].toUpperCase()}{narrow ? " DREAM ✓" : ""}</T>
          </View>
          {phase !== "done" ? <Press testID="dream-cheer-skip" onPress={close} accessibilityRole="button" accessibilityLabel="Skip celebration" style={styles.skip}>
            <T w="bold" size={13} color={arena.text}>Skip</T>
            <Glyph name="chevron-double-right" size={16} color={arena.text} />
          </Press> : reduced ? null : <Press testID="dream-cheer-again" onPress={again} accessibilityRole="button" accessibilityLabel="Celebration phir se dekho" style={styles.skip}>
            <Glyph name="replay" size={16} color={arena.text} />
            <T w="bold" size={13} color={arena.text}> Phir se</T>
          </Press>}
        </View>

        {live ? <Chant start={start} lines={lines} running={phase === "dance"} onBeat={onBeat} />
          : <View style={styles.chant}><T testID="dream-cheer-loading" w="bold" size={14} color={arena.muted} style={styles.center}>Kohinoor Legends stage par aa rahi hain…</T></View>}

        <View testID="dream-cheer-stage" style={{ width: SW, height: SH, alignSelf: "center" }}>
          {live ? <>
            {bursts.map((b, i) => <Burst key={i} {...b} />)}
            <Dancer testID="dream-cheer-lead" frames={squadFrames(level, "c")} height={Hl} aspect={geo.c.aspect} clock={clock} seq={LEAD} hops={LEAD_HOP} spins={LEAD_SPIN}
              style={{ left: SW / 2 - (Hl * geo.c.aspect) / 2, top: SH - Hl }} />
            <Animated.View style={[styles.carry, { left: gl - 4, top: top + hands[0] - bh, width: bw + 8 }, carry]}>
              <Pole side="left" level={level} height={bh + 30} />
              <Pole side="right" level={level} height={bh + 30} />
              <View style={styles.bannerAt}>
                <CheerBanner w={bw} h={bh} top={medal / 2} level={level} name={d.college} word="DREAM UNLOCKED!" clock={clock} count={COUNTS} glitter={glitter} wave={flutter} sweep={sweep} />
              </View>
              <View style={[styles.medal, { width: medal, height: medal, borderRadius: medal / 2, top: -medal / 2, left: bw / 2 + 4 - medal / 2 }]}>
                <LinearGradient colors={[K.trim[0], K.trim[1], K.trim[2]]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
                <Diamond width={medal * 0.64} tint={gemColors.kohinoor} sparkle />
              </View>
            </Animated.View>
            <Dancer testID="dream-cheer-holder-1" frames={squadFrames(level, "a")} height={Hh} aspect={geo.a.aspect} clock={clock} seq={HOLD} hops={HOLD_HOP} style={{ left: leftA, top }} />
            <Dancer testID="dream-cheer-holder-2" frames={squadFrames(level, "b")} height={Hh} aspect={geo.b.aspect} clock={clock} seq={HOLD} hops={HOLD_HOP} flip style={{ left: leftB, top }} />
            <Twinkles spots={[[6, 30, 16], [94, 26, 14], [50, 2, 12], [14, 70, 10], [86, 66, 12], [30, 12, 10], [70, 14, 10]]} color={gemColors.kohinoor} />
          </> : null}
        </View>

        <Pop delay={300}>
          <View testID="dream-cheer-card" style={styles.card}>
            <View style={styles.cardRow}>
              <View style={styles.check}><Glyph name="check-bold" size={18} color={arena.badgeInk} /></View>
              <View style={styles.flex}>
                <T testID="dream-cheer-college" w="heavy" size={16} color={arena.text} numberOfLines={2}>{d.college}</T>
                <T size={12.5} color={arena.muted} numberOfLines={2}>{d.branch}</T>
              </View>
            </View>
            <View style={styles.stats}>
              <Stat label="TARGET" value={`${d.need}`} testID="dream-cheer-need" />
              <Stat label={narrow ? "SCORE" : "TUMHARA SCORE"} value={`${score}`} hi testID="dream-cheer-score" />
              <Stat label="UPAR" value={over > 0 ? `+${over}` : "0"} testID="dream-cheer-over" />
            </View>
            {more.length ? <T testID="dream-cheer-more" w="bold" size={12.5} color={arena.gold}>
              + {more.length} aur dream unlock: {more.map(x => x.college).join(", ")}
            </T> : null}
            {short ? null : <T size={11} color={arena.faint} numberOfLines={2}>{win.mock.title} · {score}/{FULL[exam]} · 2026 cutoff par estimate, guarantee nahi.</T>}
          </View>
        </Pop>

        {/* One fixed-height slot, so the stage does not jump when the buttons replace the progress bar. */}
        <View style={styles.foot}>
          {phase === "done" ? <View style={styles.buttons}>
            <RaisedButton testID="dream-cheer-share" glyph="whatsapp" height={56} streak label="SHARE" sub="Dost ko dikhao" busy={sharer.busy} onPress={sharer.share} style={styles.flex} />
            <RaisedButton testID="dream-cheer-continue" tone="wine" glyph="arrow-right" height={56} label="Continue" sub="Agla dream!" onPress={close} style={styles.flex} />
          </View> : live ? <Progress clock={clock} /> : null}
        </View>
        {sharer.note ? <T testID="dream-cheer-share-note" w="bold" size={12} color={arena.aqua} style={styles.center}>{sharer.note}</T> : null}
      </ScrollView>
      {sharer.card}
      {fired.includes(0) ? <Cannons key={`a${round}`} count={26} power={2.2} /> : null}
      {fired.includes(32) ? <Confetti key={`b${round}`} count={64} colors={SPARKLE} /> : null}
      {fired.includes(60) ? <><Cannons key={`c${round}`} count={40} /><Confetti key={`d${round}`} count={80} colors={SPARKLE} /></> : null}
    </View>
  </Modal>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, center: { textAlign: "center" }, spaced: { letterSpacing: 1.4 }, spacedTight: { letterSpacing: 0.6 },
  foot: { minHeight: 63, justifyContent: "center" },
  tint: { backgroundColor: `${gemColors.kohinoor}1F` },
  root: { flexGrow: 1, justifyContent: "center", paddingHorizontal: 6, gap: 10 },
  topBar: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: 8, paddingHorizontal: 10, minHeight: 44 },
  pill: { flexDirection: "row", alignItems: "center", gap: 6, flexShrink: 1, paddingHorizontal: 12, height: 30, borderRadius: 15, backgroundColor: arena.gold, borderWidth: 1.5, borderColor: arena.goldDeep },
  skip: { flexDirection: "row", alignItems: "center", gap: 2, minHeight: 44, minWidth: 64, paddingHorizontal: 14, borderRadius: 22, justifyContent: "center",
    backgroundColor: arena.shade, borderWidth: 1, borderColor: arena.gloss },
  chant: { minHeight: 64, alignItems: "center", justifyContent: "center", paddingHorizontal: 16 },
  carry: { position: "absolute" },
  bannerAt: { marginHorizontal: 4 },
  medal: { position: "absolute", overflow: "hidden", alignItems: "center", justifyContent: "center", borderWidth: 2, borderColor: K.trim[0] },
  card: { alignSelf: "center", width: "100%", maxWidth: 460, gap: 10, padding: 14, marginHorizontal: 10, borderRadius: 20, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: K.trim[1] },
  cardRow: { flexDirection: "row", alignItems: "center", gap: 10 },
  check: { width: 34, height: 34, borderRadius: 17, alignItems: "center", justifyContent: "center", backgroundColor: arena.gold },
  stats: { flexDirection: "row", gap: 8 },
  stat: { flex: 1, minWidth: 0, alignItems: "center", gap: 2, paddingVertical: 8, borderRadius: 14, backgroundColor: arena.panelHi, borderWidth: 1, borderColor: arena.rim },
  statHi: { backgroundColor: arena.gold, borderColor: arena.goldDeep },
  track: { alignSelf: "center", width: "80%", maxWidth: 360, height: 6, borderRadius: 3, overflow: "hidden", backgroundColor: arena.shade },
  fill: { height: "100%", borderRadius: 3, overflow: "hidden" },
  buttons: { alignSelf: "center", flexDirection: "row", gap: 10, maxWidth: 460, width: "100%", paddingHorizontal: 10 },
  piece: { position: "absolute", left: 0, top: 0 },
  top: { zIndex: 60 },
});
