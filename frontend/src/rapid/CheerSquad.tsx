import React, { useEffect, useState } from "react";
import { Modal, Platform, ScrollView, StyleSheet, View, useWindowDimensions } from "react-native";
import * as Haptics from "expo-haptics";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import Animated, { Easing, SharedValue, cancelAnimation, useAnimatedStyle, useReducedMotion, useSharedValue, withRepeat, withTiming } from "react-native-reanimated";
import Svg, { Circle, Defs, LinearGradient as Grad, Path, Stop } from "react-native-svg";
import { T } from "@/src/components/ui";
import { Avatar } from "@/src/components/Entry";
import { playSfx } from "@/src/sfx";
import { arena, fx } from "@/src/theme";
import { GoldTitle, RaisedButton } from "./arena";
import { Confetti, Pop, Twinkles } from "./juice";
import { Crown } from "./parts";
import { CrownArt } from "./CrownArt";

const ARENA = require("../../assets/arena/bg_colosseum.webp");
const SQUAD = {
  a: [require("../../assets/arena/cheer_a1.webp"), require("../../assets/arena/cheer_a2.webp")],
  b: [require("../../assets/arena/cheer_b1.webp"), require("../../assets/arena/cheer_b2.webp")],
};
const ASPECT = 0.71; // sprite width / height
const BAR = 860; // one jump + one sway, in ms
const BEAM_W = 220;

/**
 * One cheerleader: two poses (pom-poms up in a jump, pom-poms at the hips in a sway) swapped on the beat, with the hop,
 * the sway and a floor shadow that shrinks while she is in the air. `phase` 0.5 dances the opposite move.
 */
function Dancer({ who, height, clock, phase = 0, flip, testID }: { who: "a" | "b"; height: number; clock: SharedValue<number>; phase?: number; flip?: boolean; testID?: string }) {
  const w = height * ASPECT, dir = flip ? -1 : 1;
  const body = useAnimatedStyle(() => {
    const t = (clock.value + phase) % 1, up = t < 0.5, k = up ? t / 0.5 : (t - 0.5) / 0.5;
    const hop = up ? Math.sin(k * Math.PI) : 0, sway = up ? 0 : Math.sin(k * Math.PI);
    return { transform: [{ translateY: -hop * height * 0.13 }, { translateX: sway * w * 0.07 * dir }, { rotate: `${(up ? hop * 4 : -sway * 8) * dir}deg` },
      { scaleX: dir }, { scaleY: up ? 1 + hop * 0.03 : 1 - sway * 0.025 }] };
  });
  const jump = useAnimatedStyle(() => ({ opacity: (clock.value + phase) % 1 < 0.5 ? 1 : 0 }));
  const hips = useAnimatedStyle(() => ({ opacity: (clock.value + phase) % 1 < 0.5 ? 0 : 1 }));
  const shadow = useAnimatedStyle(() => {
    const t = (clock.value + phase) % 1, hop = t < 0.5 ? Math.sin((t / 0.5) * Math.PI) : 0;
    return { opacity: 0.32 - hop * 0.18, transform: [{ scaleX: 1 - hop * 0.4 }] };
  });
  return <View testID={testID} style={{ width: w, height }}>
    <Animated.View style={[styles.shadow, { width: w * 0.44, left: w * 0.28, height: height * 0.035, borderRadius: w }, shadow]} />
    <Animated.View style={[StyleSheet.absoluteFill, body]}>
      <Animated.View style={[StyleSheet.absoluteFill, jump]}><Image source={SQUAD[who][0]} style={StyleSheet.absoluteFill} contentFit="contain" /></Animated.View>
      <Animated.View style={[StyleSheet.absoluteFill, hips]}><Image source={SQUAD[who][1]} style={StyleSheet.absoluteFill} contentFit="contain" /></Animated.View>
    </Animated.View>
  </View>;
}

/** A sweeping stage light from the top corner: a soft cone that fades out towards the floor. */
function Beam({ left, clock, height }: { left: boolean; clock: SharedValue<number>; height: number }) {
  const style = useAnimatedStyle(() => ({ transform: [{ rotate: `${(left ? -1 : 1) * (14 + Math.sin(clock.value * Math.PI * 2) * 12)}deg` }] }));
  return <Animated.View pointerEvents="none" style={[styles.beam, { height, [left ? "left" : "right"]: -100, transformOrigin: "top center" }, style]}>
    <Svg width={BEAM_W} height={height}>
      <Defs><Grad id="cone" x1="0" y1="0" x2="0" y2="1"><Stop offset="0" stopColor={arena.gold} stopOpacity={0.5} /><Stop offset="0.6" stopColor={arena.gold} stopOpacity={0.12} /><Stop offset="1" stopColor={arena.gold} stopOpacity={0} /></Grad></Defs>
      <Path d={`M${BEAM_W / 2 - 10} 0 L${BEAM_W / 2 + 10} 0 L${BEAM_W} ${height} L0 ${height} Z`} fill="url(#cone)" />
    </Svg>
  </Animated.View>;
}

/** The light bulbs round the board: two sets that blink in turn, so the lights look like they chase each other. */
function Bulbs({ w, h, set, blink }: { w: number; h: number; set: 0 | 1; blink: SharedValue<number> }) {
  const style = useAnimatedStyle(() => ({ opacity: set ? 1 - blink.value * 0.75 : 0.25 + blink.value * 0.75 }));
  const step = 18, pts: [number, number][] = [];
  for (let x = 10; x <= w - 10; x += step) pts.push([x, 6], [x, h - 6]);
  for (let y = 6 + step; y <= h - 6 - step / 2; y += step) pts.push([6, y], [w - 6, y]);
  return <Animated.View pointerEvents="none" style={[StyleSheet.absoluteFill, style]}>
    <Svg width={w} height={h}>{pts.filter((_, i) => i % 2 === set).map(([x, y]) => <Circle key={`${x}-${y}`} cx={x} cy={y} r={3.6} fill={fx.ember} stroke={fx.white} strokeWidth={1.2} />)}</Svg>
  </Animated.View>;
}

/** The hanging Congratulations board with the champion on it, swinging gently on its gold chains. */
function Board({ width, name, avatar, frame, crown, blink, swing }: { width: number; name: string; avatar?: string | null; frame?: string | null; crown: { won: number; real: number }; blink: SharedValue<number>; swing: SharedValue<number> }) {
  const h = Math.round(width * 0.6), gold = crown.real > 0;
  const sway = useAnimatedStyle(() => ({ transform: [{ rotate: `${Math.sin(swing.value * Math.PI * 2) * 2.2}deg` }] }));
  return <Animated.View testID="cheer-board" style={[{ width, transformOrigin: "top center" }, sway]}>
    <View style={styles.chains}><View style={styles.chain} /><View style={styles.chain} /></View>
    <View style={[styles.board, { height: h }]}>
      <LinearGradient colors={[arena.panelHi, arena.panel, arena.panelEdge]} style={StyleSheet.absoluteFill} />
      <Bulbs w={width} h={h} set={0} blink={blink} />
      <Bulbs w={width} h={h} set={1} blink={blink} />
      <View style={styles.boardBody}>
        <GoldTitle size={Math.min(30, width * 0.085)} center testID="cheer-board-title">CONGRATULATIONS</GoldTitle>
        <View style={styles.who}>
          <View><Avatar icon={avatar} frame={frame} size={Math.min(64, width * 0.17)} /><View style={styles.crownOn}><CrownArt size={34} gold={gold} /></View></View>
          <View style={styles.flex}>
            <T testID="cheer-board-name" w="heavy" size={Math.min(22, width * 0.06)} color={arena.text} numberOfLines={1}>{name}</T>
            <View style={styles.inline}><Crown c={crown} size="lg" /><T w="heavy" size={12} color={gold ? arena.gold : fx.smoke} numberOfLines={1}>{crown.won} CUP{crown.won === 1 ? "" : "S"} WON</T></View>
          </View>
        </View>
        <T w="heavy" size={12} color={arena.aqua} style={styles.spaced} numberOfLines={1}>KNOCKOUT CUP CHAMPION</T>
      </View>
    </View>
  </Animated.View>;
}

/**
 * The cheer squad in a champion's trophy cabinet: stage lights sweep the Colosseum, the Congratulations board swings
 * on its chains with the champion's name, and the cheerleaders dance on the beat while confetti rains. Cheer again
 * replays it. Scrolls on short phones so the buttons are always reachable.
 */
export function CheerSquad({ visible, name, avatar, frame, crown, onClose }: { visible: boolean; name: string; avatar?: string | null; frame?: string | null; crown: { won: number; real: number }; onClose: () => void }) {
  const { width: W, height: H } = useWindowDimensions();
  const reduced = !!useReducedMotion();
  const clock = useSharedValue(0), blink = useSharedValue(0), swing = useSharedValue(0), lights = useSharedValue(0);
  const [round, setRound] = useState(0);
  useEffect(() => {
    if (!visible || reduced) return;
    clock.value = 0;
    clock.value = withRepeat(withTiming(1, { duration: BAR, easing: Easing.linear }), -1, false);
    blink.value = withRepeat(withTiming(1, { duration: 260, easing: Easing.linear }), -1, true);
    swing.value = withRepeat(withTiming(1, { duration: 3400, easing: Easing.linear }), -1, false);
    lights.value = withRepeat(withTiming(1, { duration: 5200, easing: Easing.linear }), -1, false);
    return () => { [clock, blink, swing, lights].forEach((v) => cancelAnimation(v)); };
  }, [visible, reduced]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!visible) return;
    playSfx(round ? "combo" : "win");
    if (Platform.OS !== "web") Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
  }, [visible, round]);

  const boardW = Math.min(W - 32, 420);
  const wide = W >= 640; // tablets: a back row joins in
  // Short phones: the dancers give up height so the board, the line and both buttons fit without scrolling.
  const dancer = Math.min(H * 0.36, ((wide ? Math.min(W, 900) * 0.5 : W) - 16) / 2 / ASPECT, 340, Math.max(160, H - boardW * 0.6 - 300));
  return <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose} statusBarTranslucent>
    <View testID="cheer-squad" style={styles.flex}>
      <Image source={ARENA} style={StyleSheet.absoluteFill} contentFit="cover" />
      <LinearGradient pointerEvents="none" colors={[arena.scrim, arena.shade, arena.scrim]} locations={[0, 0.5, 1]} style={StyleSheet.absoluteFill} />
      <Beam left clock={lights} height={H * 0.95} />
      <Beam left={false} clock={lights} height={H * 0.95} />
      <ScrollView style={styles.flex} contentContainerStyle={styles.root} showsVerticalScrollIndicator={false} bounces={false}>
        <Pop delay={100} style={styles.center}><Board width={boardW} name={name} avatar={avatar} frame={frame} crown={crown} blink={blink} swing={swing} /></Pop>
        <View style={[styles.stage, { height: dancer * (wide ? 1.12 : 1.04) }]}>
          {wide ? <View style={[styles.backRow, { bottom: dancer * 0.16 }]}>
            <Dancer who="b" height={dancer * 0.78} clock={clock} phase={0.5} flip testID="cheer-dancer-back-1" />
            <Dancer who="a" height={dancer * 0.78} clock={clock} phase={0.5} flip testID="cheer-dancer-back-2" />
          </View> : null}
          <View style={styles.frontRow}>
            <Dancer who="a" height={dancer} clock={clock} testID="cheer-dancer-1" />
            <Dancer who="b" height={dancer} clock={clock} phase={0.5} testID="cheer-dancer-2" />
          </View>
          <Twinkles spots={[[8, 12, 16], [92, 10, 14], [50, 4, 12], [18, 58, 10], [84, 52, 12]]} />
        </View>
        <Pop delay={500}><T testID="cheer-line" w="bold" size={14} color={arena.text} style={styles.centerText}>The cheer squad is dancing for {name}! {crown.won > 1 ? `${crown.won} cups won and counting.` : "A Knockout Cup champion."}</T></Pop>
        <View style={styles.buttons}>
          <RaisedButton testID="cheer-again" glyph="party-popper" height={60} streak label="CHEER AGAIN" sub="Louder this time!" onPress={() => setRound((n) => n + 1)} />
          <RaisedButton testID="cheer-close" tone="wine" label="Continue" onPress={onClose} />
        </View>
      </ScrollView>
      <Confetti key={round} count={56} />
    </View>
  </Modal>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, center: { alignSelf: "center" }, centerText: { textAlign: "center" }, spaced: { letterSpacing: 2 },
  inline: { flexDirection: "row", alignItems: "center", gap: 6 },
  root: { flexGrow: 1, justifyContent: "center", paddingHorizontal: 16, paddingTop: 44, paddingBottom: 28, gap: 10 },
  beam: { position: "absolute", top: -10, width: BEAM_W },
  chains: { flexDirection: "row", justifyContent: "space-between", paddingHorizontal: "22%", height: 22, marginTop: -22 },
  chain: { width: 3, height: 22, borderRadius: 2, backgroundColor: arena.goldDeep, borderLeftWidth: 1, borderLeftColor: arena.gold },
  board: { borderRadius: 22, borderWidth: 3, borderColor: arena.gold, borderBottomWidth: 6, borderBottomColor: arena.goldDeep, overflow: "hidden" },
  boardBody: { flex: 1, alignItems: "center", justifyContent: "center", gap: 8, paddingHorizontal: 24, paddingVertical: 16 },
  who: { flexDirection: "row", alignItems: "center", gap: 12, alignSelf: "stretch", justifyContent: "center" },
  crownOn: { position: "absolute", top: -22, left: 0, right: 0, alignItems: "center" },
  stage: { alignSelf: "stretch", justifyContent: "flex-end" },
  frontRow: { flexDirection: "row", justifyContent: "space-around", alignItems: "flex-end" },
  backRow: { position: "absolute", left: "18%", right: "18%", flexDirection: "row", justifyContent: "space-between", opacity: 0.85 },
  shadow: { position: "absolute", bottom: 0, backgroundColor: arena.black },
  buttons: { alignSelf: "stretch", gap: 10, maxWidth: 460, width: "100%", marginHorizontal: "auto" },
});
